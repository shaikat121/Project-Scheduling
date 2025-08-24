import streamlit as st
import pandas as pd
import plotly.express as px
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent
from langchain.tools import tool

# -------------------------------
# Demo Project Plan
# -------------------------------
tasks = {
    "T1": {"name": "Design", "duration": 5, "dependencies": []},
    "T2": {"name": "Procurement", "duration": 7, "dependencies": ["T1"]},
    "T3": {"name": "Assembly", "duration": 10, "dependencies": ["T2"]},
    "T4": {"name": "Testing", "duration": 6, "dependencies": ["T3"]},
}

# -------------------------------
# LangChain Tools
# -------------------------------
@tool
def build_schedule_tool(tasks: dict) -> dict:
    """Builds project schedule with dependencies."""
    schedule = {}
    for t, data in tasks.items():
        start = 0
        for dep in data["dependencies"]:
            start = max(start, schedule[dep]["finish"])
        finish = start + data["duration"]
        schedule[t] = {"name": data["name"], "start": start, "finish": finish}
    return schedule

@tool
def detect_disruption_tool(tasks: dict, task_id: str, delay: int) -> str:
    """Adds delay to a task and reports impact."""
    tasks[task_id]["duration"] += delay
    return f"?? Task {task_id} delayed by {delay} days"

@tool
def reallocate_resources_tool(tasks: dict, delayed_task: str) -> dict:
    """Naive optimization: reduce duration of dependent tasks by 1 day."""
    for t, data in tasks.items():
        if delayed_task in data["dependencies"]:
            data["duration"] = max(1, data["duration"] - 1)
    return tasks

# -------------------------------
# Agents
# -------------------------------
llm = ChatOpenAI(model="gpt-4o-mini")

planner = initialize_agent([build_schedule_tool], llm, agent_type="openai-functions", verbose=True)
monitor = initialize_agent([detect_disruption_tool], llm, agent_type="openai-functions", verbose=True)
optimizer = initialize_agent([reallocate_resources_tool], llm, agent_type="openai-functions", verbose=True)

# -------------------------------
# Helpers for Gantt Chart
# -------------------------------
def make_gantt(schedule: dict, title="Project Schedule"):
    """Convert schedule dict to Gantt chart"""
    df = pd.DataFrame([
        {"Task": data["name"], "Start": data["start"], "Finish": data["finish"]}
        for _, data in schedule.items()
    ])
    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", title=title, color="Task")
    fig.update_yaxes(autorange="reversed")  # tasks from top to bottom
    st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("?? Agentic AI for Project Scheduling")
st.write("Multi-Agent Workflow: Planner ? Monitor ? Optimizer")

# Session state to persist changes
if "schedule" not in st.session_state:
    st.session_state.schedule = {}

# 1. Build Baseline
if st.button("?? Build Baseline Schedule"):
    baseline = planner.run(f"Build schedule for tasks: {tasks}")
    st.session_state.schedule = eval(baseline) if isinstance(baseline, str) else baseline
    st.success("Baseline Schedule Generated ?")
    st.json(st.session_state.schedule)
    make_gantt(st.session_state.schedule, title="Baseline Schedule")

# 2. Simulate Disruption
task_to_delay = st.selectbox("Select task to delay", list(tasks.keys()))
delay_days = st.slider("Delay in days", 1, 10, 3)

if st.button("?? Simulate Disruption"):
    alert = monitor.run(f"Delay task {task_to_delay} by {delay_days} days in tasks: {tasks}")
    st.warning(alert)
    baseline = planner.run(f"Recompute schedule for tasks: {tasks}")
    st.session_state.schedule = eval(baseline) if isinstance(baseline, str) else baseline
    st.json(st.session_state.schedule)
    make_gantt(st.session_state.schedule, title="Schedule After Disruption")

# 3. Optimize Schedule
if st.button("? Optimize Schedule"):
    optimized = optimizer.run(f"Optimize tasks after delay in {task_to_delay}: {tasks}")
    st.session_state.schedule = eval(optimized) if isinstance(optimized, str) else optimized
    st.success("Optimized Schedule ?")
    st.json(st.session_state.schedule)
    make_gantt(st.session_state.schedule, title="Optimized Schedule")
