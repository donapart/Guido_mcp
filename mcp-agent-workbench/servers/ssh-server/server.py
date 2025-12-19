"""
SSH MCP Server - Remote Server Verwaltung via SSH

Tools für:
- Remote-Befehle ausführen
- Dateien übertragen (SCP)
- Logs lesen
- Server-Status prüfen
- IONOS Webspace verwalten

WICHTIG: SSH-Keys oder Passwort in .env konfigurieren
"""

import os
import asyncio
from pathlib import Path
from datetime import datetime
from fastmcp import FastMCP
from pydantic import Field
from typing import Optional
import paramiko
import io

# Server initialisieren
mcp = FastMCP(
    "SSH Server",
    instructions="Remote Server via SSH - Befehle, Dateien, Logs"
)

# SSH-Konfiguration aus Environment
SSH_HOSTS = {}  # Wird aus .env geladen

def load_ssh_config():
    """Lade SSH-Hosts aus Environment"""
    hosts = {}
    
    # Format: SSH_HOST_name=user@host:port
    # Passwort: SSH_PASSWORD_name=xxx
    # Key: SSH_KEY_name=path/to/key
    
    for key, value in os.environ.items():
        if key.startswith("SSH_HOST_"):
            name = key[9:].lower()
            # Parse user@host:port
            if "@" in value:
                user, rest = value.split("@", 1)
                if ":" in rest:
                    host, port = rest.split(":", 1)
                    port = int(port)
                else:
                    host = rest
                    port = 22
            else:
                user = "root"
                host = value.split(":")[0]
                port = int(value.split(":")[1]) if ":" in value else 22
            
            hosts[name] = {
                "user": user,
                "host": host,
                "port": port,
                "password": os.getenv(f"SSH_PASSWORD_{name.upper()}"),
                "key_file": os.getenv(f"SSH_KEY_{name.upper()}")
            }
    
    return hosts


def get_ssh_client(host_name: str) -> paramiko.SSHClient:
    """Erstelle SSH-Verbindung"""
    hosts = load_ssh_config()
    
    if host_name not in hosts:
        raise ValueError(f"SSH-Host '{host_name}' nicht konfiguriert. Verfügbar: {list(hosts.keys())}")
    
    config = hosts[host_name]
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    connect_args = {
        "hostname": config["host"],
        "port": config["port"],
        "username": config["user"]
    }
    
    if config["key_file"]:
        connect_args["key_filename"] = config["key_file"]
    elif config["password"]:
        connect_args["password"] = config["password"]
    else:
        raise ValueError(f"Weder Passwort noch Key für Host '{host_name}' konfiguriert")
    
    client.connect(**connect_args)
    return client


# ==================== CONNECTION TOOLS ====================

@mcp.tool()
async def list_ssh_hosts() -> dict:
    """
    Liste alle konfigurierten SSH-Hosts.
    
    Returns:
        Verfügbare Hosts mit Verbindungsinfo
    """
    hosts = load_ssh_config()
    
    if not hosts:
        return {
            "success": False,
            "hosts": [],
            "hint": "Konfiguriere SSH-Hosts in .env:\nSSH_HOST_NAME=user@host:port\nSSH_PASSWORD_NAME=xxx"
        }
    
    return {
        "success": True,
        "hosts": [
            {
                "name": name,
                "host": config["host"],
                "port": config["port"],
                "user": config["user"],
                "auth": "key" if config["key_file"] else "password"
            }
            for name, config in hosts.items()
        ]
    }


@mcp.tool()
async def test_ssh_connection(
    host_name: str = Field(description="Name des SSH-Hosts aus Konfiguration")
) -> dict:
    """
    Teste SSH-Verbindung zu einem Host.
    
    Args:
        host_name: Konfigurierter Host-Name
        
    Returns:
        Verbindungsstatus
    """
    try:
        client = get_ssh_client(host_name)
        
        # Test mit einfachem Befehl
        stdin, stdout, stderr = client.exec_command("hostname && whoami")
        output = stdout.read().decode().strip()
        
        client.close()
        
        return {
            "success": True,
            "host_name": host_name,
            "status": "connected",
            "server_info": output
        }
    except Exception as e:
        return {"success": False, "host_name": host_name, "error": str(e)}


# ==================== COMMAND TOOLS ====================

@mcp.tool()
async def ssh_exec(
    host_name: str = Field(description="Name des SSH-Hosts"),
    command: str = Field(description="Auszuführender Befehl"),
    timeout: int = Field(default=30, description="Timeout in Sekunden")
) -> dict:
    """
    Führe einen Befehl auf Remote-Server aus.
    
    Args:
        host_name: SSH-Host
        command: Shell-Befehl
        timeout: Max. Wartezeit
        
    Returns:
        Befehlsausgabe
    """
    try:
        client = get_ssh_client(host_name)
        
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        
        output = stdout.read().decode("utf-8", errors="replace")
        errors = stderr.read().decode("utf-8", errors="replace")
        exit_code = stdout.channel.recv_exit_status()
        
        client.close()
        
        return {
            "success": exit_code == 0,
            "host": host_name,
            "command": command,
            "exit_code": exit_code,
            "stdout": output[:10000],  # Limit
            "stderr": errors[:2000] if errors else None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def ssh_multi_exec(
    host_name: str = Field(description="Name des SSH-Hosts"),
    commands: str = Field(description="Befehle, getrennt durch Semikolon")
) -> dict:
    """
    Führe mehrere Befehle nacheinander aus.
    
    Args:
        host_name: SSH-Host
        commands: "cmd1; cmd2; cmd3"
        
    Returns:
        Kombinierte Ausgabe
    """
    try:
        client = get_ssh_client(host_name)
        
        # Kombiniere zu einem Befehl
        combined = commands.replace(";", " && ")
        
        stdin, stdout, stderr = client.exec_command(combined, timeout=60)
        
        output = stdout.read().decode("utf-8", errors="replace")
        errors = stderr.read().decode("utf-8", errors="replace")
        
        client.close()
        
        return {
            "success": True,
            "host": host_name,
            "output": output[:10000],
            "errors": errors[:2000] if errors else None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== FILE TOOLS ====================

@mcp.tool()
async def ssh_read_file(
    host_name: str = Field(description="Name des SSH-Hosts"),
    remote_path: str = Field(description="Pfad zur Datei auf dem Server"),
    max_lines: int = Field(default=500, description="Max. Zeilen")
) -> dict:
    """
    Lese eine Datei vom Remote-Server.
    
    Args:
        host_name: SSH-Host
        remote_path: Dateipfad
        max_lines: Zeilenlimit
        
    Returns:
        Dateiinhalt
    """
    try:
        client = get_ssh_client(host_name)
        sftp = client.open_sftp()
        
        with sftp.file(remote_path, "r") as f:
            content = f.read().decode("utf-8", errors="replace")
        
        sftp.close()
        client.close()
        
        lines = content.splitlines()
        truncated = len(lines) > max_lines
        
        return {
            "success": True,
            "host": host_name,
            "path": remote_path,
            "content": "\n".join(lines[:max_lines]),
            "total_lines": len(lines),
            "truncated": truncated
        }
    except FileNotFoundError:
        return {"success": False, "error": f"Datei nicht gefunden: {remote_path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def ssh_write_file(
    host_name: str = Field(description="Name des SSH-Hosts"),
    remote_path: str = Field(description="Zielpfad auf dem Server"),
    content: str = Field(description="Dateiinhalt")
) -> dict:
    """
    Schreibe eine Datei auf den Remote-Server.
    
    Args:
        host_name: SSH-Host
        remote_path: Zielpfad
        content: Inhalt
        
    Returns:
        Bestätigung
    """
    try:
        client = get_ssh_client(host_name)
        sftp = client.open_sftp()
        
        with sftp.file(remote_path, "w") as f:
            f.write(content.encode("utf-8"))
        
        sftp.close()
        client.close()
        
        return {
            "success": True,
            "host": host_name,
            "path": remote_path,
            "bytes_written": len(content.encode("utf-8"))
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def ssh_list_dir(
    host_name: str = Field(description="Name des SSH-Hosts"),
    remote_path: str = Field(default="/", description="Verzeichnispfad")
) -> dict:
    """
    Liste Verzeichnisinhalt auf Remote-Server.
    
    Args:
        host_name: SSH-Host
        remote_path: Pfad
        
    Returns:
        Dateien und Ordner
    """
    try:
        client = get_ssh_client(host_name)
        sftp = client.open_sftp()
        
        items = []
        for item in sftp.listdir_attr(remote_path):
            is_dir = item.st_mode and (item.st_mode & 0o40000)
            items.append({
                "name": item.filename,
                "type": "dir" if is_dir else "file",
                "size": item.st_size,
                "modified": datetime.fromtimestamp(item.st_mtime).isoformat() if item.st_mtime else None
            })
        
        sftp.close()
        client.close()
        
        return {
            "success": True,
            "host": host_name,
            "path": remote_path,
            "items": sorted(items, key=lambda x: (x["type"] != "dir", x["name"]))
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def ssh_upload_file(
    host_name: str = Field(description="Name des SSH-Hosts"),
    local_path: str = Field(description="Lokaler Dateipfad"),
    remote_path: str = Field(description="Zielpfad auf Server")
) -> dict:
    """
    Lade eine lokale Datei auf den Server hoch.
    
    Args:
        host_name: SSH-Host
        local_path: Lokale Datei
        remote_path: Ziel auf Server
        
    Returns:
        Übertragungsstatus
    """
    try:
        if not Path(local_path).exists():
            return {"success": False, "error": f"Lokale Datei nicht gefunden: {local_path}"}
        
        client = get_ssh_client(host_name)
        sftp = client.open_sftp()
        
        sftp.put(local_path, remote_path)
        
        # Größe prüfen
        stat = sftp.stat(remote_path)
        
        sftp.close()
        client.close()
        
        return {
            "success": True,
            "host": host_name,
            "local": local_path,
            "remote": remote_path,
            "size_bytes": stat.st_size
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def ssh_download_file(
    host_name: str = Field(description="Name des SSH-Hosts"),
    remote_path: str = Field(description="Dateipfad auf Server"),
    local_path: str = Field(description="Lokaler Zielpfad")
) -> dict:
    """
    Lade eine Datei vom Server herunter.
    
    Args:
        host_name: SSH-Host
        remote_path: Datei auf Server
        local_path: Lokales Ziel
        
    Returns:
        Übertragungsstatus
    """
    try:
        client = get_ssh_client(host_name)
        sftp = client.open_sftp()
        
        # Lokales Verzeichnis erstellen falls nötig
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        
        sftp.get(remote_path, local_path)
        
        sftp.close()
        client.close()
        
        local_size = Path(local_path).stat().st_size
        
        return {
            "success": True,
            "host": host_name,
            "remote": remote_path,
            "local": local_path,
            "size_bytes": local_size
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== SERVER STATUS TOOLS ====================

@mcp.tool()
async def server_status(
    host_name: str = Field(description="Name des SSH-Hosts")
) -> dict:
    """
    Zeige Server-Status (CPU, RAM, Disk).
    
    Args:
        host_name: SSH-Host
        
    Returns:
        Systeminfo
    """
    try:
        client = get_ssh_client(host_name)
        
        commands = {
            "hostname": "hostname",
            "uptime": "uptime",
            "memory": "free -h | head -2",
            "disk": "df -h / | tail -1",
            "load": "cat /proc/loadavg",
            "os": "cat /etc/os-release | head -2"
        }
        
        results = {}
        for name, cmd in commands.items():
            stdin, stdout, stderr = client.exec_command(cmd)
            results[name] = stdout.read().decode().strip()
        
        client.close()
        
        return {
            "success": True,
            "host": host_name,
            "status": results
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def read_server_logs(
    host_name: str = Field(description="Name des SSH-Hosts"),
    log_file: str = Field(default="/var/log/syslog", description="Log-Datei"),
    lines: int = Field(default=50, description="Anzahl Zeilen")
) -> dict:
    """
    Lese Server-Logs.
    
    Args:
        host_name: SSH-Host
        log_file: Pfad zur Log-Datei
        lines: Anzahl letzte Zeilen
        
    Returns:
        Log-Inhalt
    """
    try:
        client = get_ssh_client(host_name)
        
        stdin, stdout, stderr = client.exec_command(f"tail -n {lines} {log_file}")
        output = stdout.read().decode("utf-8", errors="replace")
        
        client.close()
        
        return {
            "success": True,
            "host": host_name,
            "log_file": log_file,
            "lines": lines,
            "content": output
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def list_processes(
    host_name: str = Field(description="Name des SSH-Hosts"),
    filter_name: Optional[str] = Field(default=None, description="Prozessname zum Filtern")
) -> dict:
    """
    Liste laufende Prozesse.
    
    Args:
        host_name: SSH-Host
        filter_name: Optional: nur Prozesse mit diesem Namen
        
    Returns:
        Prozessliste
    """
    try:
        client = get_ssh_client(host_name)
        
        if filter_name:
            cmd = f"ps aux | grep -i {filter_name} | grep -v grep"
        else:
            cmd = "ps aux --sort=-%mem | head -20"
        
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read().decode()
        
        client.close()
        
        return {
            "success": True,
            "host": host_name,
            "filter": filter_name,
            "processes": output
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# Server starten
if __name__ == "__main__":
    mcp.run()
