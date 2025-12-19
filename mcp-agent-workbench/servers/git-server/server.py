"""
Git MCP Server - Git Repository Verwaltung

Tools für:
- Status über mehrere Repos
- Branches verwalten
- Commits, Logs, Diffs
- Pull, Push, Fetch
- Stash
"""

import os
from pathlib import Path
from datetime import datetime
from fastmcp import FastMCP
from pydantic import Field
from typing import Optional
import git
from git import Repo, InvalidGitRepositoryError

# Server initialisieren
mcp = FastMCP(
    "Git Server",
    instructions="Git-Verwaltung - Repos, Branches, Commits, Diffs"
)

# Standard-Pfad für Projekte
DEFAULT_PATH = os.getenv("GIT_PROJECTS_PATH", "d:\\")


def get_repo(path: str) -> Repo:
    """Öffne Git Repository"""
    return Repo(path)


# ==================== REPO INFO ====================

@mcp.tool()
async def git_status(
    repo_path: str = Field(description="Pfad zum Git Repository")
) -> dict:
    """
    Zeige Git-Status eines Repositories.
    
    Args:
        repo_path: Pfad zum Repo
        
    Returns:
        Branch, geänderte Dateien, Commits ahead/behind
    """
    try:
        repo = get_repo(repo_path)
        
        # Status sammeln
        changed = [item.a_path for item in repo.index.diff(None)]
        staged = [item.a_path for item in repo.index.diff("HEAD")]
        untracked = repo.untracked_files
        
        # Branch-Info
        branch = repo.active_branch.name
        
        # Ahead/Behind (falls Remote existiert)
        ahead, behind = 0, 0
        try:
            tracking = repo.active_branch.tracking_branch()
            if tracking:
                commits_behind = list(repo.iter_commits(f'{branch}..{tracking.name}'))
                commits_ahead = list(repo.iter_commits(f'{tracking.name}..{branch}'))
                behind = len(commits_behind)
                ahead = len(commits_ahead)
        except:
            pass
        
        return {
            "success": True,
            "repo": repo_path,
            "branch": branch,
            "is_dirty": repo.is_dirty(),
            "staged_files": staged,
            "changed_files": changed,
            "untracked_files": untracked[:20],  # Limit
            "commits_ahead": ahead,
            "commits_behind": behind
        }
    except InvalidGitRepositoryError:
        return {"success": False, "error": f"Kein Git-Repo: {repo_path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def git_log(
    repo_path: str = Field(description="Pfad zum Git Repository"),
    count: int = Field(default=10, description="Anzahl Commits"),
    branch: Optional[str] = Field(default=None, description="Branch (optional)")
) -> dict:
    """
    Zeige Commit-Historie.
    
    Args:
        repo_path: Pfad zum Repo
        count: Anzahl der Commits
        branch: Spezifischer Branch
        
    Returns:
        Liste der Commits
    """
    try:
        repo = get_repo(repo_path)
        
        commits = []
        for commit in repo.iter_commits(branch, max_count=count):
            commits.append({
                "hash": commit.hexsha[:8],
                "message": commit.message.strip()[:100],
                "author": str(commit.author),
                "date": datetime.fromtimestamp(commit.committed_date).isoformat(),
                "files_changed": len(commit.stats.files)
            })
        
        return {
            "success": True,
            "repo": repo_path,
            "branch": branch or repo.active_branch.name,
            "commits": commits
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def git_diff(
    repo_path: str = Field(description="Pfad zum Git Repository"),
    file_path: Optional[str] = Field(default=None, description="Spezifische Datei"),
    staged: bool = Field(default=False, description="Nur staged Änderungen")
) -> dict:
    """
    Zeige Änderungen (Diff).
    
    Args:
        repo_path: Pfad zum Repo
        file_path: Optional: nur diese Datei
        staged: Staged vs Working Directory
        
    Returns:
        Diff-Output
    """
    try:
        repo = get_repo(repo_path)
        
        if staged:
            diff = repo.git.diff("--staged", file_path) if file_path else repo.git.diff("--staged")
        else:
            diff = repo.git.diff(file_path) if file_path else repo.git.diff()
        
        return {
            "success": True,
            "repo": repo_path,
            "staged": staged,
            "file": file_path,
            "diff": diff[:5000] if diff else "(keine Änderungen)"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== BRANCH TOOLS ====================

@mcp.tool()
async def list_branches(
    repo_path: str = Field(description="Pfad zum Git Repository"),
    remote: bool = Field(default=False, description="Auch Remote-Branches")
) -> dict:
    """
    Liste alle Branches.
    
    Args:
        repo_path: Pfad zum Repo
        remote: Mit Remote-Branches
        
    Returns:
        Lokale und Remote Branches
    """
    try:
        repo = get_repo(repo_path)
        
        local = [b.name for b in repo.branches]
        remotes = []
        if remote:
            for ref in repo.remote().refs:
                remotes.append(ref.name)
        
        return {
            "success": True,
            "repo": repo_path,
            "current": repo.active_branch.name,
            "local_branches": local,
            "remote_branches": remotes if remote else None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def checkout_branch(
    repo_path: str = Field(description="Pfad zum Git Repository"),
    branch: str = Field(description="Branch-Name"),
    create: bool = Field(default=False, description="Branch erstellen falls nicht existiert")
) -> dict:
    """
    Wechsle zu einem Branch.
    
    Args:
        repo_path: Pfad zum Repo
        branch: Ziel-Branch
        create: Erstellen falls nicht vorhanden
        
    Returns:
        Bestätigung
    """
    try:
        repo = get_repo(repo_path)
        
        if create:
            repo.git.checkout("-b", branch)
        else:
            repo.git.checkout(branch)
        
        return {
            "success": True,
            "repo": repo_path,
            "branch": branch,
            "action": "created and checked out" if create else "checked out"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def create_branch(
    repo_path: str = Field(description="Pfad zum Git Repository"),
    branch_name: str = Field(description="Name des neuen Branches"),
    from_branch: Optional[str] = Field(default=None, description="Basis-Branch (default: aktueller)")
) -> dict:
    """
    Erstelle einen neuen Branch.
    
    Args:
        repo_path: Pfad zum Repo
        branch_name: Neuer Branch-Name
        from_branch: Optional: von diesem Branch abzweigen
        
    Returns:
        Bestätigung
    """
    try:
        repo = get_repo(repo_path)
        
        if from_branch:
            repo.git.branch(branch_name, from_branch)
        else:
            repo.git.branch(branch_name)
        
        return {
            "success": True,
            "repo": repo_path,
            "new_branch": branch_name,
            "based_on": from_branch or repo.active_branch.name
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== COMMIT/STAGE TOOLS ====================

@mcp.tool()
async def git_add(
    repo_path: str = Field(description="Pfad zum Git Repository"),
    files: str = Field(default=".", description="Dateien zum Stagen ('.' für alle)")
) -> dict:
    """
    Stage Dateien für Commit.
    
    Args:
        repo_path: Pfad zum Repo
        files: Dateipfad(e) oder '.' für alle
        
    Returns:
        Bestätigung
    """
    try:
        repo = get_repo(repo_path)
        repo.git.add(files)
        
        staged = [item.a_path for item in repo.index.diff("HEAD")]
        
        return {
            "success": True,
            "repo": repo_path,
            "added": files,
            "staged_files": staged
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def git_commit(
    repo_path: str = Field(description="Pfad zum Git Repository"),
    message: str = Field(description="Commit-Message"),
    add_all: bool = Field(default=False, description="Erst alle Änderungen stagen")
) -> dict:
    """
    Erstelle einen Commit.
    
    Args:
        repo_path: Pfad zum Repo
        message: Commit-Nachricht
        add_all: Vorher 'git add .' ausführen
        
    Returns:
        Commit-Hash und Info
    """
    try:
        repo = get_repo(repo_path)
        
        if add_all:
            repo.git.add(".")
        
        commit = repo.index.commit(message)
        
        return {
            "success": True,
            "repo": repo_path,
            "commit_hash": commit.hexsha[:8],
            "message": message,
            "files_changed": len(commit.stats.files)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== REMOTE TOOLS ====================

@mcp.tool()
async def git_pull(
    repo_path: str = Field(description="Pfad zum Git Repository"),
    remote: str = Field(default="origin", description="Remote-Name"),
    branch: Optional[str] = Field(default=None, description="Branch (default: aktueller)")
) -> dict:
    """
    Hole Änderungen vom Remote (git pull).
    
    Args:
        repo_path: Pfad zum Repo
        remote: Remote (default: origin)
        branch: Branch
        
    Returns:
        Pull-Ergebnis
    """
    try:
        repo = get_repo(repo_path)
        
        branch = branch or repo.active_branch.name
        result = repo.git.pull(remote, branch)
        
        return {
            "success": True,
            "repo": repo_path,
            "remote": remote,
            "branch": branch,
            "result": result
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def git_push(
    repo_path: str = Field(description="Pfad zum Git Repository"),
    remote: str = Field(default="origin", description="Remote-Name"),
    branch: Optional[str] = Field(default=None, description="Branch"),
    set_upstream: bool = Field(default=False, description="Upstream setzen für neuen Branch")
) -> dict:
    """
    Pushe Änderungen zum Remote.
    
    Args:
        repo_path: Pfad zum Repo
        remote: Remote
        branch: Branch
        set_upstream: -u Flag für neue Branches
        
    Returns:
        Push-Ergebnis
    """
    try:
        repo = get_repo(repo_path)
        
        branch = branch or repo.active_branch.name
        
        if set_upstream:
            result = repo.git.push("-u", remote, branch)
        else:
            result = repo.git.push(remote, branch)
        
        return {
            "success": True,
            "repo": repo_path,
            "remote": remote,
            "branch": branch,
            "result": result or "Pushed successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def git_fetch(
    repo_path: str = Field(description="Pfad zum Git Repository"),
    remote: str = Field(default="origin", description="Remote-Name"),
    prune: bool = Field(default=True, description="Gelöschte Remote-Branches entfernen")
) -> dict:
    """
    Hole Remote-Infos ohne Merge (git fetch).
    
    Args:
        repo_path: Pfad zum Repo
        remote: Remote
        prune: Aufräumen
        
    Returns:
        Fetch-Ergebnis
    """
    try:
        repo = get_repo(repo_path)
        
        if prune:
            result = repo.git.fetch(remote, "--prune")
        else:
            result = repo.git.fetch(remote)
        
        return {
            "success": True,
            "repo": repo_path,
            "remote": remote,
            "result": result or "Fetched successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== MULTI-REPO TOOLS ====================

@mcp.tool()
async def scan_repos(
    base_path: str = Field(default="d:\\", description="Basis-Pfad zum Scannen"),
    max_depth: int = Field(default=2, description="Max. Verzeichnis-Tiefe")
) -> dict:
    """
    Finde alle Git-Repositories in einem Verzeichnis.
    
    Args:
        base_path: Start-Pfad
        max_depth: Wie tief suchen
        
    Returns:
        Liste aller gefundenen Repos
    """
    repos = []
    base = Path(base_path)
    
    def scan(path: Path, depth: int):
        if depth > max_depth:
            return
        try:
            git_dir = path / ".git"
            if git_dir.exists() and git_dir.is_dir():
                repos.append(str(path))
                return  # Nicht in Submodules suchen
            
            for sub in path.iterdir():
                if sub.is_dir() and not sub.name.startswith("."):
                    scan(sub, depth + 1)
        except PermissionError:
            pass
    
    scan(base, 0)
    
    return {
        "success": True,
        "base_path": base_path,
        "repositories": repos,
        "count": len(repos)
    }


@mcp.tool()
async def multi_status(
    repo_paths: str = Field(description="Komma-getrennte Repo-Pfade")
) -> dict:
    """
    Zeige Status mehrerer Repos auf einmal.
    
    Args:
        repo_paths: Pfade mit Komma getrennt
        
    Returns:
        Status aller Repos
    """
    paths = [p.strip() for p in repo_paths.split(",")]
    results = []
    
    for path in paths:
        try:
            repo = get_repo(path)
            results.append({
                "path": path,
                "name": Path(path).name,
                "branch": repo.active_branch.name,
                "dirty": repo.is_dirty(),
                "untracked": len(repo.untracked_files)
            })
        except Exception as e:
            results.append({
                "path": path,
                "error": str(e)
            })
    
    return {
        "success": True,
        "repos": results
    }


# Server starten
if __name__ == "__main__":
    mcp.run()
