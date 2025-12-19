# MCP Agent Workbench - Schnellstart

## 🚀 In 5 Minuten loslegen

### Voraussetzungen
- Node.js >= 20
- Python >= 3.10
- Anthropic API Key (https://console.anthropic.com/)

### 1. Repository klonen & Dependencies installieren

```powershell
# Ins Projektverzeichnis wechseln
cd d:\Guido_mcp\mcp-agent-workbench

# Python-Dependencies für Server
cd servers/demo-server
pip install -r requirements.txt
cd ../..

# Node-Dependencies für Agent
cd agent
npm install
cd ..

# Node-Dependencies für Extension
cd extension
npm install
cd ..
```

### 2. Konfiguration

```powershell
# Agent konfigurieren
cd agent
copy .env.example .env
# Dann .env bearbeiten und ANTHROPIC_API_KEY eintragen
```

### 3. Demo-Server testen

```powershell
# In einem Terminal:
cd servers/demo-server
python server.py
```

### 4. Agent testen

```powershell
# In einem anderen Terminal:
cd agent
npm run dev
# Oder mit eigenem Prompt:
npm run dev "Was ist 17 + 25?"
```

### 5. VS Code Extension

1. Extension-Ordner in VS Code öffnen
2. F5 drücken für Extension Development Host
3. Ctrl+Shift+M für MCP Agent Session

---

## 📁 Projektstruktur

```
mcp-agent-workbench/
├── servers/                    # MCP Server (Python)
│   ├── demo-server/           # Demo mit Basis-Tools
│   │   ├── server.py
│   │   └── requirements.txt
│   └── filesystem-server/     # Dateisystem-Operationen
│       ├── server.py
│       └── requirements.txt
├── agent/                     # Agent-Host (TypeScript)
│   ├── src/
│   │   ├── client.ts         # MCP-Client-Wrapper
│   │   ├── registry.ts       # Tool-Registry
│   │   ├── agent.ts          # LLM-Agent-Loop
│   │   └── index.ts          # Entry Point
│   ├── package.json
│   ├── tsconfig.json
│   ├── mcp-servers.json      # Server-Konfiguration
│   └── .env.example
├── extension/                 # VS Code Extension
│   ├── src/
│   │   ├── extension.ts      # Entry Point
│   │   ├── bridge.ts         # Agent-Bridge
│   │   └── webview/
│   │       └── chatPanel.ts  # Chat-UI
│   ├── package.json
│   └── tsconfig.json
├── mcp-servers.json          # Globale Server-Config
└── README.md
```

## 🔧 Nächste Schritte

1. **Eigene Tools hinzufügen** - Erweitere `servers/demo-server/server.py`
2. **Weitere Server** - Erstelle neue Server für GitHub, Datenbanken, etc.
3. **Extension Features** - Füge Diff-Vorschläge, Code-Actions hinzu
4. **Dynamische Server-Auswahl** - Implementiere Kontext-basierte Server-Aktivierung
