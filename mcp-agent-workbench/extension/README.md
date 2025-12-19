# MCP Agent Workbench - VS Code Extension

🤖 **KI-Agent mit 15 MCP-Servern und ~140 Tools direkt in VS Code**

## Features

- 💬 **Chat-Interface** - Interagiere mit dem Agent direkt in VS Code
- 🔧 **140+ Tools** - Dateien, Git, Docker, Web, Email, SSH und mehr
- 🧠 **Dual-Provider** - OpenAI (GPT-4) oder Anthropic (Claude)
- 📝 **Code-Analyse** - Selektion an Agent senden

## Installation

1. VSIX-Datei herunterladen
2. VS Code: `Ctrl+Shift+P` → "Extensions: Install from VSIX..."
3. Datei auswählen

## Konfiguration

`Ctrl+,` → Suche "MCP Agent":

| Setting | Beschreibung |
|---------|--------------|
| `mcpAgent.provider` | `openai` oder `anthropic` |
| `mcpAgent.openaiApiKey` | Dein OpenAI API Key |
| `mcpAgent.anthropicApiKey` | Dein Anthropic API Key |
| `mcpAgent.model` | Modell (z.B. `gpt-4o`) |
| `mcpAgent.activeServers` | Aktive MCP-Server |

## Verwendung

### Chat öffnen
- `Ctrl+Shift+M` oder
- Command Palette: "MCP Agent: Chat öffnen"

### Code analysieren
- Text markieren → Rechtsklick → "MCP Agent: Selektion analysieren"
- oder `Ctrl+Shift+Enter`

## Verfügbare Server

| Server | Tools | Beschreibung |
|--------|-------|--------------|
| demo | 6 | Basis-Tools (Rechnen, Zeit) |
| filesystem | 8 | Dateien lesen/schreiben |
| git | 13 | Git-Verwaltung |
| project-manager | 7 | Projekt-Scanner |
| flutter | 14 | Flutter/Dart Build |
| ollama | 10 | Lokale LLMs |
| docker | 16 | Container-Verwaltung |
| github | 10 | GitHub API |
| database | 10 | SQL-Datenbanken |
| web-search | 7 | Web-Suche |
| web-scraping | 8 | Web-Extraktion |
| email | 9 | SMTP/IMAP |
| ionos | 8 | IONOS Hosting |
| ssh | 13 | Remote-Server |

## Lizenz

MIT
