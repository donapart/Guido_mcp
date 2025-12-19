# 🚀 MCP Agent Workbench - Schnellstart

## In 5 Minuten loslegen

### 1️⃣ Requirements

- Python 3.10+
- Node.js 18+
- Ein API-Key (OpenAI oder Anthropic)

### 2️⃣ Installation

```powershell
cd d:\Guido_mcp\mcp-agent-workbench

# Python venv erstellen
python -m venv venv
.\venv\Scripts\Activate

# Dependencies installieren
pip install -r requirements.txt
pip install -r servers/demo-server/requirements.txt
pip install -r servers/filesystem-server/requirements.txt
# ... weitere Server nach Bedarf

# Agent Host
cd agent
npm install
```

### 3️⃣ Konfiguration

```powershell
# .env erstellen
copy .env.example .env

# API-Key eintragen
notepad .env
```

Mindestens setzen:
```env
OPENAI_API_KEY=sk-...
# oder
ANTHROPIC_API_KEY=sk-ant-...
```

### 4️⃣ Starten

```powershell
cd agent
npm start
```

### 5️⃣ Testen

Eingabe im Agent:
```
Was ist 5 + 3?
```

Erwartet:
```
Ich verwende das add Tool...
5 + 3 = 8
```

---

## 🎯 Häufige Aufgaben

### Dateien lesen
```
Zeige mir den Inhalt von d:\projekte\README.md
```

### Git Status
```
Was ist der Git-Status von d:\projekte\DressCode?
```

### Flutter bauen
```
Baue die Android APK für d:\projekte\DressCode
```

### Server-Status
```
Wie ist der Status meines IONOS-Servers?
```

---

## ⚡ Tipps

| Tipp | Beschreibung |
|------|--------------|
| **Multi-Tool** | Der Agent kann mehrere Tools kombinieren |
| **Kontext** | Je mehr Details du gibst, desto besser |
| **Server** | Nur aktivierte Server sind verfügbar |

---

## 🔧 Troubleshooting

### "Tool not found"
→ Server in `mcp-servers.json` → `activeServers` hinzufügen

### "API Key invalid"
→ `.env` prüfen, Key ohne Anführungszeichen

### "Connection timeout"
→ `MCP_TIMEOUT=60000` in `.env` erhöhen

---

*Mehr Details: [docs/SERVERS.md](SERVERS.md)*
