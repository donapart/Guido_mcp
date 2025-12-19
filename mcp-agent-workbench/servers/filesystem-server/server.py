"""
Filesystem MCP Server

Ein MCP-Server für Dateisystem-Operationen.
Bietet sichere, kontrollierte Zugriffe auf das Dateisystem.
"""

from fastmcp import FastMCP
from pathlib import Path
from typing import Optional
import os
import json

mcp = FastMCP("filesystem-server")

# Sicherheit: Nur bestimmte Verzeichnisse erlauben
ALLOWED_ROOTS: list[str] = []  # Leer = alle erlaubt (für Entwicklung)


def is_path_allowed(path: str) -> bool:
    """Prüft ob ein Pfad in den erlaubten Roots liegt."""
    if not ALLOWED_ROOTS:
        return True  # Entwicklungsmodus: alles erlaubt
    
    resolved = Path(path).resolve()
    return any(
        resolved.is_relative_to(Path(root).resolve()) 
        for root in ALLOWED_ROOTS
    )


def ensure_allowed(path: str) -> Path:
    """Validiert und gibt den Pfad zurück oder wirft einen Fehler."""
    if not is_path_allowed(path):
        raise PermissionError(f"Zugriff auf '{path}' nicht erlaubt")
    return Path(path)


# ============================================================================
# TOOLS
# ============================================================================

@mcp.tool
def read_file(path: str, encoding: str = "utf-8") -> str:
    """
    Liest den Inhalt einer Datei.
    
    Args:
        path: Absoluter oder relativer Pfad zur Datei
        encoding: Zeichenkodierung (default: utf-8)
    
    Returns:
        Der Dateiinhalt als String
    """
    file_path = ensure_allowed(path)
    
    if not file_path.exists():
        return f"Fehler: Datei '{path}' existiert nicht"
    
    if not file_path.is_file():
        return f"Fehler: '{path}' ist keine Datei"
    
    try:
        return file_path.read_text(encoding=encoding)
    except Exception as e:
        return f"Fehler beim Lesen: {e}"


@mcp.tool
def write_file(path: str, content: str, encoding: str = "utf-8") -> str:
    """
    Schreibt Inhalt in eine Datei (erstellt oder überschreibt).
    
    Args:
        path: Absoluter oder relativer Pfad zur Datei
        content: Der zu schreibende Inhalt
        encoding: Zeichenkodierung (default: utf-8)
    
    Returns:
        Erfolgsmeldung oder Fehler
    """
    file_path = ensure_allowed(path)
    
    try:
        # Parent-Verzeichnis erstellen falls nötig
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding=encoding)
        return f"Erfolgreich geschrieben: {path} ({len(content)} Zeichen)"
    except Exception as e:
        return f"Fehler beim Schreiben: {e}"


@mcp.tool
def list_directory(
    path: str = ".", 
    pattern: str = "*",
    include_hidden: bool = False
) -> dict:
    """
    Listet den Inhalt eines Verzeichnisses.
    
    Args:
        path: Pfad zum Verzeichnis (default: aktuelles Verzeichnis)
        pattern: Glob-Pattern zum Filtern (default: alle Dateien)
        include_hidden: Versteckte Dateien einschließen (default: False)
    
    Returns:
        Dictionary mit Dateien und Ordnern
    """
    dir_path = ensure_allowed(path)
    
    if not dir_path.exists():
        return {"error": f"Verzeichnis '{path}' existiert nicht"}
    
    if not dir_path.is_dir():
        return {"error": f"'{path}' ist kein Verzeichnis"}
    
    files = []
    directories = []
    
    for item in dir_path.glob(pattern):
        name = item.name
        
        # Versteckte Dateien überspringen
        if not include_hidden and name.startswith("."):
            continue
        
        if item.is_file():
            files.append({
                "name": name,
                "size": item.stat().st_size,
                "modified": item.stat().st_mtime
            })
        elif item.is_dir():
            directories.append({
                "name": name,
                "items": len(list(item.iterdir())) if item.exists() else 0
            })
    
    return {
        "path": str(dir_path.resolve()),
        "directories": sorted(directories, key=lambda x: x["name"]),
        "files": sorted(files, key=lambda x: x["name"])
    }


@mcp.tool
def search_files(
    path: str,
    pattern: str,
    recursive: bool = True,
    max_results: int = 100
) -> list[str]:
    """
    Sucht nach Dateien mit einem Glob-Pattern.
    
    Args:
        path: Startverzeichnis für die Suche
        pattern: Glob-Pattern (z.B. "*.py", "**/*.json")
        recursive: Rekursiv suchen (default: True)
        max_results: Maximale Anzahl Ergebnisse (default: 100)
    
    Returns:
        Liste der gefundenen Dateipfade
    """
    dir_path = ensure_allowed(path)
    
    if not dir_path.exists():
        return [f"Fehler: Verzeichnis '{path}' existiert nicht"]
    
    glob_method = dir_path.rglob if recursive else dir_path.glob
    results = []
    
    for match in glob_method(pattern):
        if len(results) >= max_results:
            break
        results.append(str(match))
    
    return results


@mcp.tool
def get_file_info(path: str) -> dict:
    """
    Gibt detaillierte Informationen über eine Datei zurück.
    
    Args:
        path: Pfad zur Datei oder zum Verzeichnis
    
    Returns:
        Dictionary mit Datei-Metadaten
    """
    file_path = ensure_allowed(path)
    
    if not file_path.exists():
        return {"error": f"'{path}' existiert nicht"}
    
    stat = file_path.stat()
    
    return {
        "name": file_path.name,
        "path": str(file_path.resolve()),
        "type": "directory" if file_path.is_dir() else "file",
        "size": stat.st_size,
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
        "accessed": stat.st_atime,
        "extension": file_path.suffix if file_path.is_file() else None,
        "readable": os.access(file_path, os.R_OK),
        "writable": os.access(file_path, os.W_OK)
    }


@mcp.tool
def create_directory(path: str) -> str:
    """
    Erstellt ein Verzeichnis (inkl. Parent-Verzeichnisse).
    
    Args:
        path: Pfad zum zu erstellenden Verzeichnis
    
    Returns:
        Erfolgsmeldung oder Fehler
    """
    dir_path = ensure_allowed(path)
    
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return f"Verzeichnis erstellt: {dir_path.resolve()}"
    except Exception as e:
        return f"Fehler: {e}"


@mcp.tool  
def delete_file(path: str, confirm: bool = False) -> str:
    """
    Löscht eine Datei (NICHT rekursiv, nur einzelne Dateien).
    
    Args:
        path: Pfad zur zu löschenden Datei
        confirm: Muss True sein um zu löschen (Sicherheit)
    
    Returns:
        Erfolgsmeldung oder Fehler
    """
    if not confirm:
        return "Fehler: confirm=True muss gesetzt sein um zu löschen"
    
    file_path = ensure_allowed(path)
    
    if not file_path.exists():
        return f"Fehler: '{path}' existiert nicht"
    
    if file_path.is_dir():
        return "Fehler: Verzeichnisse können nicht mit diesem Tool gelöscht werden"
    
    try:
        file_path.unlink()
        return f"Datei gelöscht: {path}"
    except Exception as e:
        return f"Fehler: {e}"


@mcp.tool
def copy_file(source: str, destination: str) -> str:
    """
    Kopiert eine Datei.
    
    Args:
        source: Quellpfad
        destination: Zielpfad
    
    Returns:
        Erfolgsmeldung oder Fehler
    """
    import shutil
    
    src = ensure_allowed(source)
    dst = ensure_allowed(destination)
    
    if not src.exists():
        return f"Fehler: Quelle '{source}' existiert nicht"
    
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return f"Kopiert: {source} -> {destination}"
    except Exception as e:
        return f"Fehler: {e}"


# ============================================================================
# RESOURCES
# ============================================================================

@mcp.resource("fs://cwd")
def get_current_directory() -> str:
    """Aktuelles Arbeitsverzeichnis"""
    return str(Path.cwd().resolve())


@mcp.resource("fs://home")  
def get_home_directory() -> str:
    """Home-Verzeichnis des Benutzers"""
    return str(Path.home().resolve())


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
    
    # Optional: Erlaubte Roots setzen für Produktion
    # ALLOWED_ROOTS.extend(["/home/user/projects", "/tmp"])
    
    mcp.run()
