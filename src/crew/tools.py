import docker
from crewai.tools import tool

client = docker.from_env()


@tool("ListContainers")
def list_containers(input: str = "") -> str:
    """Lists all Docker containers and their current status."""
    containers = client.containers.list(all=True)
    if not containers:
        return "No containers found."
    result = []
    for c in containers:
        result.append(f"Name: {c.name} | Status: {c.status} | ID: {c.short_id}")
    return "\n".join(result)


@tool("DetectFailedContainers")
def detect_failed_containers(input: str = "") -> str:
    """Detects Docker containers that have stopped unexpectedly (status: exited or dead)."""
    containers = client.containers.list(all=True)
    issues = []
    for c in containers:
        if c.status in ["exited", "dead"]:
            issues.append(f"Name: {c.name} | Status: {c.status} | ID: {c.short_id}")

    
    if not issues:
        return "All containers are healthy."
    return "\n".join(issues)


@tool("GetContainerLogs")
def get_container_logs(container_name: str) -> str:
    """Fetches the last 50 lines of logs from a Docker container by name or ID."""
    try:
        if isinstance(container_name, dict):
            container_name = container_name.get("container_name", "")

        container_name = str(container_name).strip()

        # trying exact match first
        try:
            container = client.containers.get(container_name)
        except Exception:
            # fallback — search by partial ID or name
            all_containers = client.containers.list(all=True)
            container = next(
                (c for c in all_containers
                 if c.short_id in container_name or c.name in container_name),
                None
            )
            if not container:
                return f"Container not found: {container_name}"

        logs = container.logs(tail=50).decode("utf-8")
        return logs if logs else "No logs available."
    except Exception as e:
        return f"Error retrieving logs: {e}"


@tool("RestartContainer")
def restart_container(container_name: str) -> str:
    """Restarts a Docker container by name or ID."""
    try:
        if isinstance(container_name, dict):
            container_name = container_name.get("container_name", "")

        container_name = str(container_name).strip()

        try:
            container = client.containers.get(container_name)
        except Exception:
            all_containers = client.containers.list(all=True)
            container = next(
                (c for c in all_containers
                 if c.short_id in container_name or c.name in container_name),
                None
            )
            if not container:
                return f"Container not found: {container_name}"

        container.restart()
        return f"Successfully restarted: {container.name}"
    except Exception as e:
        return f"Failed to restart {container_name}: {e}"
    

@tool("MemorySearch")
def search_memory_tool(container_name: str) -> str:
    """Search past incidents by container name. Input: just the container name string."""
    try:
        from crew.memory import search_memory
        result = search_memory(container_name.strip(), "")
        if result:
            return f"MEMORY HIT: {result['fix']}"
        return "NO MEMORY HIT: analyze logs manually."
    except Exception as e:
        return f"Error: {e}"


@tool("MemorySave")
def save_memory_tool(container_name: str) -> str:
    """Save container incident to memory. Input: 'name|||diagnosis|||fix'"""
    try:
        parts = container_name.split("|||")
        if len(parts) < 3:
            return "Error: need name|||diagnosis|||fix"
        from crew.memory import save_to_memory
        save_to_memory(
            container_name=parts[0].strip(),
            logs="",
            diagnosis=parts[1].strip(),
            fix=parts[2].strip()
        )
        return f"Saved: {parts[0].strip()}"
    except Exception as e:
        return f"Error: {e}"
    

@tool("AnalyzeErrorType")
def analyze_error_type(container_name: str) -> str:
    """Analyze container logs and return the specify error type and recommand action on it."""

    try:
        if isinstance(container_name, dict):
            container_name = container_name.get("container_name", "")

        container_name = str(container_name).strip()

        try:
            container = client.containers.get(container_name)
        
        except Exception:
            all_containers = client.containers.list(all=True)

            container = next(
                (c for c in all_containers
                 if c.short_id in container_name or c.name in container_name),
                None
            )
            if not container:
                return f"Container not found: {container_name}"
            
            logs = container.logs(tail=50).decode("utf-8")
            attrs = container.attrs
            exit_code = attrs.get('State', {}).get('ExitCode', "-1")
            oom_killed = attrs.get('State', {}).get('OOMKilled', False)

            if oom_killed or exit_code == 137 or "killed" in logs:
                return "ERROR_TYPE: OOM_KILLED | ACTION: increase_memory | SEVERITY: high"

            elif "address already in use" in logs or "port" in logs and "bind" in logs:
                return "ERROR_TYPE: PORT_CONFLICT | ACTION: free_port | SEVERITY: medium"

            elif exit_code == 0:
                return "ERROR_TYPE: CLEAN_EXIT | ACTION: restart | SEVERITY: low"

            elif exit_code == 1 and any(x in logs for x in ["env", "config", "missing", "keyerror"]):
                return "ERROR_TYPE: CONFIG_ERROR | ACTION: check_env_vars | SEVERITY: high"

            elif exit_code == 1:
                return "ERROR_TYPE: APP_CRASH | ACTION: restart_and_alert | SEVERITY: high"

            elif "no space left" in logs:
                return "ERROR_TYPE: DISK_FULL | ACTION: prune_docker | SEVERITY: critical"

            elif "connection refused" in logs or "could not connect" in logs:
                return "ERROR_TYPE: NETWORK_ERROR | ACTION: restart_with_delay | SEVERITY: medium"

        else:
            return f"ERROR_TYPE: UNKNOWN | EXIT_CODE: {exit_code} | ACTION: restart_and_alert | SEVERITY: medium"

    except Exception as e:
        return f"Error analyzing container: {e}"
            
@tool("SmartFix")
def smart_fix(input: str) -> str:
    """Apply the right fix based on error type. Input: 'container_name|||error_type'"""

    try:           