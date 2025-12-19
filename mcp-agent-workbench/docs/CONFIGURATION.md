# ⚙️ Konfigurationsreferenz

> Alle Einstellungen auf einen Blick

---

## 📋 Übersicht

| Datei | Zweck | Format |
|-------|-------|--------|
| `agent/.env` | Umgebungsvariablen, API-Keys | KEY=VALUE |
| `agent/.env.example` | Vorlage mit Dokumentation | KEY=VALUE |
| `agent/mcp-servers.json` | Server-Definitionen | JSON |

---

## 🔑 API-Keys

| Variable | Beschreibung | Beispiel | Erforderlich |
|----------|--------------|----------|--------------|
| `OPENAI_API_KEY` | OpenAI API-Key | `sk-abc123...` | Einer von beiden |
| `ANTHROPIC_API_KEY` | Anthropic API-Key | `sk-ant-abc123...` | Einer von beiden |
| `GITHUB_TOKEN` | GitHub Personal Access Token | `ghp_abc123...` | Für GitHub-Server |
| `IONOS_API_KEY` | IONOS DNS API-Key | `prefix.secret` | Für IONOS-Server |

---

## 🤖 LLM-Einstellungen

| Variable | Beschreibung | Werte | Standard |
|----------|--------------|-------|----------|
| `LLM_MODEL` | KI-Modell | `gpt-4o`, `gpt-4o-mini`, `claude-sonnet-4-20250514` | `gpt-4o` |

### Modell-Empfehlungen

| Anwendungsfall | Modell | Grund |
|----------------|--------|-------|
| Allgemein | `gpt-4o` | Beste Tool-Nutzung |
| Kostengünstig | `gpt-4o-mini` | Günstig, ausreichend |
| Code-Review | `claude-3-5-sonnet` | Gute Code-Analyse |
| Komplexe Aufgaben | `claude-3-opus` | Stärkste Reasoning |

---

## 🐳 Docker

| Variable | Beschreibung | Beispiel | Standard |
|----------|--------------|----------|----------|
| `DOCKER_REMOTE_HOST` | Remote Docker URL | `tcp://192.168.0.27:2375` | Lokal |
| `DOCKER_TIMEOUT` | Timeout (Sekunden) | `30` | `30` |

---

## 🤖 Ollama

| Variable | Beschreibung | Beispiel | Standard |
|----------|--------------|----------|----------|
| `OLLAMA_HOST` | Ollama Server URL | `http://192.168.0.27:11434` | `localhost:11434` |
| `OLLAMA_DEFAULT_MODEL` | Standard-Modell | `llama3.2` | - |
| `OLLAMA_TIMEOUT` | Timeout (Sekunden) | `120` | `120` |

---

## 🔐 SSH

SSH-Hosts werden dynamisch konfiguriert:

| Variable | Beschreibung | Beispiel |
|----------|--------------|----------|
| `SSH_HOST_<NAME>` | Host-Definition | `root@server.de:22` |
| `SSH_PASSWORD_<NAME>` | Passwort (Option A) | `mein-passwort` |
| `SSH_KEY_<NAME>` | SSH-Key Pfad (Option B) | `C:\Users\ich\.ssh\id_rsa` |

### Beispiel

```env
SSH_HOST_IONOS=root@mein-server.ionos.de:22
SSH_PASSWORD_IONOS=super-geheim

SSH_HOST_PI=pi@192.168.0.100:22
SSH_KEY_PI=C:\Users\ich\.ssh\pi_key
```

---

## 📧 Email

### SMTP (Senden)

| Variable | Beschreibung | Beispiel | Standard |
|----------|--------------|----------|----------|
| `SMTP_HOST` | SMTP-Server | `smtp.gmail.com` | - |
| `SMTP_PORT` | Port | `587` | `587` |
| `SMTP_USER` | Benutzername | `ich@gmail.com` | - |
| `SMTP_PASSWORD` | Passwort | `app-password` | - |
| `SMTP_USE_TLS` | TLS aktivieren | `true` | `true` |
| `SMTP_FROM_NAME` | Absendername | `MCP Agent` | - |

### IMAP (Empfangen)

| Variable | Beschreibung | Beispiel | Standard |
|----------|--------------|----------|----------|
| `IMAP_HOST` | IMAP-Server | `imap.gmail.com` | - |
| `IMAP_PORT` | Port | `993` | `993` |
| `IMAP_USER` | Benutzername | `ich@gmail.com` | - |
| `IMAP_PASSWORD` | Passwort | `app-password` | - |
| `IMAP_USE_SSL` | SSL aktivieren | `true` | `true` |

### Provider-Einstellungen

| Provider | SMTP Host | SMTP Port | IMAP Host | IMAP Port |
|----------|-----------|-----------|-----------|-----------|
| Gmail | `smtp.gmail.com` | 587 | `imap.gmail.com` | 993 |
| Outlook | `smtp-mail.outlook.com` | 587 | `outlook.office365.com` | 993 |
| IONOS | `smtp.ionos.de` | 587 | `imap.ionos.de` | 993 |

---

## 🗄️ Datenbanken

| Variable | Beschreibung | Beispiel |
|----------|--------------|----------|
| `SQLITE_DEFAULT_DB` | SQLite-Datei | `d:\daten\app.db` |
| `POSTGRES_URL` | PostgreSQL | `postgresql://user:pass@host:5432/db` |
| `MYSQL_URL` | MySQL | `mysql://user:pass@host:3306/db` |
| `MSSQL_URL` | MS SQL Server | `mssql://user:pass@host:1433/db` |

---

## 📁 Pfade

| Variable | Beschreibung | Beispiel | Standard |
|----------|--------------|----------|----------|
| `PROJECTS_BASE_PATH` | Projekt-Scanner Basis | `d:\` | `d:\` |
| `GIT_PROJECTS_PATH` | Git-Repos Basis | `d:\` | `d:\` |
| `FLUTTER_PROJECTS_PATH` | Flutter-Projekte | `d:\` | `d:\` |
| `ALLOWED_PATHS` | Erlaubte Pfade (Sicherheit) | `d:\,c:\Users` | Alle |

---

## 🔍 Web-Suche

| Variable | Beschreibung | Werte | Standard |
|----------|--------------|-------|----------|
| `SEARCH_REGION` | Such-Region | `de-de`, `at-de`, `us-en`, `wt-wt` | `de-de` |
| `SEARCH_SAFESEARCH` | SafeSearch | `off`, `moderate`, `strict` | `moderate` |
| `SEARCH_MAX_RESULTS` | Max. Ergebnisse | `1-50` | `10` |

---

## 🌐 Web-Scraping

| Variable | Beschreibung | Beispiel | Standard |
|----------|--------------|----------|----------|
| `SCRAPING_USER_AGENT` | Browser-Identifikation | `Mozilla/5.0...` | Chrome UA |
| `SCRAPING_TIMEOUT` | Timeout (Sekunden) | `30` | `30` |
| `SCRAPING_MAX_SIZE` | Max. Seitengröße (Bytes) | `5242880` | 5 MB |

---

## 🦋 Flutter

| Variable | Beschreibung | Werte | Standard |
|----------|--------------|-------|----------|
| `FLUTTER_BUILD_MODE` | Build-Modus | `debug`, `profile`, `release` | `release` |
| `FLUTTER_SDK_PATH` | SDK-Pfad (optional) | `C:\flutter` | PATH |

---

## ⚙️ System

| Variable | Beschreibung | Werte | Standard |
|----------|--------------|-------|----------|
| `LOG_LEVEL` | Log-Stufe | `debug`, `info`, `warning`, `error` | `info` |
| `DEBUG` | Debug-Modus | `true`, `false` | `false` |
| `LOG_FILE` | Log-Datei (optional) | `d:\logs\agent.log` | - |

---

## 🔌 MCP

| Variable | Beschreibung | Beispiel | Standard |
|----------|--------------|----------|----------|
| `MCP_CONFIG_PATH` | Server-Konfiguration | `./mcp-servers.json` | `./mcp-servers.json` |
| `MCP_TIMEOUT` | Verbindungs-Timeout (ms) | `30000` | `30000` |
| `MCP_MAX_RETRIES` | Wiederholungsversuche | `3` | `3` |
| `MCP_STARTUP_TIMEOUT` | Server-Start-Timeout (ms) | `10000` | `10000` |

---

## 📄 mcp-servers.json

### Struktur

```json
{
  "servers": {
    "server-name": {
      "command": "python",
      "args": ["../servers/server-name/server.py"],
      "env": {
        "CUSTOM_VAR": "value"
      }
    }
  },
  "activeServers": ["server-name"]
}
```

### Felder

| Feld | Beschreibung | Erforderlich |
|------|--------------|--------------|
| `command` | Ausführbarer Befehl | ✅ |
| `args` | Argumente (Array) | ✅ |
| `env` | Zusätzliche Umgebungsvariablen | ❌ |
| `cwd` | Arbeitsverzeichnis | ❌ |

### Server aktivieren/deaktivieren

```json
{
  "activeServers": [
    "demo",           // ✅ Aktiv
    "filesystem",     // ✅ Aktiv
    // "github",      // ❌ Inaktiv (auskommentiert)
    "git",
    "flutter"
  ]
}
```

---

## 🔒 Sicherheitshinweise

⚠️ **Niemals committen:**
- `.env` Datei
- API-Keys
- Passwörter
- SSH-Keys

✅ **Empfohlen:**
- `.env.example` committen (ohne echte Werte)
- `.env` in `.gitignore`
- SSH-Keys mit Passphrase schützen
- `ALLOWED_PATHS` einschränken

---

*MCP Agent Workbench v1.0.0*
