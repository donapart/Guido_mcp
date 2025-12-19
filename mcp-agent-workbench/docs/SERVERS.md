# 📚 MCP Server Dokumentation

> **Vollständige Referenz aller 15 MCP-Server mit ~140 Tools**

---

## Inhaltsverzeichnis

- [🎯 Demo Server](#-demo-server)
- [📁 Filesystem Server](#-filesystem-server)
- [🐙 GitHub Server](#-github-server)
- [🗄️ Database Server](#️-database-server)
- [🐳 Docker Server](#-docker-server)
- [🐳 Docker Remote Server](#-docker-remote-server)
- [🌐 Web Scraping Server](#-web-scraping-server)
- [🔍 Web Search Server](#-web-search-server)
- [📧 Email Server](#-email-server)
- [🌐 IONOS Server](#-ionos-server)
- [🦋 Flutter Server](#-flutter-server)
- [🤖 Ollama Server](#-ollama-server)
- [📦 Git Server](#-git-server)
- [📊 Project Manager Server](#-project-manager-server)
- [🔐 SSH Server](#-ssh-server)

---

## 🎯 Demo Server

> **Demonstriert grundlegende MCP-Konzepte**

| Info | Wert |
|------|------|
| Pfad | `servers/demo-server/server.py` |
| Abhängigkeiten | `fastmcp>=2.0.0` |
| Konfiguration | Keine |

### Tools

#### `echo`
Gibt den eingegebenen Text zurück.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `text` | string | ✅ | Text der zurückgegeben werden soll |

**Beispiel:**
```
Agent: echo("Hallo Welt")
→ "Echo: Hallo Welt"
```

---

#### `add`
Addiert zwei Zahlen.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `a` | integer | ✅ | Erste Zahl |
| `b` | integer | ✅ | Zweite Zahl |

**Beispiel:**
```
Agent: add(5, 3)
→ "5 + 3 = 8"
```

---

#### `get_server_info`
Zeigt Informationen über den Server.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| - | - | - | Keine Parameter |

**Beispiel:**
```
Agent: get_server_info()
→ {name: "demo", version: "1.0.0", tools: 3}
```

---

## 📁 Filesystem Server

> **Dateisystem-Operationen (Lesen, Schreiben, Suchen)**

| Info | Wert |
|------|------|
| Pfad | `servers/filesystem-server/server.py` |
| Abhängigkeiten | `fastmcp>=2.0.0` |
| Konfiguration | `ALLOWED_PATHS` (optional) |

### Tools

#### `read_file`
Liest den Inhalt einer Datei.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `path` | string | ✅ | Absoluter oder relativer Pfad zur Datei |
| `encoding` | string | ❌ | Zeichenkodierung (Standard: `utf-8`) |

**Beispiel:**
```
Agent: read_file("d:/projekte/config.json")
→ {"name": "MeinProjekt", ...}
```

---

#### `write_file`
Schreibt Inhalt in eine Datei (erstellt oder überschreibt).

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `path` | string | ✅ | Pfad zur Datei |
| `content` | string | ✅ | Zu schreibender Inhalt |
| `encoding` | string | ❌ | Zeichenkodierung (Standard: `utf-8`) |

**⚠️ Warnung:** Überschreibt existierende Dateien ohne Nachfrage!

---

#### `list_directory`
Listet Inhalte eines Verzeichnisses.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `path` | string | ✅ | Pfad zum Verzeichnis |

**Ausgabe:**
```
Verzeichnis: d:\projekte
├── 📁 DressCode/
├── 📁 DMS/
├── 📄 README.md (2.5 KB)
└── 📄 config.json (1.2 KB)
```

---

#### `create_directory`
Erstellt ein Verzeichnis (mit Unterverzeichnissen).

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `path` | string | ✅ | Pfad zum neuen Verzeichnis |

---

#### `delete_file`
Löscht eine Datei.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `path` | string | ✅ | Pfad zur Datei |

**⚠️ Warnung:** Unwiderrufliche Löschung!

---

#### `file_info`
Zeigt Metadaten einer Datei.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `path` | string | ✅ | Pfad zur Datei |

**Ausgabe:**
```
Datei: config.json
Größe: 2,048 Bytes
Erstellt: 2024-01-15 10:30:00
Geändert: 2024-01-20 14:22:15
Typ: JSON
```

---

#### `search_files`
Sucht Dateien nach Muster.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `path` | string | ✅ | Startverzeichnis |
| `pattern` | string | ✅ | Suchmuster (z.B. `*.py`, `config.*`) |
| `recursive` | boolean | ❌ | Unterverzeichnisse durchsuchen (Standard: `true`) |

---

#### `move_file`
Verschiebt oder benennt eine Datei um.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `source` | string | ✅ | Quellpfad |
| `destination` | string | ✅ | Zielpfad |

---

#### `copy_file`
Kopiert eine Datei.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `source` | string | ✅ | Quellpfad |
| `destination` | string | ✅ | Zielpfad |

---

## 🐙 GitHub Server

> **GitHub API Integration (Repos, Issues, PRs)**

| Info | Wert |
|------|------|
| Pfad | `servers/github-server/server.py` |
| Abhängigkeiten | `fastmcp>=2.0.0`, `httpx` |
| Konfiguration | `GITHUB_TOKEN` (**erforderlich**) |

### Einrichtung

1. GitHub Token erstellen: https://github.com/settings/tokens
2. Token in `.env` setzen: `GITHUB_TOKEN=ghp_xxxx`

### Tools

#### `list_repos`
Listet Repositories des authentifizierten Nutzers.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `type` | string | ❌ | `all`, `owner`, `public`, `private` (Standard: `all`) |
| `sort` | string | ❌ | `created`, `updated`, `pushed`, `full_name` |

---

#### `get_repo`
Zeigt Details eines Repositories.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `owner` | string | ✅ | Repository-Owner (z.B. `microsoft`) |
| `repo` | string | ✅ | Repository-Name (z.B. `vscode`) |

---

#### `list_issues`
Listet Issues eines Repositories.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `owner` | string | ✅ | Repository-Owner |
| `repo` | string | ✅ | Repository-Name |
| `state` | string | ❌ | `open`, `closed`, `all` (Standard: `open`) |
| `labels` | string | ❌ | Komma-getrennte Labels |

---

#### `create_issue`
Erstellt ein neues Issue.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `owner` | string | ✅ | Repository-Owner |
| `repo` | string | ✅ | Repository-Name |
| `title` | string | ✅ | Titel des Issues |
| `body` | string | ❌ | Beschreibung (Markdown) |
| `labels` | list | ❌ | Labels als Liste |

---

#### `list_prs`
Listet Pull Requests.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `owner` | string | ✅ | Repository-Owner |
| `repo` | string | ✅ | Repository-Name |
| `state` | string | ❌ | `open`, `closed`, `all` |

---

#### `get_file_content`
Liest Dateiinhalt aus Repository.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `owner` | string | ✅ | Repository-Owner |
| `repo` | string | ✅ | Repository-Name |
| `path` | string | ✅ | Pfad zur Datei |
| `ref` | string | ❌ | Branch/Tag/Commit (Standard: default branch) |

---

#### `search_code`
Sucht Code auf GitHub.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `query` | string | ✅ | Suchbegriff |
| `language` | string | ❌ | Programmiersprache filtern |

---

#### `list_commits`
Listet Commits eines Repositories.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `owner` | string | ✅ | Repository-Owner |
| `repo` | string | ✅ | Repository-Name |
| `sha` | string | ❌ | Branch/SHA starten |
| `since` | string | ❌ | ISO-Datum (nur nach diesem Datum) |

---

#### `list_branches`
Listet alle Branches.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `owner` | string | ✅ | Repository-Owner |
| `repo` | string | ✅ | Repository-Name |

---

#### `get_user`
Zeigt Benutzer-Informationen.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `username` | string | ❌ | GitHub-Username (leer = authentifizierter Nutzer) |

---

## 🗄️ Database Server

> **Datenbank-Operationen (SQLite, PostgreSQL, MySQL, MSSQL)**

| Info | Wert |
|------|------|
| Pfad | `servers/database-server/server.py` |
| Abhängigkeiten | `fastmcp>=2.0.0`, `aiosqlite`, `asyncpg`, `aiomysql`, `aioodbc` |
| Konfiguration | `SQLITE_DEFAULT_DB`, `POSTGRES_URL`, `MYSQL_URL`, `MSSQL_URL` |

### Tools

#### `db_connect`
Stellt Verbindung zu einer Datenbank her.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `db_type` | string | ✅ | `sqlite`, `postgresql`, `mysql`, `mssql` |
| `connection_string` | string | ✅ | Verbindungsstring |

**Verbindungsstring-Formate:**
- SQLite: `d:\daten\meine.db`
- PostgreSQL: `postgresql://user:pass@host:5432/db`
- MySQL: `mysql://user:pass@host:3306/db`
- MSSQL: `mssql://user:pass@host:1433/db`

---

#### `db_query`
Führt SQL-Abfrage aus (SELECT).

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `connection_id` | string | ✅ | ID aus `db_connect` |
| `query` | string | ✅ | SQL SELECT Statement |
| `params` | list | ❌ | Parameter für Prepared Statement |

---

#### `db_execute`
Führt SQL-Befehl aus (INSERT, UPDATE, DELETE).

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `connection_id` | string | ✅ | ID aus `db_connect` |
| `query` | string | ✅ | SQL Statement |
| `params` | list | ❌ | Parameter |

---

#### `db_list_tables`
Listet alle Tabellen.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `connection_id` | string | ✅ | ID aus `db_connect` |

---

#### `db_describe_table`
Zeigt Tabellenstruktur (Spalten, Typen).

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `connection_id` | string | ✅ | ID aus `db_connect` |
| `table_name` | string | ✅ | Name der Tabelle |

---

#### `db_close`
Schließt Datenbankverbindung.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `connection_id` | string | ✅ | ID aus `db_connect` |

---

## 🐳 Docker Server

> **Lokale Docker-Verwaltung**

| Info | Wert |
|------|------|
| Pfad | `servers/docker-server/server.py` |
| Abhängigkeiten | `fastmcp>=2.0.0`, `docker` |
| Konfiguration | Keine (nutzt lokalen Docker) |

### Tools

#### `list_containers`
Listet Docker-Container.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `all` | boolean | ❌ | Auch gestoppte anzeigen (Standard: `false`) |

---

#### `container_info`
Zeigt Container-Details.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `container_id` | string | ✅ | Container-ID oder Name |

---

#### `container_logs`
Zeigt Container-Logs.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `container_id` | string | ✅ | Container-ID |
| `tail` | integer | ❌ | Letzte N Zeilen (Standard: 100) |

---

#### `start_container` / `stop_container` / `restart_container`
Container starten/stoppen/neustarten.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `container_id` | string | ✅ | Container-ID |

---

#### `list_images`
Listet Docker-Images.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| - | - | - | Keine Parameter |

---

#### `pull_image`
Lädt Image von Registry.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `image` | string | ✅ | Image-Name (z.B. `nginx:latest`) |

---

#### `docker_stats`
Zeigt Container-Ressourcennutzung.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| - | - | - | Keine Parameter |

---

## 🐳 Docker Remote Server

> **Remote Docker-Verwaltung über TCP**

| Info | Wert |
|------|------|
| Pfad | `servers/docker-remote-server/server.py` |
| Abhängigkeiten | `fastmcp>=2.0.0`, `docker` |
| Konfiguration | `DOCKER_REMOTE_HOST` |

### Konfiguration

```env
# Remote Docker Host (z.B. NAS, Server)
DOCKER_REMOTE_HOST=tcp://192.168.0.27:2375
```

**Auf dem Remote-Host aktivieren:**
```bash
# /etc/docker/daemon.json
{"hosts": ["unix:///var/run/docker.sock", "tcp://0.0.0.0:2375"]}
```

### Tools

Gleiche Tools wie Docker Server, aber mit zusätzlichem `host`-Parameter.

---

## 🌐 Web Scraping Server

> **Webseiten-Inhalte extrahieren**

| Info | Wert |
|------|------|
| Pfad | `servers/web-scraping-server/server.py` |
| Abhängigkeiten | `fastmcp>=2.0.0`, `httpx`, `beautifulsoup4`, `lxml` |
| Konfiguration | `SCRAPING_USER_AGENT`, `SCRAPING_TIMEOUT` |

### Tools

#### `fetch_page`
Lädt Webseite und extrahiert Inhalte.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `url` | string | ✅ | URL der Webseite |
| `selector` | string | ❌ | CSS-Selektor (z.B. `article`, `.content`) |
| `extract` | string | ❌ | `text`, `html`, `links`, `images` |

---

#### `extract_links`
Extrahiert alle Links von einer Seite.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `url` | string | ✅ | URL der Webseite |
| `filter` | string | ❌ | Regex zum Filtern |

---

#### `extract_tables`
Extrahiert Tabellen als JSON/CSV.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `url` | string | ✅ | URL der Webseite |
| `format` | string | ❌ | `json` oder `csv` |

---

#### `screenshot`
Erstellt Screenshot einer Webseite.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `url` | string | ✅ | URL der Webseite |
| `output` | string | ✅ | Ausgabepfad |
| `width` | integer | ❌ | Breite in Pixel |
| `height` | integer | ❌ | Höhe in Pixel |

---

## 🔍 Web Search Server

> **Web-Suche mit DuckDuckGo**

| Info | Wert |
|------|------|
| Pfad | `servers/web-search-server/server.py` |
| Abhängigkeiten | `fastmcp>=2.0.0`, `duckduckgo-search` |
| Konfiguration | `SEARCH_REGION`, `SEARCH_SAFESEARCH` |

### Tools

#### `search`
Allgemeine Web-Suche.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `query` | string | ✅ | Suchbegriff |
| `max_results` | integer | ❌ | Maximale Ergebnisse (Standard: 10) |
| `region` | string | ❌ | Region (z.B. `de-de`) |

---

#### `search_news`
Sucht aktuelle Nachrichten.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `query` | string | ✅ | Suchbegriff |
| `timelimit` | string | ❌ | `d` (Tag), `w` (Woche), `m` (Monat) |

---

#### `search_images`
Sucht Bilder.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `query` | string | ✅ | Suchbegriff |
| `size` | string | ❌ | `small`, `medium`, `large` |

---

## 📧 Email Server

> **E-Mail senden und empfangen (SMTP/IMAP)**

| Info | Wert |
|------|------|
| Pfad | `servers/email-server/server.py` |
| Abhängigkeiten | `fastmcp>=2.0.0`, `aiosmtplib`, `aioimaplib` |
| Konfiguration | `SMTP_*`, `IMAP_*` (siehe .env) |

### Tools

#### `send_email`
Sendet eine E-Mail.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `to` | string | ✅ | Empfänger-Adresse |
| `subject` | string | ✅ | Betreff |
| `body` | string | ✅ | Nachrichtentext |
| `html` | boolean | ❌ | HTML-Format |
| `attachments` | list | ❌ | Dateipfade |

---

#### `list_emails`
Listet E-Mails aus Postfach.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `folder` | string | ❌ | Ordner (Standard: `INBOX`) |
| `limit` | integer | ❌ | Maximale Anzahl |
| `unread_only` | boolean | ❌ | Nur ungelesene |

---

#### `read_email`
Liest eine E-Mail.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `message_id` | string | ✅ | Message-ID |
| `folder` | string | ❌ | Ordner |

---

#### `search_emails`
Sucht E-Mails.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `query` | string | ✅ | Suchbegriff |
| `folder` | string | ❌ | Ordner |
| `from_addr` | string | ❌ | Absender filtern |

---

## 🌐 IONOS Server

> **IONOS DNS-Verwaltung**

| Info | Wert |
|------|------|
| Pfad | `servers/ionos-server/server.py` |
| Abhängigkeiten | `fastmcp>=2.0.0`, `httpx` |
| Konfiguration | `IONOS_API_KEY` (**erforderlich**) |

### Einrichtung

1. IONOS Control Panel → Domains & SSL → DNS → API
2. API-Schlüssel erstellen
3. In `.env`: `IONOS_API_KEY=prefix.secret`

### Tools

#### `list_dns_zones`
Listet alle DNS-Zonen (Domains).

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| - | - | - | Keine Parameter |

---

#### `get_dns_zone`
Zeigt DNS-Einträge einer Zone.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `zone_id` | string | ✅ | Zone-ID |

---

#### `create_dns_record`
Erstellt neuen DNS-Eintrag.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `zone_id` | string | ✅ | Zone-ID |
| `name` | string | ✅ | Subdomain (z.B. `www`) |
| `type` | string | ✅ | `A`, `AAAA`, `CNAME`, `MX`, `TXT` |
| `content` | string | ✅ | Wert (IP, Ziel, etc.) |
| `ttl` | integer | ❌ | Time-to-Live (Standard: 3600) |
| `priority` | integer | ❌ | Priorität (für MX) |

**Beispiel:**
```
Agent: create_dns_record("zone123", "api", "A", "192.168.0.100")
→ Erstellt: api.meine-domain.de → 192.168.0.100
```

---

#### `update_dns_record`
Aktualisiert DNS-Eintrag.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `zone_id` | string | ✅ | Zone-ID |
| `record_id` | string | ✅ | Record-ID |
| `content` | string | ✅ | Neuer Wert |
| `ttl` | integer | ❌ | Neue TTL |

---

#### `delete_dns_record`
Löscht DNS-Eintrag.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `zone_id` | string | ✅ | Zone-ID |
| `record_id` | string | ✅ | Record-ID |

---

#### `quick_dns_update`
Schnelles Update per Domain-Name.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `domain` | string | ✅ | Domain (z.B. `meine-domain.de`) |
| `subdomain` | string | ✅ | Subdomain (z.B. `www`) |
| `ip` | string | ✅ | Neue IP-Adresse |

---

#### `list_all_dns_records`
Listet alle DNS-Einträge aller Zonen.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| - | - | - | Keine Parameter |

---

#### `check_ionos_config`
Prüft IONOS-Konfiguration.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| - | - | - | Keine Parameter |

---

## 🦋 Flutter Server

> **Flutter/Dart Projekt-Verwaltung**

| Info | Wert |
|------|------|
| Pfad | `servers/flutter-server/server.py` |
| Abhängigkeiten | `fastmcp>=2.0.0` |
| Konfiguration | `FLUTTER_PROJECTS_PATH`, `FLUTTER_BUILD_MODE` |

### Voraussetzungen

- Flutter SDK installiert und im PATH
- `flutter doctor` ohne Fehler

### Tools

#### `flutter_doctor`
Prüft Flutter-Installation.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| - | - | - | Keine Parameter |

---

#### `flutter_version`
Zeigt Flutter-Version.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| - | - | - | Keine Parameter |

---

#### `list_flutter_devices`
Listet verfügbare Geräte/Emulatoren.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| - | - | - | Keine Parameter |

---

#### `flutter_pub_get`
Installiert Dependencies eines Projekts.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `project_path` | string | ✅ | Pfad zum Flutter-Projekt |

---

#### `flutter_pub_upgrade`
Aktualisiert Dependencies.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `project_path` | string | ✅ | Pfad zum Flutter-Projekt |

---

#### `flutter_analyze`
Analysiert Code auf Fehler/Warnungen.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `project_path` | string | ✅ | Pfad zum Flutter-Projekt |

---

#### `flutter_test`
Führt Tests aus.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `project_path` | string | ✅ | Pfad zum Flutter-Projekt |
| `coverage` | boolean | ❌ | Coverage-Report erstellen |

---

#### `flutter_build_apk`
Baut Android APK.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `project_path` | string | ✅ | Pfad zum Flutter-Projekt |
| `mode` | string | ❌ | `debug`, `profile`, `release` |
| `split_per_abi` | boolean | ❌ | Separate APKs pro CPU-Architektur |

---

#### `flutter_build_appbundle`
Baut Android App Bundle (für Play Store).

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `project_path` | string | ✅ | Pfad zum Flutter-Projekt |
| `mode` | string | ❌ | `debug`, `profile`, `release` |

---

#### `flutter_build_web`
Baut Web-Version.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `project_path` | string | ✅ | Pfad zum Flutter-Projekt |

---

#### `flutter_build_ios`
Baut iOS-Version (nur auf macOS).

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `project_path` | string | ✅ | Pfad zum Flutter-Projekt |

---

#### `flutter_clean`
Bereinigt Build-Artefakte.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `project_path` | string | ✅ | Pfad zum Flutter-Projekt |

---

#### `flutter_project_info`
Zeigt Projektinformationen (pubspec.yaml).

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `project_path` | string | ✅ | Pfad zum Flutter-Projekt |

---

#### `list_flutter_projects`
Findet alle Flutter-Projekte.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `base_path` | string | ❌ | Suchpfad (Standard: `FLUTTER_PROJECTS_PATH`) |

---

## 🤖 Ollama Server

> **Lokale LLM-Verwaltung**

| Info | Wert |
|------|------|
| Pfad | `servers/ollama-server/server.py` |
| Abhängigkeiten | `fastmcp>=2.0.0`, `httpx` |
| Konfiguration | `OLLAMA_HOST`, `OLLAMA_DEFAULT_MODEL` |

### Einrichtung

1. Ollama installieren: https://ollama.ai
2. Model laden: `ollama pull llama3.2`
3. In `.env`: `OLLAMA_HOST=http://localhost:11434`

### Tools

#### `ollama_status`
Prüft Ollama-Server-Status.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| - | - | - | Keine Parameter |

---

#### `list_models`
Listet installierte Modelle.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| - | - | - | Keine Parameter |

---

#### `model_info`
Zeigt Model-Details.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `model` | string | ✅ | Model-Name (z.B. `llama3.2`) |

---

#### `pull_model`
Lädt Model herunter.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `model` | string | ✅ | Model-Name (z.B. `mistral`) |

---

#### `delete_model`
Löscht Model.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `model` | string | ✅ | Model-Name |

---

#### `copy_model`
Kopiert/Benennt Model um.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `source` | string | ✅ | Quell-Model |
| `destination` | string | ✅ | Neuer Name |

---

#### `chat`
Chat mit einem Model.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `model` | string | ❌ | Model (Standard: `OLLAMA_DEFAULT_MODEL`) |
| `messages` | list | ✅ | Chat-Verlauf |
| `temperature` | float | ❌ | Kreativität (0.0-2.0) |
| `max_tokens` | integer | ❌ | Max. Antwortlänge |

**Messages-Format:**
```json
[
  {"role": "user", "content": "Hallo!"},
  {"role": "assistant", "content": "Hi! Wie kann ich helfen?"},
  {"role": "user", "content": "Erkläre Python."}
]
```

---

#### `generate`
Textgenerierung (single prompt).

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `model` | string | ❌ | Model |
| `prompt` | string | ✅ | Eingabe-Prompt |
| `system` | string | ❌ | System-Prompt |

---

#### `embeddings`
Erstellt Embeddings für Text.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `model` | string | ✅ | Embedding-Model (z.B. `nomic-embed-text`) |
| `input` | string | ✅ | Text für Embedding |

---

#### `list_running`
Zeigt laufende Models.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| - | - | - | Keine Parameter |

---

## 📦 Git Server

> **Git Repository-Verwaltung**

| Info | Wert |
|------|------|
| Pfad | `servers/git-server/server.py` |
| Abhängigkeiten | `fastmcp>=2.0.0`, `gitpython` |
| Konfiguration | `GIT_PROJECTS_PATH` |

### Tools

#### `git_status`
Zeigt Repository-Status.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `repo_path` | string | ✅ | Pfad zum Repository |

---

#### `git_log`
Zeigt Commit-Historie.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `repo_path` | string | ✅ | Pfad zum Repository |
| `max_count` | integer | ❌ | Maximale Commits (Standard: 10) |
| `branch` | string | ❌ | Branch |

---

#### `git_diff`
Zeigt Änderungen.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `repo_path` | string | ✅ | Pfad zum Repository |
| `staged` | boolean | ❌ | Nur staged Änderungen |
| `file` | string | ❌ | Spezifische Datei |

---

#### `list_branches`
Listet alle Branches.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `repo_path` | string | ✅ | Pfad zum Repository |
| `remote` | boolean | ❌ | Remote-Branches einschließen |

---

#### `checkout_branch`
Wechselt Branch.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `repo_path` | string | ✅ | Pfad zum Repository |
| `branch` | string | ✅ | Branch-Name |

---

#### `create_branch`
Erstellt neuen Branch.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `repo_path` | string | ✅ | Pfad zum Repository |
| `branch` | string | ✅ | Neuer Branch-Name |
| `checkout` | boolean | ❌ | Direkt wechseln |

---

#### `git_add`
Fügt Dateien zum Index hinzu.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `repo_path` | string | ✅ | Pfad zum Repository |
| `files` | list | ❌ | Dateien (Standard: alle) |

---

#### `git_commit`
Erstellt Commit.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `repo_path` | string | ✅ | Pfad zum Repository |
| `message` | string | ✅ | Commit-Nachricht |

---

#### `git_pull`
Holt Änderungen von Remote.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `repo_path` | string | ✅ | Pfad zum Repository |
| `remote` | string | ❌ | Remote-Name (Standard: `origin`) |
| `branch` | string | ❌ | Branch |

---

#### `git_push`
Pusht Änderungen zu Remote.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `repo_path` | string | ✅ | Pfad zum Repository |
| `remote` | string | ❌ | Remote-Name |
| `branch` | string | ❌ | Branch |
| `force` | boolean | ❌ | Force-Push |

---

#### `git_fetch`
Holt Metadaten von Remote.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `repo_path` | string | ✅ | Pfad zum Repository |
| `all` | boolean | ❌ | Alle Remotes |

---

#### `scan_repos`
Findet alle Git-Repos in Verzeichnis.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `base_path` | string | ❌ | Suchpfad |
| `max_depth` | integer | ❌ | Maximale Suchtiefe |

---

#### `multi_status`
Status mehrerer Repos gleichzeitig.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `repo_paths` | list | ✅ | Liste von Repository-Pfaden |

---

## 📊 Project Manager Server

> **Projekt-Scanner für D:\ Laufwerk**

| Info | Wert |
|------|------|
| Pfad | `servers/project-manager-server/server.py` |
| Abhängigkeiten | `fastmcp>=2.0.0`, `pyyaml` |
| Konfiguration | `PROJECTS_BASE_PATH` |

### Erkannte Projekttypen

- 🐍 **Python**: `requirements.txt`, `pyproject.toml`, `setup.py`
- 📦 **Node.js**: `package.json`
- 🦋 **Flutter**: `pubspec.yaml`
- 🐳 **Docker**: `Dockerfile`, `docker-compose.yml`
- 🦀 **Rust**: `Cargo.toml`
- 🐹 **Go**: `go.mod`
- ☕ **Java**: `pom.xml`, `build.gradle`
- #️⃣ **C#**: `*.csproj`, `*.sln`

### Tools

#### `scan_all_projects`
Scannt alle Projekte im Basis-Pfad.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `base_path` | string | ❌ | Pfad (Standard: `PROJECTS_BASE_PATH`) |
| `max_depth` | integer | ❌ | Suchtiefe (Standard: 3) |

---

#### `project_details`
Zeigt Details eines Projekts.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `project_path` | string | ✅ | Pfad zum Projekt |

**Ausgabe:**
```
Projekt: DressCode
Pfad: d:\projekte\DressCode
Typ: Flutter
Größe: 45 MB (324 Dateien)
Letzte Änderung: 2024-01-20
Dependencies: 15 packages
Git: main branch, 5 uncommitted changes
```

---

#### `check_python_deps`
Prüft Python-Dependencies auf Updates.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `project_path` | string | ✅ | Pfad zum Python-Projekt |

---

#### `check_node_deps`
Prüft Node.js-Dependencies auf Updates.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `project_path` | string | ✅ | Pfad zum Node.js-Projekt |

---

#### `projects_summary`
Zeigt Zusammenfassung aller Projekte.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `base_path` | string | ❌ | Pfad |

**Ausgabe:**
```
📊 Projekt-Zusammenfassung
─────────────────────────
Gesamt: 12 Projekte

Nach Typ:
  🐍 Python: 5
  📦 Node.js: 3
  🦋 Flutter: 2
  🐳 Docker: 2

Nach Status:
  ✅ Aktiv (< 30 Tage): 8
  ⏸️ Inaktiv: 4
```

---

#### `find_outdated_projects`
Findet Projekte mit alten Dependencies.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `base_path` | string | ❌ | Pfad |

---

#### `find_large_projects`
Findet große Projekte (nach Dateigröße).

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `base_path` | string | ❌ | Pfad |
| `min_size_mb` | integer | ❌ | Mindestgröße (Standard: 100 MB) |

---

## 🔐 SSH Server

> **Remote Server-Verwaltung via SSH**

| Info | Wert |
|------|------|
| Pfad | `servers/ssh-server/server.py` |
| Abhängigkeiten | `fastmcp>=2.0.0`, `paramiko` |
| Konfiguration | `SSH_HOST_*`, `SSH_PASSWORD_*`, `SSH_KEY_*` |

### Einrichtung

Für jeden SSH-Host in `.env`:

```env
# IONOS Server
SSH_HOST_IONOS=root@server.ionos.de:22
SSH_PASSWORD_IONOS=mein-passwort

# Raspberry Pi (mit SSH-Key)
SSH_HOST_PI=pi@192.168.0.100:22
SSH_KEY_PI=C:\Users\ich\.ssh\id_rsa
```

### Tools

#### `list_ssh_hosts`
Listet konfigurierte SSH-Hosts.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| - | - | - | Keine Parameter |

---

#### `test_ssh_connection`
Testet SSH-Verbindung.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `host_name` | string | ✅ | Host-Name (z.B. `IONOS`) |

---

#### `ssh_exec`
Führt Befehl auf Remote-Server aus.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `host_name` | string | ✅ | Host-Name |
| `command` | string | ✅ | Shell-Befehl |
| `timeout` | integer | ❌ | Timeout in Sekunden |

**Beispiel:**
```
Agent: ssh_exec("IONOS", "df -h")
→ Zeigt Festplatten-Nutzung des Servers
```

---

#### `ssh_multi_exec`
Führt Befehl auf mehreren Servern aus.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `host_names` | list | ✅ | Liste von Host-Namen |
| `command` | string | ✅ | Shell-Befehl |

---

#### `ssh_read_file`
Liest Datei von Remote-Server.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `host_name` | string | ✅ | Host-Name |
| `remote_path` | string | ✅ | Pfad auf Server |

---

#### `ssh_write_file`
Schreibt Datei auf Remote-Server.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `host_name` | string | ✅ | Host-Name |
| `remote_path` | string | ✅ | Pfad auf Server |
| `content` | string | ✅ | Dateiinhalt |

---

#### `ssh_list_dir`
Listet Verzeichnis auf Remote-Server.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `host_name` | string | ✅ | Host-Name |
| `remote_path` | string | ✅ | Pfad auf Server |

---

#### `ssh_upload_file`
Lädt lokale Datei auf Server hoch.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `host_name` | string | ✅ | Host-Name |
| `local_path` | string | ✅ | Lokaler Dateipfad |
| `remote_path` | string | ✅ | Zielpfad auf Server |

---

#### `ssh_download_file`
Lädt Datei von Server herunter.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `host_name` | string | ✅ | Host-Name |
| `remote_path` | string | ✅ | Pfad auf Server |
| `local_path` | string | ✅ | Lokaler Zielpfad |

---

#### `server_status`
Zeigt Server-Status (CPU, RAM, Disk).

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `host_name` | string | ✅ | Host-Name |

**Ausgabe:**
```
🖥️ Server: IONOS
─────────────────
CPU: 23% (4 Cores)
RAM: 2.1 GB / 8.0 GB (26%)
Disk: 45 GB / 100 GB (45%)
Uptime: 45 days, 3:22:15
Load: 0.42, 0.38, 0.35
```

---

#### `read_server_logs`
Liest Server-Logs.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `host_name` | string | ✅ | Host-Name |
| `log_file` | string | ❌ | Log-Datei (Standard: `/var/log/syslog`) |
| `lines` | integer | ❌ | Letzte N Zeilen |

---

#### `list_processes`
Listet laufende Prozesse auf Server.

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|--------------|--------------|
| `host_name` | string | ✅ | Host-Name |
| `filter` | string | ❌ | Prozess-Filter (z.B. `python`) |

---

## 📎 Anhang

### Server aktivieren/deaktivieren

In `agent/mcp-servers.json`:

```json
{
  "servers": { ... },
  "activeServers": ["demo", "filesystem", "git", "flutter"]
}
```

### Neue Server hinzufügen

1. Verzeichnis erstellen: `servers/mein-server/`
2. `server.py` mit FastMCP erstellen
3. `requirements.txt` mit Dependencies
4. In `mcp-servers.json` registrieren
5. Dependencies installieren: `pip install -r servers/mein-server/requirements.txt`

### Troubleshooting

| Problem | Lösung |
|---------|--------|
| Server startet nicht | `LOG_LEVEL=debug` in `.env` setzen |
| Tool nicht gefunden | Server in `activeServers` prüfen |
| Timeout-Fehler | `MCP_TIMEOUT` erhöhen |
| Authentifizierungs-Fehler | API-Keys in `.env` prüfen |

---

*Dokumentation generiert für MCP Agent Workbench v1.0.0*
