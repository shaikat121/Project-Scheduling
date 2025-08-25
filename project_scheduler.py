# streamlit_app_free.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.title("Autonomous Project Scheduling & Resource Optimization (Free Version)")

st.markdown("Demo of project scheduling with automatic rescheduling and resource optimization without extra libraries.")

# -----------------------------
# Step 1: Define Example Project
# -----------------------------
@st.cache_data
def load_project():
    tasks = pd.DataFrame({
        "Task": ["Foundation", "Framing", "Plumbing", "Electrical", "Finishing"],
        "Duration": [5, 10, 7, 6, 8],
        "Predecessor": [None, "Foundation", "Framing", "Framing", "Plumbing"],
        "Workers_Required": [5, 8, 4, 3, 6]
    })
    resources = pd.DataFrame({
        "Worker": [f"Worker_{i+1}" for i in range(15)],
        "Available": [True]*15
    })
    return tasks, resources

tasks, resources = load_project()
st.subheader("Project Tasks")
st.dataframe(tasks)

st.subheader("Resources")
st.dataframe(resources)

# -----------------------------
# Step 2: Disruption Simulation
# -----------------------------
st.subheader("Disruption Simulation")
worker_unavailable = st.slider("Number of workers unavailable", 0, 5, 2)

# Mark first N workers unavailable
resources.loc[:worker_unavailable-1, "Available"] = False
available_workers = resources["Available"].sum()
st.write(f"Available Workers after disruption: {available_workers}")

# -----------------------------
# Step 3: Simple Scheduling Algorithm
# -----------------------------
def simple_schedule(tasks, available_workers):
    schedule = []
    task_start = {}
    for idx, row in tasks.iterrows():
        pred = row["Predecessor"]
        start = 0
        if pred and pred in task_start:
            start = task_start[pred] + tasks.loc[tasks["Task"]==pred, "Duration"].values[0]
        # Check if enough workers
        if row["Workers_Required"] > available_workers:
            start += 1  # delay by 1 day for simplicity
        task_start[row["Task"]] = start
        schedule.append({"Task": row["Task"], "Start": start, "End": start + row["Duration"]})
    return pd.DataFrame(schedule)

schedule = simple_schedule(tasks, available_workers)

# -----------------------------
# Step 4: Visualization
# -----------------------------
st.subheader("Updated Gantt Chart After Disruption")
fig = px.timeline(schedule, x_start="Start", x_end="End", y="Task", color="Task")
fig.update_yaxes(autorange="reversed")
st.plotly_chart(fig)

st.subheader("Resource Utilization")
st.bar_chart([available_workers, resources.shape[0] - available_workers])
