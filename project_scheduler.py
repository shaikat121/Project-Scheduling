import streamlit as st
import pandas as pd
import plotly.express as px
from langchain_ollama import OllamaLLM
from langchain.agents import initialize_agent
from langchain.tools import tool

# -------------------------------
# Dummy Task Data
# -------------------------------
tasks = {
    "T1": {"name": "Design", "duration": 5, "dependencies": []},
    "T2": {"name": "Procurement", "duration": 7, "dependencies": ["T1"]},
    "T3": {"name": "Assembly", "duration": 10, "dependencies": ["T2"]},
    "T4": {"name": "Testing", "duration": 6, "dependencies": ["T3"]},
}

# -------------------------------
# Tools (Agents� actions)
# -------------------------------
@tool
def build_schedule_tool(tasks: dict) -> dict:
    """Builds project schedule based on dependencies."""
    schedule = {}
    for t, data in tasks.items():
        start = 0
        for dep in data["dependencies"]:
            start = max(start, schedule[dep]["finish"])
        finish = start + data["duration"]
        schedule[t] = {"name": data["name"], "start": start, "finish": finish}
    return schedule

@tool
def delay_task_tool(tasks: dict, task_id: str, delay: int) -> dict:
    """Delays a task by X days and propagates changes."""
    tasks[task_id]["duration"] += delay
    return tasks

@tool
def optimize_tool(tasks: dict) -> dict:
    """Naive optimization: reduce all non-root task durations by 1 day."""
    for t, data in tasks.items():
        if data["dependencies"]:
            data["duration"] = max(1, data["duration"] - 1)
    return tasks

# -------------------------------
# Local LLM (Ollama)
# -------------------------------
llm = OllamaLLM(model="llama3")

planner = initialize_agent([build_schedule_tool], llm, agent_type="openai-functions", verbose=True)
monitor = initialize_agent([delay_task_tool], llm, agent_type="openai-functions", verbose=True)
optimizer = initialize_agent([optimize_tool], llm, agent_type="openai-functions", verbose=True)

# -------------------------------
# Streamlit Dashboard
# -------------------------------
st.set_page_config(page_title="Agentic AI Project Scheduler", layout="wide")
st.title("?? Agentic AI Project Scheduler with Gantt Chart")
st.write("Built using **Streamlit + LangChain + Ollama + Plotly**")

# Gantt Chart Helper
def show_gantt(schedule):
    df = pd.DataFrame([
        {"Task": v["name"], "Start": v["start"], "Finish": v["finish"]}
        for v in schedule.values()
    ])
    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Task")
    fig.update_yaxes(autorange="reversed")  # Gantt-style
    st.plotly_chart(fig, use_container_width=True)

# State
if "schedule" not in st.session_state:
    st.session_state.schedule = {}

# Actions
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("?? Build Schedule"):
        st.session_state.schedule = build_schedule_tool.invoke(tasks)
        show_gantt(st.session_state.schedule)

with col2:
    task = st.selectbox("Select task to delay", list(tasks.keys()))
    delay = st.slider("Delay (days)", 1, 7, 2)
    if st.button("?? Delay Task"):
        updated = delay_task_tool.invoke(tasks, task_id=task, delay=delay)
        st.session_state.schedule = build_schedule_tool.invoke(updated)
        show_gantt(st.session_state.schedule)

with col3:
    if st.button("? Optimize"):
        optimized = optimize_tool.invoke(tasks)
        st.session_state.schedule = build_schedule_tool.invoke(optimized)
        show_gantt(st.session_state.schedule)
