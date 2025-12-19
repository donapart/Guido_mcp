#!/usr/bin/env python3
"""Repariert VS Code mcp.json mit vollständigem Python-Pfad"""

import json
import os
import sys

# Finde Python-Pfad
python_path = sys.executable.replace("\\", "/")
print(f"🐍 Python gefunden: {python_path}")

mcp_config = {
    "servers": {
        "guido-mcp": {
            "command": python_path,
            "args": ["d:/Guido_mcp/mcp-agent-workbench/mcp-bridge-server/server.py"],
            "env": {
                "MCP_AUTO_CONNECT": "filesystem,git,demo",
                "ALLOWED_DIRECTORIES": "d:/,c:/Users/donApart,f:/",
                "PYTHONIOENCODING": "utf-8"
            },
            "type": "stdio"
        },
        "huggingface": {
            "type": "http", 
            "url": "https://hf.co/mcp", 
            "gallery": True
        },
        "microsoft-docs": {
            "type": "http", 
            "url": "https://learn.microsoft.com/api/mcp", 
            "gallery": True
        },
        "deepwiki": {
            "type": "http", 
            "url": "https://mcp.deepwiki.com/sse", 
            "gallery": True
        },
        "GitKraken": {
            "command": "c:/Users/donApart/AppData/Roaming/Code/User/globalStorage/eamodio.gitlens/gk.exe",
            "type": "stdio",
            "args": ["mcp", "--host=vscode", "--source=gitlens", "--scheme=vscode"]
        },
        "markitdown": {
            "type": "stdio", 
            "command": "uvx", 
            "args": ["markitdown-mcp"], 
            "gallery": True
        },
        "sequentialthinking": {
            "type": "stdio", 
            "command": "npx", 
            "args": ["-y", "@modelcontextprotocol/server-sequential-thinking@latest"], 
            "gallery": True
        }
    },
    "inputs": []
}

if __name__ == "__main__":
    path = os.path.expandvars(r"%APPDATA%\Code\User\mcp.json")
    
    # Backup
    if os.path.exists(path):
        backup = path + ".backup2"
        with open(path, 'r', encoding='utf-8') as f:
            old = f.read()
        with open(backup, 'w', encoding='utf-8') as f:
            f.write(old)
        print(f"📦 Backup: {backup}")
    
    # Schreiben
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(mcp_config, f, indent=4)
    
    print(f"✅ mcp.json aktualisiert: {path}")
    print()
    print("🔧 guido-mcp Konfiguration:")
    print(f"   command: {mcp_config['servers']['guido-mcp']['command']}")
    print(f"   args: {mcp_config['servers']['guido-mcp']['args']}")
    print()
    print("⚡ Jetzt: Ctrl+Shift+P → 'Developer: Reload Window'")
