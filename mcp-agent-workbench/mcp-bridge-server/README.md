# MCP Bridge Server für VS Code Copilot Chat

Der **MCP Bridge Server** ist ein **dynamischer Tool-Aggregator** der alle MCP-Server der Workbench bei Bedarf lädt - nicht alle auf einmal!

## 🎯 Das Problem & Die Lösung

**Problem**: VS Code meldet "zu viele Tools aktiviert" (423+ Tools) wenn alle MCP-Server gleichzeitig laufen.

**Lösung**: Der Bridge-Server bietet nur **~15 Meta-Tools** an. Die eigentlichen Server werden **on-demand** aktiviert wenn du sie brauchst!

## 🚀 Installation

### 1. VS Code Settings öffnen

Drücke `Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)"

### 2. MCP-Konfiguration hinzufügen

Füge folgendes zu deinen User Settings hinzu:

```json
{
  "mcp": {
    "servers": {
      "workbench": {
        "command": "python",
        "args": ["d:/Guido_mcp/mcp-agent-workbench/mcp-bridge-server/server.py"],
        "env": {
          "MCP_BRIDGE_SERVERS": "demo,filesystem,git,project-manager,flutter,ollama"
        }
      }
    }
  }
}
```

Falls VS Code meldet, dass `python` nicht gefunden wurde, nutze stattdessen **entweder** einen absoluten Pfad:

```json
{
  "command": "C:/Users/<YOU>/AppData/Local/Programs/Python/Python311/python.exe",
  "args": ["d:/Guido_mcp/mcp-agent-workbench/mcp-bridge-server/server.py"]
}
```

…oder den Python Launcher:

```json
{
  "command": "py",
  "args": ["-3.11", "d:/Guido_mcp/mcp-agent-workbench/mcp-bridge-server/server.py"]
}
```

### 3. VS Code neu laden

`Ctrl+Shift+P` → "Developer: Reload Window"

## 📦 Verfügbare Tools

Der Bridge Server stellt **nur wenige Meta-Tools** bereit - die eigentlichen Server werden bei Bedarf geladen:

### Meta-Tools (Server-Verwaltung)
- `list_servers()` - Alle verfügbaren Server anzeigen
- `activate_server(name)` - Server aktivieren
- `deactivate_server(name)` - Server deaktivieren  
- `get_active_tools()` - Aktive Tools anzeigen
- `execute(server, tool, args)` - Tool direkt ausführen
- `check_env(server?)` - Prüft notwendige ENV-Variablen (ohne Werte)
- `get_system_status()` - Bridge Uptime/CPU/RAM (falls verfügbar)
- `shutdown_bridge()` - Ressourcen sauber schließen
- `help()` - Hilfe anzeigen

💡 `check_env()` enthält eine **Ampel-Übersicht** und eine **Next-Actions-Sektion**, welche Server mit der aktuellen Environment sofort nutzbar sind und was als nächstes zu konfigurieren ist.

Optional kannst du `check_env()` um kurze Laufzeit-Checks erweitern (z.B. ob `docker`/`flutter` im PATH sind und ob `OLLAMA_HOST` erreichbar ist):

```json
{
  "env": {
    "MCP_CHECK_RUNTIME": "true"
  }
}
```

### Schnellzugriff-Tools (immer verfügbar)
- `read_file(path)` - Datei lesen
- `write_file(path, content)` - Datei schreiben
- `list_directory(path)` - Verzeichnis listen
- `search_files(path, pattern)` - Dateien suchen
- `git_status(repo_path)` - Git Status
- `git_log(repo_path)` - Git Log
- `git_diff(repo_path)` - Git Diff
- `calculate(expression)` - Berechnung
- `get_time()` - Aktuelle Zeit

### Server die ON-DEMAND geladen werden
- `demo` - Basis-Tools
- `filesystem` - Dateien lesen/schreiben (auto-connect)
- `git` - Git-Verwaltung (auto-connect)
- `project-manager` - Projekt-Scanner
- `flutter` - Flutter/Dart Build
- `ollama` - Lokale LLMs
- `docker` - Docker Container
- `docker-remote` - Docker Remote
- `github` - GitHub API
- `database` - SQL-Datenbanken
- `web-search` - Web-Suche
- `web-scraping` - Web-Extraktion
- `email` - SMTP/IMAP
- `ionos` - IONOS Hosting
- `ssh` - Remote SSH

## 🔧 Konfiguration

### Umgebungsvariablen

```json
"env": {
  "MCP_AUTO_CONNECT": "filesystem,git,demo"  // Server die automatisch starten
}
```

**Standard Auto-Connect:** `filesystem`, `git`, `demo` (nur Basis-Tools)

## 🔐 .env / Secrets

Mehrere Server (z.B. GitHub, IONOS, LLM Provider) erwarten Keys über Umgebungsvariablen.
In diesem Repo ist dafür die Datei `agent/.env` vorgesehen (Vorlage: `agent/.env.example`).

### Optional: `agent/.env` automatisch laden

Die Bridge versucht beim Start **optional** `agent/.env` zu laden (nur wenn `python-dotenv` installiert ist).
Standard ist **aktiviert**. Deaktivieren kannst du es über:

```json
{
  "env": {
    "MCP_LOAD_DOTENV": "false"
  }
}
```

## 💬 Verwendung in Copilot Chat

### Server-Verwaltung

```
@workspace Zeig mir alle verfügbaren Server
→ list_servers()

@workspace Aktiviere Docker
→ activate_server("docker")

@workspace Welche Tools sind aktiv?
→ get_active_tools()
```

### Direkte Tool-Nutzung

```
@workspace Lies die Datei package.json
→ read_file("package.json")

@workspace Git Status dieses Repos
→ git_status(".")

@workspace Führe Docker ps aus
→ execute("docker", "ps", "{}")
```

### Automatisches Laden

Wenn du ein Tool benutzt das einen inaktiven Server braucht, wird dieser **automatisch aktiviert**:

```
@workspace Zeig mir die Docker Container
→ Bridge aktiviert docker-Server automatisch
→ Führt docker_ps aus
```

## 🐛 Debugging

Falls der Server nicht startet:

1. Prüfe Python-Installation: `python --version`
2. Prüfe MCP SDK: `pip show mcp`
3. Teste manuell:
   ```powershell
   cd d:\Guido_mcp\mcp-agent-workbench\mcp-bridge-server
   python server.py
   ```
4. Schau in die VS Code Output-Konsole (View → Output → MCP)

## 📋 Beispiel User Settings (komplett)

```json
{
  "mcp": {
    "servers": {
      "workbench": {
        "command": "python",
        "args": ["d:/Guido_mcp/mcp-agent-workbench/mcp-bridge-server/server.py"],
        "env": {
          "MCP_BRIDGE_SERVERS": "demo,filesystem,git,project-manager,flutter,ollama",
          "ALLOWED_DIRECTORIES": "d:/,c:/Users/donApart"
        }
      }
    }
  },
  "chat.mcp.enabled": true
}
```
