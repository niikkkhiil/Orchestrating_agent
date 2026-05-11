from crewai import Agent
from crew.tools import (
    list_containers,
    detect_failed_containers,
    get_container_logs,
    restart_container,
    search_memory_tool,
    save_memory_tool
)

def get_monitor_agent(llm):
    return Agent(
        role = "Infrastructure Monitor",
        goal= "Detect any Docker container that are failling or have stopped unexpectedly",
        backstory = """You are an Expert Infrastructure Monitoring specialist, with years of experience watching over containerized systems You are vigilant, precise, 
        and always the first to spot when something goes wrong.""",
        tools = [list_containers, detect_failed_containers],
        llm=llm,
        verbose = True
    )
def get_analyzer_agent(llm):
    return Agent(
        role = "Failure Analyzer",
        goal = "Analyze the container logs to determine the root cause of failure and recommend fixes",
        backstory = """" You are a senior DevOps engineer specializing in diagnosing 
        containerized application failures. You read logs carefully, identify patterns, 
        and always provide clear cause and fix recommendations.""",
        tools = [get_container_logs],
        llm=llm,
        verbose = True
    )

def get_executor_agent(llm):
    return Agent(
        role = "Infrastructure Executor",
        goal = "Apply fixes to failed Docker containers based on the analyst's recommendations",
        backstory = """You are a reliable infrastructure engineer responsible for applying 
        fixes to production systems. You act on clear instructions, restart containers, 
        and confirm every action you take.""",
        tools = [restart_container],
        llm=llm,
        verbose = True
    )


def get_monitor_agent(llm):
    return Agent(
        role="Infrastructure Monitor",
        goal="Detect Docker containers that have failed or stopped unexpectedly",
        backstory="""You are an expert infrastructure monitoring specialist. 
        You use the DetectFailedContainers tool to find failed containers 
        and report exactly what you find.""",
        tools=[detect_failed_containers],
        llm=llm,
        verbose=True
    )


def get_analyzer_agent(llm):
    return Agent(
        role="Failure Analyst",
        goal="""Analyze container failures efficiently. Always check memory first 
        before doing full log analysis. If memory has a known fix, use it directly.""",
        backstory="""You are a senior DevOps engineer specializing in diagnosing 
        containerized application failures. You always check incident memory 
        first — why reinvent the wheel? You save new findings to memory.""",
        tools=[get_container_logs, search_memory_tool, save_memory_tool],
        llm=llm,
        verbose=True
    )


def get_executor_agent(llm):
    return Agent(
        role="Infrastructure Executor",
        goal="Apply fixes to failed Docker containers based on analyst recommendations",
        backstory="""You are a reliable infrastructure engineer responsible for 
        applying fixes to production systems. You restart containers and confirm 
        every action you take.""",
        tools=[restart_container],
        llm=llm,
        verbose=True
    )