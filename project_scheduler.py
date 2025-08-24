import streamlit as st
import networkx as nx
import plotly.figure_factory as ff

# -------------------------------
# 1. Define Project Plan
# -------------------------------
tasks = {
    "T1": {"name": "Design", "duration": 5, "dependencies": []},
    "T2": {"name": "Procurement", "duration": 7, "dependencies": ["T1"]},
    "T3": {"name": "Assembly", "duration": 10, "dependencies": ["T2"]},
    "T4": {"name": "Testing", "duration": 6, "dependencies": ["T3"]},
}

# -------------------------------
# 2. Build Schedule
# -------------------------------
def build_schedule(tasks):
    G = nx.DiGraph()
    for t, data in tasks.items():
        G.add_node(t, **data)
    for t, data in tasks.items():
        for dep in data["dependencies"]:
            G.add_edge(dep, t)

    schedule = {}
    for t in nx.topological_sort(G):
        start = 0
        for dep in tasks[t]["dependencies"]:
            start = max(start, schedule[dep]["finish"])
        finish = start + tasks[t]["duration"]
        schedule[t] = {
            "id": t,
            "name": tasks[t]["name"],
            "start": start,
            "finish": finish
        }
    return schedule

# -------------------------------
# 3. Convert to Gantt Data
# -------------------------------
def schedule_to_gantt(schedule):
    data = []
    for s in schedule.values():
        data.append(dict(
            Task=s["name"],
            Start=f"2025-01-01 {s['start']:02}:00:00",
            Finish=f"2025-01-01 {s['finish']:02}:00:00"
        ))
    return data

# -------------------------------
# 4. Streamlit UI
# -------------------------------
st.set_page_config(page_title="AI Project Scheduler", layout="wide")
st.title("🤖 Agentic AI Project Scheduler & Optimizer")

# Baseline
baseline = build_schedule(tasks)
st.subheader("📌 Baseline Schedule")
fig1 = ff.create_gantt(schedule_to_gantt(baseline), index_col='Task', show_colorbar=True, group_tasks=True)
st.plotly_chart(fig1, use_container_width=True)

# Disruption Simulation
if st.button("⚠️ Simulate Delay in Procurement (T2)"):
    tasks["T2"]["duration"] += 3  # inject delay
    updated = build_schedule(tasks)

    st.subheader("🚧 Updated Schedule After Delay")
    fig2 = ff.create_gantt(schedule_to_gantt(updated), index_col='Task', show_colorbar=True, group_tasks=True)
    st.plotly_chart(fig2, use_container_width=True)

    st.success(f"Task T2 delayed by 3 days. New project finish = Day {updated['T4']['finish']}")
