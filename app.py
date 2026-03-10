import streamlit as st
import data.database as db
from datetime import date
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import datetime

# Initialize database
db.init_db()

st.title("Hobby Tracker")

# -------------------
# Sidebar Navigation
# -------------------

page = st.sidebar.radio(
    "Navigation",
    ["Add Hobby", "Log Activity", "View Hobby Activity", "Statistics", "Tasks"]
)

# -------------------
# Add Hobby Page
# -------------------

if page == "Add Hobby":
    st.header("Add a New Hobby")
    name = st.text_input("Hobby name")
    if st.button("Add"):
        db.add_hobby(name)
        st.success("Hobby added successfully!")
    st.subheader("Existing Hobbies")
    hobbies = db.get_hobbies()
    for h in hobbies:
        st.write(h[1])

# -------------------
# Log Activity Page
# -------------------

elif page == "Log Activity":
    st.header("Log Your Activity")
    hobbies = db.get_hobbies()
    if hobbies:
        hobby_dict = {name: id for id, name in hobbies}
        with st.form("entry_form"):
            hobby_name = st.selectbox("Choose Hobby", list(hobby_dict.keys()))
            minutes = st.number_input("Minutes spent", min_value=0, max_value=1000)
            notes = st.text_area("Activity Notes")
            points = st.number_input("Points earned", min_value=0, max_value=100)
            entry_date = st.date_input("Date", value=date.today())
            submitted = st.form_submit_button("Save Activity")
            if submitted:
                hobby_id = hobby_dict[hobby_name]
                db.add_entry(
                    hobby_id,
                    str(entry_date),
                    minutes,
                    notes,
                    points
                )
                st.success("Activity saved!")
    else:
        st.warning("Please add a hobby first.")

# -------------------
# View Hobby Activity Page
# -------------------

elif page == "View Hobby Activity":
    st.header("View Activity by Hobby")
    hobbies = db.get_hobbies()
    if hobbies:
        hobby_dict = {name: id for id, name in hobbies}
        hobby_name = st.selectbox("Select Hobby", list(hobby_dict.keys()))
        hobby_id = hobby_dict[hobby_name]
        entries = db.get_entries_for_hobby(hobby_id)
        if entries:
            for entry in entries:
                st.write(f"📅 {entry[2]} | ⏱ {entry[3]} minutes | ⭐ {entry[5]}")
                st.write(f"Notes: {entry[4]}")
                st.divider()
        else:
            st.info("No activities logged yet.")
    else:
        st.warning("No hobbies available. Please add a hobby first.")

# -------------------
# Statistics Page
# -------------------

elif page == "Statistics":
    st.header("Statistics Dashboard")
    df_hobby = db.get_total_minutes_per_hobby()
    if not df_hobby.empty:
        st.subheader("Total Minutes per Hobby")
        st.bar_chart(df_hobby.set_index('hobby')['total_minutes'])
    else:
        st.info("No activity data yet.")

    df_daily = db.get_daily_minutes()
    if not df_daily.empty:
        st.subheader("Daily Total Minutes")
        st.line_chart(df_daily.set_index('date')['total_minutes'])

    df_points = db.get_points_over_time()
    if not df_points.empty:
        st.subheader("Points Over Time")
        st.line_chart(df_points.set_index('date')['total_points'])

    total_minutes = df_daily['total_minutes'].sum() if not df_daily.empty else 0
    total_points = df_points['total_points'].sum() if not df_points.empty else 0
    total_hobbies = len(df_hobby) if not df_hobby.empty else 0

    st.subheader("Summary Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Minutes", total_minutes)
    col2.metric("Total Points", total_points)
    col3.metric("Tracked Hobbies", total_hobbies)

    if not df_daily.empty:
        df_daily['date'] = pd.to_datetime(df_daily['date'])
        df_daily.set_index('date', inplace=True)
        today = datetime.date.today()
        start = today - pd.Timedelta(days=30)
        all_days = pd.date_range(start, today)
        df_full = pd.DataFrame(index=all_days)
        df_full['minutes'] = df_daily['total_minutes']
        df_full['minutes'] = df_full['minutes'].fillna(0)
        df_full['weekday'] = df_full.index.weekday
        df_full['week_of_month'] = ((df_full.index.day - 1) // 7) + 1
        heatmap_data = df_full.pivot_table(
            index='week_of_month',
            columns='weekday',
            values='minutes',
            aggfunc='sum',
            fill_value=0
        )
        plt.figure(figsize=(12, 4))
        sns.heatmap(
            heatmap_data,
            cmap="YlGn",
            linewidths=0.5,
            linecolor="gray",
            cbar_kws={'label': 'Minutes'}
        )
        plt.title("Daily Activity Heatmap (Last 30 Days)")
        st.pyplot(plt)

# -------------------
# Tasks & Subtasks Page (robust)
# -------------------
elif page == "Tasks":
    st.header("Tasks & Subtasks")

    hobbies = db.get_hobbies()
    if not hobbies:
        st.warning("Please add a hobby first.")
    else:
        hobby_dict = {name: id for id, name in hobbies}
        hobby_name = st.selectbox("Select Hobby", list(hobby_dict.keys()))
        hobby_id = hobby_dict[hobby_name]

        # Initialize session state
        if "tasks_data" not in st.session_state:
            st.session_state["tasks_data"] = {}

        if hobby_id not in st.session_state["tasks_data"]:
            tasks = db.get_tasks(hobby_id)
            # store in session dict keyed by task id
            st.session_state["tasks_data"][hobby_id] = {
                t[0]: {"task": t, "subtasks": db.get_subtasks(t[0])} for t in tasks
            }

        # ---- Add New Task ----
        st.subheader("Add Task")
        task_name = st.text_input("Task name", key="new_task_name")
        task_points = st.number_input("Points", min_value=0, max_value=100, key="new_task_points")
        task_minutes = st.number_input("Estimated minutes", min_value=0, max_value=1000, key="new_task_minutes")
        if st.button("Add Task", key="add_task_btn"):
            db.add_task(hobby_id, task_name, task_minutes, task_points)
            # reload tasks and put new task at top
            tasks = db.get_tasks(hobby_id)
            st.session_state["tasks_data"][hobby_id] = {
                t[0]: {"task": t, "subtasks": db.get_subtasks(t[0])} for t in tasks
            }
            st.success("Task added!")

        # ---- Show Existing Tasks ----
        st.subheader("Existing Tasks")
        tasks_dict = st.session_state["tasks_data"][hobby_id]
        # Sort tasks newest first
        for t_id in sorted(tasks_dict.keys(), reverse=True):
            t_data = tasks_dict[t_id]
            t = t_data["task"]
            subtasks = t_data["subtasks"]

            # Total minutes (sum of subtasks if any)
            total_minutes = sum(stsk[4] for stsk in subtasks) if subtasks else t[4]
            done_status = "✓" if t[3] else ""

            with st.expander(f"{done_status} {t[2]} (Estimated: {total_minutes} min)"):
                # Edit task minutes if no subtasks and not done
                if not subtasks and not t[3]:
                    new_minutes = st.number_input(
                        "Edit estimated minutes",
                        min_value=0,
                        max_value=1000,
                        value=t[4],
                        key=f"edit_task_{t[0]}"
                    )
                    t_data["task"] = t[:4] + (new_minutes,) + t[5:]

                # Mark task done
                if not t[3] and st.button(f"Mark Task '{t[2]}' Done", key=f"task_done_{t[0]}"):
                    db.mark_task_done(t[0], is_subtask=False)
                    t_data["task"] = t[:3] + (True,) + t[4:]
                    # log activity if needed
                    st.success("Task marked done and activity logged!")

                # Subtasks display
                for stsk in subtasks:
                    st_done = "✓" if stsk[3] else ""
                    cols = st.columns([3,1])
                    cols[0].write(f"{st_done} {stsk[2]} (Estimated: {stsk[4]} min)")
                    if not stsk[3]:
                        new_st_minutes = cols[0].number_input(
                            "Edit minutes",
                            min_value=0,
                            max_value=1000,
                            value=stsk[4],
                            key=f"edit_sub_{stsk[0]}"
                        )
                        stsk = stsk[:4] + (new_st_minutes,) + stsk[5:]
                    if not stsk[3] and cols[1].button("Done", key=f"subtask_done_{stsk[0]}"):
                        db.mark_task_done(stsk[0], is_subtask=True)
                        # update session state immediately
                        stsk = stsk[:3] + (True,) + stsk[4:]
                        st.success("Subtask marked done and activity logged!")

                # Add subtask only if task not done
                if not t[3]:
                    new_subtask_name = st.text_input("New Subtask Name", key=f"newsub_{t[0]}")
                    new_subtask_minutes = st.number_input("Minutes", min_value=0, max_value=1000, key=f"sub_min_{t[0]}")
                    new_subtask_points = st.number_input("Points", min_value=0, max_value=100, key=f"sub_pts_{t[0]}")
                    if st.button("Add Subtask", key=f"addsub_{t[0]}"):
                        db.add_subtask(t[0], new_subtask_name, new_subtask_minutes, new_subtask_points)
                        # reload subtasks
                        st.session_state["tasks_data"][hobby_id][t[0]]["subtasks"] = db.get_subtasks(t[0])
                        st.success("Subtask added!")