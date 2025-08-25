# streamlit_app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from ortools.sat.python import cp_model

st.title("Autonomous Project Scheduling & Resource Optimization")

st.markdown("""
This demo simulates project scheduling with automatic rescheduling and resource optimization.
""")

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

# Mark random workers unavailable
resources.loc[:worker_unavailable-1, "Available"] = False

# -----------------------------
# Step 3: Scheduling Optimization using OR-Tools
# -----------------------------
def optimize_schedule(tasks, resources):
    model = cp_model.CpModel()
    task_vars = {}
    horizon = sum(tasks["Duration"]) + 10

    for idx, row in tasks.iterrows():
        task_vars[row["Task"]] = model.NewIntVar(0, horizon, row["Task"])

    # Predecessor constraints
    for idx, row in tasks.iterrows():
        if row["Predecessor"]:
            model.Add(task_vars[row["Task"]] >= task_vars[row["Predecessor"]] + tasks.loc[tasks["Task"]==row["Predecessor"], "Duration"].values[0])

    # Resource constraints
    available_workers = resources[resources["Available"]].shape[0]
    for t in range(horizon):
        tasks_running = []
        for idx, row in tasks.iterrows():
            # Task running indicator
            running = model.NewBoolVar(f"running_{row['Task']}_{t}")
            model.Add(task_vars[row["Task"]] <= t).OnlyEnforceIf(running)
            model.Add(task_vars[row["Task"]] + row["Duration"] > t).OnlyEnforceIf(running)
            tasks_running.append((running, row["Workers_Required"]))
        # Total workers used <= available
        model.Add(sum(running * req for running, req in tasks_running) <= available_workers)

    # Minimize project makespan
    makespan = model.NewIntVar(0, horizon, "makespan")
    model.AddMaxEquality(makespan, [task_vars[t] + tasks.loc[tasks["Task"]==t, "Duration"].values[0] for t in tasks["Task"]])
    model.Minimize(makespan)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        schedule = []
        for t in tasks["Task"]:
            start = solver.Value(task_vars[t])
            end = start + tasks.loc[tasks["Task"]==t, "Duration"].values[0]
            schedule.append({"Task": t, "Start": start, "End": end})
        return pd.DataFrame(schedule)
    else:
        return pd.DataFrame()

schedule = optimize_schedule(tasks, resources)

# -----------------------------
# Step 4: Visualization
# -----------------------------
st.subheader("Updated Gantt Chart After Disruption")
if not schedule.empty:
    fig = px.timeline(schedule, x_start="Start", x_end="End", y="Task", color="Task")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig)

    st.subheader("Resource Utilization")
    st.bar_chart([resources["Available"].sum(), resources.shape[0] - resources["Available"].sum()])
else:
    st.warning("No feasible schedule found with current resource availability.")
