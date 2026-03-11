import streamlit as st
import data.database as db
from datetime import date
import pandas as pd
import datetime
import altair as alt

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

    /* All checkbox labels in handwriting */
    div.stCheckbox label {
        font-family: 'Caveat', 'Nunito', system-ui, sans-serif !important;
        font-size: 1.15rem !important;
        color: #7c2d12 !important;
    }
    /* Only the tree-view checkbox tick in blue */
    div.stCheckbox input[id^="tree_view_toggle"] {
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
        font-family: 'Caveat', cursive, system-ui, sans-serif !important;
        font-size: 1.2rem !important;
    }
    .task-tree-sub-active {
        color: #1f2933;
        font-family: 'Caveat', cursive, system-ui, sans-serif !important;
    }
    .task-tree-sub-done {
        color: #15803d;
        text-decoration: line-through;
        opacity: 0.9;
        font-family: 'Caveat', cursive, system-ui, sans-serif !important;
        animation: subtaskDone 0.4s ease-out;
    }
    @keyframes subtaskDone {
        from { opacity: 0.5; transform: scale(0.98); }
        to { opacity: 0.9; transform: scale(1); }
    }
    .glance-task-done {
        color: #15803d !important;
        text-decoration: line-through;
        font-family: 'Caveat', cursive, system-ui, sans-serif !important;
        animation: taskDone 0.4s ease-out;
    }
    @keyframes taskDone {
        from { opacity: 0.5; transform: scale(0.98); }
        to { opacity: 1; transform: scale(1); }
    }
    .planner-glance-tree {
        margin: 0.2rem 0 0.4rem 0;
        padding-left: 2rem;
        margin-left: 0.5rem;
        border-left: 2px solid rgba(124, 45, 18, 0.25);
        font-size: 1.1rem;
        line-height: 1.35;
        font-family: 'Caveat', cursive, system-ui, sans-serif !important;
    }
    .planner-glance-sub {
        margin: 0.25rem 0;
        font-size: 1.05rem;
        line-height: 1.3;
        font-family: 'Caveat', cursive, system-ui, sans-serif !important;
    }

    /* Weekly planner remove: text link style */
    .planner-delete {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0;
        margin: 0;
    }
    .planner-delete div[data-testid="stButton"],
    .planner-delete div[data-testid="stButton"] > button {
        background: transparent !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        padding: 0.15rem 0.35rem !important;
        margin: 0 !important;
        min-width: auto !important;
        width: auto !important;
        height: auto !important;
        border-radius: 0.25rem !important;
        font-size: 0.8rem !important;
        font-family: 'Caveat', cursive, system-ui, sans-serif !important;
        line-height: 1 !important;
        color: #78716c !important;
        cursor: pointer !important;
    }
    .planner-delete div[data-testid="stButton"] > button:hover {
        color: #dc2626 !important;
        background: rgba(220, 38, 38, 0.08) !important;
    }
    .planner-delete div[data-testid="stButton"] > button:focus {
        box-shadow: none !important;
        outline: none !important;
    }

    /* Weekly planner minutes input */
    input[id^="planner_minutes_"] {
        width: 6.5rem !important;
        min-width: 6.5rem !important;
        font-size: 1.05rem !important;
        padding: 0.2rem 0.4rem !important;
        height: 2.1rem !important;
        box-sizing: border-box !important;
        background-color: #ffffff !important;
        color: #111827 !important;
        border: 1px solid #9ca3af !important;
        border-radius: 0.4rem !important;
    }

   .planner-task-label {
    font-family: 'Caveat', cursive;
    font-size: 18px;
    line-height: 1.4;
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 0;
    }
    /* Glance row: keep delete and minutes compact */
    .planner-delete { flex-shrink: 0 !important; }
    button[data-testid="stPopoverTriggerButton"] { min-width: 2rem !important; max-width: 2.5rem !important; padding: 0.2rem 0.25rem !important; font-size: 0.9rem !important; }
    
    .planner-trash {
    text-decoration: none;
    font-size: 18px;
    color: #444;
    cursor: pointer;
    }

    .planner-trash:hover {
        color: #cc0000;
    }

    /* Hide default checkbox box for weekly planner tasks, keep label clickable */
    input[id^="planner_task_"] {
        opacity: 0;
        width: 0;
        margin: 0;
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

# Persist current page in URL so refresh returns to same page
nav_options = ["Add Hobby", "Statistics", "Weekly Planner"]
current_page = st.query_params.get("page", nav_options[0])
if current_page not in nav_options:
    current_page = nav_options[0]
page_idx = nav_options.index(current_page)
page = st.sidebar.radio("Navigation", nav_options, index=page_idx, key="sidebar_nav")
if page != current_page:
    st.query_params["page"] = page
    st.rerun()

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
                    st.query_params["page"] = "Add Hobby"
                    st.rerun()

# -------------------
# Statistics Page (completed + estimated per hobby, this week)
# -------------------

elif page == "Statistics":
    st.markdown('<div class="stats-title">📊 Statistics</div>', unsafe_allow_html=True)

    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=(today.weekday() + 1) % 7)
    week_end = week_start + datetime.timedelta(days=6)

    st.markdown(
        f'<div class="section-title">✅ Completed vs Estimated Tasks per Hobby (Week of {week_start.strftime("%d %b")} – {week_end.strftime("%d %b")})</div>',
        unsafe_allow_html=True,
    )
    df_tasks = db.get_completed_and_estimated_tasks_per_hobby_for_week(
        week_start.isoformat(), week_end.isoformat()
    )
    if df_tasks is not None and not df_tasks.empty:
        df_long = df_tasks.melt(
            id_vars=["hobby"],
            value_vars=["completed_count", "estimated_count"],
            var_name="series",
            value_name="count",
        )
        df_long["series"] = df_long["series"].replace(
            {"completed_count": "Completed", "estimated_count": "Estimated"}
        )
        try:
            chart = (
                alt.Chart(df_long, width=600, height=280)
                .mark_bar(size=28)
                .encode(
                    x=alt.X("hobby:N", title="Hobby", sort="-y"),
                    y=alt.Y("count:Q", title="Count"),
                    xOffset="series:N",
                    color=alt.Color("series:N", title="", scale=alt.Scale(range=["#7c3aed", "#0ea5e9"])),
                )
            )
        except (AttributeError, TypeError):
            chart = (
                alt.Chart(df_long, width=280, height=280)
                .mark_bar(size=32)
                .encode(
                    x=alt.X("hobby:N", title="Hobby", sort="-y"),
                    y=alt.Y("count:Q", title="Count"),
                    color=alt.Color("series:N", title="", scale=alt.Scale(range=["#7c3aed", "#0ea5e9"])),
                    column=alt.Column("series:N", header=alt.Header(title="")),
                )
            )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No completed or planned activities for this week.")

    # Estimated vs Actual minutes per hobby (current week, Sunday–Saturday; estimated only for done tasks)
    st.markdown('<div class="section-title">📊 Estimated vs Actual Minutes per Hobby (This Week)</div>', unsafe_allow_html=True)
    planner_rows = db.get_planner_tasks_for_range(week_start.isoformat(), week_end.isoformat())
    tasks_by_date = {}
    for row in planner_rows:
        t_id, d_str, title, notes, done_flag, freq, packet_id, minutes, hobby_id, points, linked_task_id = row
        tasks_by_date.setdefault(d_str, []).append({
            "id": t_id, "title": title, "notes": notes, "done": bool(done_flag),
            "minutes": minutes, "hobby_id": hobby_id, "points": points,
        })
    est_by_hobby = {}
    scheduled_hobby_ids = set()
    for rows in tasks_by_date.values():
        for t in rows:
            hid = t.get("hobby_id")
            if hid is not None:
                scheduled_hobby_ids.add(hid)
            if hid is None or not t.get("done"):
                continue
            est_by_hobby.setdefault(hid, 0)
            est_by_hobby[hid] += t.get("minutes") or 0
    hobby_map = {hid: name for hid, name in db.get_hobbies()}
    df_actual = db.get_minutes_for_hobbies_in_range(week_start.isoformat(), week_end.isoformat())
    hobbies_list = {hobby_map[hid] for hid in scheduled_hobby_ids if hid in hobby_map}
    if df_actual is not None and not df_actual.empty:
        hobbies_list.update(df_actual["hobby"].tolist())
    if hobbies_list:
        data = []
        for hobby_name in sorted(hobbies_list):
            hid = next((_hid for _hid, _name in hobby_map.items() if _name == hobby_name), None)
            est = est_by_hobby.get(hid, 0)
            act = 0
            if df_actual is not None and not df_actual.empty:
                row = df_actual[df_actual["hobby"] == hobby_name]
                if not row.empty:
                    act = int(row["total_minutes"].iloc[0])
            data.append({"hobby": hobby_name, "Estimated": est, "Actual": act})
        if data:
            df_min = pd.DataFrame(data)
            df_long = df_min.melt(
                id_vars=["hobby"],
                value_vars=["Estimated", "Actual"],
                var_name="series",
                value_name="minutes",
            )
            try:
                chart = (
                    alt.Chart(df_long, width=600, height=280)
                    .mark_bar(size=28)
                    .encode(
                        x=alt.X("hobby:N", title="Hobby", sort="-y"),
                        y=alt.Y("minutes:Q", title="Minutes"),
                        xOffset="series:N",
                        color=alt.Color("series:N", title="", scale=alt.Scale(range=["#0d9488", "#ea580c"])),
                    )
                )
            except (AttributeError, TypeError):
                chart = (
                    alt.Chart(df_long, width=280, height=280)
                    .mark_bar(size=32)
                    .encode(
                        x=alt.X("hobby:N", title="Hobby", sort="-y"),
                        y=alt.Y("minutes:Q", title="Minutes"),
                        color=alt.Color("series:N", title="", scale=alt.Scale(range=["#0d9488", "#ea580c"])),
                        column=alt.Column("series:N", header=alt.Header(title="")),
                    )
                )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.caption("No estimated or actual minutes for this week yet.")
    else:
        st.caption("No estimated or actual minutes for this week yet.")

    # Packet completion per day: for each packet, is every task done on that day?
    st.markdown(
        '<div class="section-title">📦 Packet completion per day (all tasks done?)</div>',
        unsafe_allow_html=True,
    )
    week_days = [week_start + datetime.timedelta(days=i) for i in range(7)]
    packets = db.get_planner_packets()
    packet_id_to_name = {pid: name for pid, name in packets}
    planner_rows = db.get_planner_tasks_for_range(week_start.isoformat(), week_end.isoformat())
    by_day_packet = {}
    for row in planner_rows:
        t_id, d_str, title, notes, done_flag, freq, packet_id, minutes, hobby_id, points, linked_task_id = row
        if packet_id is None:
            continue
        key = (d_str, packet_id)
        by_day_packet.setdefault(key, []).append(bool(done_flag))
    packet_completion = []
    for (d_str, p_id), dones in by_day_packet.items():
        all_done = all(dones)
        packet_completion.append(
            {
                "day": datetime.datetime.strptime(d_str, "%Y-%m-%d").strftime("%a %d"),
                "packet": packet_id_to_name.get(p_id, f"Packet {p_id}"),
                "all_done": 1 if all_done else 0,
                "label": "All done" if all_done else "Not all done",
            }
        )
    if packet_completion:
        df_packet = pd.DataFrame(packet_completion)
        day_order = [(week_start + datetime.timedelta(days=i)).strftime("%a %d") for i in range(7)]
        chart_packet = (
            alt.Chart(df_packet, width=600, height=240)
            .mark_rect()
            .encode(
                x=alt.X("day:O", title="Day", sort=day_order),
                y=alt.Y("packet:N", title="Packet", sort="-x"),
                color=alt.Color(
                    "label:N",
                    title="",
                    scale=alt.Scale(domain=["All done", "Not all done"], range=["#15803d", "#fef3c7"]),
                ),
                tooltip=["day", "packet", "label"],
            )
        )
        st.altair_chart(chart_packet, use_container_width=True)
    else:
        st.info("No packet tasks planned for this week.")

# -------------------
# Weekly Planner Page
# -------------------
elif page == "Weekly Planner":
    st.header("Weekly Planner")

    today = datetime.date.today()
    # Week starts on Sunday
    week_start = today - datetime.timedelta(days=(today.weekday() + 1) % 7)
    week_days = [week_start + datetime.timedelta(days=i) for i in range(7)]
    week_end = week_days[-1]

    st.markdown(
        f"<div class='section-title'>Week of {week_start.strftime('%d %b %Y')} – {week_end.strftime('%d %b %Y')}</div>",
        unsafe_allow_html=True,
    )

    # Fetch tasks for this week
    planner_rows = db.get_planner_tasks_for_range(
        week_start.isoformat(), week_end.isoformat()
    )
    tasks_by_date = {}
    for row in planner_rows:
        t_id, d_str, title, notes, done_flag, freq, packet_id, minutes, hobby_id, points, linked_task_id = row
        tasks_by_date.setdefault(d_str, []).append(
            {
                "id": t_id,
                "title": title,
                "notes": notes,
                "done": bool(done_flag),
                "frequency": freq,
                "packet_id": packet_id,
                "minutes": minutes,
                "hobby_id": hobby_id,
                "points": points,
                "task_id": linked_task_id,
            }
        )

    # This Week at a Glance (first)
    st.subheader("This Week at a Glance")
    cols = st.columns(7)

    for i, d in enumerate(week_days):
        with cols[i]:
            st.markdown(
                f"<div class='section-title'>{d.strftime('%a')}</div>",
                unsafe_allow_html=True,
            )
            d_str = d.isoformat()
            day_tasks = tasks_by_date.get(d_str, [])

            if not day_tasks:
                st.caption("No tasks")

            for t in day_tasks:
                label = t["title"]
                if t["notes"]:
                    label += f" — {t['notes']}"
                done_class = " glance-task-done" if t["done"] else ""
                # Count how many days this task appears (same task_id in week) – if >1, toggle only this row
                same_task_in_week = sum(
                    1 for rows in tasks_by_date.values() for r in rows if r.get("task_id") == t.get("task_id")
                )

                row_cols = st.columns([0.4, 5.6])
                with row_cols[0]:
                    checked = st.checkbox(
                        "",
                        value=t["done"],
                        key=f"planner_task_{t['id']}_{t['done']}",
                    )
                with row_cols[1]:
                    st.markdown(
                        f'<div class="task-tree-item task-tree-task{done_class}">📌 {label}</div>',
                        unsafe_allow_html=True,
                    )

                if checked != t["done"]:
                    actual_minutes = t["minutes"] or 0
                    db.update_planner_task_minutes(t["id"], actual_minutes)
                    if same_task_in_week > 1:
                        db.set_planner_row_done_only(t["id"], done=checked, minutes_override=actual_minutes)
                    else:
                        db.toggle_planner_task_done(t["id"], done=checked, minutes_override=actual_minutes)
                    st.query_params["page"] = "Weekly Planner"
                    st.rerun()

                if t.get("task_id"):
                    subtasks = db.get_subtasks(t["task_id"])
                    if subtasks:
                        st.markdown('<div class="planner-glance-tree">', unsafe_allow_html=True)
                        for stsk in subtasks:
                            sub_done = bool(stsk[3])
                            c0, c1, c2 = st.columns([0.9, 0.35, 5.15])  # c0 = tab indent for whole row
                            with c0:
                                st.write("")
                            with c1:
                                sub_checked = st.checkbox(
                                    "",
                                    value=sub_done,
                                    key=f"planner_sub_{stsk[0]}_{sub_done}",
                                    label_visibility="collapsed",
                                )
                            with c2:
                                icon = "✅" if sub_done else "🟠"
                                klass = "task-tree-sub-done" if sub_done else "task-tree-sub-active"
                                st.markdown(
                                    f'<div class="planner-glance-sub {klass}">{icon} {stsk[2]}</div>',
                                    unsafe_allow_html=True,
                                )
                            if sub_checked != sub_done:
                                if sub_checked:
                                    db.mark_task_done(stsk[0], is_subtask=True)
                                else:
                                    db.mark_subtask_undone(stsk[0])
                                st.query_params["page"] = "Weekly Planner"
                                st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

    # Add a Task to This Week (collapsed by default)
    hobbies = db.get_hobbies()
    st.subheader("Add a Task to This Week")
    with st.expander("Plan a new weekly task", expanded=False):
        if not hobbies:
            st.warning("Please add at least one hobby first (Add Hobby page).")
        col_day, col_title = st.columns([1, 2])
        with col_day:
            day_for_task = st.date_input(
                "Day",
                value=today,
                min_value=week_start,
                max_value=week_end,
                key="planner_add_day",
            )
        with col_title:
            title_for_task = st.text_input("Task title", key="planner_add_title")
        notes_for_task = st.text_input("Notes (optional)", key="planner_add_notes")
        est_minutes = st.number_input(
            "Estimated minutes", min_value=0, max_value=600, value=0, key="planner_add_minutes"
        )
        frequency = st.selectbox(
            "Frequency",
            ["Once", "Daily", "Weekly"],
            index=0,
            key="planner_add_frequency",
        )
        if hobbies:
            hobby_dict = {name: id for id, name in hobbies}
            hobby_for_task = st.selectbox(
                "Linked hobby",
                options=list(hobby_dict.keys()),
                key="planner_add_hobby",
            )
        else:
            hobby_dict = {}
            hobby_for_task = None
        if st.button("Add Weekly Task", key="planner_add_btn"):
            if not hobbies:
                st.warning("Cannot add planner tasks until you have at least one hobby.")
            elif not title_for_task.strip():
                st.warning("Please provide a task title.")
            elif not hobby_for_task:
                st.warning("Please choose a hobby for this task.")
            else:
                freq_value = frequency.lower()
                if freq_value == "daily":
                    task_id = db.add_task(
                        hobby_dict[hobby_for_task],
                        title_for_task.strip(),
                        est_minutes,
                        0,
                    )
                    for d in week_days:
                        db.add_planner_task(
                            d.isoformat(),
                            title_for_task.strip(),
                            notes_for_task.strip(),
                            freq_value,
                            None,
                            est_minutes,
                            hobby_dict[hobby_for_task],
                            0,
                            task_id,
                        )
                else:
                    task_id = db.add_task(
                        hobby_dict[hobby_for_task],
                        title_for_task.strip(),
                        est_minutes,
                        0,
                    )
                    db.add_planner_task(
                        day_for_task.isoformat(),
                        title_for_task.strip(),
                        notes_for_task.strip(),
                        freq_value,
                        None,
                        est_minutes,
                        hobby_dict[hobby_for_task],
                        0,
                        task_id,
                    )
                st.success("Task added to weekly planner!")
                st.query_params["page"] = "Weekly Planner"
                st.rerun()

    # Packets (Templates) – before Existing Tasks
    st.subheader("Packets (Templates)")
    packets = db.get_planner_packets()
    with st.expander("Create / edit packets", expanded=False):
        new_packet_name = st.text_input("New packet name", key="planner_new_packet_name")
        if st.button("Create packet", key="planner_create_packet_btn") and new_packet_name.strip():
            pid = db.add_planner_packet(new_packet_name.strip())
            st.success(f"Packet '{new_packet_name.strip()}' created.")
            st.query_params["page"] = "Weekly Planner"
            st.rerun()
        packets = db.get_planner_packets()
        if packets:
            pkt_names = {name: pid for pid, name in packets}
            edit_name = st.selectbox("Edit packet", options=list(pkt_names.keys()), key="planner_edit_packet")
            edit_pid = pkt_names[edit_name]
            st.caption("Existing items:")
            items = db.get_planner_packet_items(edit_pid)
            for _, title in items:
                st.markdown(f"- {title}")
            new_item_title = st.text_input("New item title", key="planner_new_packet_item")
            if st.button("Add item to packet", key="planner_add_packet_item_btn") and new_item_title.strip():
                db.add_planner_packet_item(edit_pid, new_item_title.strip())
                st.success("Item added to packet.")
                st.query_params["page"] = "Weekly Planner"
                st.rerun()
        else:
            st.caption("No packets yet – create one above.")

    if packets:
        packet_dict = {name: pid for pid, name in packets}
        with st.expander("Add packet to week", expanded=False):
            col_p_day, col_p_packet = st.columns([1, 2])
            with col_p_day:
                packet_day = st.selectbox(
                    "Day for packet",
                    options=week_days,
                    format_func=lambda d: d.strftime("%a %d %b"),
                    key="planner_packet_day_main",
                )
            with col_p_packet:
                packet_name = st.selectbox(
                    "Choose packet",
                    options=list(packet_dict.keys()),
                    key="planner_packet_name",
                )
            est_packet_minutes = st.number_input(
                "Minutes per packet item",
                min_value=0,
                max_value=600,
                value=0,
                key="planner_packet_minutes",
            )
            if st.button("Add Packet to Day", key="planner_add_packet_btn"):
                p_id = packet_dict[packet_name]
                existing_for_day = tasks_by_date.get(packet_day.isoformat(), [])
                if any(t["packet_id"] == p_id for t in existing_for_day):
                    st.warning("This packet has already been added for the selected day.")
                else:
                    items = db.get_planner_packet_items(p_id)
                    for _, item_title in items:
                        db.add_planner_task(
                            packet_day.isoformat(),
                            item_title,
                            "",
                            "once",
                            packet_id=p_id,
                            minutes=est_packet_minutes,
                            hobby_id=None,
                            points=0,
                        )
                    st.success(f"Packet '{packet_name}' added to {packet_day.strftime('%a %d %b')}.")
                    st.query_params["page"] = "Weekly Planner"
                    st.rerun()
            if st.button("Add Packet for All Days", key="planner_add_packet_all_btn"):
                p_id = packet_dict[packet_name]
                already = {
                    d_str
                    for d_str, rows in tasks_by_date.items()
                    for t in rows
                    if t["packet_id"] == p_id
                }
                items = db.get_planner_packet_items(p_id)
                for d in week_days:
                    d_str = d.isoformat()
                    if d_str in already:
                        continue
                    for _, item_title in items:
                        db.add_planner_task(
                            d_str,
                            item_title,
                            "",
                            "once",
                            packet_id=p_id,
                            minutes=est_packet_minutes,
                            hobby_id=None,
                            points=0,
                        )
                st.success(f"Packet '{packet_name}' added to all days of the week.")
                st.query_params["page"] = "Weekly Planner"
                st.rerun()
            if st.button("Remove Selected Packet", key="planner_remove_packet_btn"):
                p_id = packet_dict[packet_name]
                db.delete_planner_packet(p_id)
                st.success(f"Packet '{packet_name}' removed.")
                st.query_params["page"] = "Weekly Planner"
                st.rerun()
    else:
        st.info("No packets defined yet.")

    # Existing tasks (manage here – syncs to glance above)
    if hobbies:
        hobby_dict = {name: id for id, name in hobbies}
        st.subheader("Existing Tasks (manage tasks – changes sync to the glance)")
        task_hobby_name = st.selectbox("Select Hobby", list(hobby_dict.keys()), key="planner_task_hobby")
        task_hobby_id = hobby_dict[task_hobby_name]
        db.ensure_recurring_tasks_for_today(task_hobby_id)
        tasks = db.get_tasks(task_hobby_id)
        task_search = st.text_input("Search tasks", placeholder="Filter by task name...", key="planner_task_search")
        search_lower = (task_search or "").strip().lower()
        done_tasks = [t for t in tasks if t[3]]
        recent_done_ids = {t[0] for t in sorted(done_tasks, key=lambda x: x[0], reverse=True)[:10]}
        tasks_sorted = sorted(tasks, key=lambda x: x[0], reverse=True)
        if search_lower:
            tasks_sorted = [t for t in tasks_sorted if search_lower in (t[2] or "").lower()]
        for t in tasks_sorted:
            t_id = t[0]
            is_done = bool(t[3])
            if is_done and t_id not in recent_done_ids:
                continue
            subtasks = db.get_subtasks(t_id)
            total_minutes = sum(stsk[4] for stsk in subtasks) if subtasks else t[4]
            done_status = "✅" if is_done else "⬜"
            with st.expander(f"{done_status} {t[2]} • {total_minutes} min", expanded=False):
                if not is_done:
                    actual_mins = st.number_input("Actual minutes (for log)", min_value=0, max_value=600, value=total_minutes, key=f"task_actual_min_{t_id}")
                    if st.button(f"Mark Task '{t[2]}' Done", key=f"task_done_{t_id}"):
                        db.mark_task_done(t_id, is_subtask=False, actual_minutes_override=actual_mins)
                        st.success("Task marked done and activity logged!")
                        st.query_params["page"] = "Weekly Planner"
                        st.rerun()
                else:
                    if st.button(f"Mark '{t[2]}' Undone", key=f"task_undone_{t_id}"):
                        db.mark_task_undone(t_id)
                        st.success("Task marked undone (also in weekly glance).")
                        st.query_params["page"] = "Weekly Planner"
                        st.rerun()
                if st.button("Remove from week", key=f"task_remove_week_{t_id}"):
                    db.delete_task(t_id)
                    st.success("Task removed from week and from list.")
                    st.query_params["page"] = "Weekly Planner"
                    st.rerun()
                # For daily tasks: option to remove from a single day
                planner_entries = [
                    (d_str, task["id"])
                    for d_str, rows in tasks_by_date.items()
                    for task in rows
                    if task.get("task_id") == t_id
                ]
                if len(planner_entries) > 1:
                    day_options = {d_str: pid for d_str, pid in sorted(planner_entries)}
                    remove_day = st.selectbox(
                        "Remove from day",
                        options=list(day_options.keys()),
                        key=f"task_remove_day_{t_id}",
                        format_func=lambda x: datetime.datetime.strptime(x, "%Y-%m-%d").strftime("%a %d %b"),
                    )
                    if st.button("Remove from this day only", key=f"task_remove_day_btn_{t_id}"):
                        db.delete_planner_task(day_options[remove_day])
                        st.success("Removed from that day only.")
                        st.query_params["page"] = "Weekly Planner"
                        st.rerun()
                for stsk in subtasks:
                    st_done = "✅" if stsk[3] else "⬜"
                    cols = st.columns([3, 1, 1])
                    cols[0].write(f"{st_done} {stsk[2]} ({stsk[4]} min)")
                    if not stsk[3] and cols[1].button("Done", key=f"subtask_done_{stsk[0]}"):
                        db.mark_task_done(stsk[0], is_subtask=True)
                        st.success("Subtask marked done and activity logged!")
                        st.query_params["page"] = "Weekly Planner"
                        st.rerun()
                    if stsk[3] and cols[1].button("Undone", key=f"subtask_undone_{stsk[0]}"):
                        db.mark_subtask_undone(stsk[0])
                        st.success("Subtask marked undone.")
                        st.query_params["page"] = "Weekly Planner"
                        st.rerun()
                    if cols[2].button("Remove", key=f"subtask_remove_{stsk[0]}"):
                        db.delete_subtask(stsk[0])
                        st.success("Subtask removed.")
                        st.query_params["page"] = "Weekly Planner"
                        st.rerun()
                if not is_done:
                    new_sub_name = st.text_input("New subtask name", key=f"newsub_{t_id}")
                    new_sub_min = st.number_input("Minutes", min_value=0, max_value=1000, value=0, key=f"sub_min_{t_id}")
                    if st.button("Add Subtask", key=f"addsub_{t_id}") and new_sub_name.strip():
                        db.add_subtask(t_id, new_sub_name.strip(), new_sub_min, 0)
                        st.success("Subtask added!")
                        st.query_params["page"] = "Weekly Planner"
                        st.rerun()

    # (legacy packets block removed – packets logic lives above)
