#!/usr/bin/env python3
"""Aktualisiert VS Code mcp.json für dynamisches Tool-Loading"""

import json
import os

mcp_config = {
    "servers": {
        "guido-mcp": {
            "command": "python",
            "args": ["d:/Guido_mcp/mcp-agent-workbench/mcp-bridge-server/server.py"],
            "env": {
                "MCP_AUTO_CONNECT": "filesystem,git,demo",
                "ALLOWED_DIRECTORIES": "d:/,c:/Users/donApart,f:/"
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
            "command": "c:\\Users\\donApart\\AppData\\Roaming\\Code\\User\\globalStorage\\eamodio.gitlens\\gk.exe",
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
        },
        "codacy": {
            "type": "stdio", 
            "command": "npx", 
            "args": ["-y", "@codacy/codacy-mcp@latest"], 
            "env": {"CODACY_ACCOUNT_TOKEN": "${input:codacy_account_token}"}, 
            "gallery": True
        },
        "memory": {
            "type": "stdio", 
            "command": "npx", 
            "args": ["-y", "@modelcontextprotocol/server-memory@latest"], 
            "env": {"MEMORY_FILE_PATH": "${input:memory_file_path}"}, 
            "gallery": True
        }
    },
    "inputs": [
        {
            "id": "codacy_account_token", 
            "type": "promptString", 
            "description": "Codacy Account Token", 
            "password": True
        },
        {
            "id": "memory_file_path", 
            "type": "promptString", 
            "description": "Memory file path", 
            "password": False
        }
    ]
}

if __name__ == "__main__":
    path = os.path.expandvars(r"%APPDATA%\Code\User\mcp.json")
    
    # Backup erstellen
    if os.path.exists(path):
        backup = path + ".backup"
        with open(path, 'r', encoding='utf-8') as f:
            old = f.read()
        with open(backup, 'w', encoding='utf-8') as f:
            f.write(old)
        print(f"📦 Backup erstellt: {backup}")
    
    # Neue Config schreiben
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(mcp_config, f, indent=4)
    
    print(f"✅ mcp.json aktualisiert: {path}")
    print(f"📊 Server: {len(mcp_config['servers'])} (statt ~25)")
    print()
    print("🔧 Aktive Server:")
    for name in mcp_config["servers"]:
        print(f"   - {name}")
    print()
    print("⚡ WICHTIG: VS Code neu laden (Ctrl+Shift+P → Reload Window)")
