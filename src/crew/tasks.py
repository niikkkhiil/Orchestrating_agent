from crewai import Task
from crew.agents import get_monitor_agent, get_analyzer_agent, get_executor_agent

def get_monitor_task(agent):
    return Task(
        description = """Scan all running and stopped Docker containers on this system. Identify any container that have status of 'exited' or 'dead', Return a clear list of failed containers with their name, status and ID.
        If all containers are healthy, report that clearly.""",
        expected_output=""" A list of failed containers in this format:
        - Container Name: <name> | Status: <status> | ID: <id>
        Or: 'All containers are healthy.' if none are failing.""",
        agent=agent
    )

def get_analyzer_task(agent, context):
    return Task(
        description="""
        For each failed container identified by the monitor:
        1. Search memory using SearchMemory tool with the container name
        2. If MEMORY HIT — use the known fix directly
        3. If NO MEMORY HIT:
           - Fetch logs using GetContainerLogs
           - Analyze root cause
           - Save to memory using SaveToMemory: 'container_name|||diagnosis|||fix'
        """,
        expected_output="""
        For each failed container:
        - Container: <name>
        - Source: MEMORY or LLM ANALYSIS
        - Cause: <cause>
        - Fix: <fix>
        """,
        agent=agent,
        context=context
    )


def get_executor_task(agent, context):
    return Task(
        description="""
        Based on the analyst's recommendations:
        1. Restart each failed container
        2. Confirm whether the restart was successful
        3. Report the final status of each container
        """,
        expected_output="""
        For each container actioned:
        - Container: <name>
        - Action taken: <restart/skip>
        - Result: <success/failed>
        - Final status: <running/still failing>
        """,
        agent=agent,
        context=context
    )

