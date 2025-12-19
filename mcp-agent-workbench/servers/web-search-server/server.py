"""
Web Search MCP Server

Ein MCP-Server für Web-Suche.
Verwendet DuckDuckGo für anonyme Suchen.
"""

from fastmcp import FastMCP
from duckduckgo_search import DDGS
from typing import Optional
import json

mcp = FastMCP("web-search-server")


# ============================================================================
# SEARCH TOOLS
# ============================================================================

@mcp.tool
def web_search(
    query: str,
    max_results: int = 10,
    region: str = "de-de"
) -> dict:
    """
    Führt eine Web-Suche durch.
    
    Args:
        query: Suchbegriff
        max_results: Maximale Anzahl Ergebnisse (default: 10)
        region: Region für Suchergebnisse (default: de-de)
    
    Returns:
        Liste der Suchergebnisse
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(
                query,
                region=region,
                max_results=max_results
            ))
        
        return {
            "query": query,
            "total_results": len(results),
            "results": [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "description": r.get("body", "")
                }
                for r in results
            ]
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def news_search(
    query: str,
    max_results: int = 10,
    region: str = "de-de"
) -> dict:
    """
    Sucht nach aktuellen Nachrichten.
    
    Args:
        query: Suchbegriff
        max_results: Maximale Anzahl Ergebnisse
        region: Region für Suchergebnisse
    
    Returns:
        Liste der News-Ergebnisse
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(
                query,
                region=region,
                max_results=max_results
            ))
        
        return {
            "query": query,
            "type": "news",
            "total_results": len(results),
            "results": [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "source": r.get("source", ""),
                    "date": r.get("date", ""),
                    "description": r.get("body", "")
                }
                for r in results
            ]
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def image_search(
    query: str,
    max_results: int = 10,
    size: str = None,
    type_image: str = None
) -> dict:
    """
    Sucht nach Bildern.
    
    Args:
        query: Suchbegriff
        max_results: Maximale Anzahl Ergebnisse
        size: Bildgröße (Small, Medium, Large, Wallpaper)
        type_image: Bildtyp (photo, clipart, gif, transparent, line)
    
    Returns:
        Liste der Bilder
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(
                query,
                max_results=max_results,
                size=size,
                type_image=type_image
            ))
        
        return {
            "query": query,
            "type": "images",
            "total_results": len(results),
            "results": [
                {
                    "title": r.get("title", ""),
                    "image_url": r.get("image", ""),
                    "thumbnail": r.get("thumbnail", ""),
                    "source": r.get("source", ""),
                    "width": r.get("width"),
                    "height": r.get("height")
                }
                for r in results
            ]
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def video_search(
    query: str,
    max_results: int = 10,
    region: str = "de-de"
) -> dict:
    """
    Sucht nach Videos.
    
    Args:
        query: Suchbegriff
        max_results: Maximale Anzahl Ergebnisse
        region: Region für Suchergebnisse
    
    Returns:
        Liste der Videos
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.videos(
                query,
                region=region,
                max_results=max_results
            ))
        
        return {
            "query": query,
            "type": "videos",
            "total_results": len(results),
            "results": [
                {
                    "title": r.get("title", ""),
                    "url": r.get("content", ""),
                    "description": r.get("description", ""),
                    "publisher": r.get("publisher", ""),
                    "duration": r.get("duration", ""),
                    "views": r.get("statistics", {}).get("viewCount")
                }
                for r in results
            ]
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def maps_search(
    query: str,
    place: str = None,
    max_results: int = 10
) -> dict:
    """
    Sucht nach Orten/Karten.
    
    Args:
        query: Suchbegriff (z.B. "Restaurant")
        place: Ort für die Suche (z.B. "Berlin")
        max_results: Maximale Anzahl Ergebnisse
    
    Returns:
        Liste der Orte
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.maps(
                query,
                place=place,
                max_results=max_results
            ))
        
        return {
            "query": query,
            "place": place,
            "type": "maps",
            "total_results": len(results),
            "results": [
                {
                    "title": r.get("title", ""),
                    "address": r.get("address", ""),
                    "phone": r.get("phone", ""),
                    "url": r.get("url", ""),
                    "latitude": r.get("latitude"),
                    "longitude": r.get("longitude"),
                    "rating": r.get("rating"),
                    "reviews": r.get("reviews")
                }
                for r in results
            ]
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def instant_answer(query: str) -> dict:
    """
    Holt eine Instant-Antwort (wie Definitionen, Fakten).
    
    Args:
        query: Frage oder Begriff
    
    Returns:
        Instant-Antwort falls verfügbar
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.answers(query))
        
        if results:
            return {
                "query": query,
                "has_answer": True,
                "answers": [
                    {
                        "text": r.get("text", ""),
                        "source": r.get("url", "")
                    }
                    for r in results
                ]
            }
        else:
            return {
                "query": query,
                "has_answer": False,
                "message": "Keine Instant-Antwort verfügbar"
            }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def suggestions(query: str) -> dict:
    """
    Holt Suchvorschläge für einen Begriff.
    
    Args:
        query: Begonnener Suchbegriff
    
    Returns:
        Liste der Vorschläge
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.suggestions(query))
        
        return {
            "query": query,
            "suggestions": [r.get("phrase", "") for r in results]
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# RESOURCE
# ============================================================================

@mcp.resource("search://help")
def search_help() -> str:
    """Hilfe zu Web-Search-Tools."""
    return json.dumps({
        "description": "Web Search MCP Server (DuckDuckGo)",
        "tools": [
            "web_search - Allgemeine Web-Suche",
            "news_search - Aktuelle Nachrichten",
            "image_search - Bilder suchen",
            "video_search - Videos suchen",
            "maps_search - Orte suchen",
            "instant_answer - Schnelle Antworten",
            "suggestions - Suchvorschläge"
        ],
        "regions": [
            "de-de (Deutschland)",
            "at-de (Österreich)",
            "ch-de (Schweiz)",
            "en-us (USA)",
            "en-gb (UK)"
        ]
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
