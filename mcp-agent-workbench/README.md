# 🤖 MCP Agent Workbench

> **Ein modulares KI-Agenten-System mit 15 spezialisierten MCP-Servern und ~140 Tools**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)]()
[![Node.js](https://img.shields.io/badge/node.js-18+-green.svg)]()
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)]()

---

## 📖 Inhaltsverzeichnis

- [Was ist das?](#-was-ist-das)
- [Schnellstart](#-schnellstart)
- [Architektur](#-architektur)
- [Server-Übersicht](#-server-übersicht)
- [Konfiguration](#-konfiguration)
- [Verwendung](#-verwendung)
- [Server im Detail](#-server-im-detail)
- [Eigene Server erstellen](#-eigene-server-erstellen)
- [Troubleshooting](#-troubleshooting)

## 📚 Dokumentation

| Dokument | Beschreibung |
|----------|--------------|
| 📖 [README.md](README.md) | Diese Übersicht |
| 🚀 [docs/QUICKSTART.md](docs/QUICKSTART.md) | In 5 Minuten loslegen |
| 📚 [docs/SERVERS.md](docs/SERVERS.md) | Alle 15 Server mit 140 Tools dokumentiert |
| ⚙️ [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Alle Einstellungen erklärt |
| 🖥️ [docs/VSCODE-REMOTE.md](docs/VSCODE-REMOTE.md) | VS Code Remote-Entwicklung: Wann was nutzen? |
| 🔐 [agent/.env.example](agent/.env.example) | Konfigurationsvorlage mit Kommentaren |

---

## 🎯 Was ist das?

Die **MCP Agent Workbench** ist ein intelligenter Assistent, der nicht nur reden, sondern auch **handeln** kann:

```
┌─────────────────────────────────────────────────────────────┐
│  DU: "Zeige mir alle Docker-Container und deren Logs"       │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              🧠 AGENT HOST (GPT-4 / Claude)                 │
│                                                             │
│  1. Versteht deine Anfrage                                  │
│  2. Wählt passende Tools aus                                │
│  3. Führt sie aus                                           │
│  4. Formuliert Antwort                                      │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   🔧 MCP SERVER                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Docker  │ │  Git    │ │ Flutter │ │ Ollama  │  ...      │
│  │   🐳    │ │   📂    │ │   🦋    │ │   🤖    │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### ✨ Hauptfunktionen

| Kategorie | Beschreibung | Server |
|-----------|--------------|--------|
| 📁 **Dateisystem** | Dateien lesen, schreiben, suchen, kopieren | `filesystem` |
| 🐳 **Docker** | Container verwalten (lokal & remote) | `docker`, `docker-remote` |
| 🔍 **Web** | Suchen, Scrapen, Analysieren | `web-search`, `web-scraping` |
| 📧 **Email** | Senden und Empfangen | `email` |
| 🗄️ **Datenbank** | SQLite, PostgreSQL, MySQL, MSSQL | `database` |
| 🐙 **GitHub** | Repos, Issues, Pull Requests | `github` |
| 🦋 **Flutter** | Build, Test, Analyze | `flutter` |
| 🤖 **Ollama** | Lokale LLMs nutzen | `ollama` |
| 📂 **Git** | Branches, Commits, Diffs | `git` |
| 🌐 **IONOS** | DNS, Domains, Hosting | `ionos` |
| 🔐 **SSH** | Remote-Server verwalten | `ssh` |
| 📊 **Projekte** | Alle Projekte scannen | `project-manager` |

---

## 🚀 Schnellstart

### 1️⃣ Voraussetzungen prüfen

```powershell
# Python 3.11+ prüfen
python --version

# Node.js 18+ prüfen  
node --version
```

### 2️⃣ Dependencies installieren

```powershell
# Ins Projektverzeichnis wechseln
cd d:\Guido_mcp\mcp-agent-workbench

# Python-Dependencies (für alle Server)
pip install fastmcp pydantic httpx docker gitpython paramiko pyyaml beautifulsoup4 lxml duckduckgo-search aiosmtplib aioimaplib

# Node.js-Dependencies (für Agent)
cd agent
npm install
```

### 3️⃣ Konfiguration

```powershell
# .env Datei bearbeiten
notepad agent\.env
```

**Mindestens einen API-Key setzen:**
```env
OPENAI_API_KEY=sk-xxx...
# oder
ANTHROPIC_API_KEY=sk-ant-xxx...
```

### 4️⃣ Starten!

```powershell
cd agent
npm run dev "Hallo, was kannst du alles?"
```

---

## 🏗️ Architektur

```
mcp-agent-workbench/
│
├── 📁 agent/                    # Agent Host (TypeScript)
│   ├── src/
│   │   ├── index.ts            # 🚀 Haupteinstiegspunkt
│   │   ├── llm-client.ts       # 🧠 OpenAI/Anthropic Integration
│   │   ├── mcp-manager.ts      # 🔌 MCP Server Verwaltung
│   │   └── tool-executor.ts    # ⚡ Tool-Ausführung
│   ├── .env                    # 🔐 Konfiguration (GEHEIM!)
│   ├── mcp-servers.json        # 📋 Server-Definitionen
│   └── package.json
│
├── 📁 servers/                  # MCP Server (Python)
│   ├── demo-server/            # 🧮 Basis-Tools
│   ├── filesystem-server/      # 📁 Dateioperationen
│   ├── docker-server/          # 🐳 Docker lokal
│   ├── docker-remote-server/   # 🐳 Docker remote
│   ├── github-server/          # 🐙 GitHub API
│   ├── database-server/        # 🗄️ SQL-Datenbanken
│   ├── web-scraping-server/    # 🌐 Web-Extraktion
│   ├── web-search-server/      # 🔍 DuckDuckGo
│   ├── email-server/           # 📧 SMTP/IMAP
│   ├── ionos-server/           # 🌐 IONOS Hosting
│   ├── flutter-server/         # 🦋 Flutter/Dart
│   ├── ollama-server/          # 🤖 Lokale LLMs
│   ├── git-server/             # 📂 Git-Verwaltung
│   ├── project-manager-server/ # 📊 Projekt-Übersicht
│   └── ssh-server/             # 🔐 Remote SSH
│
├── 📁 docs/                     # 📚 Dokumentation
│   └── SERVERS.md              # Detaillierte Server-Doku
│
└── README.md                    # 📖 Diese Datei
```

---

## 📦 Server-Übersicht

### Alle 15 verfügbaren Server

| Server | Tools | Icon | Status | Beschreibung |
|--------|-------|------|--------|--------------|
| `demo` | 6 | 🧮 | ✅ Standard | Rechnen, Zeit, Text-Analyse |
| `filesystem` | 8 | 📁 | ✅ Standard | Lesen, Schreiben, Suchen |
| `project-manager` | 8 | 📊 | ✅ Standard | Alle Projekte scannen |
| `git` | 16 | 📂 | ✅ Standard | Branches, Commits, Diffs |
| `flutter` | 14 | 🦋 | ✅ Standard | Build, Test, Analyze |
| `ollama` | 11 | 🤖 | ✅ Standard | Lokale LLMs |
| `docker` | 16 | 🐳 | ⏸️ Optional | Docker lokal |
| `docker-remote` | 16 | 🐳 | ⏸️ Optional | Docker Remote-Host |
| `github` | 10 | 🐙 | ⏸️ Optional | Repos, Issues, PRs |
| `database` | 10 | 🗄️ | ⏸️ Optional | SQL-Abfragen |
| `web-scraping` | 8 | 🌐 | ⏸️ Optional | HTML extrahieren |
| `web-search` | 7 | 🔍 | ⏸️ Optional | DuckDuckGo |
| `email` | 9 | 📧 | ⏸️ Optional | SMTP/IMAP |
| `ionos` | 8 | 🌐 | ⏸️ Optional | DNS, Domains |
| `ssh` | 13 | 🔐 | ⏸️ Optional | Server-Verwaltung |

**Gesamt: ~140 Tools**

---

## ⚙️ Konfiguration

Vollständige Konfigurationsdatei: [`agent/.env`](agent/.env)

### Schnellreferenz

```env
# ═══════════════════════════════════════════════════════════
# 🧠 KI-PROVIDER (mindestens einen setzen!)
# ═══════════════════════════════════════════════════════════
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
LLM_MODEL=gpt-4o

# ═══════════════════════════════════════════════════════════
# 🐳 DOCKER
# ═══════════════════════════════════════════════════════════
DOCKER_REMOTE_HOST=tcp://192.168.0.27:2375

# ═══════════════════════════════════════════════════════════
# 🤖 OLLAMA
# ═══════════════════════════════════════════════════════════
OLLAMA_HOST=http://192.168.0.27:11434

# ═══════════════════════════════════════════════════════════
# 🌐 IONOS (DNS-Verwaltung)
# ═══════════════════════════════════════════════════════════
IONOS_API_KEY=xxx.yyy

# ═══════════════════════════════════════════════════════════
# 🔐 SSH
# ═══════════════════════════════════════════════════════════
SSH_HOST_IONOS=root@server.ionos.de:22
SSH_PASSWORD_IONOS=xxx
```

---

## 💻 Verwendung

### Beispiel-Befehle

```powershell
# Dateien
npm run dev "Zeige mir den Inhalt von package.json"
npm run dev "Erstelle eine neue Datei test.txt"

# Git
npm run dev "Zeige Git-Status von D:\MeinProjekt"
npm run dev "Liste alle Branches in D:\DMS"

# Docker
npm run dev "Welche Container laufen auf dem Docker-Server?"
npm run dev "Zeige Logs vom Container nginx"

# Projekte
npm run dev "Zeige mir alle meine Projekte auf D:"
npm run dev "Welche Flutter-Projekte habe ich?"

# Web
npm run dev "Suche nach Python MCP Tutorial"
npm run dev "Extrahiere den Text von https://example.com"

# Ollama
npm run dev "Welche Modelle sind auf Ollama verfügbar?"
npm run dev "Chatte mit llama3.2: Was ist MCP?"
```

---

## 📚 Server im Detail

Siehe [docs/SERVERS.md](docs/SERVERS.md) für vollständige Dokumentation aller Server und Tools.

---

## 🔧 Eigene Server erstellen

### Minimal-Template

```python
"""Mein Custom MCP Server"""
from fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("Mein Server", description="Beschreibung")

@mcp.tool()
async def mein_tool(
    param: str = Field(description="Parameter-Beschreibung")
) -> dict:
    """Tool-Beschreibung für den Agent."""
    return {"success": True, "result": param}

if __name__ == "__main__":
    mcp.run()
```

---

## 🔍 Troubleshooting

| Problem | Lösung |
|---------|--------|
| Server startet nicht | `python servers/demo-server/server.py` direkt testen |
| API-Key Fehler | `.env` prüfen: `OPENAI_API_KEY` oder `ANTHROPIC_API_KEY` |
| Docker nicht erreichbar | `curl http://192.168.0.27:2375/version` |
| Ollama offline | `curl http://192.168.0.27:11434/api/version` |

---

## 📖 Weiterführende Ressourcen

- [MCP Protocol Spezifikation](https://modelcontextprotocol.io/)
- [FastMCP Dokumentation](https://gofastmcp.com/)
- [@modelcontextprotocol/sdk](https://www.npmjs.com/package/@modelcontextprotocol/sdk)

---

## 📄 License

MIT License

---

**Erstellt mit ❤️ für produktive KI-gestützte Entwicklung**
