"""
Docker MCP Server

Ein MCP-Server für Docker-Operationen.
Verwaltet Container, Images, Volumes und Networks.
"""

from fastmcp import FastMCP
import docker
from docker.errors import DockerException, NotFound, APIError
from typing import Optional
import json

mcp = FastMCP("docker-server")

# Docker Client
_docker_client: Optional[docker.DockerClient] = None


def get_docker() -> docker.DockerClient:
    """Holt oder erstellt den Docker Client."""
    global _docker_client
    if _docker_client is None:
        try:
            _docker_client = docker.from_env()
        except DockerException as e:
            raise RuntimeError(f"Docker nicht verfügbar: {e}")
    return _docker_client


# ============================================================================
# CONTAINER TOOLS
# ============================================================================

@mcp.tool
def list_containers(all: bool = False) -> list[dict]:
    """
    Listet Docker Container.
    
    Args:
        all: Auch gestoppte Container anzeigen (default: False)
    
    Returns:
        Liste der Container
    """
    try:
        client = get_docker()
        containers = []
        
        for container in client.containers.list(all=all):
            containers.append({
                "id": container.short_id,
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else container.image.short_id,
                "status": container.status,
                "created": container.attrs["Created"],
                "ports": container.ports,
            })
        
        return containers
    except DockerException as e:
        return [{"error": f"Docker-Fehler: {str(e)}"}]


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
        
        return {
            "id": container.id,
            "short_id": container.short_id,
            "name": container.name,
            "image": container.image.tags[0] if container.image.tags else container.image.short_id,
            "status": container.status,
            "created": container.attrs["Created"],
            "started_at": container.attrs["State"].get("StartedAt"),
            "ports": container.ports,
            "env": container.attrs["Config"].get("Env", []),
            "command": container.attrs["Config"].get("Cmd"),
            "mounts": [
                {
                    "source": m.get("Source"),
                    "destination": m.get("Destination"),
                    "mode": m.get("Mode"),
                }
                for m in container.attrs.get("Mounts", [])
            ],
            "networks": list(container.attrs["NetworkSettings"]["Networks"].keys()),
        }
    except NotFound:
        return {"error": f"Container '{container_id}' nicht gefunden"}
    except DockerException as e:
        return {"error": f"Docker-Fehler: {str(e)}"}


@mcp.tool
def start_container(container_id: str) -> dict:
    """
    Startet einen Container.
    
    Args:
        container_id: Container ID oder Name
    
    Returns:
        Status
    """
    try:
        client = get_docker()
        container = client.containers.get(container_id)
        container.start()
        return {"success": True, "message": f"Container '{container_id}' gestartet"}
    except NotFound:
        return {"error": f"Container '{container_id}' nicht gefunden"}
    except DockerException as e:
        return {"error": f"Docker-Fehler: {str(e)}"}


@mcp.tool
def stop_container(container_id: str, timeout: int = 10) -> dict:
    """
    Stoppt einen Container.
    
    Args:
        container_id: Container ID oder Name
        timeout: Timeout in Sekunden (default: 10)
    
    Returns:
        Status
    """
    try:
        client = get_docker()
        container = client.containers.get(container_id)
        container.stop(timeout=timeout)
        return {"success": True, "message": f"Container '{container_id}' gestoppt"}
    except NotFound:
        return {"error": f"Container '{container_id}' nicht gefunden"}
    except DockerException as e:
        return {"error": f"Docker-Fehler: {str(e)}"}


@mcp.tool
def restart_container(container_id: str, timeout: int = 10) -> dict:
    """
    Startet einen Container neu.
    
    Args:
        container_id: Container ID oder Name
        timeout: Timeout in Sekunden (default: 10)
    
    Returns:
        Status
    """
    try:
        client = get_docker()
        container = client.containers.get(container_id)
        container.restart(timeout=timeout)
        return {"success": True, "message": f"Container '{container_id}' neu gestartet"}
    except NotFound:
        return {"error": f"Container '{container_id}' nicht gefunden"}
    except DockerException as e:
        return {"error": f"Docker-Fehler: {str(e)}"}


@mcp.tool
def get_container_logs(
    container_id: str, 
    tail: int = 100,
    timestamps: bool = False
) -> dict:
    """
    Holt Logs eines Containers.
    
    Args:
        container_id: Container ID oder Name
        tail: Anzahl Zeilen vom Ende (default: 100)
        timestamps: Zeitstempel anzeigen (default: False)
    
    Returns:
        Container-Logs
    """
    try:
        client = get_docker()
        container = client.containers.get(container_id)
        logs = container.logs(tail=tail, timestamps=timestamps).decode("utf-8")
        
        return {
            "container": container_id,
            "logs": logs,
            "lines": len(logs.splitlines()),
        }
    except NotFound:
        return {"error": f"Container '{container_id}' nicht gefunden"}
    except DockerException as e:
        return {"error": f"Docker-Fehler: {str(e)}"}


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
        image: Image-Name (z.B. "nginx:latest")
        name: Container-Name (optional)
        command: Befehl zum Ausführen (optional)
        detach: Im Hintergrund ausführen (default: True)
        ports: Port-Mappings (z.B. {"80/tcp": 8080})
        environment: Umgebungsvariablen (z.B. {"KEY": "value"})
        volumes: Volume-Mappings (z.B. {"/host/path": {"bind": "/container/path", "mode": "rw"}})
    
    Returns:
        Container-Info
    """
    try:
        client = get_docker()
        container = client.containers.run(
            image,
            command=command,
            name=name,
            detach=detach,
            ports=ports,
            environment=environment,
            volumes=volumes,
        )
        
        return {
            "success": True,
            "id": container.short_id,
            "name": container.name,
            "status": container.status,
        }
    except DockerException as e:
        return {"error": f"Docker-Fehler: {str(e)}"}


@mcp.tool
def remove_container(container_id: str, force: bool = False) -> dict:
    """
    Entfernt einen Container.
    
    Args:
        container_id: Container ID oder Name
        force: Erzwingen (auch laufende Container)
    
    Returns:
        Status
    """
    try:
        client = get_docker()
        container = client.containers.get(container_id)
        container.remove(force=force)
        return {"success": True, "message": f"Container '{container_id}' entfernt"}
    except NotFound:
        return {"error": f"Container '{container_id}' nicht gefunden"}
    except DockerException as e:
        return {"error": f"Docker-Fehler: {str(e)}"}


@mcp.tool
def exec_in_container(container_id: str, command: str) -> dict:
    """
    Führt einen Befehl in einem laufenden Container aus.
    
    Args:
        container_id: Container ID oder Name
        command: Befehl zum Ausführen
    
    Returns:
        Befehlsausgabe
    """
    try:
        client = get_docker()
        container = client.containers.get(container_id)
        result = container.exec_run(command)
        
        return {
            "exit_code": result.exit_code,
            "output": result.output.decode("utf-8") if result.output else "",
        }
    except NotFound:
        return {"error": f"Container '{container_id}' nicht gefunden"}
    except DockerException as e:
        return {"error": f"Docker-Fehler: {str(e)}"}


# ============================================================================
# IMAGE TOOLS
# ============================================================================

@mcp.tool
def list_images() -> list[dict]:
    """
    Listet alle Docker Images.
    
    Returns:
        Liste der Images
    """
    try:
        client = get_docker()
        images = []
        
        for image in client.images.list():
            images.append({
                "id": image.short_id,
                "tags": image.tags,
                "size": f"{image.attrs['Size'] / (1024*1024):.1f} MB",
                "created": image.attrs["Created"],
            })
        
        return images
    except DockerException as e:
        return [{"error": f"Docker-Fehler: {str(e)}"}]


@mcp.tool
def pull_image(image_name: str, tag: str = "latest") -> dict:
    """
    Lädt ein Docker Image herunter.
    
    Args:
        image_name: Image-Name (z.B. "nginx")
        tag: Tag (default: "latest")
    
    Returns:
        Status
    """
    try:
        client = get_docker()
        image = client.images.pull(image_name, tag=tag)
        
        return {
            "success": True,
            "image": f"{image_name}:{tag}",
            "id": image.short_id,
        }
    except DockerException as e:
        return {"error": f"Docker-Fehler: {str(e)}"}


@mcp.tool
def remove_image(image_id: str, force: bool = False) -> dict:
    """
    Entfernt ein Docker Image.
    
    Args:
        image_id: Image ID oder Name
        force: Erzwingen
    
    Returns:
        Status
    """
    try:
        client = get_docker()
        client.images.remove(image_id, force=force)
        return {"success": True, "message": f"Image '{image_id}' entfernt"}
    except NotFound:
        return {"error": f"Image '{image_id}' nicht gefunden"}
    except DockerException as e:
        return {"error": f"Docker-Fehler: {str(e)}"}


# ============================================================================
# VOLUME TOOLS
# ============================================================================

@mcp.tool
def list_volumes() -> list[dict]:
    """
    Listet alle Docker Volumes.
    
    Returns:
        Liste der Volumes
    """
    try:
        client = get_docker()
        volumes = []
        
        for volume in client.volumes.list():
            volumes.append({
                "name": volume.name,
                "driver": volume.attrs["Driver"],
                "mountpoint": volume.attrs["Mountpoint"],
                "created": volume.attrs["CreatedAt"],
            })
        
        return volumes
    except DockerException as e:
        return [{"error": f"Docker-Fehler: {str(e)}"}]


@mcp.tool
def create_volume(name: str, driver: str = "local") -> dict:
    """
    Erstellt ein Docker Volume.
    
    Args:
        name: Volume-Name
        driver: Volume-Driver (default: "local")
    
    Returns:
        Volume-Info
    """
    try:
        client = get_docker()
        volume = client.volumes.create(name=name, driver=driver)
        
        return {
            "success": True,
            "name": volume.name,
            "driver": volume.attrs["Driver"],
        }
    except DockerException as e:
        return {"error": f"Docker-Fehler: {str(e)}"}


# ============================================================================
# NETWORK TOOLS
# ============================================================================

@mcp.tool
def list_networks() -> list[dict]:
    """
    Listet alle Docker Networks.
    
    Returns:
        Liste der Networks
    """
    try:
        client = get_docker()
        networks = []
        
        for network in client.networks.list():
            networks.append({
                "id": network.short_id,
                "name": network.name,
                "driver": network.attrs["Driver"],
                "scope": network.attrs["Scope"],
            })
        
        return networks
    except DockerException as e:
        return [{"error": f"Docker-Fehler: {str(e)}"}]


# ============================================================================
# SYSTEM TOOLS
# ============================================================================

@mcp.tool
def docker_info() -> dict:
    """
    Holt Docker System-Informationen.
    
    Returns:
        System-Info
    """
    try:
        client = get_docker()
        info = client.info()
        
        return {
            "containers": info["Containers"],
            "containers_running": info["ContainersRunning"],
            "containers_paused": info["ContainersPaused"],
            "containers_stopped": info["ContainersStopped"],
            "images": info["Images"],
            "server_version": info["ServerVersion"],
            "os": info["OperatingSystem"],
            "architecture": info["Architecture"],
            "cpus": info["NCPU"],
            "memory": f"{info['MemTotal'] / (1024**3):.1f} GB",
        }
    except DockerException as e:
        return {"error": f"Docker-Fehler: {str(e)}"}


@mcp.tool
def docker_disk_usage() -> dict:
    """
    Zeigt Docker Disk Usage.
    
    Returns:
        Disk Usage Info
    """
    try:
        client = get_docker()
        df = client.df()
        
        return {
            "images": {
                "count": len(df.get("Images", [])),
                "size": sum(i.get("Size", 0) for i in df.get("Images", [])) / (1024**3),
            },
            "containers": {
                "count": len(df.get("Containers", [])),
                "size": sum(c.get("SizeRw", 0) for c in df.get("Containers", [])) / (1024**3),
            },
            "volumes": {
                "count": len(df.get("Volumes", [])),
                "size": sum(v.get("UsageData", {}).get("Size", 0) for v in df.get("Volumes", [])) / (1024**3),
            },
        }
    except DockerException as e:
        return {"error": f"Docker-Fehler: {str(e)}"}


# ============================================================================
# RESOURCES
# ============================================================================

@mcp.resource("docker://info")
def get_docker_info() -> str:
    """Docker System-Informationen"""
    return json.dumps(docker_info(), indent=2)


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
