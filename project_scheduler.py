import streamlit as st
from langchain_community.llms import HuggingFacePipeline
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
import matplotlib.pyplot as plt
from transformers import pipeline

# -----------------------
# Example Task Dictionary
# -----------------------
tasks = {
    "T1": {"name": "Design", "duration": 5, "dependencies": []},
    "T2": {"name": "Procurement", "duration": 7, "dependencies": ["T1"]},
    "T3": {"name": "Implementation", "duration": 10, "dependencies": ["T2"]},
    "T4": {"name": "Testing", "duration": 4, "dependencies": ["T3"]},
}

# -----------------------
# Tools
# -----------------------
def build_schedule(_):
    return tasks

build_schedule_tool = Tool(
    name="BuildSchedule",
    description="Builds a project schedule and returns tasks with durations and dependencies.",
    func=lambda _: build_schedule(None),
)

def delay_task_str(query: str):
    try:
        tid, d = query.split(",")
        tid = tid.strip()
        d = int(d.strip())
        tasks[tid]["duration"] += d
        return f"Task {tid} delayed by {d} days. Updated duration: {tasks[tid]['duration']}"
    except Exception as e:
        return f"Error: {str(e)}. Use format 'T2,3'."

delay_task_tool = Tool(
    name="DelayTask",
    description="Delay a task by providing 'task_id,days' (e.g. 'T2,3').",
    func=delay_task_str,
)

def optimize_schedule(_):
    for t in tasks.values():
        t["duration"] = max(1, t["duration"] - 1)
    return tasks

optimize_tool = Tool(
    name="OptimizeSchedule",
    description="Optimize schedule by reducing duration of each task (simulation).",
    func=lambda _: optimize_schedule(None),
)

# -----------------------
# Local HuggingFace LLM
# -----------------------
pipe = pipeline("text-generation", model="distilbert-base-uncased", max_new_tokens=50)
llm = HuggingFacePipeline(pipeline=pipe)

# -----------------------
# LangChain Agent
# -----------------------
agent = initialize_agent(
    tools=[build_schedule_tool, delay_task_tool, optimize_tool],
    llm=llm,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)

# -----------------------
# Streamlit UI
# -----------------------
st.title("📊 Agentic AI Project Scheduler (Offline Mode)")

query = st.text_input("Ask me (e.g., 'Build schedule', 'Delay T2 by 3 days', 'Optimize schedule'):")

if st.button("Run Agent"):
    if query:
        response = agent.run(query)
        st.write("### 🤖 Agent Response")
        st.write(response)

        # Draw Gantt chart
        fig, ax = plt.subplots()
        yticks, labels = [], []
        start = 0
        for i, (tid, t) in enumerate(tasks.items()):
            ax.barh(i, t["duration"], left=start)
            yticks.append(i)
            labels.append(tid + " - " + t["name"])
            start += t["duration"]
        ax.set_yticks(yticks)
        ax.set_yticklabels(labels)
        ax.set_xlabel("Days")
        ax.set_title("Gantt Chart (Simulated)")
        st.pyplot(fig)
    else:
        st.warning("Please enter a query.")
