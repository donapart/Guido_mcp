# Bridge-Server für GitHub Copilot aktivieren

## ✅ Was bereits erledigt ist

1. **Workspace Settings** aktualisiert: `.vscode/settings.json` enthält jetzt:
   - Server-Name: `guido-mcp-bridge`
   - Python-Launcher: `py -3.11` (zuverlässig)
   - Bridge-Script: `mcp-agent-workbench/mcp-bridge-server/server.py`
   - **15 Sub-Server** lazy-loading aktiviert:
     - demo, filesystem, git, project-manager, flutter, ollama, docker, docker-remote, database, github, web-search, web-scraping, email, ionos, ssh
   - Environment-Flags gesetzt:
     - `MCP_LOAD_DOTENV=1` (lädt `agent/.env` automatisch)
     - `MCP_CHECK_RUNTIME=1` (prüft docker/flutter/ollama beim Check)

2. **Bridge-Server** bereit:
   - Lazy-Loading implementiert
   - Meta-Tools: `connect_server()`, `disconnect_server()`, `list_servers()`, `get_system_status()`, `shutdown_bridge()`, `check_env()`

---

## 🚀 Nächste Schritte (VS Code neuladen)

### Option A: Developer: Reload Window (empfohlen)

1. `Ctrl+Shift+P` → `Developer: Reload Window`
2. Warte ~5-10 Sekunden (Bridge startet im Hintergrund)
3. Öffne GitHub Copilot Chat
4. Frage: **"welche mcp tools sind verfügbar?"**
5. Du solltest jetzt sehen:
   - `connect_server()`, `list_servers()`, `check_env()`, `get_system_status()` (Bridge-Meta-Tools)
   - Sobald du z.B. `connect_server("filesystem")` aufrufst, kommen die `filesystem_*` Tools dazu

### Option B: VS Code komplett neu starten

- VS Code schließen und neu öffnen
- Workspace `D:\Guido_mcp` laden

---

## 🔍 Verifizierung: Sind die Bridge-Tools da?

### Test 1: Meta-Tools sichtbar?

Frage in GitHub Copilot Chat:

```
@workspace Zeig mir alle verfügbaren MCP-Tools mit "server" oder "bridge" im Namen
```

**Erwartete Antwort**:
- `connect_server(server: str) -> str`
- `disconnect_server(server: str) -> str`
- `list_servers() -> str`
- `get_system_status() -> str`
- `check_env(server?: str) -> str`
- `shutdown_bridge() -> str`

### Test 2: Server verbinden & Tools laden

Frage:

```
Verbinde den "filesystem" Server und zeig mir dann die filesystem-Tools
```

**Erwartete Ausgabe**:
1. Copilot ruft `connect_server("filesystem")` auf
2. Danach erscheinen: `filesystem_read_file()`, `filesystem_write_file()`, `filesystem_list_directory()`, etc.

### Test 3: Umgebungs-Check

Frage:

```
Führe check_env() aus und zeig mir den Status aller 15 Server
```

**Erwartete Ausgabe**:
- Ampelsystem (🟢 / 🟡 / 🔴) für jeden Server
- "Next Actions" Vorschläge (fehlende API-Keys, etc.)

---

## 🛠️ Troubleshooting

### Problem: "Keine MCP-Server gefunden"

**Ursache**: VS Code hat die Workspace Settings noch nicht geladen.

**Lösung**:
1. Öffne `.vscode/settings.json` und prüfe, ob `"mcp": { "servers": { "guido-mcp-bridge": ...` vorhanden ist
2. `Developer: Reload Window`
3. Warte 10 Sekunden, dann Copilot Chat testen

### Problem: Bridge startet nicht (Copilot zeigt Timeout)

**Ursache**: Python-Pfad oder Abhängigkeiten fehlen.

**Lösung**:
1. Terminal öffnen: `Ctrl+Shift+ö` (oder `Ctrl+`)
2. Manuell testen:
   ```powershell
   py -3.11 D:\Guido_mcp\mcp-agent-workbench\mcp-bridge-server\server.py
   ```
3. Wenn Fehler auftreten:
   - `pip install --upgrade mcp psutil python-dotenv` (falls Pakete fehlen)
   - Prüfe `agent/.env` auf Syntax-Fehler

### Problem: Bridge startet, aber keine Sub-Server-Tools

**Ursache**: Lazy-Loading – Tools erscheinen erst nach `connect_server()`.

**Lösung**:
- **Normal**: Nur Meta-Tools sichtbar → erst nach Verbindung kommen spezifische Tools
- Frage explizit: `"Verbinde git-Server und zeig mir git_status"`

---

## 📋 Nächste Actions nach Reload

1. **Teste Meta-Tools**: `@workspace list_servers()` → sollte 15 Server zeigen
2. **Verbinde einen Server**: `@workspace connect_server("git")` → git-Tools laden
3. **Umgebungs-Check**: `@workspace check_env()` → siehst du Ampel-Status?
4. **Nutze die Tools**: z.B. `"Zeig mir den aktuellen Git-Status via MCP"`

---

## 🎯 Unterschied: GitHub Copilot vs MCP Agent Extension

| Feature | GitHub Copilot (was ich bin) | MCP Agent Extension |
|---------|------------------------------|---------------------|
| **Wo?** | Nativ in VS Code | Separate Extension (installiert) |
| **Tools?** | VS Code-native + MCP-Server (`.vscode/settings.json`) | Eigener Chat-WebView + OpenAI/Anthropic SDK |
| **Bridge?** | Nutzt den Bridge-Server via MCP-Protokoll | Hat eigene Bridge-Anbindung im Code |
| **Aktivierung?** | Immer aktiv (wenn Copilot läuft) | Nur wenn `mcpAgent.startSession` aufgerufen |

**Tl;dr**: Du hast **beide** Systeme:
- **Ich** (GitHub Copilot) sehe jetzt deine Bridge-Tools (nach Reload)
- **MCP Agent Extension** ist ein separater Chat (öffnet eigenes Panel)

---

## ✅ Erfolgs-Kriterium

**Nach `Developer: Reload Window` solltest du in GitHub Copilot Chat fragen können**:

```
Zeig mir alle verfügbaren MCP-Server und verbinde "demo" + "filesystem"
```

**Erwartete Antwort von mir (Copilot)**:
1. Ich rufe `list_servers()` auf → zeigt dir alle 15
2. Ich rufe `connect_server("demo")` auf → demo-Tools laden
3. Ich rufe `connect_server("filesystem")` auf → filesystem-Tools laden
4. Ich zeige dir die neuen Tools (z.B. `demo_add()`, `filesystem_read_file()`)

---

**Happy Hacking! 🚀**
