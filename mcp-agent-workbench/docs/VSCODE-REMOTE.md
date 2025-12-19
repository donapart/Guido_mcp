# 🖥️ VS Code Remote-Entwicklung - Entscheidungshilfe

> **Wann benutze ich was?** - Ein praktischer Guide für dein Setup

---

## 🎯 Schnell-Entscheidung

```
Wo willst du entwickeln?
│
├─► Lokal auf Windows, aber Linux-Tools brauchen?
│   └─► WSL (Option 2/3)
│
├─► Auf einem Remote-Server?
│   │
│   ├─► Server hat offenen SSH-Port?
│   │   └─► Remote-SSH (Option 4/5)
│   │
│   └─► Server hat KEINEN offenen SSH-Port?
│       └─► Remote-Tunnel (Option 1)
│
├─► In einem Docker-Container?
│   │
│   ├─► Neues Projekt, saubere Umgebung?
│   │   └─► Neuer Entwicklungscontainer (Option 7)
│   │
│   ├─► Bestehendes Projekt containerisieren?
│   │   └─► Dev-Container hinzufügen (Option 9)
│   │
│   └─► Laufenden Container debuggen?
│       └─► An Container anfügen (Option 8)
│
├─► In der Cloud (GitHub)?
│   └─► Codespaces (Option 11/12)
│
├─► Mit jemandem zusammenarbeiten?
│   └─► Live Share (Option 13/14)
│
└─► Nur kurz in ein Repo schauen?
    └─► Remote Repository (Option 15)
```

---

## 📊 Übersicht: Alle 15 Optionen

| # | Option | Wann benutzen | Voraussetzung |
|---|--------|---------------|---------------|
| 1 | **Remote-Tunnel** | Server ohne SSH, aber mit Internet | `code tunnel` auf Server |
| 2 | **WSL** | Linux auf Windows (Standard-Distro) | WSL installiert |
| 3 | **WSL über Distribution** | Mehrere Linux-Distros | Mehrere WSL-Distros |
| 4 | **Remote-SSH** | Server mit SSH-Zugang | SSH-Zugang |
| 5 | **Fenster mit Host verbinden** | Wie 4, aber aktuelles Fenster | SSH-Zugang |
| 6 | **Container-Config öffnen** | Dev-Container anpassen | `.devcontainer` vorhanden |
| 7 | **Neuer Dev-Container** | Saubere Docker-Umgebung | Docker Desktop |
| 8 | **An Container anfügen** | Laufenden Container debuggen | Container läuft |
| 9 | **Dev-Container hinzufügen** | Projekt containerisieren | Docker Desktop |
| 10 | **Im Container öffnen** | In Dev-Container wechseln | `.devcontainer` vorhanden |
| 11 | **Codespace verbinden** | GitHub Cloud-VM nutzen | GitHub Codespaces |
| 12 | **Codespace erstellen** | Neue Cloud-VM | GitHub Codespaces |
| 13 | **Live Share starten** | Pair Programming | Live Share Extension |
| 14 | **Live Share beitreten** | Session beitreten | Live Share Extension |
| 15 | **Remote Repository** | Repo ohne Clone öffnen | Extension |

---

## 🏠 Für DEIN Setup: Konkrete Empfehlungen

Basierend auf deinem MCP Agent Workbench Setup:

### Dein aktuelles Setup
```
┌─────────────────────────────────────────────────────────────┐
│  Lokaler Windows-PC                                         │
│  └─► VS Code mit MCP Agent Workbench                       │
│      └─► Verbindet sich zu:                                │
│          • Docker auf 192.168.0.27:2375                    │
│          • Ollama auf 192.168.0.27:11434                   │
│          • (Potentiell) IONOS Server via SSH              │
└─────────────────────────────────────────────────────────────┘
```

### Empfohlene Remote-Optionen für dich:

#### 1️⃣ **Remote-SSH** → Für IONOS Server
```
Situation: Du willst direkt auf deinem IONOS-Server entwickeln/debuggen

Einrichtung:
1. SSH Extension installieren
2. In ~/.ssh/config eintragen:
   Host ionos
     HostName dein-server.ionos.de
     User root
     IdentityFile ~/.ssh/id_rsa

3. "Verbindung mit Host herstellen..." → ionos
4. VS Code öffnet Fenster direkt auf dem Server

Wann sinnvoll:
✅ Server-Logs live beobachten
✅ Configs direkt bearbeiten
✅ Server-Software debuggen
✅ Docker auf Server verwalten
```

#### 2️⃣ **WSL** → Für Linux-kompatible Entwicklung
```
Situation: Du willst Linux-Tools auf Windows nutzen

Einrichtung:
1. PowerShell (Admin): wsl --install
2. Ubuntu einrichten
3. "Verbindung mit WSL herstellen..."

Wann sinnvoll:
✅ MCP Server testen (Python läuft besser in Linux)
✅ Bash-Skripte entwickeln
✅ Docker in WSL nutzen (performanter als Docker Desktop)
✅ Linux-Pfade statt Windows-Pfade
```

#### 3️⃣ **Dev-Container** → Für saubere MCP-Entwicklung
```
Situation: Du willst eine isolierte, reproduzierbare Umgebung

Einrichtung:
1. Docker Desktop installiert
2. "Konfigurationsdateien für Entwicklungscontainer hinzufügen..."
3. Python-Template wählen
4. "Im Container erneut öffnen"

Wann sinnvoll:
✅ Jeder MCP-Server in eigenem Container
✅ Keine Konflikte zwischen Python-Versionen
✅ Team kann exakt gleiche Umgebung nutzen
✅ CI/CD nutzt gleichen Container
```

#### 4️⃣ **An Container anfügen** → Für Docker-Debugging
```
Situation: Du willst in einen laufenden Container auf 192.168.0.27 schauen

Einrichtung:
1. Docker Extension installiert
2. DOCKER_HOST=tcp://192.168.0.27:2375 setzen
3. "An ausgeführten Container anfügen..."
4. Container wählen

Wann sinnvoll:
✅ Ollama-Container debuggen
✅ Andere Services auf Docker-Server untersuchen
✅ Logs, Configs, Prozesse im Container checken
```

---

## 🔀 Kombinationen für Power-User

### Szenario A: Multi-Server Entwicklung
```
┌─────────────────────────────────────────────────────────────┐
│  VS Code Fenster 1: Lokal (MCP Agent Workbench)            │
│  VS Code Fenster 2: Remote-SSH zu IONOS (Server-Code)      │
│  VS Code Fenster 3: An Docker-Container (Ollama debugging) │
└─────────────────────────────────────────────────────────────┘
```

### Szenario B: Pair Programming
```
Du: VS Code mit Live Share gestartet
    ↓ Link teilen
Kollege: "Join Collaboration Session"
    ↓
Beide arbeiten gleichzeitig im Code
```

### Szenario C: Unterwegs ohne lokales Setup
```
Laptop ohne Dev-Tools
    ↓
"Connect to Codespace..."
    ↓
Vollständige Entwicklungsumgebung in der Cloud
```

---

## 🛠️ Setup-Anleitungen

### Remote-SSH einrichten (für IONOS)

**1. Extension installieren:**
```
Extensions → "Remote - SSH" suchen → Install
```

**2. SSH-Key erstellen (falls nicht vorhanden):**
```powershell
ssh-keygen -t ed25519 -C "mcp-agent"
# Enter drücken (Standard-Pfad)
# Passphrase optional
```

**3. Key auf Server kopieren:**
```powershell
# Manuell oder:
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh root@dein-server "cat >> ~/.ssh/authorized_keys"
```

**4. SSH-Config erstellen:**
```powershell
notepad $env:USERPROFILE\.ssh\config
```
Inhalt:
```
Host ionos
    HostName dein-server.ionos.de
    User root
    IdentityFile ~/.ssh/id_ed25519
    
Host docker-server
    HostName 192.168.0.27
    User guido
    IdentityFile ~/.ssh/id_ed25519
```

**5. Verbinden:**
- `F1` → "Remote-SSH: Connect to Host..." → Host wählen

---

### WSL einrichten

**1. WSL installieren:**
```powershell
# Als Administrator
wsl --install
# Neustart
```

**2. Ubuntu einrichten:**
```bash
# Nach Neustart öffnet sich Ubuntu
# Username + Passwort setzen

# Updates
sudo apt update && sudo apt upgrade -y

# Python für MCP
sudo apt install python3 python3-pip python3-venv -y
```

**3. In VS Code:**
- Extension "WSL" installieren
- `F1` → "WSL: Connect to WSL"

**4. Projekt in WSL öffnen:**
```
# In WSL-Terminal:
cd /mnt/d/Guido_mcp/mcp-agent-workbench
code .
```

---

### Dev-Container für MCP erstellen

**1. Docker Desktop installieren:**
- https://www.docker.com/products/docker-desktop/

**2. Extension installieren:**
- "Dev Containers" Extension

**3. Config erstellen:**

Erstelle `.devcontainer/devcontainer.json`:
```json
{
    "name": "MCP Agent Workbench",
    "image": "mcr.microsoft.com/devcontainers/python:3.11",
    "features": {
        "ghcr.io/devcontainers/features/node:1": {
            "version": "18"
        }
    },
    "postCreateCommand": "pip install -r requirements.txt",
    "customizations": {
        "vscode": {
            "extensions": [
                "ms-python.python",
                "ms-python.vscode-pylance"
            ]
        }
    },
    "forwardPorts": [8080],
    "remoteEnv": {
        "OLLAMA_HOST": "http://192.168.0.27:11434",
        "DOCKER_HOST": "tcp://192.168.0.27:2375"
    }
}
```

**4. Container starten:**
- `F1` → "Dev Containers: Reopen in Container"

---

## ❓ FAQ

### Wann SSH vs. Tunnel?

| SSH | Tunnel |
|-----|--------|
| Server hat Port 22 offen | Server kann nur raus, nicht rein |
| Direkter Zugriff | NAT, Firewall, kein Port-Forwarding |
| Schneller (direkter) | Etwas langsamer (über Microsoft) |
| Klassische Server | Homelab, Uni-Rechner, Firmen-PCs |

### Wann WSL vs. Dev-Container?

| WSL | Dev-Container |
|-----|---------------|
| Eine Linux-Umgebung für alles | Pro Projekt eigene Umgebung |
| Schneller (kein Container-Overhead) | Komplett isoliert |
| Gut für allgemeine Linux-Arbeit | Gut für Team-Entwicklung |
| Persistent (Änderungen bleiben) | Reproduzierbar (rebuild möglich) |

### Wann Codespace vs. eigener Server?

| Codespaces | Eigener Server |
|------------|----------------|
| Kein eigener Server nötig | Volle Kontrolle |
| Bezahlung nach Nutzung | Einmalig/monatlich |
| Perfekt für GitHub-Projekte | Für alles |
| Schnell starten | Mehr Setup |

---

## 🔗 Integration mit MCP Agent Workbench

### SSH-Server nutzen (von Workbench aus)

Dein MCP `ssh-server` kann SSH-Befehle ausführen. Das ist **anders** als VS Code Remote-SSH:

| MCP SSH-Server | VS Code Remote-SSH |
|----------------|-------------------|
| Agent führt Befehle aus | Du entwickelst auf Server |
| Automatisierung | Interaktiv |
| Tool-Aufrufe | Normales Editing |
| `ssh_exec("IONOS", "df -h")` | Ordner öffnen, Dateien bearbeiten |

**Beide ergänzen sich:**
- Remote-SSH: Für "ich will auf dem Server arbeiten"
- MCP SSH: Für "der Agent soll auf dem Server was tun"

### Docker Integration

| MCP Docker-Server | VS Code Dev-Container |
|-------------------|----------------------|
| Container verwalten (start/stop/logs) | IN Container entwickeln |
| Monitoring | Coding |
| `list_containers()` | Ordner im Container öffnen |

**Beide ergänzen sich:**
- Dev-Container: Für "ich entwickle in sauberer Umgebung"
- MCP Docker: Für "der Agent verwaltet Container"

---

## 📚 Weiterführende Links

- [VS Code Remote Development](https://code.visualstudio.com/docs/remote/remote-overview)
- [WSL Dokumentation](https://docs.microsoft.com/windows/wsl/)
- [Dev Containers Spec](https://containers.dev/)
- [GitHub Codespaces](https://github.com/features/codespaces)
- [Live Share](https://visualstudio.microsoft.com/services/live-share/)

---

*Erstellt für MCP Agent Workbench v1.0.0*
