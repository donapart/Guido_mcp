#!/usr/bin/env python3
"""
MCP Bridge Server - Dynamisches Tool-Loading für VS Code Copilot Chat

Dieser Server löst das "zu viele Tools" Problem durch:
1. Nur Meta-Tools werden initial geladen (wenige Tools)
2. Server werden ON-DEMAND verbunden wenn benötigt
3. Tools werden dynamisch aktiviert/deaktiviert

VS Code sieht nur ~15 Tools statt 400+!
"""

import asyncio
import json
import os
import sys
import time
try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover
    psutil = None
from pathlib import Path
from typing import Any
from contextlib import AsyncExitStack
from datetime import datetime

# Startzeit für Uptime
START_TIME = time.time()

# Pfade
AGENT_DIR = Path(__file__).parent.parent / "agent"
SERVERS_DIR = Path(__file__).parent.parent / "servers"

# MCP SDK
from mcp.server.fastmcp import FastMCP
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

# Server initialisieren mit LAZY Loading
mcp = FastMCP(
    "Guido MCP Bridge",
    instructions="""
    🚀 Guido MCP Bridge - Dynamischer Tool-Aggregator
    
    Dieser Server lädt Tools ON-DEMAND um VS Code nicht zu überlasten.
    
    📋 VERFÜGBARE KOMMANDOS:
    
    1. list_servers() - Zeigt alle verfügbaren MCP-Server
    2. activate_server(name) - Aktiviert einen Server und seine Tools
    3. deactivate_server(name) - Deaktiviert einen Server
    4. get_active_tools() - Zeigt aktuell aktive Tools
    5. execute(server, tool, args) - Führt ein Tool aus
    
    🔧 SCHNELLZUGRIFF (immer verfügbar):
    - read_file, write_file, list_directory
    - git_status, git_log, git_diff
    - search_files, calculate
    
    💡 BEISPIELE:
    - "Aktiviere den docker Server" → activate_server("docker")
    - "Zeig mir alle Server" → list_servers()
    - "Lies die package.json" → read_file("package.json")
    """
)

# ============================================================
# Globale State-Verwaltung
# ============================================================

class BridgeState:
    """Verwaltet den Zustand aller Server und Tools"""
    
    def __init__(self):
        self.exit_stack: AsyncExitStack | None = None
        self.server_configs: dict[str, dict] = {}  # Alle verfügbaren Server-Configs
        self.connected_servers: dict[str, ClientSession] = {}  # Aktiv verbundene
        self.tool_registry: dict[str, tuple[str, Any]] = {}  # tool_name -> (server, def)
        self.server_tools: dict[str, list[str]] = {}  # server -> [tool_names]
        self.initialized = False
        
    async def initialize(self):
        """Lädt Konfiguration OHNE Server zu verbinden"""
        if self.initialized:
            return
            
        self.exit_stack = AsyncExitStack()
        await self.exit_stack.__aenter__()
        
        # Konfiguration laden
        self.server_configs = self._load_config()
        self.initialized = True
        
        print(f"[Bridge] 📦 {len(self.server_configs)} Server verfügbar (lazy loading)", file=sys.stderr)
        
        # NUR Basis-Server vorab verbinden (filesystem, git für Grundfunktionen)
        auto_connect = os.environ.get("MCP_AUTO_CONNECT", "filesystem,git,demo").split(",")
        for name in auto_connect:
            name = name.strip()
            if name and name in self.server_configs:
                await self.connect_server(name)
    
    def _load_config(self) -> dict:
        """Lädt Server-Konfiguration aus mcp-servers.json"""
        config_path = AGENT_DIR / "mcp-servers.json"
        if not config_path.exists():
            print(f"[Bridge] ⚠️ {config_path} nicht gefunden", file=sys.stderr)
            return {}
        
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return data.get("mcpServers", data.get("servers", {}))
    
    async def connect_server(self, name: str) -> tuple[bool, str]:
        """Verbindet einen Server ON-DEMAND"""
        if name in self.connected_servers:
            return True, f"Server '{name}' ist bereits verbunden"
        
        if name not in self.server_configs:
            return False, f"Server '{name}' nicht in Konfiguration gefunden"
        
        config = self.server_configs[name]
        
        try:
            command = config.get("command", "python")
            args = list(config.get("args", []))
            env = {**os.environ, **config.get("env", {})}
            
            # Server-Pfad anpassen falls relativ
            if args and not Path(args[0]).is_absolute():
                server_script = SERVERS_DIR / args[0]
                if server_script.exists():
                    args[0] = str(server_script)
            
            params = StdioServerParameters(command=command, args=args, env=env)
            
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            
            await session.initialize()
            self.connected_servers[name] = session
            
            # Tools registrieren
            tools_response = await session.list_tools()
            self.server_tools[name] = []
            
            for tool in tools_response.tools:
                prefixed_name = f"{name}_{tool.name}"
                self.tool_registry[prefixed_name] = (name, tool)
                self.server_tools[name].append(prefixed_name)
            
            tool_count = len(tools_response.tools)
            print(f"[Bridge] ✅ {name}: {tool_count} Tools aktiviert", file=sys.stderr)
            return True, f"Server '{name}' verbunden mit {tool_count} Tools"
            
        except Exception as e:
            print(f"[Bridge] ❌ {name}: {e}", file=sys.stderr)
            return False, f"Fehler beim Verbinden von '{name}': {str(e)}"
    
    async def disconnect_server(self, name: str) -> tuple[bool, str]:
        """Trennt einen Server und entfernt seine Tools"""
        if name not in self.connected_servers:
            return False, f"Server '{name}' ist nicht verbunden"
        
        # Tools entfernen
        if name in self.server_tools:
            for tool_name in self.server_tools[name]:
                self.tool_registry.pop(tool_name, None)
            del self.server_tools[name]
        
        # Session entfernen (wird durch exit_stack geschlossen)
        del self.connected_servers[name]
        
        print(f"[Bridge] 🔌 {name}: Getrennt", file=sys.stderr)
        return True, f"Server '{name}' getrennt"
    
    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Ruft ein Tool auf, verbindet Server falls nötig"""
        
        # Prüfen ob Tool bekannt ist
        if tool_name in self.tool_registry:
            server_name, tool_def = self.tool_registry[tool_name]
        else:
            # Versuche Server aus Tool-Name zu extrahieren
            parts = tool_name.split("_", 1)
            if len(parts) == 2:
                server_name = parts[0]
                if server_name in self.server_configs and server_name not in self.connected_servers:
                    # Auto-Connect!
                    success, msg = await self.connect_server(server_name)
                    if success and tool_name in self.tool_registry:
                        server_name, tool_def = self.tool_registry[tool_name]
                    else:
                        return f"Tool '{tool_name}' nicht gefunden nach Auto-Connect"
                else:
                    return f"Tool '{tool_name}' nicht gefunden"
            else:
                return f"Tool '{tool_name}' nicht gefunden"
        
        session = self.connected_servers.get(server_name)
        if not session:
            return f"Server '{server_name}' nicht verbunden"
        
        try:
            # Original-Toolname ohne Prefix
            original_name = tool_name.replace(f"{server_name}_", "", 1)
            result = await session.call_tool(original_name, arguments)
            
            if result.content:
                texts = []
                for item in result.content:
                    if hasattr(item, "text"):
                        texts.append(item.text)
                    elif hasattr(item, "data"):
                        texts.append(f"[Binary: {len(item.data)} bytes]")
                return "\n".join(texts) if texts else "✓ Erfolgreich"
            return "✓ Erfolgreich (keine Ausgabe)"
            
        except Exception as e:
            return f"❌ Fehler: {e}"

    async def shutdown(self) -> None:
        """Schließt alle Ressourcen sauber (Sessions/Transports via AsyncExitStack)."""
        if not self.initialized:
            return

        # Registries leeren (die eigentlichen Ressourcen werden über exit_stack geschlossen)
        self.connected_servers.clear()
        self.tool_registry.clear()
        self.server_tools.clear()

        if self.exit_stack is not None:
            try:
                await self.exit_stack.aclose()
            finally:
                self.exit_stack = None

        # Konfig kann beim nächsten Zugriff neu geladen werden
        self.server_configs = {}
        self.initialized = False


# Globaler State
state = BridgeState()


# ============================================================
# META-TOOLS (Diese sieht VS Code)
# ============================================================

@mcp.tool()
async def list_servers() -> str:
    """
    📋 Zeigt alle verfügbaren MCP-Server und ihren Status.
    
    Returns:
        Liste aller Server mit Verbindungsstatus
    """
    await state.initialize()
    
    lines = ["# 🔌 Verfügbare MCP-Server\n"]
    
    # Kategorisieren
    categories = {
        "Dateisystem": ["filesystem", "git"],
        "Entwicklung": ["project-manager", "flutter", "docker", "docker-remote"],
        "AI/LLM": ["ollama"],
        "Web": ["web-search", "web-scraping", "github"],
        "Kommunikation": ["email", "ssh"],
        "Datenbanken": ["database"],
        "Hosting": ["ionos"],
        "Sonstige": ["demo"]
    }
    
    for category, servers in categories.items():
        available = [s for s in servers if s in state.server_configs]
        if not available:
            continue
            
        lines.append(f"\n## {category}")
        for name in available:
            status = "🟢 AKTIV" if name in state.connected_servers else "⚪ verfügbar"
            tool_count = len(state.server_tools.get(name, []))
            info = f" ({tool_count} Tools)" if tool_count else ""
            lines.append(f"- **{name}**: {status}{info}")
    
    lines.append(f"\n---\n💡 Nutze `activate_server('name')` zum Aktivieren")
    lines.append(f"📊 Aktiv: {len(state.connected_servers)}/{len(state.server_configs)} Server")
    
    return "\n".join(lines)


@mcp.tool()
async def get_system_status() -> str:
    """
    🏥 Zeigt Systemstatus, Ressourcenverbrauch und Uptime.
    """
    uptime_seconds = int(time.time() - START_TIME)

    # Formatierung der Uptime
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"

    if psutil is None:
        return "\n".join(
            [
                "# 🏥 Systemstatus Bridge Server",
                f"- **Uptime**: {uptime_str}",
                "- **CPU**: (psutil nicht installiert)",
                "- **RAM**: (psutil nicht installiert)",
                f"- **Python**: {sys.version.split()[0]}",
                f"- **Aktive Server**: {len(state.connected_servers)}",
                f"- **Registrierte Tools**: {len(state.tool_registry)}",
                f"- **PID**: {os.getpid()}",
            ]
        )

    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    
    status = [
        "# 🏥 Systemstatus Bridge Server",
        f"- **Uptime**: {uptime_str}",
        f"- **CPU**: {psutil.cpu_percent()}%",
        f"- **RAM**: {mem_info.rss / 1024 / 1024:.1f} MB",
        f"- **Python**: {sys.version.split()[0]}",
        f"- **Aktive Server**: {len(state.connected_servers)}",
        f"- **Registrierte Tools**: {len(state.tool_registry)}",
        f"- **PID**: {os.getpid()}"
    ]
    
    return "\n".join(status)


@mcp.tool()
async def check_env(server: str | None = None) -> str:
    """
    🔐 Prüft Environment-Variablen für typische Server-Konfigurationen.

    Gibt nur an, ob Variablen gesetzt sind (keine Werte).

    Args:
        server: Optionaler Server-Name (z.B. "github", "email", "ssh"). Wenn leer, werden alle geprüft.
    """

    def is_set(key: str) -> bool:
        val = os.environ.get(key)
        return bool(val and str(val).strip())

    def keys_with_prefix(prefix: str) -> list[str]:
        return sorted([k for k in os.environ.keys() if k.startswith(prefix)])

    checks: dict[str, dict[str, Any]] = {
        "llm": {
            "summary": "Mindestens ein Provider-Key ist nötig.",
            "any_of": [
                ["OPENAI_API_KEY"],
                ["ANTHROPIC_API_KEY"],
            ],
            "optional": ["LLM_MODEL"],
        },
        "github": {
            "required": ["GITHUB_TOKEN"],
        },
        "ionos": {
            "required": ["IONOS_API_KEY"],
        },
        "docker-remote": {
            "optional": ["DOCKER_REMOTE_HOST", "DOCKER_TIMEOUT"],
        },
        "ollama": {
            "optional": ["OLLAMA_HOST", "OLLAMA_DEFAULT_MODEL", "OLLAMA_TIMEOUT"],
        },
        "email": {
            "groups": [
                {
                    "name": "SMTP (Senden)",
                    "required": ["SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"],
                    "optional": ["SMTP_PORT", "SMTP_USE_TLS"],
                },
                {
                    "name": "IMAP (Lesen)",
                    "required": ["IMAP_HOST", "IMAP_USER", "IMAP_PASSWORD"],
                    "optional": ["IMAP_PORT", "IMAP_USE_SSL"],
                },
            ]
        },
        "ssh": {
            "summary": "Für jeden Host: SSH_HOST_<NAME>=user@host:port und entweder SSH_PASSWORD_<NAME> oder SSH_KEY_<NAME>.",
            "prefixes": ["SSH_HOST_", "SSH_PASSWORD_", "SSH_KEY_"],
        },
    }

    target = server.strip().lower() if server else None
    if target and target not in checks:
        known = ", ".join(sorted(checks.keys()))
        return f"❌ Unbekannter Check '{target}'. Verfügbar: {known}"

    lines: list[str] = ["# 🔐 Environment-Check"]
    lines.append("(Es werden **keine Werte** ausgegeben – nur ob Variablen gesetzt sind.)\n")

    to_run = [target] if target else list(checks.keys())

    for name in to_run:
        cfg = checks[name]
        lines.append(f"## {name}")
        if cfg.get("summary"):
            lines.append(f"- Hinweis: {cfg['summary']}")

        # any_of (z.B. LLM Provider)
        if "any_of" in cfg:
            satisfied = False
            for option in cfg["any_of"]:
                if all(is_set(k) for k in option):
                    satisfied = True
                    break
            lines.append(f"- Required (any-of): {'✅ ok' if satisfied else '❌ fehlt'}")
            if not satisfied:
                opts = [" + ".join(o) for o in cfg["any_of"]]
                lines.append(f"  - Setze mindestens eins von: {', '.join(opts)}")

        # required
        required = cfg.get("required", [])
        if required:
            missing = [k for k in required if not is_set(k)]
            lines.append(f"- Required: {'✅ ok' if not missing else '❌ fehlt'}")
            for k in required:
                lines.append(f"  - {k}: {'✅ gesetzt' if is_set(k) else '❌ fehlt'}")

        # groups (email)
        for group in cfg.get("groups", []) or []:
            lines.append(f"- {group['name']}")
            req = group.get("required", [])
            opt = group.get("optional", [])
            for k in req:
                lines.append(f"  - {k}: {'✅ gesetzt' if is_set(k) else '❌ fehlt'}")
            for k in opt:
                lines.append(f"  - {k} (optional): {'✅ gesetzt' if is_set(k) else '—'}")

        # optional
        optional = cfg.get("optional", [])
        if optional:
            lines.append("- Optional:")
            for k in optional:
                lines.append(f"  - {k}: {'✅ gesetzt' if is_set(k) else '—'}")

        # prefixes (ssh)
        prefixes = cfg.get("prefixes", [])
        if prefixes:
            lines.append("- Gefundene Prefix-Variablen:")
            for pfx in prefixes:
                found = keys_with_prefix(pfx)
                if found:
                    lines.append(f"  - {pfx}: ✅ {len(found)} gefunden")
                    for k in found[:20]:
                        lines.append(f"    - {k}")
                    if len(found) > 20:
                        lines.append(f"    - … und {len(found) - 20} weitere")
                else:
                    lines.append(f"  - {pfx}: ❌ keine")

        lines.append("")

    lines.append("---")
    lines.append("💡 Tipp: Keys in `mcp-agent-workbench/agent/.env` pflegen (Vorlage: `agent/.env.example`).")
    lines.append("⚠️ Wenn ein Key jemals im Klartext im Workspace stand: bitte rotieren/revoken.")
    return "\n".join(lines)


@mcp.tool()
async def shutdown_bridge() -> str:
    """🛑 Fährt die Bridge sauber herunter (schließt Sessions/Transports)."""
    await state.shutdown()
    return "✅ Bridge Ressourcen geschlossen. Prozess kann nun beendet werden."


@mcp.tool()
async def activate_server(server_name: str) -> str:
    """
    🔌 Aktiviert einen MCP-Server und macht seine Tools verfügbar.
    
    Args:
        server_name: Name des Servers (z.B. 'docker', 'database', 'web-search')
    
    Returns:
        Status der Aktivierung und Liste der neuen Tools
    """
    await state.initialize()
    
    success, message = await state.connect_server(server_name)
    
    if success:
        tools = state.server_tools.get(server_name, [])
        tool_list = "\n".join([f"  - {t}" for t in tools[:15]])
        if len(tools) > 15:
            tool_list += f"\n  ... und {len(tools) - 15} weitere"
        return f"✅ {message}\n\n**Verfügbare Tools:**\n{tool_list}"
    else:
        return f"❌ {message}"


@mcp.tool()
async def deactivate_server(server_name: str) -> str:
    """
    🔌 Deaktiviert einen MCP-Server und entfernt seine Tools.
    
    Args:
        server_name: Name des Servers
    
    Returns:
        Status der Deaktivierung
    """
    await state.initialize()
    
    success, message = await state.disconnect_server(server_name)
    return f"{'✅' if success else '❌'} {message}"


@mcp.tool()
async def get_active_tools() -> str:
    """
    📋 Zeigt alle aktuell aktiven Tools aus verbundenen Servern.
    
    Returns:
        Gruppierte Liste aller verfügbaren Tools
    """
    await state.initialize()
    
    if not state.tool_registry:
        return "Keine Tools aktiv. Nutze `activate_server()` um Server zu aktivieren."
    
    lines = [f"# 🔧 Aktive Tools ({len(state.tool_registry)} gesamt)\n"]
    
    for server, tools in sorted(state.server_tools.items()):
        lines.append(f"\n## {server} ({len(tools)} Tools)")
        for tool_name in tools[:10]:
            _, tool_def = state.tool_registry[tool_name]
            desc = tool_def.description[:60] + "..." if len(tool_def.description) > 60 else tool_def.description
            lines.append(f"- `{tool_name}`: {desc}")
        if len(tools) > 10:
            lines.append(f"- *... und {len(tools) - 10} weitere*")
    
    return "\n".join(lines)


@mcp.tool()
async def execute(server: str, tool: str, arguments: str = "{}") -> str:
    """
    ⚡ Führt ein beliebiges Tool aus (aktiviert Server automatisch falls nötig).
    
    Args:
        server: Server-Name (z.B. 'docker', 'git')
        tool: Tool-Name ohne Prefix (z.B. 'ps', 'status')
        arguments: JSON-String mit Argumenten
    
    Returns:
        Ergebnis des Tool-Aufrufs
    
    Beispiele:
        execute("docker", "ps", "{}")
        execute("git", "status", '{"repo_path": "d:/project"}')
        execute("database", "query", '{"sql": "SELECT * FROM users"}')
    """
    await state.initialize()
    
    # Auto-aktivieren falls nötig
    if server not in state.connected_servers:
        success, msg = await state.connect_server(server)
        if not success:
            return f"❌ Server '{server}' konnte nicht aktiviert werden: {msg}"
    
    # Tool aufrufen
    tool_name = f"{server}_{tool}"
    
    try:
        args = json.loads(arguments) if arguments else {}
    except json.JSONDecodeError as e:
        return f"❌ Ungültiges JSON: {e}"
    
    return await state.call_tool(tool_name, args)


# ============================================================
# SCHNELLZUGRIFF-TOOLS (häufig genutzt, immer verfügbar)
# ============================================================

@mcp.tool()
async def read_file(path: str) -> str:
    """📄 Liest eine Datei (aktiviert filesystem-Server automatisch)."""
    await state.initialize()
    if "filesystem" not in state.connected_servers:
        await state.connect_server("filesystem")
    return await state.call_tool("filesystem_read_file", {"path": path})


@mcp.tool()
async def write_file(path: str, content: str) -> str:
    """📝 Schreibt eine Datei (aktiviert filesystem-Server automatisch)."""
    await state.initialize()
    if "filesystem" not in state.connected_servers:
        await state.connect_server("filesystem")
    return await state.call_tool("filesystem_write_file", {"path": path, "content": content})


@mcp.tool()
async def list_directory(path: str) -> str:
    """📁 Listet Verzeichnisinhalt."""
    await state.initialize()
    if "filesystem" not in state.connected_servers:
        await state.connect_server("filesystem")
    return await state.call_tool("filesystem_list_directory", {"path": path})


@mcp.tool()
async def search_files(path: str, pattern: str) -> str:
    """🔍 Sucht Dateien nach Pattern."""
    await state.initialize()
    if "filesystem" not in state.connected_servers:
        await state.connect_server("filesystem")
    return await state.call_tool("filesystem_search_files", {"path": path, "pattern": pattern})


@mcp.tool()
async def git_status(repo_path: str = ".") -> str:
    """📊 Git-Status eines Repositories."""
    await state.initialize()
    if "git" not in state.connected_servers:
        await state.connect_server("git")
    return await state.call_tool("git_status", {"repo_path": repo_path})


@mcp.tool()
async def git_log(repo_path: str = ".", max_commits: int = 10) -> str:
    """📜 Git-Log eines Repositories."""
    await state.initialize()
    if "git" not in state.connected_servers:
        await state.connect_server("git")
    return await state.call_tool("git_log", {"repo_path": repo_path, "max_commits": max_commits})


@mcp.tool()
async def git_diff(repo_path: str = ".") -> str:
    """📝 Git-Diff (unstaged changes)."""
    await state.initialize()
    if "git" not in state.connected_servers:
        await state.connect_server("git")
    return await state.call_tool("git_diff", {"repo_path": repo_path})


@mcp.tool()
async def calculate(expression: str) -> str:
    """🧮 Berechnet einen mathematischen Ausdruck."""
    await state.initialize()
    if "demo" not in state.connected_servers:
        await state.connect_server("demo")
    return await state.call_tool("demo_calculate", {"expression": expression})


@mcp.tool()
async def get_time() -> str:
    """🕐 Gibt aktuelle Zeit zurück."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@mcp.tool()
async def help() -> str:
    """
    ❓ Zeigt Hilfe zur Verwendung des Bridge-Servers.
    """
    return """
# 🚀 Guido MCP Bridge - Hilfe

## Konzept
Der Bridge-Server lädt MCP-Server **on-demand** statt alle gleichzeitig.
So sieht VS Code nur ~15 Tools statt 400+!

## Befehle

### Server-Verwaltung
- `list_servers()` - Alle verfügbaren Server anzeigen
- `activate_server("docker")` - Server aktivieren
- `deactivate_server("docker")` - Server deaktivieren
- `get_active_tools()` - Aktive Tools anzeigen

### Direkter Tool-Aufruf
- `execute("docker", "ps", "{}")` - Tool direkt ausführen
- `execute("database", "query", '{"sql": "SELECT 1"}')` 

### Schnellzugriff (immer aktiv)
- `read_file("path")` - Datei lesen
- `write_file("path", "content")` - Datei schreiben
- `list_directory("path")` - Verzeichnis auflisten
- `git_status("repo")` - Git Status
- `calculate("2+2")` - Rechnen

## Verfügbare Server
filesystem, git, docker, database, web-search, 
web-scraping, github, email, ssh, ionos, flutter, 
ollama, project-manager, demo

## Beispiele

"Aktiviere Docker und zeig mir die Container"
→ activate_server("docker"), dann execute("docker", "ps", "{}")

"Durchsuche das Web nach Python tutorials"  
→ activate_server("web-search"), dann execute("web-search", "search", '{"query": "python tutorials"}')
"""


# ============================================================
# SERVER-START
# ============================================================

async def main():
    """Hauptfunktion - Server mit Lazy Loading starten"""
    await state.initialize()
    print("[Bridge] 🚀 Guido MCP Bridge gestartet (Dynamic Loading)", file=sys.stderr)
    print(f"[Bridge] 📊 {len(state.connected_servers)} Server vorab verbunden", file=sys.stderr)
    try:
        await mcp.run_async()
    finally:
        await state.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
