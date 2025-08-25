import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict
from pydantic import BaseModel, Field

from langchain_ollama import OllamaLLM
from langchain.agents import initialize_agent, AgentType
from langchain.tools import StructuredTool

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
# Tool 1: Build Schedule
# -------------------------------
def build_schedule(tasks: Dict) -> Dict:
    schedule = {}
    for t, data in tasks.items():
        start = 0
        for dep in data["dependencies"]:
            start = max(start, schedule[dep]["finish"])
        finish = start + data["duration"]
        schedule[t] = {"name": data["name"], "start": start, "finish": finish}
    return schedule

build_schedule_tool = StructuredTool.from_function(
    func=build_schedule,
    name="BuildSchedule",
    description="Build project schedule from tasks and dependencies",
)

# -------------------------------
# Tool 2: Delay Task (Structured)
# -------------------------------
class DelayInput(BaseModel):
    task_id: str = Field(..., description="Task ID to delay, e.g. 'T2'")
    delay: int = Field(..., description="Number of days to delay")

def delay_task(input_data: DelayInput) -> Dict:
    """Delays a given task by X days."""
    tid = input_data.task_id
    d = input_data.delay
    tasks[tid]["duration"] += d
    return tasks

delay_task_tool = StructuredTool(
    name="DelayTask",
    description="Delay a given task by X days. Inputs: task_id (str), delay (int).",
    func=delay_task,
    args_schema=DelayInput,
)

# -------------------------------
# Tool 3: Optimize Schedule
# -------------------------------
def optimize_schedule(tasks: Dict) -> Dict:
    for t, data in tasks.items():
        if data["dependencies"]:
            data["duration"] = max(1, data["duration"] - 1)
    return tasks

optimize_tool = StructuredTool.from_function(
    func=optimize_schedule,
    name="OptimizeSchedule",
    description="Optimize schedule by reducing downstream tasks",
)

# -------------------------------
# Local LLM (Ollama)
# -------------------------------
llm = OllamaLLM(model="llama3")

agent = initialize_agent(
    tools=[build_schedule_tool, delay_task_tool, optimize_tool],
    llm=llm,
    agent_type=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,  # ✅ FIXED
    verbose=True,
)

# -------------------------------
# Streamlit Dashboard
# -------------------------------
st.set_page_config(page_title="Agentic AI Project Scheduler", layout="wide")
st.title("🤖 Agentic AI Project Scheduler with Gantt Chart")
st.write("Built using **Streamlit + LangChain + Ollama + Plotly**")

# Helper: Gantt Chart
def show_gantt(schedule):
    df = pd.DataFrame([
        {"Task": v["name"], "Start": v["start"], "Finish": v["finish"]}
        for v in schedule.values()
    ])
    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Task")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

# Session State
if "schedule" not in st.session_state:
    st.session_state.schedule = {}

# -------------------------------
# Actions via Buttons
# -------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📌 Build Schedule"):
        st.session_state.schedule = build_schedule(tasks)
        show_gantt(st.session_state.schedule)

with col2:
    task = st.selectbox("Select task to delay", list(tasks.keys()))
    delay = st.slider("Delay (days)", 1, 7, 2)
    if st.button("⚠️ Delay Task"):
        updated = delay_task(DelayInput(task_id=task, delay=delay))
        st.session_state.schedule = build_schedule(updated)
        show_gantt(st.session_state.schedule)

with col3:
    if st.button("✅ Optimize"):
        optimized = optimize_schedule(tasks)
        st.session_state.schedule = build_schedule(optimized)
        show_gantt(st.session_state.schedule)

# -------------------------------
# Natural Language Agent Input
# -------------------------------
st.subheader("💬 Natural Language Agent")
user_query = st.text_input("Ask me (e.g. 'Delay Procurement by 3 days and optimize'):")

if st.button("Run Agent"):
    if user_query:
        response = agent.run(user_query)
        st.write("🧠 Agent Response:", response)
        st.session_state.schedule = build_schedule(tasks)
        show_gantt(st.session_state.schedule)
