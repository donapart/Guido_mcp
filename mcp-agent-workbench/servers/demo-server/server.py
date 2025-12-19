"""
Demo MCP Server mit FastMCP

Dieser Server demonstriert die Grundlagen eines MCP-Servers:
- Tool-Definitionen mit Typisierung
- Resource-Bereitstellung
- Prompts für häufige Aufgaben
"""

from fastmcp import FastMCP
from datetime import datetime
import json
import os

# Server initialisieren
mcp = FastMCP("demo-server")


# ============================================================================
# TOOLS - Funktionen, die das LLM aufrufen kann
# ============================================================================

@mcp.tool
def sum_two_numbers(a: int, b: int) -> int:
    """
    Addiert zwei Zahlen und gibt das Ergebnis zurück.
    
    Args:
        a: Erste Zahl
        b: Zweite Zahl
    
    Returns:
        Die Summe von a und b
    """
    return a + b


@mcp.tool
def multiply_numbers(a: float, b: float) -> float:
    """
    Multipliziert zwei Zahlen.
    
    Args:
        a: Erste Zahl
        b: Zweite Zahl
    
    Returns:
        Das Produkt von a und b
    """
    return a * b


@mcp.tool
def get_current_time() -> str:
    """
    Gibt die aktuelle Uhrzeit und das Datum zurück.
    
    Returns:
        Aktuelles Datum und Uhrzeit im ISO-Format
    """
    return datetime.now().isoformat()


@mcp.tool
def analyze_text(text: str) -> dict:
    """
    Analysiert einen Text und gibt Statistiken zurück.
    
    Args:
        text: Der zu analysierende Text
    
    Returns:
        Dictionary mit Statistiken (Zeichen, Wörter, Zeilen)
    """
    return {
        "characters": len(text),
        "words": len(text.split()),
        "lines": len(text.splitlines()),
        "has_numbers": any(c.isdigit() for c in text),
    }


@mcp.tool
def format_json(data: str, indent: int = 2) -> str:
    """
    Formatiert einen JSON-String mit Einrückung.
    
    Args:
        data: JSON-String zum Formatieren
        indent: Anzahl der Leerzeichen für Einrückung (default: 2)
    
    Returns:
        Formatierter JSON-String
    """
    try:
        parsed = json.loads(data)
        return json.dumps(parsed, indent=indent, ensure_ascii=False)
    except json.JSONDecodeError as e:
        return f"Fehler beim Parsen: {e}"


@mcp.tool
def list_environment_vars(prefix: str = "") -> dict:
    """
    Listet Umgebungsvariablen auf (optional gefiltert nach Prefix).
    
    Args:
        prefix: Nur Variablen anzeigen, die mit diesem Prefix beginnen
    
    Returns:
        Dictionary mit Umgebungsvariablen
    """
    if prefix:
        return {k: v for k, v in os.environ.items() if k.startswith(prefix)}
    # Nur sichere Variablen zurückgeben
    safe_vars = ["PATH", "HOME", "USER", "SHELL", "LANG", "TERM"]
    return {k: os.environ.get(k, "") for k in safe_vars if k in os.environ}


# ============================================================================
# RESOURCES - Kontextdaten, die das LLM lesen kann
# ============================================================================

@mcp.resource("info://server/status")
def get_server_status() -> str:
    """Aktueller Status des Demo-Servers"""
    return json.dumps({
        "name": "demo-server",
        "version": "0.1.0",
        "status": "running",
        "tools_available": 6,
        "started_at": datetime.now().isoformat()
    }, indent=2)


@mcp.resource("info://server/capabilities")
def get_capabilities() -> str:
    """Liste aller verfügbaren Capabilities"""
    return """
# Demo Server Capabilities

## Tools
- sum_two_numbers: Addiert zwei Zahlen
- multiply_numbers: Multipliziert zwei Zahlen  
- get_current_time: Gibt aktuelle Zeit zurück
- analyze_text: Analysiert Textstatistiken
- format_json: Formatiert JSON-Strings
- list_environment_vars: Listet Umgebungsvariablen

## Resources
- info://server/status: Server-Status
- info://server/capabilities: Diese Liste

## Prompts
- explain_tool: Erklärt ein Tool im Detail
- code_review: Code-Review-Template
"""


# ============================================================================
# PROMPTS - Vordefinierte Prompt-Templates
# ============================================================================

@mcp.prompt
def explain_tool(tool_name: str) -> str:
    """
    Generiert einen Prompt, um ein Tool zu erklären.
    
    Args:
        tool_name: Name des zu erklärenden Tools
    """
    return f"""
Bitte erkläre das Tool '{tool_name}' im Detail:

1. Was macht das Tool?
2. Welche Parameter benötigt es?
3. Was gibt es zurück?
4. Wann sollte man es verwenden?
5. Gib ein Beispiel für die Verwendung.
"""


@mcp.prompt
def code_review(code: str, language: str = "python") -> str:
    """
    Generiert einen Code-Review-Prompt.
    
    Args:
        code: Der zu reviewende Code
        language: Programmiersprache des Codes
    """
    return f"""
Bitte führe ein Code-Review für folgenden {language}-Code durch:

```{language}
{code}
```

Beachte dabei:
1. Code-Qualität und Lesbarkeit
2. Potenzielle Bugs oder Fehler
3. Performance-Optimierungen
4. Best Practices für {language}
5. Sicherheitsaspekte
"""


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys
    import io
    
    # Fix für Windows-Konsole und Unicode
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    # Server starten (stdio-Modus für MCP-Clients)
    # Keine Print-Ausgaben bei stdio, da diese das Protokoll stören
    mcp.run()
