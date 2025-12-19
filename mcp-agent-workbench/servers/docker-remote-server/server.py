"""
Docker Remote MCP Server

Ein MCP-Server für Docker-Operationen auf einem Remote-Host.
Verbindet sich über TCP zu einem Docker-Daemon.
"""

from fastmcp import FastMCP
import docker
from docker.errors import DockerException, NotFound
from typing import Optional
import os
import json

mcp = FastMCP("docker-remote-server")

# Docker Client für Remote-Verbindung
_docker_client: Optional[docker.DockerClient] = None


def get_docker() -> docker.DockerClient:
    """Holt oder erstellt den Docker Client für Remote-Verbindung."""
    global _docker_client
    if _docker_client is None:
        # Remote Docker Host aus Umgebungsvariable
        docker_host = os.environ.get("DOCKER_REMOTE_HOST", "tcp://192.168.0.27:2375")
        try:
            _docker_client = docker.DockerClient(base_url=docker_host)
            # Test connection
            _docker_client.ping()
        except DockerException as e:
            raise RuntimeError(f"Docker Remote nicht erreichbar ({docker_host}): {e}")
    return _docker_client


# ============================================================================
# SYSTEM INFO
# ============================================================================

@mcp.tool
def docker_info() -> dict:
    """
    Holt Docker System-Informationen vom Remote-Host.
    
    Returns:
        Dictionary mit System-Infos
    """
    try:
        client = get_docker()
        info = client.info()
        
        return {
            "host": os.environ.get("DOCKER_REMOTE_HOST", "tcp://192.168.0.27:2375"),
            "name": info.get("Name", "unknown"),
            "containers": info.get("Containers", 0),
            "containers_running": info.get("ContainersRunning", 0),
            "containers_paused": info.get("ContainersPaused", 0),
            "containers_stopped": info.get("ContainersStopped", 0),
            "images": info.get("Images", 0),
            "docker_version": info.get("ServerVersion", "unknown"),
            "os": info.get("OperatingSystem", "unknown"),
            "architecture": info.get("Architecture", "unknown"),
            "cpus": info.get("NCPU", 0),
            "memory_gb": round(info.get("MemTotal", 0) / (1024**3), 2)
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def docker_ping() -> dict:
    """
    Testet die Verbindung zum Remote Docker Host.
    
    Returns:
        Status der Verbindung
    """
    docker_host = os.environ.get("DOCKER_REMOTE_HOST", "tcp://192.168.0.27:2375")
    try:
        client = get_docker()
        client.ping()
        return {
            "success": True,
            "host": docker_host,
            "message": "Docker Remote Host erreichbar"
        }
    except Exception as e:
        return {
            "success": False,
            "host": docker_host,
            "error": str(e)
        }


# ============================================================================
# CONTAINER TOOLS
# ============================================================================

@mcp.tool
def list_containers(all: bool = False) -> list[dict]:
    """
    Listet Docker Container auf dem Remote-Host.
    
    Args:
        all: Auch gestoppte Container anzeigen (default: False)
    
    Returns:
        Liste der Container
    """
    try:
        client = get_docker()
        containers = []
        
        for container in client.containers.list(all=all):
            image_name = "unknown"
            if container.image and container.image.tags:
                image_name = container.image.tags[0]
            elif container.image:
                image_name = container.image.short_id
                
            containers.append({
                "id": container.short_id,
                "name": container.name,
                "image": image_name,
                "status": container.status,
                "created": str(container.attrs.get("Created", "")),
            })
        
        return containers
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool
def get_container(container_id: str) -> dict:
    """
    Holt Details zu einem Container.
    
    Args:
        container_id: Container ID oder Name
    
    Returns:
        Container-Details
    """
    try:
        client = get_docker()
        container = client.containers.get(container_id)
        
        image_name = "unknown"
        if container.image and container.image.tags:
            image_name = container.image.tags[0]
        elif container.image:
            image_name = container.image.short_id
        
        return {
            "id": container.short_id,
            "name": container.name,
            "image": image_name,
            "status": container.status,
            "created": str(container.attrs.get("Created", "")),
            "ports": container.attrs.get("NetworkSettings", {}).get("Ports", {}),
            "mounts": [m.get("Source", "") + ":" + m.get("Destination", "") 
                      for m in container.attrs.get("Mounts", [])],
            "networks": list(container.attrs.get("NetworkSettings", {}).get("Networks", {}).keys()),
            "env": container.attrs.get("Config", {}).get("Env", [])[:10]  # Erste 10
        }
    except NotFound:
        return {"error": f"Container '{container_id}' nicht gefunden"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def start_container(container_id: str) -> dict:
    """
    Startet einen Container.
    
    Args:
        container_id: Container ID oder Name
    """
    try:
        client = get_docker()
        container = client.containers.get(container_id)
        container.start()
        return {"success": True, "message": f"Container '{container_id}' gestartet"}
    except NotFound:
        return {"error": f"Container '{container_id}' nicht gefunden"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def stop_container(container_id: str, timeout: int = 10) -> dict:
    """
    Stoppt einen Container.
    
    Args:
        container_id: Container ID oder Name
        timeout: Timeout in Sekunden
    """
    try:
        client = get_docker()
        container = client.containers.get(container_id)
        container.stop(timeout=timeout)
        return {"success": True, "message": f"Container '{container_id}' gestoppt"}
    except NotFound:
        return {"error": f"Container '{container_id}' nicht gefunden"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def restart_container(container_id: str) -> dict:
    """
    Startet einen Container neu.
    
    Args:
        container_id: Container ID oder Name
    """
    try:
        client = get_docker()
        container = client.containers.get(container_id)
        container.restart()
        return {"success": True, "message": f"Container '{container_id}' neu gestartet"}
    except NotFound:
        return {"error": f"Container '{container_id}' nicht gefunden"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_container_logs(
    container_id: str,
    tail: int = 100,
    since: str = None
) -> dict:
    """
    Holt Logs eines Containers.
    
    Args:
        container_id: Container ID oder Name
        tail: Anzahl der letzten Zeilen
        since: Seit wann (z.B. "1h", "30m")
    """
    try:
        client = get_docker()
        container = client.containers.get(container_id)
        
        kwargs = {"tail": tail, "timestamps": True}
        if since:
            kwargs["since"] = since
            
        logs = container.logs(**kwargs).decode("utf-8", errors="replace")
        
        return {
            "container": container_id,
            "lines": tail,
            "logs": logs
        }
    except NotFound:
        return {"error": f"Container '{container_id}' nicht gefunden"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def exec_in_container(container_id: str, command: str) -> dict:
    """
    Führt einen Befehl in einem laufenden Container aus.
    
    Args:
        container_id: Container ID oder Name
        command: Auszuführender Befehl
    """
    try:
        client = get_docker()
        container = client.containers.get(container_id)
        
        result = container.exec_run(command)
        
        return {
            "container": container_id,
            "command": command,
            "exit_code": result.exit_code,
            "output": result.output.decode("utf-8", errors="replace")
        }
    except NotFound:
        return {"error": f"Container '{container_id}' nicht gefunden"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# IMAGE TOOLS
# ============================================================================

@mcp.tool
def list_images() -> list[dict]:
    """
    Listet alle Docker Images auf dem Remote-Host.
    
    Returns:
        Liste der Images
    """
    try:
        client = get_docker()
        images = []
        
        for image in client.images.list():
            tags = image.tags if image.tags else ["<none>"]
            images.append({
                "id": image.short_id,
                "tags": tags,
                "size_mb": round(image.attrs.get("Size", 0) / (1024**2), 2),
                "created": str(image.attrs.get("Created", ""))
            })
        
        return images
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool
def pull_image(image: str, tag: str = "latest") -> dict:
    """
    Lädt ein Docker Image herunter.
    
    Args:
        image: Image-Name (z.B. "nginx", "python")
        tag: Image-Tag (default: "latest")
    """
    try:
        client = get_docker()
        full_name = f"{image}:{tag}"
        
        result = client.images.pull(image, tag=tag)
        
        return {
            "success": True,
            "image": full_name,
            "id": result.short_id,
            "message": f"Image '{full_name}' erfolgreich geladen"
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def run_container(
    image: str,
    name: str = None,
    command: str = None,
    detach: bool = True,
    ports: dict = None,
    environment: dict = None,
    volumes: dict = None
) -> dict:
    """
    Erstellt und startet einen neuen Container.
    
    Args:
        image: Image-Name
        name: Container-Name (optional)
        command: Startbefehl (optional)
        detach: Im Hintergrund laufen (default: True)
        ports: Port-Mapping (z.B. {"80/tcp": 8080})
        environment: Umgebungsvariablen
        volumes: Volume-Mapping
    """
    try:
        client = get_docker()
        
        kwargs = {
            "image": image,
            "detach": detach,
        }
        
        if name:
            kwargs["name"] = name
        if command:
            kwargs["command"] = command
        if ports:
            kwargs["ports"] = ports
        if environment:
            kwargs["environment"] = environment
        if volumes:
            kwargs["volumes"] = volumes
            
        container = client.containers.run(**kwargs)
        
        return {
            "success": True,
            "id": container.short_id if hasattr(container, 'short_id') else "unknown",
            "name": container.name if hasattr(container, 'name') else name,
            "message": f"Container aus '{image}' gestartet"
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def remove_container(container_id: str, force: bool = False) -> dict:
    """
    Entfernt einen Container.
    
    Args:
        container_id: Container ID oder Name
        force: Auch laufende Container entfernen
    """
    try:
        client = get_docker()
        container = client.containers.get(container_id)
        container.remove(force=force)
        return {"success": True, "message": f"Container '{container_id}' entfernt"}
    except NotFound:
        return {"error": f"Container '{container_id}' nicht gefunden"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# VOLUME & NETWORK TOOLS
# ============================================================================

@mcp.tool
def list_volumes() -> list[dict]:
    """Listet alle Docker Volumes."""
    try:
        client = get_docker()
        volumes = []
        
        for volume in client.volumes.list():
            volumes.append({
                "name": volume.name,
                "driver": volume.attrs.get("Driver", "local"),
                "mountpoint": volume.attrs.get("Mountpoint", ""),
                "created": str(volume.attrs.get("CreatedAt", ""))
            })
        
        return volumes
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool
def list_networks() -> list[dict]:
    """Listet alle Docker Networks."""
    try:
        client = get_docker()
        networks = []
        
        for network in client.networks.list():
            networks.append({
                "id": network.short_id,
                "name": network.name,
                "driver": network.attrs.get("Driver", ""),
                "scope": network.attrs.get("Scope", ""),
                "containers": len(network.attrs.get("Containers", {}))
            })
        
        return networks
    except Exception as e:
        return [{"error": str(e)}]


# ============================================================================
# RESOURCE
# ============================================================================

@mcp.resource("docker://remote/status")
def docker_status() -> str:
    """Aktueller Status des Remote Docker Hosts."""
    try:
        info = docker_info()
        return json.dumps(info, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
