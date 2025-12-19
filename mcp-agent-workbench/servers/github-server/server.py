"""
GitHub MCP Server

Ein MCP-Server für GitHub Repository-Operationen.
Bietet Tools für Issues, PRs, Repos und mehr.
"""

from fastmcp import FastMCP
from github import Github, GithubException
from typing import Optional
import os
import json

mcp = FastMCP("github-server")

# GitHub Client (wird bei Bedarf initialisiert)
_github_client: Optional[Github] = None


def get_github() -> Github:
    """Holt oder erstellt den GitHub Client."""
    global _github_client
    if _github_client is None:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN Umgebungsvariable nicht gesetzt")
        _github_client = Github(token)
    return _github_client


# ============================================================================
# REPOSITORY TOOLS
# ============================================================================

@mcp.tool
def get_repo_info(owner: str, repo: str) -> dict:
    """
    Holt Informationen über ein GitHub Repository.
    
    Args:
        owner: Repository-Owner (User oder Organisation)
        repo: Repository-Name
    
    Returns:
        Dictionary mit Repository-Informationen
    """
    try:
        g = get_github()
        repository = g.get_repo(f"{owner}/{repo}")
        
        return {
            "name": repository.name,
            "full_name": repository.full_name,
            "description": repository.description,
            "url": repository.html_url,
            "stars": repository.stargazers_count,
            "forks": repository.forks_count,
            "open_issues": repository.open_issues_count,
            "language": repository.language,
            "default_branch": repository.default_branch,
            "created_at": repository.created_at.isoformat() if repository.created_at else None,
            "updated_at": repository.updated_at.isoformat() if repository.updated_at else None,
            "topics": repository.get_topics(),
        }
    except GithubException as e:
        return {"error": f"GitHub API Fehler: {e.data.get('message', str(e))}"}


@mcp.tool
def list_repos(username: str, max_results: int = 10) -> list[dict]:
    """
    Listet Repositories eines Users oder einer Organisation.
    
    Args:
        username: GitHub Username oder Organisation
        max_results: Maximale Anzahl Ergebnisse (default: 10)
    
    Returns:
        Liste von Repository-Informationen
    """
    try:
        g = get_github()
        user = g.get_user(username)
        repos = []
        
        for repo in user.get_repos()[:max_results]:
            repos.append({
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "url": repo.html_url,
                "stars": repo.stargazers_count,
                "language": repo.language,
            })
        
        return repos
    except GithubException as e:
        return [{"error": f"GitHub API Fehler: {e.data.get('message', str(e))}"}]


@mcp.tool
def search_repos(query: str, max_results: int = 10) -> list[dict]:
    """
    Sucht nach Repositories auf GitHub.
    
    Args:
        query: Suchbegriff (z.B. "mcp server python")
        max_results: Maximale Anzahl Ergebnisse (default: 10)
    
    Returns:
        Liste gefundener Repositories
    """
    try:
        g = get_github()
        repos = []
        
        for repo in g.search_repositories(query)[:max_results]:
            repos.append({
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "url": repo.html_url,
                "stars": repo.stargazers_count,
                "language": repo.language,
            })
        
        return repos
    except GithubException as e:
        return [{"error": f"GitHub API Fehler: {e.data.get('message', str(e))}"}]


# ============================================================================
# ISSUE TOOLS
# ============================================================================

@mcp.tool
def list_issues(
    owner: str, 
    repo: str, 
    state: str = "open",
    max_results: int = 10
) -> list[dict]:
    """
    Listet Issues eines Repositories.
    
    Args:
        owner: Repository-Owner
        repo: Repository-Name
        state: Issue-Status ("open", "closed", "all")
        max_results: Maximale Anzahl Ergebnisse
    
    Returns:
        Liste von Issues
    """
    try:
        g = get_github()
        repository = g.get_repo(f"{owner}/{repo}")
        issues = []
        
        for issue in repository.get_issues(state=state)[:max_results]:
            if not issue.pull_request:  # Nur echte Issues, keine PRs
                issues.append({
                    "number": issue.number,
                    "title": issue.title,
                    "state": issue.state,
                    "url": issue.html_url,
                    "author": issue.user.login,
                    "labels": [l.name for l in issue.labels],
                    "created_at": issue.created_at.isoformat(),
                    "comments": issue.comments,
                })
        
        return issues
    except GithubException as e:
        return [{"error": f"GitHub API Fehler: {e.data.get('message', str(e))}"}]


@mcp.tool
def get_issue(owner: str, repo: str, issue_number: int) -> dict:
    """
    Holt Details zu einem spezifischen Issue.
    
    Args:
        owner: Repository-Owner
        repo: Repository-Name
        issue_number: Issue-Nummer
    
    Returns:
        Issue-Details
    """
    try:
        g = get_github()
        repository = g.get_repo(f"{owner}/{repo}")
        issue = repository.get_issue(issue_number)
        
        return {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body,
            "state": issue.state,
            "url": issue.html_url,
            "author": issue.user.login,
            "labels": [l.name for l in issue.labels],
            "assignees": [a.login for a in issue.assignees],
            "created_at": issue.created_at.isoformat(),
            "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
            "comments": issue.comments,
        }
    except GithubException as e:
        return {"error": f"GitHub API Fehler: {e.data.get('message', str(e))}"}


@mcp.tool
def create_issue(
    owner: str, 
    repo: str, 
    title: str, 
    body: str = "",
    labels: list[str] = []
) -> dict:
    """
    Erstellt ein neues Issue.
    
    Args:
        owner: Repository-Owner
        repo: Repository-Name
        title: Issue-Titel
        body: Issue-Beschreibung (optional)
        labels: Labels für das Issue (optional)
    
    Returns:
        Erstelltes Issue
    """
    try:
        g = get_github()
        repository = g.get_repo(f"{owner}/{repo}")
        issue = repository.create_issue(title=title, body=body, labels=labels)
        
        return {
            "success": True,
            "number": issue.number,
            "title": issue.title,
            "url": issue.html_url,
        }
    except GithubException as e:
        return {"error": f"GitHub API Fehler: {e.data.get('message', str(e))}"}


# ============================================================================
# PULL REQUEST TOOLS
# ============================================================================

@mcp.tool
def list_pull_requests(
    owner: str, 
    repo: str, 
    state: str = "open",
    max_results: int = 10
) -> list[dict]:
    """
    Listet Pull Requests eines Repositories.
    
    Args:
        owner: Repository-Owner
        repo: Repository-Name
        state: PR-Status ("open", "closed", "all")
        max_results: Maximale Anzahl Ergebnisse
    
    Returns:
        Liste von Pull Requests
    """
    try:
        g = get_github()
        repository = g.get_repo(f"{owner}/{repo}")
        prs = []
        
        for pr in repository.get_pulls(state=state)[:max_results]:
            prs.append({
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "url": pr.html_url,
                "author": pr.user.login,
                "head": pr.head.ref,
                "base": pr.base.ref,
                "created_at": pr.created_at.isoformat(),
                "merged": pr.merged,
            })
        
        return prs
    except GithubException as e:
        return [{"error": f"GitHub API Fehler: {e.data.get('message', str(e))}"}]


@mcp.tool
def get_pull_request(owner: str, repo: str, pr_number: int) -> dict:
    """
    Holt Details zu einem spezifischen Pull Request.
    
    Args:
        owner: Repository-Owner
        repo: Repository-Name
        pr_number: PR-Nummer
    
    Returns:
        Pull Request Details
    """
    try:
        g = get_github()
        repository = g.get_repo(f"{owner}/{repo}")
        pr = repository.get_pull(pr_number)
        
        return {
            "number": pr.number,
            "title": pr.title,
            "body": pr.body,
            "state": pr.state,
            "url": pr.html_url,
            "author": pr.user.login,
            "head": pr.head.ref,
            "base": pr.base.ref,
            "mergeable": pr.mergeable,
            "merged": pr.merged,
            "additions": pr.additions,
            "deletions": pr.deletions,
            "changed_files": pr.changed_files,
            "commits": pr.commits,
            "created_at": pr.created_at.isoformat(),
        }
    except GithubException as e:
        return {"error": f"GitHub API Fehler: {e.data.get('message', str(e))}"}


# ============================================================================
# FILE TOOLS
# ============================================================================

@mcp.tool
def get_file_content(
    owner: str, 
    repo: str, 
    path: str,
    ref: str = "main"
) -> dict:
    """
    Holt den Inhalt einer Datei aus einem Repository.
    
    Args:
        owner: Repository-Owner
        repo: Repository-Name
        path: Pfad zur Datei (z.B. "src/main.py")
        ref: Branch oder Commit (default: "main")
    
    Returns:
        Dateiinhalt und Metadaten
    """
    try:
        g = get_github()
        repository = g.get_repo(f"{owner}/{repo}")
        content = repository.get_contents(path, ref=ref)
        
        if isinstance(content, list):
            return {"error": "Pfad ist ein Verzeichnis, keine Datei"}
        
        return {
            "name": content.name,
            "path": content.path,
            "size": content.size,
            "encoding": content.encoding,
            "content": content.decoded_content.decode("utf-8"),
            "sha": content.sha,
            "url": content.html_url,
        }
    except GithubException as e:
        return {"error": f"GitHub API Fehler: {e.data.get('message', str(e))}"}


@mcp.tool
def list_directory(
    owner: str, 
    repo: str, 
    path: str = "",
    ref: str = "main"
) -> list[dict]:
    """
    Listet den Inhalt eines Verzeichnisses im Repository.
    
    Args:
        owner: Repository-Owner
        repo: Repository-Name
        path: Pfad zum Verzeichnis (leer = Root)
        ref: Branch oder Commit (default: "main")
    
    Returns:
        Liste von Dateien und Verzeichnissen
    """
    try:
        g = get_github()
        repository = g.get_repo(f"{owner}/{repo}")
        contents = repository.get_contents(path, ref=ref)
        
        if not isinstance(contents, list):
            contents = [contents]
        
        items = []
        for item in contents:
            items.append({
                "name": item.name,
                "path": item.path,
                "type": item.type,  # "file" oder "dir"
                "size": item.size if item.type == "file" else None,
            })
        
        return sorted(items, key=lambda x: (x["type"] != "dir", x["name"]))
    except GithubException as e:
        return [{"error": f"GitHub API Fehler: {e.data.get('message', str(e))}"}]


# ============================================================================
# USER TOOLS
# ============================================================================

@mcp.tool
def get_user_info(username: str) -> dict:
    """
    Holt Informationen über einen GitHub User.
    
    Args:
        username: GitHub Username
    
    Returns:
        User-Informationen
    """
    try:
        g = get_github()
        user = g.get_user(username)
        
        return {
            "login": user.login,
            "name": user.name,
            "bio": user.bio,
            "company": user.company,
            "location": user.location,
            "url": user.html_url,
            "public_repos": user.public_repos,
            "followers": user.followers,
            "following": user.following,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
    except GithubException as e:
        return {"error": f"GitHub API Fehler: {e.data.get('message', str(e))}"}


# ============================================================================
# RESOURCES
# ============================================================================

@mcp.resource("github://authenticated-user")
def get_authenticated_user() -> str:
    """Informationen über den authentifizierten User"""
    try:
        g = get_github()
        user = g.get_user()
        return json.dumps({
            "login": user.login,
            "name": user.name,
            "email": user.email,
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


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
    
    mcp.run()
