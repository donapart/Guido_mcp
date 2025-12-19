"""
Flutter MCP Server - Flutter/Dart Projekt-Verwaltung

Tools für:
- Flutter Doctor (Umgebung prüfen)
- Pub Get/Upgrade (Dependencies)
- Build (APK, iOS, Web)
- Analyze (Code-Qualität)
- Test
- Geräte-Verwaltung
"""

import os
import subprocess
import asyncio
from pathlib import Path
from fastmcp import FastMCP
from pydantic import Field
from typing import Optional

# Server initialisieren
mcp = FastMCP(
    "Flutter Server",
    instructions="Flutter/Dart Entwicklung und Build-Verwaltung"
)

# Standard-Pfad für Flutter-Projekte
DEFAULT_PROJECTS_PATH = os.getenv("FLUTTER_PROJECTS_PATH", "d:\\")


async def run_command(cmd: list, cwd: str = None, timeout: int = 300) -> dict:
    """Führe Shell-Befehl aus und gib Ergebnis zurück"""
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )
        return {
            "success": process.returncode == 0,
            "returncode": process.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace")
        }
    except asyncio.TimeoutError:
        return {"success": False, "error": f"Timeout nach {timeout} Sekunden"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== ENVIRONMENT TOOLS ====================

@mcp.tool()
async def flutter_doctor() -> dict:
    """
    Prüfe Flutter-Installation und Umgebung (flutter doctor).
    
    Returns:
        Detaillierter Status aller Flutter-Komponenten
    """
    result = await run_command(["flutter", "doctor", "-v"], timeout=120)
    if result.get("success"):
        return {
            "success": True,
            "doctor_output": result["stdout"],
            "hint": "✓ = OK, ✗ = Problem, ! = Warnung"
        }
    return result


@mcp.tool()
async def flutter_version() -> dict:
    """
    Zeige installierte Flutter-Version.
    
    Returns:
        Flutter und Dart Versionen
    """
    result = await run_command(["flutter", "--version"])
    return {
        "success": result.get("success", False),
        "version_info": result.get("stdout", result.get("error"))
    }


@mcp.tool()
async def list_flutter_devices() -> dict:
    """
    Liste alle verfügbaren Geräte/Emulatoren.
    
    Returns:
        Liste der verbundenen Geräte
    """
    result = await run_command(["flutter", "devices"])
    return {
        "success": result.get("success", False),
        "devices": result.get("stdout", result.get("error"))
    }


# ==================== PROJECT TOOLS ====================

@mcp.tool()
async def flutter_pub_get(
    project_path: str = Field(description="Pfad zum Flutter-Projekt")
) -> dict:
    """
    Installiere Dependencies eines Flutter-Projekts (flutter pub get).
    
    Args:
        project_path: Pfad zum Projekt (mit pubspec.yaml)
        
    Returns:
        Ergebnis der Installation
    """
    if not Path(project_path).exists():
        return {"success": False, "error": f"Pfad nicht gefunden: {project_path}"}
    
    pubspec = Path(project_path) / "pubspec.yaml"
    if not pubspec.exists():
        return {"success": False, "error": "Kein pubspec.yaml gefunden - ist das ein Flutter-Projekt?"}
    
    result = await run_command(["flutter", "pub", "get"], cwd=project_path)
    return {
        "success": result.get("success", False),
        "project": project_path,
        "output": result.get("stdout", "") + result.get("stderr", "")
    }


@mcp.tool()
async def flutter_pub_upgrade(
    project_path: str = Field(description="Pfad zum Flutter-Projekt"),
    major_versions: bool = Field(default=False, description="Auch Major-Versions upgraden")
) -> dict:
    """
    Aktualisiere Dependencies auf neueste Versionen.
    
    Args:
        project_path: Pfad zum Projekt
        major_versions: Mit --major-versions auch Breaking Changes
        
    Returns:
        Upgrade-Ergebnis
    """
    cmd = ["flutter", "pub", "upgrade"]
    if major_versions:
        cmd.append("--major-versions")
    
    result = await run_command(cmd, cwd=project_path)
    return {
        "success": result.get("success", False),
        "project": project_path,
        "output": result.get("stdout", "") + result.get("stderr", "")
    }


@mcp.tool()
async def flutter_analyze(
    project_path: str = Field(description="Pfad zum Flutter-Projekt")
) -> dict:
    """
    Analysiere Code-Qualität (Linting, Fehler).
    
    Args:
        project_path: Pfad zum Projekt
        
    Returns:
        Liste aller Warnings und Errors
    """
    result = await run_command(["flutter", "analyze"], cwd=project_path, timeout=180)
    
    output = result.get("stdout", "") + result.get("stderr", "")
    
    # Zähle Issues
    errors = output.count(" error ")
    warnings = output.count(" warning ")
    infos = output.count(" info ")
    
    return {
        "success": result.get("success", False),
        "project": project_path,
        "summary": {
            "errors": errors,
            "warnings": warnings,
            "infos": infos
        },
        "details": output
    }


@mcp.tool()
async def flutter_test(
    project_path: str = Field(description="Pfad zum Flutter-Projekt"),
    coverage: bool = Field(default=False, description="Mit Code-Coverage")
) -> dict:
    """
    Führe Tests aus.
    
    Args:
        project_path: Pfad zum Projekt
        coverage: Coverage-Report generieren
        
    Returns:
        Test-Ergebnisse
    """
    cmd = ["flutter", "test"]
    if coverage:
        cmd.append("--coverage")
    
    result = await run_command(cmd, cwd=project_path, timeout=300)
    return {
        "success": result.get("success", False),
        "project": project_path,
        "test_output": result.get("stdout", "") + result.get("stderr", "")
    }


# ==================== BUILD TOOLS ====================

@mcp.tool()
async def flutter_build_apk(
    project_path: str = Field(description="Pfad zum Flutter-Projekt"),
    release: bool = Field(default=True, description="Release-Build (optimiert)"),
    split_per_abi: bool = Field(default=False, description="Separate APKs pro CPU-Architektur")
) -> dict:
    """
    Baue Android APK.
    
    Args:
        project_path: Pfad zum Projekt
        release: Release oder Debug
        split_per_abi: Kleinere APKs für jede Architektur
        
    Returns:
        Pfad zur erstellten APK
    """
    cmd = ["flutter", "build", "apk"]
    if release:
        cmd.append("--release")
    else:
        cmd.append("--debug")
    if split_per_abi:
        cmd.append("--split-per-abi")
    
    result = await run_command(cmd, cwd=project_path, timeout=600)
    
    if result.get("success"):
        apk_path = Path(project_path) / "build" / "app" / "outputs" / "flutter-apk"
        apks = list(apk_path.glob("*.apk")) if apk_path.exists() else []
        return {
            "success": True,
            "project": project_path,
            "apk_files": [str(a) for a in apks],
            "output": result.get("stdout", "")
        }
    return {
        "success": False,
        "error": result.get("stderr", result.get("error")),
        "output": result.get("stdout", "")
    }


@mcp.tool()
async def flutter_build_appbundle(
    project_path: str = Field(description="Pfad zum Flutter-Projekt")
) -> dict:
    """
    Baue Android App Bundle (für Play Store).
    
    Args:
        project_path: Pfad zum Projekt
        
    Returns:
        Pfad zum AAB
    """
    result = await run_command(
        ["flutter", "build", "appbundle", "--release"],
        cwd=project_path,
        timeout=600
    )
    
    if result.get("success"):
        return {
            "success": True,
            "project": project_path,
            "bundle_path": str(Path(project_path) / "build" / "app" / "outputs" / "bundle" / "release"),
            "output": result.get("stdout", "")
        }
    return {
        "success": False,
        "error": result.get("stderr", result.get("error"))
    }


@mcp.tool()
async def flutter_build_web(
    project_path: str = Field(description="Pfad zum Flutter-Projekt"),
    renderer: str = Field(default="auto", description="Renderer: html, canvaskit, auto")
) -> dict:
    """
    Baue Web-Version.
    
    Args:
        project_path: Pfad zum Projekt
        renderer: html (klein), canvaskit (performant), auto
        
    Returns:
        Pfad zum Build-Output
    """
    result = await run_command(
        ["flutter", "build", "web", f"--web-renderer={renderer}"],
        cwd=project_path,
        timeout=300
    )
    
    if result.get("success"):
        return {
            "success": True,
            "project": project_path,
            "build_path": str(Path(project_path) / "build" / "web"),
            "output": result.get("stdout", "")
        }
    return {
        "success": False,
        "error": result.get("stderr", result.get("error"))
    }


@mcp.tool()
async def flutter_build_ios(
    project_path: str = Field(description="Pfad zum Flutter-Projekt")
) -> dict:
    """
    Baue iOS-App (nur auf macOS möglich).
    
    Args:
        project_path: Pfad zum Projekt
        
    Returns:
        Build-Ergebnis
    """
    result = await run_command(
        ["flutter", "build", "ios", "--release", "--no-codesign"],
        cwd=project_path,
        timeout=600
    )
    return {
        "success": result.get("success", False),
        "project": project_path,
        "note": "Für App Store: Öffne Xcode für Signierung",
        "output": result.get("stdout", "") + result.get("stderr", "")
    }


@mcp.tool()
async def flutter_clean(
    project_path: str = Field(description="Pfad zum Flutter-Projekt")
) -> dict:
    """
    Lösche Build-Cache und temporäre Dateien.
    
    Args:
        project_path: Pfad zum Projekt
        
    Returns:
        Bestätigung
    """
    result = await run_command(["flutter", "clean"], cwd=project_path)
    return {
        "success": result.get("success", False),
        "project": project_path,
        "output": result.get("stdout", "") + result.get("stderr", "")
    }


# ==================== PROJECT INFO ====================

@mcp.tool()
async def flutter_project_info(
    project_path: str = Field(description="Pfad zum Flutter-Projekt")
) -> dict:
    """
    Zeige Projekt-Informationen aus pubspec.yaml.
    
    Args:
        project_path: Pfad zum Projekt
        
    Returns:
        Name, Version, Dependencies
    """
    pubspec = Path(project_path) / "pubspec.yaml"
    if not pubspec.exists():
        return {"success": False, "error": "pubspec.yaml nicht gefunden"}
    
    try:
        import yaml
        with open(pubspec, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        return {
            "success": True,
            "project": project_path,
            "name": data.get("name"),
            "description": data.get("description"),
            "version": data.get("version"),
            "environment": data.get("environment", {}),
            "dependencies": list(data.get("dependencies", {}).keys()),
            "dev_dependencies": list(data.get("dev_dependencies", {}).keys())
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def list_flutter_projects(
    search_path: str = Field(default="d:\\", description="Pfad zum Durchsuchen")
) -> dict:
    """
    Finde alle Flutter-Projekte in einem Verzeichnis.
    
    Args:
        search_path: Basis-Pfad für Suche
        
    Returns:
        Liste aller gefundenen Flutter-Projekte
    """
    projects = []
    search = Path(search_path)
    
    if not search.exists():
        return {"success": False, "error": f"Pfad nicht gefunden: {search_path}"}
    
    # Suche pubspec.yaml (max 3 Ebenen tief)
    for pubspec in search.glob("**/pubspec.yaml"):
        # Prüfe ob es Flutter ist (nicht nur Dart)
        try:
            with open(pubspec, "r", encoding="utf-8") as f:
                content = f.read()
            if "flutter:" in content:
                projects.append({
                    "path": str(pubspec.parent),
                    "name": pubspec.parent.name
                })
        except:
            pass
        
        if len(projects) >= 50:  # Limit
            break
    
    return {
        "success": True,
        "search_path": search_path,
        "flutter_projects": projects,
        "count": len(projects)
    }


# Server starten
if __name__ == "__main__":
    mcp.run()
