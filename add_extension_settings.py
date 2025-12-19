#!/usr/bin/env python3
"""Ergänzt fehlende mcpAgent Extension-Einstellungen in VS Code settings.json"""

import json
import os
import re

settings_path = os.path.expandvars(r"%APPDATA%\Code\User\settings.json")

# Aktuelle Settings laden
with open(settings_path, 'r', encoding='utf-8') as f:
    content = f.read()

# JSON mit Kommentaren parsen (VS Code erlaubt Kommentare)
# Entferne Kommentare für Parsing
clean_content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
clean_content = re.sub(r'/\*.*?\*/', '', clean_content, flags=re.DOTALL)

try:
    settings = json.loads(clean_content)
except json.JSONDecodeError as e:
    print(f"❌ JSON Parse Error: {e}")
    print("Füge die Einstellungen manuell über VS Code UI hinzu.")
    exit(1)

# Neue/fehlende Einstellungen
new_settings = {
    # Modell-Einstellungen
    "mcpAgent.model": "claude-sonnet-4-20250514",
    
    # Google AI (optional - für Gemini)
    "mcpAgent.googleApiKey": "",
    
    # Azure (optional)
    "mcpAgent.azureEndpoint": "",
    "mcpAgent.azureApiKey": "",
    "mcpAgent.azureDeployment": "",
    
    # Ollama
    "mcpAgent.ollamaEndpoint": "http://localhost:11434",
    
    # Generation-Parameter
    "mcpAgent.temperature": 0.7,
    "mcpAgent.maxTokens": 4096,
    "mcpAgent.topP": 1.0,
    "mcpAgent.frequencyPenalty": 0,
    
    # UI-Einstellungen
    "mcpAgent.showTimestamps": True,
    "mcpAgent.showToolCalls": True,
    "mcpAgent.autoScroll": True,
    "mcpAgent.systemPrompt": "Du bist ein hilfreicher KI-Assistent mit Zugriff auf MCP-Tools.",
    
    # Server-Einstellungen
    "mcpAgent.autoStartServers": True,
    "mcpAgent.serverTimeout": 30000,
    "mcpAgent.maxRetries": 3
}

# Nur fehlende Settings hinzufügen
added = []
for key, value in new_settings.items():
    if key not in settings:
        settings[key] = value
        added.append(key)
    else:
        print(f"  ✓ {key} bereits vorhanden")

# Speichern
if added:
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)
    
    print(f"\n✅ {len(added)} Einstellungen hinzugefügt:\n")
    for key in added:
        print(f"  + {key}: {new_settings[key]}")
else:
    print("\n✅ Alle Einstellungen bereits vorhanden!")

print("\n📋 Aktuelle mcpAgent Einstellungen:")
for key, value in sorted(settings.items()):
    if key.startswith("mcpAgent"):
        # API-Keys maskieren
        if "Key" in key and value:
            display = value[:10] + "..." + value[-4:] if len(str(value)) > 14 else value
        else:
            display = value
        print(f"  {key}: {display}")

print("\n⚡ VS Code neu laden: Ctrl+Shift+P → 'Developer: Reload Window'")
