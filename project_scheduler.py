# streamlit_app_interactive.py

import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Interactive Project Scheduling with AI Auto-Rescheduling")

st.markdown("""
Adjust task start times manually and see how dependent tasks and resource allocation are updated automatically.
""")

# -----------------------------
# Step 1: Load Project & Resources
# -----------------------------
@st.cache_data
def load_project():
    tasks = pd.DataFrame({
        "Task": ["Foundation", "Framing", "Plumbing", "Electrical", "Finishing"],
        "Duration": [5, 10, 7, 6, 8],
        "Predecessor": [None, "Foundation", "Framing", "Framing", "Plumbing"],
        "Workers_Required": [5, 8, 4, 3, 6],
        "Start": [0, 0, 0, 0, 0]  # editable column
    })
    resources = pd.DataFrame({
        "Worker": [f"Worker_{i+1}" for i in range(15)],
        "Available": [True]*15
    })
    return tasks, resources

tasks, resources = load_project()

st.subheader("Edit Task Start Times (Simulates Drag-and-Drop)")
edited_tasks = st.data_editor(
    tasks,
    column_config={
        "Task": st.column_config.TextColumn("Task", disabled=True),
        "Duration": st.column_config.NumberColumn("Duration", disabled=True),
        "Predecessor": st.column_config.TextColumn("Predecessor", disabled=True),
        "Workers_Required": st.column_config.NumberColumn("Workers Required", disabled=True),
        "Start": st.column_config.NumberColumn("Start", min_value=0)
    },
    use_container_width=True
)

# -----------------------------
# Step 2: Auto-Reschedule Dependent Tasks
# -----------------------------
def auto_reschedule(df, total_workers):
    schedule = df.copy()
    recovery_actions = []
    # Compute actual start based on predecessor and resource availability
    for idx, row in schedule.iterrows():
        pred = row["Predecessor"]
        # Ensure task starts after predecessor ends
        if pred:
            pred_end = schedule.loc[schedule["Task"]==pred, "Start"].values[0] + \
                       schedule.loc[schedule["Task"]==pred, "Duration"].values[0]
            if schedule.at[idx, "Start"] < pred_end:
                schedule.at[idx, "Start"] = pred_end
        # Check worker availability
        if row["Workers_Required"] > total_workers:
            schedule.at[idx, "Start"] += 1  # simple delay
            recovery_actions.append({
                "Task": row["Task"],
                "Action": f"Overtime / hire backup ({row['Workers_Required']} needed)"
            })
        # Compute end
        schedule.at[idx, "End"] = schedule.at[idx, "Start"] + row["Duration"]
    total_duration = schedule["End"].max()
    return schedule, recovery_actions, total_duration

available_workers = resources["Available"].sum()
schedule, recovery_actions, total_duration = auto_reschedule(edited_tasks, available_workers)

# -----------------------------
# Step 3: Visualize Schedule
# -----------------------------
st.subheader("Updated Gantt Chart")
fig = px.timeline(schedule, x_start="Start", x_end="End", y="Task", color="Task")
fig.update_yaxes(autorange="reversed")
st.plotly_chart(fig)

st.subheader("Resource Utilization")
st.bar_chart([available_workers, resources.shape[0] - available_workers], use_container_width=True)

st.subheader("Recovery / Overtime Suggestions")
if recovery_actions:
    st.table(pd.DataFrame(recovery_actions))
else:
    st.write("No extra resources needed.")

st.subheader("Predicted Total Project Duration")
st.write(f"**{total_duration} days**")
