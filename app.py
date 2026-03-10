import streamlit as st
import data.database as db
from datetime import date
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import datetime

# Initialize database
db.init_db()

# Basic theming / styling
st.set_page_config(page_title="Hobby Tracker", page_icon="🎯", layout="wide")

st.markdown(
    """
    <style>
    /* Import playful handwritten + clean body fonts */
    @import url('https://fonts.googleapis.com/css2?family=Caveat:wght@500;600&family=Nunito:wght@400;600;700&display=swap');

    /* Apply background to full Streamlit app with layered, subtle orange theme */
    .stApp {
        background:
            radial-gradient(circle at 12% 0%, rgba(254, 215, 170, 0.9) 0, rgba(254, 249, 195, 0.0) 55%),
            radial-gradient(circle at 90% 8%, rgba(254, 226, 226, 0.85) 0, rgba(254, 226, 226, 0.0) 55%),
            linear-gradient(180deg, #fffaf3 0%, #fde7c7 45%, #fed7aa 80%, #fef3c7 100%) !important;
        color: #1f2933;
        font-family: 'Caveat', 'Nunito', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    }
    /* Ensure main content container is transparent so gradient shows through */
    [data-testid="stAppViewContainer"],
    [data-testid="stVerticalBlock"] {
        background-color: transparent !important;
    }

    /* Global headers use handwritten font (override Streamlit defaults) */
    h1, h2, h3,
    .block-container h1,
    .block-container h2,
    .block-container h3,
    [data-testid="stHeader"] h1 {
        font-family: 'Caveat', 'Nunito', system-ui, sans-serif !important;
        color: #7c2d12 !important;
    }

    /* Handwritten-style main title and section titles */
    .hobby-title {
        font-family: 'Caveat', 'Nunito', system-ui, sans-serif;
        font-size: 3rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: none;
        color: #7c2d12;
        margin-bottom: 0.3rem;
    }
    .hobby-subtitle-main {
        font-family: 'Caveat', 'Nunito', system-ui, sans-serif;
        font-size: 1.7rem;
        color: #7c2d12;
        opacity: 0.95;
        margin-bottom: 1.6rem;
    }
    .section-card {
        padding: 0;
        border-radius: 0;
        background: transparent;
        border: none;
        box-shadow: none;
        margin-bottom: 0.8rem;
    }
    .section-title {
        font-family: 'Caveat', 'Nunito', system-ui, sans-serif;
        font-weight: 600;
        font-size: 1.7rem;
        color: #7c2d12;
        margin-bottom: 0.4rem;
    }
    .stats-title {
        font-family: 'Caveat', 'Nunito', system-ui, sans-serif;
        font-weight: 600;
        font-size: 2rem;
        margin: 0.8rem 0 0.4rem 0;
        color: #7c2d12;
    }

    /* Enlarge tab labels like "Overview", "By Hobby", etc. */
    .stTabs button[role="tab"] {
        font-family: 'Caveat', 'Nunito', system-ui, sans-serif !important;
        font-size: 1.2rem !important;
    }
    .hobby-pill {
        display: inline-flex;
        align-items: center;
        padding: 0.45rem 0.9rem;
        margin: 0.18rem 0.3rem 0.18rem 0;
        border-radius: 999px;
        background: linear-gradient(135deg, rgba(15,23,42,0.9), rgba(30,64,175,0.9));
        border: 1px solid rgba(251,191,36,0.85);
        font-size: 1.3rem;
        color: #fefce8;
        font-family: 'Caveat', 'Nunito', system-ui, sans-serif;
    }
    .hobby-pill-label {
        margin-right: 0.5rem;
    }
    .hobby-pill-delete button {
        background: transparent !important;
        color: #fecaca !important;
        font-family: 'Caveat', 'Nunito', system-ui, sans-serif;
    }

    /* Tree-view checkbox: handwriting label + blue tick */
    .task-tree-toggle label {
        font-family: 'Caveat', 'Nunito', system-ui, sans-serif !important;
        font-size: 1.15rem !important;
        color: #7c2d12 !important;
    }
    .task-tree-toggle input[type="checkbox"] {
        accent-color: #3b82f6 !important;
    }

    /* Task tree styling */
    .task-tree {
        font-family: 'Caveat', 'Nunito', system-ui, sans-serif;
        font-size: 1.05rem;
        padding-left: 0.4rem;
    }
    .task-tree-item {
        margin: 0.1rem 0;
    }
    .task-tree-task {
        color: #7c2d12;
        font-weight: 600;
    }
    .task-tree-sub-active {
        color: #1f2933;
    }
    .task-tree-sub-done {
        color: #15803d;
        text-decoration: line-through;
        opacity: 0.9;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

hero_left, hero_right = st.columns([2, 1])
with hero_left:
    st.markdown('<div class="hobby-title">Hobby Tracker</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hobby-subtitle-main">Track your passions, daily wins, and long‑term progress with color and clarity.</div>',
        unsafe_allow_html=True,
    )
with hero_right:
    st.image(
        "https://images.pexels.com/photos/102127/pexels-photo-102127.jpeg?auto=compress&cs=tinysrgb&w=800",
        width=260,
    )

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
    st.header("🎨 Add a New Hobby")
    name = st.text_input("Hobby name")
    if st.button("Add"):
        trimmed = name.strip()
        hobbies_existing = db.get_hobbies()
        existing_names = {h[1].strip().lower() for h in hobbies_existing}
        if not trimmed:
            st.warning("Please enter a hobby name.")
        elif trimmed.lower() in existing_names:
            st.error("This hobby already exists.")
        else:
            db.add_hobby(trimmed)
            st.success("Hobby added successfully!")
    st.subheader("Existing Hobbies")
    hobbies = db.get_hobbies()
    if not hobbies:
        st.info("No hobbies yet. Add your first one above!")
    else:
        cols = st.columns(2)
        for idx, (h_id, h_name) in enumerate(hobbies):
            col = cols[idx % 2]
            with col:
                st.markdown(
                    f'<span class="hobby-pill"><span class="hobby-pill-label">🏷️ {h_name}</span></span>',
                    unsafe_allow_html=True,
                )
                remove_key = f"remove_hobby_{h_id}"
                if st.button("Remove", key=remove_key):
                    db.delete_hobby(h_id)
                    st.success(f"Hobby '{h_name}' removed (with its tasks and entries).")
                    st.rerun()

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
    # Standalone colored title without card background
    st.markdown('<div class="stats-title">📊 Statistics Dashboard</div>', unsafe_allow_html=True)

    df_hobby = db.get_total_minutes_per_hobby()
    df_daily = db.get_daily_minutes()
    df_points = db.get_points_over_time()
    df_by_hobby = db.get_daily_minutes_by_hobby()
    df_tasks = db.get_task_completion_stats()
    df_hobby_points = db.get_hobby_points_and_minutes()
    df_weekly = db.get_weekly_minutes_by_hobby()

    total_minutes = df_daily["total_minutes"].sum() if not df_daily.empty else 0
    total_points = df_points["total_points"].sum() if not df_points.empty else 0
    total_hobbies = len(df_hobby) if not df_hobby.empty else 0

    # ---- Overview cards ----
    with st.container():
        col1, col2, col3 = st.columns(3)
        col1.metric("⏱ Total Minutes", int(total_minutes))
        col2.metric("⭐ Total Points", int(total_points))
        col3.metric("🎯 Tracked Hobbies", int(total_hobbies))

    tabs = st.tabs(["Overview", "By Hobby", "Trends & Heatmap", "Weekly Hours", "Tasks & Completion"])

    # ---- Overview tab ----
    with tabs[0]:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🏆 Total Minutes per Hobby</div>', unsafe_allow_html=True)
        if not df_hobby.empty:
            st.bar_chart(df_hobby.set_index("hobby")["total_minutes"])
        else:
            st.info("No activity data yet.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎯 Points per Hobby</div>', unsafe_allow_html=True)
        if df_hobby_points is not None and not df_hobby_points.empty:
            st.bar_chart(df_hobby_points.set_index("hobby")["total_points"])
        else:
            st.info("No points logged yet.")
        st.markdown("</div>", unsafe_allow_html=True)

        if not df_points.empty:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">💹 Points Over Time (All Hobbies)</div>', unsafe_allow_html=True)
            st.line_chart(df_points.set_index("date")["total_points"])
            st.markdown("</div>", unsafe_allow_html=True)

    # ---- By Hobby tab ----
    with tabs[1]:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📈 Minutes per Hobby Over Time</div>', unsafe_allow_html=True)
        if not df_by_hobby.empty:
            df_by_hobby_plot = df_by_hobby.copy()
            df_by_hobby_plot["date"] = pd.to_datetime(df_by_hobby_plot["date"])
            pivot = df_by_hobby_plot.pivot_table(
                index="date", columns="hobby", values="total_minutes", aggfunc="sum"
            ).fillna(0)
            st.line_chart(pivot)
        else:
            st.info("No activity data yet to show per-hobby trends.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Points efficiency scale per hobby
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">⭐ Points Scale per Hobby</div>', unsafe_allow_html=True)
        if df_hobby_points is not None and not df_hobby_points.empty:
            df_scale = df_hobby_points.copy()
            df_scale["points_per_hour"] = df_scale["points_per_hour"].round(2)
            st.dataframe(
                df_scale.rename(
                    columns={
                        "hobby": "Hobby",
                        "total_minutes": "Total Minutes",
                        "total_points": "Total Points",
                        "points_per_hour": "Points per Hour",
                    }
                ),
                use_container_width=True,
            )
        else:
            st.info("No data yet to compute a points scale per hobby.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ---- Trends & Heatmap tab ----
    with tabs[2]:
        if not df_daily.empty:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">📅 Daily Total Minutes</div>', unsafe_allow_html=True)
            df_trend = df_daily.copy()
            df_trend["date"] = pd.to_datetime(df_trend["date"])
            df_trend.sort_values("date", inplace=True)
            df_trend.set_index("date", inplace=True)
            st.area_chart(df_trend["total_minutes"])
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">🔥 Activity Heatmap (Last 30 Days)</div>', unsafe_allow_html=True)
            df_daily_heat = df_daily.copy()
            df_daily_heat["date"] = pd.to_datetime(df_daily_heat["date"])
            df_daily_heat.set_index("date", inplace=True)
            today = datetime.date.today()
            start = today - pd.Timedelta(days=30)
            all_days = pd.date_range(start, today)
            df_full = pd.DataFrame(index=all_days)
            df_full["minutes"] = df_daily_heat["total_minutes"]
            df_full["minutes"] = df_full["minutes"].fillna(0)
            df_full["weekday"] = df_full.index.weekday
            df_full["week_of_month"] = ((df_full.index.day - 1) // 7) + 1
            heatmap_data = df_full.pivot_table(
                index="week_of_month",
                columns="weekday",
                values="minutes",
                aggfunc="sum",
                fill_value=0,
            )
            plt.figure(figsize=(12, 4))
            sns.heatmap(
                heatmap_data,
                cmap="YlGn",
                linewidths=0.5,
                linecolor="gray",
                cbar_kws={"label": "Minutes"},
            )
            plt.title("Daily Activity Heatmap (Last 30 Days)")
            st.pyplot(plt)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No daily activity data yet.")

    # ---- Weekly Hours tab ----
    with tabs[3]:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📆 Weekly Hours per Hobby</div>', unsafe_allow_html=True)
        if df_weekly is not None and not df_weekly.empty:
            df_week = df_weekly.copy()
            df_week["hours"] = (df_week["total_minutes"] / 60.0).round(2)
            pivot_week = df_week.pivot_table(
                index="year_week", columns="hobby", values="hours", aggfunc="sum"
            ).fillna(0)
            st.line_chart(pivot_week)
        else:
            st.info("No data yet to calculate weekly hours per hobby.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ---- Tasks & Completion tab ----
    with tabs[4]:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">✅ Task Completion by Hobby</div>', unsafe_allow_html=True)
        if not df_tasks.empty:
            df_display = df_tasks.copy()
            df_display["completion_rate"] = (df_display["completion_rate"] * 100).round(1)
            st.dataframe(
                df_display.rename(
                    columns={
                        "hobby": "Hobby",
                        "total_tasks": "Total Tasks",
                        "completed_tasks": "Completed Tasks",
                        "completion_rate": "Completion %",
                    }
                ),
                use_container_width=True,
            )
        else:
            st.info("No tasks yet to calculate completion statistics.")
        st.markdown("</div>", unsafe_allow_html=True)

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

        # Generate concrete tasks from recurring templates for this hobby
        db.ensure_recurring_tasks_for_today(hobby_id)

        # Layout: regular vs recurring tasks side by side
        col_tasks, col_recurring = st.columns(2)

        # ---- Add New One-Off Task ----
        with col_tasks:
            st.subheader("One-off Task")
            task_name = st.text_input("Task name", key="new_task_name")
            task_points = st.number_input("Points", min_value=0, max_value=100, key="new_task_points")
            task_minutes = st.number_input("Estimated minutes", min_value=0, max_value=1000, key="new_task_minutes")
            if st.button("Add Task", key="add_task_btn"):
                db.add_task(hobby_id, task_name, task_minutes, task_points)
                st.success("Task added!")
                st.rerun()

        # ---- Add New Recurring Task ----
        with col_recurring:
            st.subheader("Recurring Task")
            r_name = st.text_input("Recurring task name", key="rec_task_name")
            r_points = st.number_input("Points", min_value=0, max_value=100, key="rec_task_points")
            r_minutes = st.number_input("Estimated minutes", min_value=0, max_value=1000, key="rec_task_minutes")
            frequency = st.selectbox("Frequency", ["Daily", "Weekly"], key="rec_task_frequency")
            if st.button("Add Recurring Task", key="add_rec_task_btn"):
                if r_name:
                    db.add_recurring_task(
                        hobby_id,
                        r_name,
                        r_minutes,
                        r_points,
                        frequency.lower(),
                    )
                    st.success(f"Recurring task ({frequency.lower()}) added!")
                else:
                    st.warning("Please provide a name for the recurring task.")

        # ---- Show Existing Tasks ----
        st.subheader("Existing Tasks")
        tasks = db.get_tasks(hobby_id)

        # Determine up to 10 most recent completed task ids (if any)
        done_tasks = [t for t in tasks if t[3]]
        recent_done_ids = {
            t[0] for t in sorted(done_tasks, key=lambda x: x[0], reverse=True)[:10]
        }

        # Sort tasks newest first and display:
        # - all not-done tasks
        # - up to 10 most recent done tasks
        for t in sorted(tasks, key=lambda x: x[0], reverse=True):
            t_id = t[0]
            is_done = bool(t[3])

            if is_done and t_id not in recent_done_ids:
                # Skip older completed tasks beyond the latest 10
                continue

            subtasks = db.get_subtasks(t_id)

            # Total minutes (sum of subtasks if any)
            total_minutes = sum(stsk[4] for stsk in subtasks) if subtasks else t[4]
            # Original checkmark indicator when done
            done_status = "✅" if is_done else "⬜"

            with st.expander(f"{done_status} {t[2]} • {total_minutes} min • {t[5]} pts"):
                # Mark task done
                if not is_done and st.button(f"Mark Task '{t[2]}' Done", key=f"task_done_{t_id}"):
                    db.mark_task_done(t_id, is_subtask=False)
                    st.success("Task marked done and activity logged!")
                    st.rerun()

                # Subtasks display
                for stsk in subtasks:
                    st_done = "✅" if stsk[3] else "⬜"
                    cols = st.columns([3, 1])
                    cols[0].write(f"{st_done} {stsk[2]} (Estimated: {stsk[4]} min, {stsk[5]} pts)")

                    if not stsk[3] and cols[1].button("Done", key=f"subtask_done_{stsk[0]}"):
                        db.mark_task_done(stsk[0], is_subtask=True)
                        st.success("Subtask marked done and activity logged!")
                        st.rerun()

                # Add subtask only if task not done
                if not is_done:
                    new_subtask_name = st.text_input("New Subtask Name", key=f"newsub_{t_id}")
                    new_subtask_minutes = st.number_input(
                        "Minutes", min_value=0, max_value=1000, key=f"sub_min_{t_id}"
                    )
                    new_subtask_points = st.number_input(
                        "Points", min_value=0, max_value=100, key=f"sub_pts_{t_id}"
                    )
                    if st.button("Add Subtask", key=f"addsub_{t_id}"):
                        db.add_subtask(t_id, new_subtask_name, new_subtask_minutes, new_subtask_points)
                        st.success("Subtask added!")
                        st.rerun()

        # ---- Active tasks tree overview ----
        st.subheader("Active Tasks Overview")
        if tasks:
            st.markdown('<div class="task-tree-toggle">', unsafe_allow_html=True)
            show_tree = st.checkbox("Show tasks and subtasks in a tree view", value=True, key="tree_view_toggle")
            st.markdown("</div>", unsafe_allow_html=True)
            if show_tree:
                tree_html = ['<div class="task-tree">']
                for t in sorted(tasks, key=lambda x: x[0]):
                    if t[3]:  # skip fully completed tasks
                        continue
                    t_minutes = t[4]
                    t_points = t[5]
                    tree_html.append(
                        f'<div class="task-tree-item task-tree-task">📌 {t[2]} '
                        f'({t_minutes} min, {t_points} pts)</div>'
                    )
                    subtasks = db.get_subtasks(t[0])
                    if subtasks:
                        tree_html.append('<div class="task-tree-item">')
                        for stsk in subtasks:
                            sub_minutes = stsk[4]
                            sub_points = stsk[5]
                            if stsk[3]:
                                klass = "task-tree-sub-done"
                                icon = "✅"
                            else:
                                klass = "task-tree-sub-active"
                                icon = "🟠"
                            tree_html.append(
                                f'<div class="{klass}" style="margin-left:1.4rem;">'
                                f'{icon} {stsk[2]} ({sub_minutes} min, {sub_points} pts)'
                                f'</div>'
                            )
                        tree_html.append("</div>")
                tree_html.append("</div>")
                if len(tree_html) > 2:
                    st.markdown("\n".join(tree_html), unsafe_allow_html=True)
                else:
                    st.info("No active tasks or subtasks for this hobby.")
        else:
            st.info("No tasks yet for this hobby.")