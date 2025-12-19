"""
IONOS MCP Server - Hosting-Verwaltung via IONOS API

Tools für:
- DNS-Verwaltung (Zonen, Records)
- Domain-Verwaltung
- SSL-Zertifikate
- Webspace/Hosting
- Datenbanken

API Docs: https://developer.hosting.ionos.de/docs/dns
"""

import os
import httpx
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Server initialisieren
mcp = FastMCP(
    "IONOS Server",
    instructions="IONOS Hosting-Verwaltung - DNS, Domains, SSL, Webspace"
)

# IONOS API Konfiguration
IONOS_API_KEY = os.getenv("IONOS_API_KEY", "")
IONOS_API_URL = "https://api.hosting.ionos.com"
DNS_API_URL = "https://dns.api.ionos.com/v1"


def get_headers():
    """API Headers mit Key"""
    if not IONOS_API_KEY:
        raise ValueError("IONOS_API_KEY nicht konfiguriert! Bitte in .env setzen.")
    return {
        "X-API-Key": IONOS_API_KEY,
        "Content-Type": "application/json"
    }


# ==================== DNS TOOLS ====================

@mcp.tool()
async def list_dns_zones() -> dict:
    """
    Liste alle DNS-Zonen (Domains) im IONOS-Account.
    
    Returns:
        Liste aller DNS-Zonen mit ID und Name
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{DNS_API_URL}/zones",
                headers=get_headers(),
                timeout=30.0
            )
            response.raise_for_status()
            zones = response.json()
            return {
                "success": True,
                "count": len(zones),
                "zones": [{"id": z.get("id"), "name": z.get("name"), "type": z.get("type")} for z in zones]
            }
    except ValueError as e:
        return {"success": False, "error": str(e), "hint": "IONOS_API_KEY in .env setzen"}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"API Fehler: {e.response.status_code}", "details": e.response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_dns_zone(zone_id: str = Field(description="Zone-ID oder Domain-Name")) -> dict:
    """
    Zeige Details einer DNS-Zone inkl. aller Records.
    
    Args:
        zone_id: Die Zone-ID oder der Domain-Name
        
    Returns:
        Alle DNS-Records der Zone
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{DNS_API_URL}/zones/{zone_id}",
                headers=get_headers(),
                timeout=30.0
            )
            response.raise_for_status()
            zone = response.json()
            return {
                "success": True,
                "zone": {
                    "id": zone.get("id"),
                    "name": zone.get("name"),
                    "type": zone.get("type")
                },
                "records": zone.get("records", [])
            }
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"API Fehler: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def create_dns_record(
    zone_id: str = Field(description="Zone-ID"),
    name: str = Field(description="Record-Name (z.B. 'www' oder '@' für Root)"),
    record_type: str = Field(description="Record-Typ: A, AAAA, CNAME, MX, TXT, NS, SRV"),
    content: str = Field(description="Record-Inhalt (z.B. IP-Adresse für A-Record)"),
    ttl: int = Field(default=3600, description="Time-to-Live in Sekunden"),
    priority: Optional[int] = Field(default=None, description="Priorität (nur für MX/SRV)")
) -> dict:
    """
    Erstelle einen neuen DNS-Record.
    
    Args:
        zone_id: ID der DNS-Zone
        name: Subdomain oder @ für Root
        record_type: A, AAAA, CNAME, MX, TXT, NS, SRV
        content: Ziel-IP oder Wert
        ttl: Cache-Zeit (Standard: 3600)
        priority: Für MX-Records
        
    Returns:
        Erstellter Record
    """
    try:
        record_data = {
            "name": name,
            "type": record_type.upper(),
            "content": content,
            "ttl": ttl,
            "disabled": False
        }
        if priority is not None:
            record_data["prio"] = priority
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DNS_API_URL}/zones/{zone_id}/records",
                headers=get_headers(),
                json=[record_data],
                timeout=30.0
            )
            response.raise_for_status()
            return {
                "success": True,
                "message": f"DNS-Record {record_type} für '{name}' erstellt",
                "record": record_data
            }
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"API Fehler: {e.response.status_code}", "details": e.response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def update_dns_record(
    zone_id: str = Field(description="Zone-ID"),
    record_id: str = Field(description="Record-ID"),
    content: str = Field(description="Neuer Record-Inhalt"),
    ttl: Optional[int] = Field(default=None, description="Neue TTL")
) -> dict:
    """
    Aktualisiere einen bestehenden DNS-Record.
    
    Args:
        zone_id: ID der DNS-Zone
        record_id: ID des Records
        content: Neuer Wert
        ttl: Neue TTL (optional)
        
    Returns:
        Aktualisierter Record
    """
    try:
        update_data = {"content": content}
        if ttl:
            update_data["ttl"] = ttl
            
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{DNS_API_URL}/zones/{zone_id}/records/{record_id}",
                headers=get_headers(),
                json=update_data,
                timeout=30.0
            )
            response.raise_for_status()
            return {
                "success": True,
                "message": "DNS-Record aktualisiert",
                "new_content": content
            }
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"API Fehler: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def delete_dns_record(
    zone_id: str = Field(description="Zone-ID"),
    record_id: str = Field(description="Record-ID zum Löschen")
) -> dict:
    """
    Lösche einen DNS-Record.
    
    Args:
        zone_id: ID der DNS-Zone
        record_id: ID des zu löschenden Records
        
    Returns:
        Bestätigung
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{DNS_API_URL}/zones/{zone_id}/records/{record_id}",
                headers=get_headers(),
                timeout=30.0
            )
            response.raise_for_status()
            return {
                "success": True,
                "message": f"DNS-Record {record_id} gelöscht"
            }
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"API Fehler: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== DOMAIN TOOLS ====================

@mcp.tool()
async def check_ionos_config() -> dict:
    """
    Prüfe die IONOS-Konfiguration und API-Verbindung.
    
    Returns:
        Status der Konfiguration
    """
    config_status = {
        "api_key_set": bool(IONOS_API_KEY),
        "api_key_preview": IONOS_API_KEY[:10] + "..." if IONOS_API_KEY else None,
        "dns_api_url": DNS_API_URL,
        "timestamp": datetime.now().isoformat()
    }
    
    if not IONOS_API_KEY:
        return {
            "success": False,
            "config": config_status,
            "error": "IONOS_API_KEY nicht gesetzt",
            "hint": "Füge IONOS_API_KEY=dein-api-key zur .env Datei hinzu"
        }
    
    # Test API-Verbindung
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{DNS_API_URL}/zones",
                headers=get_headers(),
                timeout=10.0
            )
            response.raise_for_status()
            zones = response.json()
            return {
                "success": True,
                "config": config_status,
                "connection": "OK",
                "zones_found": len(zones)
            }
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "config": config_status,
            "error": f"API antwortet mit Fehler: {e.response.status_code}",
            "hint": "Prüfe ob der API-Key gültig ist"
        }
    except Exception as e:
        return {
            "success": False,
            "config": config_status,
            "error": str(e)
        }


@mcp.tool()
async def quick_dns_update(
    domain: str = Field(description="Domain-Name (z.B. example.com)"),
    ip_address: str = Field(description="Neue IP-Adresse")
) -> dict:
    """
    Schnelle Aktualisierung der Haupt-IP einer Domain (A-Record für @).
    
    Args:
        domain: Der Domain-Name
        ip_address: Die neue IP-Adresse
        
    Returns:
        Ergebnis der Aktualisierung
    """
    try:
        async with httpx.AsyncClient() as client:
            # Erst Zone finden
            response = await client.get(
                f"{DNS_API_URL}/zones",
                headers=get_headers(),
                timeout=30.0
            )
            response.raise_for_status()
            zones = response.json()
            
            # Zone mit passendem Namen finden
            zone = next((z for z in zones if z.get("name") == domain), None)
            if not zone:
                return {
                    "success": False,
                    "error": f"Domain '{domain}' nicht gefunden",
                    "available_zones": [z.get("name") for z in zones]
                }
            
            zone_id = zone.get("id")
            
            # Records holen
            response = await client.get(
                f"{DNS_API_URL}/zones/{zone_id}",
                headers=get_headers(),
                timeout=30.0
            )
            response.raise_for_status()
            zone_data = response.json()
            
            # A-Record für Root (@) finden
            records = zone_data.get("records", [])
            root_a = next((r for r in records if r.get("type") == "A" and r.get("name") in ["@", domain, ""]), None)
            
            if root_a:
                # Update existierenden Record
                record_id = root_a.get("id")
                response = await client.put(
                    f"{DNS_API_URL}/zones/{zone_id}/records/{record_id}",
                    headers=get_headers(),
                    json={"content": ip_address},
                    timeout=30.0
                )
                response.raise_for_status()
                return {
                    "success": True,
                    "action": "updated",
                    "domain": domain,
                    "old_ip": root_a.get("content"),
                    "new_ip": ip_address
                }
            else:
                # Neuen Record erstellen
                response = await client.post(
                    f"{DNS_API_URL}/zones/{zone_id}/records",
                    headers=get_headers(),
                    json=[{"name": "@", "type": "A", "content": ip_address, "ttl": 3600}],
                    timeout=30.0
                )
                response.raise_for_status()
                return {
                    "success": True,
                    "action": "created",
                    "domain": domain,
                    "new_ip": ip_address
                }
                
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def list_all_dns_records() -> dict:
    """
    Liste ALLE DNS-Records über ALLE Zonen.
    Nützlich für Übersicht aller konfigurierten Domains.
    
    Returns:
        Komplette DNS-Übersicht
    """
    try:
        async with httpx.AsyncClient() as client:
            # Alle Zonen holen
            response = await client.get(
                f"{DNS_API_URL}/zones",
                headers=get_headers(),
                timeout=30.0
            )
            response.raise_for_status()
            zones = response.json()
            
            all_records = []
            for zone in zones:
                zone_id = zone.get("id")
                zone_name = zone.get("name")
                
                # Records dieser Zone holen
                response = await client.get(
                    f"{DNS_API_URL}/zones/{zone_id}",
                    headers=get_headers(),
                    timeout=30.0
                )
                if response.status_code == 200:
                    zone_data = response.json()
                    for record in zone_data.get("records", []):
                        all_records.append({
                            "zone": zone_name,
                            "name": record.get("name"),
                            "type": record.get("type"),
                            "content": record.get("content"),
                            "ttl": record.get("ttl")
                        })
            
            return {
                "success": True,
                "total_zones": len(zones),
                "total_records": len(all_records),
                "records": all_records
            }
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Server starten
if __name__ == "__main__":
    mcp.run()
