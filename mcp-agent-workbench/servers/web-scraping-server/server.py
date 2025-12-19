"""
Web Scraping MCP Server

Ein MCP-Server für Web-Scraping-Operationen.
Extrahiert Inhalte von Webseiten.
"""

from fastmcp import FastMCP
import httpx
from bs4 import BeautifulSoup
from typing import Optional
import json
import re
from urllib.parse import urljoin, urlparse

mcp = FastMCP("web-scraping-server")

# HTTP Client
_http_client: Optional[httpx.AsyncClient] = None

# Default Headers für realistische Anfragen
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
}


async def get_client() -> httpx.AsyncClient:
    """Holt oder erstellt den HTTP Client."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            follow_redirects=True,
            timeout=30.0
        )
    return _http_client


# ============================================================================
# SCRAPING TOOLS
# ============================================================================

@mcp.tool
async def fetch_page(url: str) -> dict:
    """
    Lädt eine Webseite und gibt den rohen HTML-Inhalt zurück.
    
    Args:
        url: Die URL der Webseite
    
    Returns:
        HTML-Inhalt und Metadaten
    """
    try:
        client = await get_client()
        response = await client.get(url)
        response.raise_for_status()
        
        return {
            "url": str(response.url),
            "status_code": response.status_code,
            "content_type": response.headers.get("content-type", ""),
            "content_length": len(response.text),
            "html": response.text[:50000]  # Erste 50KB
        }
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP Fehler: {e.response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
async def extract_text(url: str, selector: str = None) -> dict:
    """
    Extrahiert Text von einer Webseite.
    
    Args:
        url: Die URL der Webseite
        selector: CSS-Selector (optional, z.B. "article", "main", ".content")
    
    Returns:
        Extrahierter Text
    """
    try:
        client = await get_client()
        response = await client.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        
        # Script und Style entfernen
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        
        if selector:
            elements = soup.select(selector)
            text = "\n\n".join(el.get_text(strip=True, separator=" ") for el in elements)
        else:
            # Versuche Hauptinhalt zu finden
            main = soup.find("main") or soup.find("article") or soup.find("body")
            text = main.get_text(strip=True, separator=" ") if main else ""
        
        # Mehrfache Whitespaces entfernen
        text = re.sub(r'\s+', ' ', text)
        
        return {
            "url": str(response.url),
            "selector": selector or "auto",
            "text_length": len(text),
            "text": text[:20000]  # Erste 20KB
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
async def extract_links(url: str, filter_pattern: str = None) -> dict:
    """
    Extrahiert alle Links von einer Webseite.
    
    Args:
        url: Die URL der Webseite
        filter_pattern: Regex-Pattern zum Filtern (optional)
    
    Returns:
        Liste der gefundenen Links
    """
    try:
        client = await get_client()
        response = await client.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        links = []
        
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            absolute_url = urljoin(url, href)
            text = a_tag.get_text(strip=True)[:100]
            
            if filter_pattern:
                if not re.search(filter_pattern, absolute_url):
                    continue
            
            links.append({
                "url": absolute_url,
                "text": text
            })
        
        return {
            "url": str(response.url),
            "total_links": len(links),
            "links": links[:100]  # Erste 100
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
async def extract_images(url: str) -> dict:
    """
    Extrahiert alle Bilder von einer Webseite.
    
    Args:
        url: Die URL der Webseite
    
    Returns:
        Liste der gefundenen Bilder
    """
    try:
        client = await get_client()
        response = await client.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        images = []
        
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src:
                absolute_url = urljoin(url, src)
                images.append({
                    "url": absolute_url,
                    "alt": img.get("alt", "")[:100],
                    "width": img.get("width"),
                    "height": img.get("height")
                })
        
        return {
            "url": str(response.url),
            "total_images": len(images),
            "images": images[:50]
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
async def extract_metadata(url: str) -> dict:
    """
    Extrahiert Metadaten einer Webseite (Title, Description, OG-Tags).
    
    Args:
        url: Die URL der Webseite
    
    Returns:
        Metadaten der Seite
    """
    try:
        client = await get_client()
        response = await client.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        
        # Title
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)
        
        # Meta Description
        description = ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            description = meta_desc.get("content", "")
        
        # Open Graph Tags
        og_tags = {}
        for og in soup.find_all("meta", attrs={"property": re.compile(r"^og:")}):
            prop = og.get("property", "").replace("og:", "")
            og_tags[prop] = og.get("content", "")
        
        # Keywords
        keywords = []
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        if meta_keywords:
            keywords = [k.strip() for k in meta_keywords.get("content", "").split(",")]
        
        # Canonical URL
        canonical = ""
        canonical_tag = soup.find("link", attrs={"rel": "canonical"})
        if canonical_tag:
            canonical = canonical_tag.get("href", "")
        
        return {
            "url": str(response.url),
            "title": title,
            "description": description,
            "keywords": keywords[:20],
            "canonical": canonical,
            "og_tags": og_tags
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
async def extract_tables(url: str) -> dict:
    """
    Extrahiert Tabellen von einer Webseite.
    
    Args:
        url: Die URL der Webseite
    
    Returns:
        Liste der Tabellen als strukturierte Daten
    """
    try:
        client = await get_client()
        response = await client.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        tables = []
        
        for table_idx, table in enumerate(soup.find_all("table")):
            rows = []
            headers = []
            
            # Headers extrahieren
            thead = table.find("thead")
            if thead:
                for th in thead.find_all(["th", "td"]):
                    headers.append(th.get_text(strip=True))
            
            # Rows extrahieren
            tbody = table.find("tbody") or table
            for tr in tbody.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if cells:
                    if not headers and all(tr.find_all("th")):
                        headers = cells
                    else:
                        rows.append(cells)
            
            tables.append({
                "index": table_idx,
                "headers": headers,
                "rows": rows[:50],  # Erste 50 Zeilen
                "total_rows": len(rows)
            })
        
        return {
            "url": str(response.url),
            "total_tables": len(tables),
            "tables": tables[:10]  # Erste 10 Tabellen
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
async def extract_by_selector(url: str, selectors: list[str]) -> dict:
    """
    Extrahiert Elemente anhand mehrerer CSS-Selektoren.
    
    Args:
        url: Die URL der Webseite
        selectors: Liste von CSS-Selektoren
    
    Returns:
        Gefundene Elemente pro Selektor
    """
    try:
        client = await get_client()
        response = await client.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        results = {}
        
        for selector in selectors:
            elements = soup.select(selector)
            results[selector] = [
                {
                    "text": el.get_text(strip=True)[:500],
                    "html": str(el)[:1000],
                    "attrs": dict(el.attrs)
                }
                for el in elements[:20]
            ]
        
        return {
            "url": str(response.url),
            "results": results
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
async def check_url(url: str) -> dict:
    """
    Prüft ob eine URL erreichbar ist und gibt Status-Infos zurück.
    
    Args:
        url: Die zu prüfende URL
    
    Returns:
        Status-Informationen
    """
    try:
        client = await get_client()
        response = await client.head(url)
        
        return {
            "url": str(response.url),
            "reachable": True,
            "status_code": response.status_code,
            "content_type": response.headers.get("content-type", ""),
            "content_length": response.headers.get("content-length"),
            "server": response.headers.get("server", ""),
            "redirect": str(response.url) != url
        }
    except Exception as e:
        return {
            "url": url,
            "reachable": False,
            "error": str(e)
        }


# ============================================================================
# RESOURCE
# ============================================================================

@mcp.resource("scraping://help")
def scraping_help() -> str:
    """Hilfe zu Web-Scraping-Tools."""
    return json.dumps({
        "description": "Web Scraping MCP Server",
        "tools": [
            "fetch_page - Rohen HTML-Inhalt laden",
            "extract_text - Text extrahieren",
            "extract_links - Links extrahieren",
            "extract_images - Bilder extrahieren",
            "extract_metadata - Meta-Tags extrahieren",
            "extract_tables - Tabellen extrahieren",
            "extract_by_selector - CSS-Selektoren verwenden",
            "check_url - URL-Erreichbarkeit prüfen"
        ],
        "tips": [
            "Verwende extract_text für Artikel-Inhalte",
            "CSS-Selektoren: 'article', 'main', '.content', '#main'",
            "Tabellen werden automatisch strukturiert"
        ]
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
