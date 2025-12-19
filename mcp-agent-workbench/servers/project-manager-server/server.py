"""
Project Manager MCP Server - Projekt-Übersicht für alle D:\ Projekte

Tools für:
- Alle Projekte scannen
- Projekt-Typen erkennen (Python, Node, Flutter, etc.)
- Dependencies prüfen
- Status-Übersicht
- Outdated Checks
"""

import os
import json
from pathlib import Path
from datetime import datetime
from fastmcp import FastMCP
from pydantic import Field
from typing import Optional

# Server initialisieren
mcp = FastMCP(
    "Project Manager Server",
    instructions="Projekt-Übersicht und -Verwaltung für alle lokalen Projekte"
)

# Basis-Pfad
BASE_PATH = os.getenv("PROJECTS_BASE_PATH", "d:\\")


def detect_project_type(path: Path) -> dict:
    """Erkenne Projekt-Typ anhand von Konfigurationsdateien"""
    types = []
    frameworks = []
    
    # Python
    if (path / "requirements.txt").exists() or (path / "pyproject.toml").exists() or (path / "setup.py").exists():
        types.append("python")
        if (path / "pyproject.toml").exists():
            try:
                content = (path / "pyproject.toml").read_text()
                if "fastapi" in content.lower():
                    frameworks.append("FastAPI")
                if "django" in content.lower():
                    frameworks.append("Django")
                if "flask" in content.lower():
                    frameworks.append("Flask")
            except:
                pass
    
    # Node.js
    if (path / "package.json").exists():
        types.append("nodejs")
        try:
            pkg = json.loads((path / "package.json").read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "react" in deps:
                frameworks.append("React")
            if "vue" in deps:
                frameworks.append("Vue")
            if "next" in deps:
                frameworks.append("Next.js")
            if "express" in deps:
                frameworks.append("Express")
        except:
            pass
    
    # Flutter/Dart
    if (path / "pubspec.yaml").exists():
        types.append("flutter" if (path / "pubspec.yaml").read_text().find("flutter:") >= 0 else "dart")
    
    # Docker
    if (path / "docker-compose.yml").exists() or (path / "docker-compose.yaml").exists():
        types.append("docker-compose")
    if (path / "Dockerfile").exists():
        types.append("dockerfile")
    
    # Rust
    if (path / "Cargo.toml").exists():
        types.append("rust")
    
    # Go
    if (path / "go.mod").exists():
        types.append("go")
    
    # Java
    if (path / "pom.xml").exists():
        types.append("java-maven")
    if (path / "build.gradle").exists():
        types.append("java-gradle")
    
    # Git
    has_git = (path / ".git").exists()
    
    return {
        "types": types,
        "frameworks": frameworks,
        "has_git": has_git
    }


# ==================== SCAN TOOLS ====================

@mcp.tool()
async def scan_all_projects(
    base_path: str = Field(default="d:\\", description="Basis-Pfad"),
    max_depth: int = Field(default=1, description="Suchtiefe (1 = nur direkte Unterordner)")
) -> dict:
    """
    Scanne alle Projekte und erkenne deren Typen.
    
    Args:
        base_path: Start-Verzeichnis
        max_depth: Wie tief suchen
        
    Returns:
        Liste aller Projekte mit Typ-Info
    """
    projects = []
    base = Path(base_path)
    
    if not base.exists():
        return {"success": False, "error": f"Pfad nicht gefunden: {base_path}"}
    
    # Direkte Unterordner scannen
    for item in base.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            project_info = detect_project_type(item)
            if project_info["types"]:  # Nur wenn als Projekt erkannt
                projects.append({
                    "name": item.name,
                    "path": str(item),
                    "types": project_info["types"],
                    "frameworks": project_info["frameworks"],
                    "has_git": project_info["has_git"]
                })
    
    # Nach Typ gruppieren
    by_type = {}
    for p in projects:
        for t in p["types"]:
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(p["name"])
    
    return {
        "success": True,
        "base_path": base_path,
        "total_projects": len(projects),
        "projects": projects,
        "by_type": by_type
    }


@mcp.tool()
async def project_details(
    project_path: str = Field(description="Pfad zum Projekt")
) -> dict:
    """
    Zeige detaillierte Informationen zu einem Projekt.
    
    Args:
        project_path: Pfad zum Projekt
        
    Returns:
        Detaillierte Projekt-Infos
    """
    path = Path(project_path)
    
    if not path.exists():
        return {"success": False, "error": f"Projekt nicht gefunden: {project_path}"}
    
    info = detect_project_type(path)
    details = {
        "name": path.name,
        "path": str(path),
        "types": info["types"],
        "frameworks": info["frameworks"],
        "has_git": info["has_git"]
    }
    
    # Python-spezifisch
    if "python" in info["types"]:
        req_file = path / "requirements.txt"
        if req_file.exists():
            deps = [l.strip() for l in req_file.read_text().splitlines() if l.strip() and not l.startswith("#")]
            details["python_dependencies"] = deps[:30]
            details["python_dep_count"] = len(deps)
    
    # Node.js-spezifisch
    if "nodejs" in info["types"]:
        pkg_file = path / "package.json"
        if pkg_file.exists():
            try:
                pkg = json.loads(pkg_file.read_text())
                details["node_name"] = pkg.get("name")
                details["node_version"] = pkg.get("version")
                details["node_scripts"] = list(pkg.get("scripts", {}).keys())
                details["node_dependencies"] = list(pkg.get("dependencies", {}).keys())
                details["node_dev_dependencies"] = list(pkg.get("devDependencies", {}).keys())
            except:
                pass
    
    # Flutter-spezifisch
    if "flutter" in info["types"]:
        pubspec = path / "pubspec.yaml"
        if pubspec.exists():
            try:
                import yaml
                data = yaml.safe_load(pubspec.read_text())
                details["flutter_name"] = data.get("name")
                details["flutter_version"] = data.get("version")
                details["flutter_dependencies"] = list(data.get("dependencies", {}).keys())
            except:
                pass
    
    # Datei-Statistiken
    file_counts = {}
    for ext in [".py", ".js", ".ts", ".dart", ".java", ".go", ".rs"]:
        count = len(list(path.rglob(f"*{ext}")))
        if count > 0:
            file_counts[ext] = count
    details["file_counts"] = file_counts
    
    # Größe
    try:
        total_size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        details["total_size_mb"] = round(total_size / (1024 * 1024), 1)
    except:
        pass
    
    return {
        "success": True,
        **details
    }


# ==================== DEPENDENCY TOOLS ====================

@mcp.tool()
async def check_python_deps(
    project_path: str = Field(description="Pfad zum Python-Projekt")
) -> dict:
    """
    Prüfe Python-Dependencies auf Verfügbarkeit.
    
    Args:
        project_path: Pfad zum Projekt
        
    Returns:
        Liste der Dependencies mit Status
    """
    path = Path(project_path)
    req_file = path / "requirements.txt"
    
    if not req_file.exists():
        return {"success": False, "error": "Keine requirements.txt gefunden"}
    
    import subprocess
    
    deps = []
    for line in req_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            # Parse Paketname
            pkg = line.split(">=")[0].split("==")[0].split("<")[0].split("[")[0].strip()
            deps.append(pkg)
    
    # Prüfe welche installiert sind
    result = subprocess.run(
        ["pip", "list", "--format=json"],
        capture_output=True,
        text=True
    )
    installed = {}
    if result.returncode == 0:
        for pkg in json.loads(result.stdout):
            installed[pkg["name"].lower()] = pkg["version"]
    
    status = []
    for dep in deps:
        dep_lower = dep.lower()
        status.append({
            "package": dep,
            "installed": dep_lower in installed,
            "version": installed.get(dep_lower)
        })
    
    return {
        "success": True,
        "project": project_path,
        "total": len(status),
        "installed": sum(1 for s in status if s["installed"]),
        "missing": [s["package"] for s in status if not s["installed"]],
        "dependencies": status
    }


@mcp.tool()
async def check_node_deps(
    project_path: str = Field(description="Pfad zum Node.js-Projekt")
) -> dict:
    """
    Prüfe Node.js-Dependencies.
    
    Args:
        project_path: Pfad zum Projekt
        
    Returns:
        Dependencies-Status
    """
    path = Path(project_path)
    pkg_file = path / "package.json"
    node_modules = path / "node_modules"
    
    if not pkg_file.exists():
        return {"success": False, "error": "Keine package.json gefunden"}
    
    pkg = json.loads(pkg_file.read_text())
    deps = pkg.get("dependencies", {})
    dev_deps = pkg.get("devDependencies", {})
    
    return {
        "success": True,
        "project": project_path,
        "node_modules_exists": node_modules.exists(),
        "dependencies": list(deps.keys()),
        "dev_dependencies": list(dev_deps.keys()),
        "total_deps": len(deps) + len(dev_deps),
        "hint": "npm install" if not node_modules.exists() else "Dependencies installiert"
    }


# ==================== OVERVIEW TOOLS ====================

@mcp.tool()
async def projects_summary() -> dict:
    """
    Zeige Übersicht aller D:\\ Projekte.
    
    Returns:
        Zusammenfassung mit Statistiken
    """
    base = Path(BASE_PATH)
    
    stats = {
        "total": 0,
        "python": 0,
        "nodejs": 0,
        "flutter": 0,
        "docker": 0,
        "with_git": 0
    }
    
    projects = []
    
    for item in base.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            info = detect_project_type(item)
            if info["types"]:
                stats["total"] += 1
                if "python" in info["types"]:
                    stats["python"] += 1
                if "nodejs" in info["types"]:
                    stats["nodejs"] += 1
                if "flutter" in info["types"]:
                    stats["flutter"] += 1
                if "docker-compose" in info["types"] or "dockerfile" in info["types"]:
                    stats["docker"] += 1
                if info["has_git"]:
                    stats["with_git"] += 1
                
                projects.append({
                    "name": item.name,
                    "types": info["types"],
                    "frameworks": info["frameworks"]
                })
    
    return {
        "success": True,
        "base_path": BASE_PATH,
        "statistics": stats,
        "projects": projects
    }


@mcp.tool()
async def find_outdated_projects(
    base_path: str = Field(default="d:\\", description="Basis-Pfad"),
    days: int = Field(default=30, description="Als veraltet nach X Tagen")
) -> dict:
    """
    Finde Projekte die lange nicht geändert wurden.
    
    Args:
        base_path: Start-Verzeichnis
        days: Tage seit letzter Änderung
        
    Returns:
        Liste veralteter Projekte
    """
    from datetime import timedelta
    
    base = Path(base_path)
    threshold = datetime.now() - timedelta(days=days)
    outdated = []
    
    for item in base.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            info = detect_project_type(item)
            if info["types"]:
                # Finde neueste Datei
                try:
                    newest = max(
                        (f.stat().st_mtime for f in item.rglob("*") if f.is_file()),
                        default=0
                    )
                    newest_date = datetime.fromtimestamp(newest) if newest else None
                    
                    if newest_date and newest_date < threshold:
                        outdated.append({
                            "name": item.name,
                            "path": str(item),
                            "last_modified": newest_date.isoformat(),
                            "days_ago": (datetime.now() - newest_date).days
                        })
                except:
                    pass
    
    outdated.sort(key=lambda x: x["days_ago"], reverse=True)
    
    return {
        "success": True,
        "threshold_days": days,
        "outdated_projects": outdated,
        "count": len(outdated)
    }


@mcp.tool()
async def find_large_projects(
    base_path: str = Field(default="d:\\", description="Basis-Pfad"),
    min_size_mb: int = Field(default=100, description="Mindestgröße in MB")
) -> dict:
    """
    Finde große Projekte (z.B. für Aufräumen).
    
    Args:
        base_path: Start-Verzeichnis
        min_size_mb: Minimale Größe
        
    Returns:
        Liste großer Projekte
    """
    base = Path(base_path)
    large = []
    
    for item in base.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            try:
                size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                size_mb = size / (1024 * 1024)
                
                if size_mb >= min_size_mb:
                    # Finde größte Unterordner
                    subdir_sizes = []
                    for sub in item.iterdir():
                        if sub.is_dir():
                            sub_size = sum(f.stat().st_size for f in sub.rglob("*") if f.is_file())
                            subdir_sizes.append((sub.name, sub_size / (1024 * 1024)))
                    subdir_sizes.sort(key=lambda x: x[1], reverse=True)
                    
                    large.append({
                        "name": item.name,
                        "path": str(item),
                        "size_mb": round(size_mb, 1),
                        "largest_subdirs": subdir_sizes[:5]
                    })
            except:
                pass
    
    large.sort(key=lambda x: x["size_mb"], reverse=True)
    
    return {
        "success": True,
        "min_size_mb": min_size_mb,
        "large_projects": large,
        "total_size_gb": round(sum(p["size_mb"] for p in large) / 1024, 1)
    }


# Server starten
if __name__ == "__main__":
    mcp.run()
