"""
Ollama MCP Server - Lokale LLM-Verwaltung

Tools für:
- Modelle auflisten, laden, löschen
- Chat/Completion
- Embeddings generieren
- Modell-Info
- Server-Status

Verbindet sich mit Remote-Ollama auf Docker-Host
"""

import os
import httpx
from fastmcp import FastMCP
from pydantic import Field
from typing import Optional
from datetime import datetime

# Server initialisieren
mcp = FastMCP(
    "Ollama Server",
    instructions="Lokale LLMs mit Ollama - Chat, Embeddings, Modell-Verwaltung"
)

# Ollama-Konfiguration (Remote Docker oder lokal)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://192.168.0.27:11434")


def get_base_url():
    """Hole Ollama API URL"""
    return OLLAMA_HOST.rstrip("/")


# ==================== STATUS TOOLS ====================

@mcp.tool()
async def ollama_status() -> dict:
    """
    Prüfe ob Ollama-Server erreichbar ist.
    
    Returns:
        Server-Status und Version
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{get_base_url()}/api/version", timeout=10.0)
            if response.status_code == 200:
                return {
                    "success": True,
                    "status": "online",
                    "host": OLLAMA_HOST,
                    "version": response.json()
                }
            return {
                "success": False,
                "status": "error",
                "host": OLLAMA_HOST,
                "http_code": response.status_code
            }
    except httpx.ConnectError:
        return {
            "success": False,
            "status": "offline",
            "host": OLLAMA_HOST,
            "error": "Ollama-Server nicht erreichbar",
            "hint": f"Ist Ollama auf {OLLAMA_HOST} gestartet?"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def list_models() -> dict:
    """
    Liste alle lokal verfügbaren Ollama-Modelle.
    
    Returns:
        Liste der installierten Modelle mit Größe
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{get_base_url()}/api/tags", timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            models = []
            for m in data.get("models", []):
                size_gb = m.get("size", 0) / (1024**3)
                models.append({
                    "name": m.get("name"),
                    "size": f"{size_gb:.1f} GB",
                    "modified": m.get("modified_at"),
                    "family": m.get("details", {}).get("family")
                })
            
            return {
                "success": True,
                "count": len(models),
                "models": models
            }
    except httpx.ConnectError:
        return {"success": False, "error": "Ollama nicht erreichbar", "host": OLLAMA_HOST}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def model_info(
    model: str = Field(description="Modell-Name (z.B. llama3.2, mistral, codellama)")
) -> dict:
    """
    Zeige Details zu einem Modell.
    
    Args:
        model: Name des Modells
        
    Returns:
        Modell-Architektur, Parameter, Kontext-Länge
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{get_base_url()}/api/show",
                json={"name": model},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "model": model,
                "license": data.get("license", "")[:200],
                "modelfile": data.get("modelfile", "")[:500],
                "parameters": data.get("parameters"),
                "template": data.get("template"),
                "details": data.get("details")
            }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"success": False, "error": f"Modell '{model}' nicht gefunden"}
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== MODEL MANAGEMENT ====================

@mcp.tool()
async def pull_model(
    model: str = Field(description="Modell zum Herunterladen (z.B. llama3.2:8b, mistral, codellama)")
) -> dict:
    """
    Lade ein Modell von Ollama-Registry herunter.
    
    Args:
        model: Modell-Name (optional mit Tag wie :8b, :70b)
        
    Returns:
        Download-Status
    """
    try:
        async with httpx.AsyncClient() as client:
            # Stream für Progress
            async with client.stream(
                "POST",
                f"{get_base_url()}/api/pull",
                json={"name": model},
                timeout=None  # Kein Timeout für große Downloads
            ) as response:
                last_status = ""
                async for line in response.aiter_lines():
                    if line:
                        import json
                        data = json.loads(line)
                        last_status = data.get("status", "")
                        if "error" in data:
                            return {"success": False, "error": data["error"]}
                
                return {
                    "success": True,
                    "model": model,
                    "status": last_status,
                    "message": f"Modell '{model}' erfolgreich geladen"
                }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def delete_model(
    model: str = Field(description="Modell zum Löschen")
) -> dict:
    """
    Lösche ein lokales Modell.
    
    Args:
        model: Name des Modells
        
    Returns:
        Bestätigung
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{get_base_url()}/api/delete",
                json={"name": model},
                timeout=30.0
            )
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Modell '{model}' gelöscht"
                }
            return {
                "success": False,
                "error": f"Fehler: {response.status_code}"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def copy_model(
    source: str = Field(description="Quell-Modell"),
    destination: str = Field(description="Neuer Name für Kopie")
) -> dict:
    """
    Erstelle eine Kopie eines Modells (für Custom-Versionen).
    
    Args:
        source: Existierendes Modell
        destination: Name der Kopie
        
    Returns:
        Bestätigung
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{get_base_url()}/api/copy",
                json={"source": source, "destination": destination},
                timeout=60.0
            )
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Modell kopiert: {source} → {destination}"
                }
            return {"success": False, "error": f"Fehler: {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== INFERENCE TOOLS ====================

@mcp.tool()
async def chat(
    model: str = Field(description="Modell-Name"),
    message: str = Field(description="Deine Nachricht/Frage"),
    system_prompt: Optional[str] = Field(default=None, description="System-Prompt (Rolle/Kontext)"),
    temperature: float = Field(default=0.7, description="Kreativität 0.0-1.0")
) -> dict:
    """
    Chatte mit einem Ollama-Modell.
    
    Args:
        model: Welches Modell (z.B. llama3.2, mistral)
        message: Deine Frage
        system_prompt: Optional: Definiere Rolle
        temperature: 0=deterministic, 1=creative
        
    Returns:
        Antwort des Modells
    """
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{get_base_url()}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": temperature}
                },
                timeout=120.0
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "model": model,
                "response": data.get("message", {}).get("content", ""),
                "stats": {
                    "total_duration_ms": data.get("total_duration", 0) / 1_000_000,
                    "eval_count": data.get("eval_count"),
                    "tokens_per_second": data.get("eval_count", 0) / max(data.get("eval_duration", 1) / 1_000_000_000, 0.001)
                }
            }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"success": False, "error": f"Modell '{model}' nicht gefunden. Erst mit pull_model laden!"}
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def generate(
    model: str = Field(description="Modell-Name"),
    prompt: str = Field(description="Dein Prompt"),
    max_tokens: int = Field(default=500, description="Max. Antwort-Länge")
) -> dict:
    """
    Generiere Text-Completion (ohne Chat-Format).
    
    Args:
        model: Welches Modell
        prompt: Der Prompt
        max_tokens: Maximale Tokens in Antwort
        
    Returns:
        Generierter Text
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{get_base_url()}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": max_tokens}
                },
                timeout=120.0
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "model": model,
                "response": data.get("response", ""),
                "done": data.get("done"),
                "context_length": len(data.get("context", []))
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def embeddings(
    model: str = Field(description="Embedding-Modell (z.B. nomic-embed-text, mxbai-embed-large)"),
    text: str = Field(description="Text zum Embedden")
) -> dict:
    """
    Generiere Embeddings für einen Text (für Semantic Search, RAG).
    
    Args:
        model: Embedding-Modell
        text: Der zu verarbeitende Text
        
    Returns:
        Embedding-Vektor und Dimensionen
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{get_base_url()}/api/embeddings",
                json={"model": model, "prompt": text},
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            
            embedding = data.get("embedding", [])
            return {
                "success": True,
                "model": model,
                "dimensions": len(embedding),
                "embedding_preview": embedding[:10] if embedding else [],
                "full_embedding": embedding
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== RUNNING MODELS ====================

@mcp.tool()
async def list_running() -> dict:
    """
    Zeige aktuell in VRAM geladene Modelle.
    
    Returns:
        Liste aktiver Modelle mit VRAM-Nutzung
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{get_base_url()}/api/ps", timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            models = []
            for m in data.get("models", []):
                size_gb = m.get("size", 0) / (1024**3)
                vram_gb = m.get("size_vram", 0) / (1024**3)
                models.append({
                    "name": m.get("name"),
                    "size": f"{size_gb:.1f} GB",
                    "vram": f"{vram_gb:.1f} GB",
                    "processor": m.get("details", {}).get("processor", "unknown"),
                    "expires": m.get("expires_at")
                })
            
            return {
                "success": True,
                "running_models": models,
                "count": len(models)
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


# Server starten
if __name__ == "__main__":
    mcp.run()
