import sys
from pathlib import Path

# Ensure project root is on path (e.g. when running streamlit from another directory)
_project_root = Path(__file__).resolve().parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import importlib
import streamlit as st
import data.database as db

# Reload so a normal push/deploy always uses the latest database.py (avoids stale module cache)
importlib.reload(db)

from datetime import date
from itertools import groupby
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

    /* Sidebar: orange / warm theme to match the app */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fef3c7 0%, #fde7c7 35%, #fed7aa 70%, #fef3c7 100%) !important;
        border-right: 2px solid rgba(124, 45, 18, 0.35) !important;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        background: transparent !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-family: 'Caveat', 'Nunito', system-ui, sans-serif !important;
        color: #7c2d12 !important;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label {
        background: rgba(255, 255, 255, 0.4) !important;
        border-radius: 0.5rem !important;
        padding: 0.5rem 0.75rem !important;
        border: 1px solid rgba(124, 45, 18, 0.2) !important;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: rgba(254, 215, 170, 0.7) !important;
        border-color: rgba(124, 45, 18, 0.4) !important;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input[type="radio"]:checked) {
        background: linear-gradient(135deg, #fde7c7, #fed7aa) !important;
        border-color: #b45309 !important;
        color: #7c2d12 !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] p {
        color: #7c2d12 !important;
        font-family: 'Caveat', 'Nunito', system-ui, sans-serif !important;
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
        font-size: 1.4rem !important;
    }
    /* Packet tasks: pin icon tinted amber/orange to distinguish from regular task pin */
    .task-tree-task .pin-packet {
        display: inline;
        filter: sepia(1) saturate(3) hue-rotate(15deg);
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
    .glance-scheduled-divider {
        margin: 0.5rem 0 0.35rem 0;
        padding: 0 0 0.35rem 0;
        border-bottom: 1px dashed rgba(124, 45, 18, 0.4);
        font-size: 0.75rem;
        color: rgba(124, 45, 18, 0.6);
        font-family: 'Nunito', system-ui, sans-serif;
    }
    .planner-glance-tree {
        margin: 0.2rem 0 0.4rem 0;
        padding-left: 2rem;
        margin-left: 0.5rem;
        border-left: 2px solid rgba(124, 45, 18, 0.25);
        font-size: 1.2rem;
        line-height: 1.4;
        font-family: 'Caveat', cursive, system-ui, sans-serif !important;
    }
    .planner-glance-sub {
        margin: 0.25rem 0;
        font-size: 1.2rem;
        line-height: 1.35;
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

    /* Marker for week-at-a-glance row only (invisible, no layout space) */
    .glance-days-marker { display: block !important; height: 0 !important; margin: 0 !important; padding: 0 !important; overflow: hidden !important; }

    /* ---------- Mobile layout (phone): responsive adjustments for viewport <= 768px ---------- */
    @media (max-width: 768px) {
        .stApp { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
        [data-testid="stAppViewContainer"] > section { padding-left: 0.75rem !important; padding-right: 0.75rem !important; max-width: 100% !important; }
        [data-testid="block-container"] { max-width: 100% !important; padding: 0.5rem 0.25rem !important; }

        /* Hero: stack title and image, smaller title */
        .hobby-title { font-size: 2rem !important; line-height: 1.2 !important; }
        .hobby-subtitle-main { font-size: 1.1rem !important; margin-bottom: 0.75rem !important; }
        [data-testid="column"] img { max-width: 140px !important; height: auto !important; }

        /* Section titles a bit smaller */
        .section-title { font-size: 1.35rem !important; }
        .stats-title { font-size: 1.5rem !important; }

        /* Sidebar: ensure nav is tappable (Streamlit collapses to overlay on mobile) */
        [data-testid="stSidebar"] { min-width: 260px !important; }
        [data-testid="stSidebar"] [role="radiogroup"] label { min-height: 2.75rem !important; padding: 0.5rem 0.75rem !important; font-size: 1rem !important; }

        /* Week-at-a-glance: horizontal scroll so 7 days stay in one row (desktop narrow / tablet) */
        [data-testid="stHorizontalBlock"]:has(> [data-testid="column"]:nth-child(7)) {
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch;
            margin-left: -0.5rem !important;
            margin-right: -0.5rem !important;
            padding: 0.25rem 0.5rem !important;
            scrollbar-width: thin;
            display: flex !important;
            flex-wrap: nowrap !important;
        }
        [data-testid="stHorizontalBlock"]:has(> [data-testid="column"]:nth-child(7)) [data-testid="column"] {
            min-width: 100px !important;
            flex: 0 0 auto !important;
        }
        [data-testid="stHorizontalBlock"]:has(> [data-testid="column"]:nth-child(7)) .section-title { font-size: 0.95rem !important; white-space: nowrap; }

        /* Android / touch: only the week row is slidable (marker + next sibling; no :has() needed) */
        @media (max-width: 768px) and (pointer: coarse) {
            .glance-days-marker + [data-testid="stHorizontalBlock"] {
                display: flex !important;
                flex-wrap: nowrap !important;
                overflow-x: auto !important;
                -webkit-overflow-scrolling: touch !important;
                scrollbar-width: thin;
                margin-left: -0.5rem !important;
                margin-right: -0.5rem !important;
                padding: 0.25rem 0.5rem !important;
            }
            .glance-days-marker + [data-testid="stHorizontalBlock"] [data-testid="column"] {
                flex: 0 0 auto !important;
                min-width: 92px !important;
            }
            .glance-days-marker + [data-testid="stHorizontalBlock"] .section-title { font-size: 0.95rem !important; white-space: nowrap !important; }
        }

        /* Task rows in glance: larger tap targets */
        div.stCheckbox { min-height: 2.25rem !important; }
        div.stCheckbox label { font-size: 1.05rem !important; }
        .task-tree-task { font-size: 1.25rem !important; }
        .planner-glance-sub { font-size: 1.1rem !important; }

        /* Buttons and inputs: larger touch targets, prevent iOS zoom on focus */
        [data-testid="stHorizontalBlock"] button { min-height: 2.5rem !important; padding: 0.4rem 0.75rem !important; }
        [data-testid="stVerticalBlock"] > div input[type="text"],
        [data-testid="stVerticalBlock"] > div input[type="number"] { min-height: 2.5rem !important; font-size: 16px !important; }
        select, input, textarea { font-size: 16px !important; }

        /* Hobby pills: stack or wrap nicely */
        .hobby-pill { display: inline-block !important; margin: 0.25rem !important; padding: 0.5rem 0.85rem !important; font-size: 1.1rem !important; }

        /* Very small: stack 2-column layouts (hero, hobby pills); leave 7-day glance as horizontal scroll */
        @media (max-width: 480px) {
            [data-testid="stHorizontalBlock"]:not(:has(> [data-testid="column"]:nth-child(7))) [data-testid="column"] {
                min-width: 100% !important;
                flex: 1 1 100% !important;
            }
        }

        /* Charts: use full width */
        [data-testid="stVerticalBlock"] iframe { max-width: 100% !important; }
        .js-plotly-plot, .vega-embed { max-width: 100% !important; }

        /* Expanders: easier tap */
        .streamlit-expanderHeader { min-height: 2.75rem !important; padding: 0.5rem 0 !important; }
    }

    /* Groceries page: market / garden aesthetic */
    .groceries-hero {
        font-family: 'Caveat', 'Nunito', system-ui, sans-serif;
        font-size: 2.2rem;
        font-weight: 600;
        color: #166534;
        margin-bottom: 0.25rem;
    }
    .groceries-missing-card {
        background: linear-gradient(145deg, rgba(254, 243, 199, 0.95), rgba(254, 249, 195, 0.9));
        border: 2px solid rgba(22, 101, 52, 0.35);
        border-radius: 1rem;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 14px rgba(22, 101, 52, 0.12);
    }
    .groceries-missing-title {
        font-family: 'Caveat', 'Nunito', system-ui, sans-serif;
        font-size: 1.4rem;
        font-weight: 700;
        color: #166534;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .groceries-missing-list {
        font-family: 'Caveat', cursive, system-ui, sans-serif;
        font-size: 1.1rem;
        color: #1c1917;
        line-height: 1.7;
    }
    .groceries-missing-list span {
        display: inline-block;
        margin-right: 0.5rem;
        margin-bottom: 0.25rem;
    }
    .groceries-category-card {
        background: linear-gradient(180deg, rgba(255,255,255,0.7) 0%, rgba(254, 249, 195, 0.4) 100%);
        border: 1px solid rgba(124, 45, 18, 0.2);
        border-radius: 0.85rem;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(124, 45, 18, 0.06);
    }
    .groceries-category-name {
        font-family: 'Caveat', 'Nunito', system-ui, sans-serif;
        font-size: 1.35rem;
        font-weight: 600;
        color: #7c2d12;
        margin-bottom: 0.5rem;
    }
    .groceries-item-row {
        font-family: 'Caveat', cursive, system-ui, sans-serif !important;
        font-size: 1.2rem;
        color: #1f2933;
        padding: 0.35rem 0;
        border-bottom: 1px solid rgba(124, 45, 18, 0.08);
    }
    .groceries-item-row:last-child { border-bottom: none; }
    .groceries-item-have { color: #15803d; text-decoration: line-through; opacity: 0.85; font-family: 'Caveat', cursive, system-ui, sans-serif !important; }
    .groceries-empty-msg {
        font-family: 'Caveat', cursive, system-ui, sans-serif;
        color: #78716c;
        font-style: italic;
        padding: 1rem 0;
    }
    .groceries-cat-label, .groceries-section-head {
        font-family: 'Caveat', cursive, system-ui, sans-serif !important;
        font-size: 1.25rem;
        font-weight: 600;
        color: #7c2d12;
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
nav_options = ["Add Hobby", "Statistics", "Weekly Planner", "Groceries", "General Tasks"]
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
                    color=alt.Color("series:N", title="", scale=alt.Scale(range=["#7c2d12", "#b45309"])),
                )
            )
        except (AttributeError, TypeError):
            chart = (
                alt.Chart(df_long, width=280, height=280)
                .mark_bar(size=32)
                .encode(
                    x=alt.X("hobby:N", title="Hobby", sort="-y"),
                    y=alt.Y("count:Q", title="Count"),
                    color=alt.Color("series:N", title="", scale=alt.Scale(range=["#7c2d12", "#b45309"])),
                    column=alt.Column("series:N", header=alt.Header(title="")),
                )
            )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No completed or planned activities for this week.")

    # Estimated vs Actual minutes per hobby (current week)
    # Estimated = total planned minutes (all scheduled tasks); Actual = logged minutes when tasks were done
    st.markdown('<div class="section-title">📊 Estimated vs Actual Minutes per Hobby (This Week)</div>', unsafe_allow_html=True)
    planner_rows = db.get_planner_tasks_for_range(week_start.isoformat(), week_end.isoformat())
    tasks_by_date = {}
    for row in planner_rows:
        t_id, d_str, title, notes, done_flag, freq, packet_id, minutes, hobby_id, points, linked_task_id, _ = row
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
                # Estimated = sum of ALL planned minutes for this hobby (done + undone)
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
                        color=alt.Color("series:N", title="", scale=alt.Scale(range=["#0d9488", "#c2410c"])),
                    )
                )
            except (AttributeError, TypeError):
                chart = (
                    alt.Chart(df_long, width=280, height=280)
                    .mark_bar(size=32)
                    .encode(
                        x=alt.X("hobby:N", title="Hobby", sort="-y"),
                        y=alt.Y("minutes:Q", title="Minutes"),
                        color=alt.Color("series:N", title="", scale=alt.Scale(range=["#0d9488", "#c2410c"])),
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
        t_id, d_str, title, notes, done_flag, freq, packet_id, minutes, hobby_id, points, linked_task_id, _ = row
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
                    scale=alt.Scale(domain=["All done", "Not all done"], range=["#15803d", "#d97706"]),
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
        t_id, d_str, title, notes, done_flag, freq, packet_id, minutes, hobby_id, points, linked_task_id, scheduled_time = row
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
                "scheduled_time": scheduled_time,
            }
        )

    # This Week at a Glance (first) – marker so only this row is slidable on mobile
    st.subheader("This Week at a Glance")
    st.markdown('<div class="glance-days-marker" aria-hidden="true"></div>', unsafe_allow_html=True)
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

            for idx, t in enumerate(day_tasks):
                # Separator between scheduled and unscheduled (tasks are ordered: scheduled first, then unscheduled)
                has_time = t.get("scheduled_time") and len((t.get("scheduled_time") or "").strip()) >= 5
                prev_had_time = (
                    day_tasks[idx - 1].get("scheduled_time") and len((day_tasks[idx - 1].get("scheduled_time") or "").strip()) >= 5
                ) if idx > 0 else False
                if not has_time and prev_had_time:
                    st.markdown(
                        '<div class="glance-scheduled-divider">— no time set —</div>',
                        unsafe_allow_html=True,
                    )
                label = t["title"]
                if t.get("scheduled_time"):
                    label = f"{t['scheduled_time']}  {label}"
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
                    pin_icon = (
                        '<span class="pin-packet">📌</span>'
                        if t.get("packet_id")
                        else "📌"
                    )
                    st.markdown(
                        f'<div class="task-tree-item task-tree-task{done_class}">{pin_icon} {label}</div>',
                        unsafe_allow_html=True,
                    )

                if checked != t["done"]:
                    # Task can be marked done only when all subtasks are done
                    if checked and t.get("task_id"):
                        subtasks_check = db.get_subtasks(t["task_id"])
                        if subtasks_check and not all(bool(stsk[3]) for stsk in subtasks_check):
                            st.warning("Complete all subtasks first.")
                            st.rerun()
                        else:
                            actual_minutes = t["minutes"] or 0
                            db.update_planner_task_minutes(t["id"], actual_minutes)
                            if same_task_in_week > 1:
                                db.set_planner_row_done_only(t["id"], done=checked, minutes_override=actual_minutes)
                            else:
                                db.toggle_planner_task_done(t["id"], done=checked, minutes_override=actual_minutes)
                            st.toast("Task updated", icon="✅")
                            st.query_params["page"] = "Weekly Planner"
                            st.rerun()
                    else:
                        actual_minutes = t["minutes"] or 0
                        db.update_planner_task_minutes(t["id"], actual_minutes)
                        if same_task_in_week > 1:
                            db.set_planner_row_done_only(t["id"], done=checked, minutes_override=actual_minutes)
                        else:
                            db.toggle_planner_task_done(t["id"], done=checked, minutes_override=actual_minutes)
                        st.toast("Task updated", icon="✅")
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
        hobby_dict = {name: id for id, name in hobbies} if hobbies else {}
        hobby_options = ["— General (no hobby) —"] + list(hobby_dict.keys())
        hobby_for_task = st.selectbox(
            "Linked hobby",
            options=hobby_options,
            key="planner_add_hobby",
        )
        add_scheduled_time = st.checkbox("Set scheduled time (order in glance)", key="planner_add_scheduled_time")
        scheduled_time_val = None
        if add_scheduled_time:
            t = st.time_input("Time", value=datetime.time(9, 0), key="planner_add_time", label_visibility="collapsed")
            scheduled_time_val = t.strftime("%H:%M")
        is_general_task = hobby_for_task == "— General (no hobby) —"
        if st.button("Add Weekly Task", key="planner_add_btn"):
            if not title_for_task.strip():
                st.warning("Please provide a task title.")
            elif is_general_task:
                # General task: planner row(s) only, no hobby, no task link (no time logging when done)
                freq_value = frequency.lower()
                if freq_value == "daily":
                    for d in week_days:
                        db.add_planner_task(
                            d.isoformat(),
                            title_for_task.strip(),
                            notes_for_task.strip(),
                            freq_value,
                            None,
                            est_minutes,
                            None,
                            0,
                            None,
                            scheduled_time_val,
                        )
                else:
                    db.add_planner_task(
                        day_for_task.isoformat(),
                        title_for_task.strip(),
                        notes_for_task.strip(),
                        freq_value,
                        None,
                        est_minutes,
                        None,
                        0,
                        None,
                        scheduled_time_val,
                    )
                st.toast("General task added to week.", icon="✅")
                st.query_params["page"] = "Weekly Planner"
                st.rerun()
            elif hobby_for_task not in hobby_dict:
                st.warning("Please choose a hobby or General (no hobby).")
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
                            scheduled_time_val,
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
                        scheduled_time_val,
                    )
                st.toast("Task added to weekly planner!", icon="✅")
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
            st.caption("Existing items (edit title + time for week, Update, or Remove):")
            items = db.get_planner_packet_items(edit_pid)
            for row in items:
                item_id, title = row[0], row[1]
                saved_default_time = row[2] if len(row) >= 3 else None
                # Default time: from instance in week, else saved default for this item, else 09:00
                current_time_str = None
                for rows in tasks_by_date.values():
                    for task in rows:
                        if task.get("packet_id") == edit_pid and task.get("title") == title and task.get("scheduled_time"):
                            current_time_str = task.get("scheduled_time")
                            break
                    if current_time_str:
                        break
                if not current_time_str and saved_default_time and len(str(saved_default_time).strip()) >= 5:
                    current_time_str = str(saved_default_time).strip()
                if current_time_str and len(current_time_str) >= 5:
                    try:
                        default_time = datetime.time(int(current_time_str[:2]), int(current_time_str[3:5]))
                    except (ValueError, IndexError):
                        default_time = datetime.time(9, 0)
                else:
                    default_time = datetime.time(9, 0)
                col_label, col_time, col_update, col_remove = st.columns([2, 1.2, 0.8, 0.6])
                with col_label:
                    edited_title = st.text_input(
                        "Item title",
                        value=title,
                        key=f"packet_item_edit_{item_id}",
                        label_visibility="collapsed",
                        placeholder="Item title",
                    )
                with col_time:
                    item_time = st.time_input(
                        "Time",
                        value=default_time,
                        key=f"packet_item_time_week_{item_id}",
                        label_visibility="collapsed",
                    )
                with col_update:
                    if st.button("Update", key=f"packet_item_update_{item_id}"):
                        if not edited_title.strip():
                            st.warning("Title cannot be empty.")
                        else:
                            new_title = edited_title.strip()
                            db.update_planner_packet_item(item_id, new_title)
                            time_str = item_time.strftime("%H:%M")
                            # Save as default so adding packet to a day later uses this time (and 09:00 if never set)
                            db.update_planner_packet_item_default_time(item_id, time_str)
                            # Update scheduled_time for existing planner rows in the week (glance will reflect)
                            db.update_planner_packet_item_scheduled_time_for_week_by_item_id(
                                item_id, time_str,
                                week_start.isoformat(), week_end.isoformat(),
                            )
                            st.toast("Item title & time updated (saved as default for when you add packet to a day).")
                            st.query_params["page"] = "Weekly Planner"
                            st.rerun()
                with col_remove:
                    if st.button("Remove", key=f"packet_item_remove_{item_id}"):
                        db.delete_planner_packet_item(item_id)
                        st.toast("Item removed.")
                        st.query_params["page"] = "Weekly Planner"
                        st.rerun()
            new_item_title = st.text_input("New item title", key="planner_new_packet_item")
            if st.button("Add item to packet", key="planner_add_packet_item_btn") and new_item_title.strip():
                db.add_planner_packet_item_and_schedule_for_week(
                    edit_pid, new_item_title.strip(),
                    week_start.isoformat(), week_end.isoformat(),
                    minutes=0,
                )
                st.toast("Item added to packet and to every day this week that has this packet.", icon="✅")
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
            items_for_packet = db.get_planner_packet_items(packet_dict[packet_name]) if packet_dict.get(packet_name) else []
            if st.button("Add Packet to Day", key="planner_add_packet_btn"):
                p_id = packet_dict[packet_name]
                if not items_for_packet:
                    st.warning("This packet has no items. Add items in **Create / edit packets** first.")
                else:
                    existing_for_day = tasks_by_date.get(packet_day.isoformat(), [])
                    if any(t["packet_id"] == p_id for t in existing_for_day):
                        st.warning("This packet has already been added for the selected day.")
                    else:
                        for row in items_for_packet:
                            item_id, item_title = row[0], row[1]
                            default_time = row[2] if len(row) >= 3 else None
                            stime = (default_time if default_time and str(default_time).strip() else "09:00")
                            db.add_planner_task(
                                packet_day.isoformat(),
                                item_title,
                                "",
                                "once",
                                packet_id=p_id,
                                minutes=est_packet_minutes,
                                hobby_id=None,
                                points=0,
                                scheduled_time=stime,
                            )
                        st.success(f"Packet '{packet_name}' added to {packet_day.strftime('%a %d %b')}.")
                        st.query_params["page"] = "Weekly Planner"
                        st.rerun()
            if st.button("Add Packet for All Days", key="planner_add_packet_all_btn"):
                p_id = packet_dict[packet_name]
                items_all = db.get_planner_packet_items(p_id)
                if not items_all:
                    st.warning("This packet has no items. Add items in **Create / edit packets** first.")
                else:
                    already = {
                        d_str
                        for d_str, rows in tasks_by_date.items()
                        for t in rows
                        if t["packet_id"] == p_id
                    }
                    for d in week_days:
                        d_str = d.isoformat()
                        if d_str in already:
                            continue
                        for row in items_all:
                            item_title = row[1]
                            default_time = row[2] if len(row) >= 3 else None
                            stime = (default_time if default_time and str(default_time).strip() else "09:00")
                            db.add_planner_task(
                                d_str,
                                item_title,
                                "",
                                "once",
                                packet_id=p_id,
                                minutes=est_packet_minutes,
                                hobby_id=None,
                                points=0,
                                scheduled_time=stime,
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

    # Build lists of general (no-hobby) and packet planner rows for Existing Tasks
    general_by_title = {}
    packet_by_key = {}
    packet_id_to_name = {pid: name for pid, name in packets} if packets else {}
    for d_str, rows in tasks_by_date.items():
        for task in rows:
            if task.get("task_id") is None and task.get("packet_id") is None:
                general_by_title.setdefault(task["title"], []).append((d_str, task))
            if task.get("packet_id") is not None:
                key = (task["packet_id"], task["title"])
                packet_by_key.setdefault(key, []).append((d_str, task))

    # Existing tasks (manage here – syncs to glance above). One list: hobby, general, or packet; search filters.
    has_hobby_tasks = bool(hobbies)
    has_general = bool(general_by_title)
    has_packet_items = bool(packet_by_key)
    if has_hobby_tasks or has_general or has_packet_items:
        st.subheader("Existing Tasks (manage tasks – changes sync to the glance)")
        hobby_dict = {name: id for id, name in hobbies} if hobbies else {}
        task_list_options = list(hobby_dict.keys())
        if has_general:
            task_list_options.append("— General (no hobby) —")
        if has_packet_items:
            task_list_options.append("— Packet items —")
        task_list_choice = st.selectbox(
            "Show tasks from",
            task_list_options,
            key="planner_task_list_choice",
        )
        task_search = st.text_input("Search tasks", placeholder="Filter by name...", key="planner_task_search")

        if task_list_choice == "— General (no hobby) —":
            search_lower = (task_search or "").strip().lower()
            general_sorted = sorted(general_by_title.items())
            if search_lower:
                general_sorted = [(title, entries) for title, entries in general_sorted if search_lower in title.lower()]
            for title, entries in general_sorted:
                day_planner = [(d_str, task["id"]) for d_str, task in entries]
                first_id = entries[0][1]["id"]
                first_task = entries[0][1]
                done_status = "✅" if first_task.get("done") else "⬜"
                with st.expander(f"{done_status} {title}", expanded=False):
                    # Edit task name (general tasks: updates all instances in the week)
                    edited_gen_name = st.text_input(
                        "Task name",
                        value=title,
                        key=f"gen_edit_name_{first_id}",
                        label_visibility="collapsed",
                        placeholder="Task name",
                    )
                    if st.button("Update task name", key=f"gen_update_name_btn_{first_id}"):
                        if edited_gen_name.strip():
                            db.update_general_planner_task_title(
                                title, edited_gen_name.strip(),
                                week_start.isoformat(), week_end.isoformat(),
                            )
                            st.toast("Task name updated (glance updated too).")
                            st.query_params["page"] = "Weekly Planner"
                            st.rerun()
                        else:
                            st.warning("Task name cannot be empty.")
                    day_options = {d_str: pid for d_str, pid in sorted(day_planner)}
                    time_day = st.selectbox(
                        "Day (for time or remove)",
                        options=list(day_options.keys()),
                        key=f"gen_time_day_{first_id}",
                        format_func=lambda x: datetime.datetime.strptime(x, "%Y-%m-%d").strftime("%a %d %b"),
                    )
                    planner_id = day_options[time_day]
                    current_time_str = next(
                        (task.get("scheduled_time") for task in tasks_by_date.get(time_day, []) if task["id"] == planner_id),
                        None,
                    )
                    if current_time_str and len(current_time_str) >= 5:
                        try:
                            h, m = int(current_time_str[:2]), int(current_time_str[3:5])
                            default_time = datetime.time(h, m)
                        except (ValueError, IndexError):
                            default_time = datetime.time(9, 0)
                    else:
                        default_time = datetime.time(9, 0)
                    new_time = st.time_input("Scheduled time (order in glance)", value=default_time, key=f"gen_scheduled_time_{planner_id}")
                    if st.button("Set scheduled time", key=f"gen_set_time_{planner_id}"):
                        db.update_planner_task_scheduled_time(planner_id, new_time.strftime("%H:%M"))
                        st.toast("Scheduled time updated.")
                        st.query_params["page"] = "Weekly Planner"
                        st.rerun()
                    if st.button("Remove from selected day only", key=f"gen_remove_day_{planner_id}"):
                        db.delete_planner_task(planner_id)
                        st.toast("Removed from that day only.")
                        st.query_params["page"] = "Weekly Planner"
                        st.rerun()
                    if st.button("Remove from week (all days for this task)", key=f"gen_remove_week_{first_id}"):
                        for _d, t in entries:
                            db.delete_planner_task(t["id"])
                        st.toast("Removed from week.")
                        st.query_params["page"] = "Weekly Planner"
                        st.rerun()
                    row_done = next((t["done"] for d_str, t in entries if t["id"] == planner_id), False)
                    if st.button("Mark done" if not row_done else "Mark undone", key=f"gen_done_{planner_id}"):
                        db.toggle_planner_task_done(planner_id, done=not row_done)
                        st.toast("Updated.")
                        st.query_params["page"] = "Weekly Planner"
                        st.rerun()

        elif task_list_choice == "— Packet items —":
            search_lower = (task_search or "").strip().lower()
            packet_sorted = sorted(packet_by_key.items(), key=lambda x: (x[0][0], x[0][1]))
            if search_lower:
                packet_sorted = [
                    (k, v) for k, v in packet_sorted
                    if search_lower in (packet_id_to_name.get(k[0], "") + " " + k[1]).lower()
                ]
            for (p_id, item_title), entries in packet_sorted:
                pkt_name = packet_id_to_name.get(p_id, f"Packet {p_id}")
                day_planner = [(d_str, task["id"]) for d_str, task in entries]
                first_planner_id = entries[0][1]["id"]
                first_task = entries[0][1]
                done_status = "✅" if first_task.get("done") else "⬜"
                with st.expander(f"{done_status} {pkt_name}: {item_title}", expanded=False):
                    day_options = {d_str: pid for d_str, pid in sorted(day_planner)}
                    time_day = st.selectbox(
                        "Day (for remove or mark done)",
                        options=list(day_options.keys()),
                        key=f"pkt_time_day_{first_planner_id}",
                        format_func=lambda x: datetime.datetime.strptime(x, "%Y-%m-%d").strftime("%a %d %b"),
                    )
                    planner_id = day_options[time_day]
                    st.caption("Set scheduled time for this item in **Create / edit packets** (applies to entire week).")
                    if st.button("Remove from selected day only", key=f"pkt_remove_day_{planner_id}"):
                        db.delete_planner_task(planner_id)
                        st.toast("Removed from that day only.")
                        st.query_params["page"] = "Weekly Planner"
                        st.rerun()
                    row_done = next((t["done"] for d_str, t in entries if t["id"] == planner_id), False)
                    if st.button("Mark done" if not row_done else "Mark undone", key=f"pkt_done_{planner_id}"):
                        db.toggle_planner_task_done(planner_id, done=not row_done)
                        st.toast("Updated.")
                        st.query_params["page"] = "Weekly Planner"
                        st.rerun()

        else:
            # Hobby selected
            task_hobby_id = hobby_dict[task_list_choice]
            db.ensure_recurring_tasks_for_today(task_hobby_id)
            tasks = db.get_tasks(task_hobby_id)
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
                    # Edit task name (hobby tasks only; packet tasks are edited via packet edit)
                    edited_task_name = st.text_input(
                        "Task name",
                        value=t[2],
                        key=f"task_edit_name_{t_id}",
                        label_visibility="collapsed",
                        placeholder="Task name",
                    )
                    if st.button("Update task name", key=f"task_update_name_btn_{t_id}"):
                        if edited_task_name.strip():
                            db.update_task_name(t_id, edited_task_name.strip())
                            st.toast("Task name updated (glance updated too).")
                            st.query_params["page"] = "Weekly Planner"
                            st.rerun()
                        else:
                            st.warning("Task name cannot be empty.")
                    if not is_done:
                        all_subtasks_done = (not subtasks) or all(bool(stsk[3]) for stsk in subtasks)
                        if subtasks and not all_subtasks_done:
                            st.caption("Complete all subtasks below to mark this task done.")
                        actual_mins = st.number_input("Actual minutes (for log)", min_value=0, max_value=600, value=total_minutes, key=f"task_actual_min_{t_id}")
                        if (not subtasks or all_subtasks_done) and st.button(f"Mark Task '{t[2]}' Done", key=f"task_done_{t_id}"):
                            db.mark_task_done(t_id, is_subtask=False, actual_minutes_override=actual_mins)
                            st.toast("Task marked done and activity logged!", icon="✅")
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
                    planner_entries = [
                        (d_str, task["id"])
                        for d_str, rows in tasks_by_date.items()
                        for task in rows
                        if task.get("task_id") == t_id
                    ]
                    if planner_entries:
                        day_options_any = {d_str: pid for d_str, pid in sorted(planner_entries)}
                        time_day = st.selectbox(
                            "Day (for time or remove)",
                            options=list(day_options_any.keys()),
                            key=f"task_time_day_{t_id}",
                            format_func=lambda x: datetime.datetime.strptime(x, "%Y-%m-%d").strftime("%a %d %b"),
                        )
                        planner_id_for_time = day_options_any[time_day]
                        current_time_str = next(
                            (task.get("scheduled_time") for task in tasks_by_date.get(time_day, []) if task["id"] == planner_id_for_time),
                            None,
                        )
                        if current_time_str and len(current_time_str) >= 5:
                            try:
                                h, m = int(current_time_str[:2]), int(current_time_str[3:5])
                                default_time = datetime.time(h, m)
                            except (ValueError, IndexError):
                                default_time = datetime.time(9, 0)
                        else:
                            default_time = datetime.time(9, 0)
                        new_time = st.time_input("Scheduled time (order in glance)", value=default_time, key=f"task_scheduled_time_{t_id}")
                        if st.button("Set scheduled time", key=f"task_set_time_btn_{t_id}"):
                            db.update_planner_task_scheduled_time(planner_id_for_time, new_time.strftime("%H:%M"))
                            st.toast("Scheduled time updated.")
                            st.query_params["page"] = "Weekly Planner"
                            st.rerun()
                    if len(planner_entries) > 1 and planner_entries:
                        if st.button("Remove from selected day only", key=f"task_remove_day_btn_{t_id}"):
                            db.delete_planner_task(planner_id_for_time)
                            st.toast("Removed from that day only.")
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

# -------------------
# Groceries Page
# -------------------
elif page == "Groceries":
    if not hasattr(db, "get_all_missing_groceries"):
        st.error("Groceries feature is not loaded. Redeploy the app (or restart Streamlit) so the latest database module is used.")
    else:
        st.markdown('<div class="groceries-hero">🛒 Groceries</div>', unsafe_allow_html=True)
        st.caption("Keep a list by category. Check off what you have at home and see what’s missing in one place.")

        missing = db.get_all_missing_groceries()
        st.markdown('<div class="groceries-missing-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="groceries-missing-title">📋 To buy</div>',
            unsafe_allow_html=True,
        )
        if not missing:
            st.markdown(
                '<div class="groceries-missing-list groceries-empty-msg">Nothing missing — you’re all set!</div>',
                unsafe_allow_html=True,
            )
        else:
            st.caption("Check an item when you’ve bought it; it will move to “have at home” below.")
            by_cat = groupby(missing, key=lambda x: (x[2], x[3]))
            for (_, cat_name), items in by_cat:
                st.markdown(f'<div class="groceries-cat-label">{cat_name}</div>', unsafe_allow_html=True)
                for item_id, item_name, _, _ in items:
                    row_cols = st.columns([0.12, 3])
                    with row_cols[0]:
                        bought = st.checkbox("Bought", value=False, key=f"tobuy_cb_{item_id}", label_visibility="collapsed")
                    with row_cols[1]:
                        st.markdown(f'<div class="groceries-item-row">{item_name}</div>', unsafe_allow_html=True)
                    if bought:
                        db.set_grocery_item_have_at_home(item_id, True)
                        st.toast(f"Marked «{item_name}» as have at home.")
                        st.query_params["page"] = "Groceries"
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="groceries-section-head">Categories & items</div>', unsafe_allow_html=True)

        new_cat = st.text_input("New category", placeholder="e.g. Dairy, Produce…", key="grocery_new_cat")
        if st.button("Add category", key="grocery_add_cat") and new_cat.strip():
            db.add_grocery_category(new_cat.strip())
            st.toast("Category added.")
            st.query_params["page"] = "Groceries"
            st.rerun()

        categories = db.get_grocery_categories()
        if not categories:
            st.info("No categories yet. Add one above, then add items to each category.")
        else:
            for cat_id, cat_name, _ in categories:
                items = db.get_grocery_items(cat_id)
                with st.expander(f"**{cat_name}** ({len(items)} items)", expanded=False):
                    new_item = st.text_input("Add item", placeholder="New item…", key=f"grocery_new_{cat_id}", label_visibility="collapsed")
                    add_col, _ = st.columns([1, 4])
                    with add_col:
                        if st.button("Add", key=f"grocery_add_item_{cat_id}") and new_item.strip():
                            db.add_grocery_item(cat_id, new_item.strip())
                            st.toast(f"Added to {cat_name}.")
                            st.query_params["page"] = "Groceries"
                            st.rerun()

                    if not items:
                        st.markdown('<div class="groceries-empty-msg">No items in this category yet.</div>', unsafe_allow_html=True)
                    else:
                        for item_id, item_name, have_at_home in items:
                            row_cols = st.columns([0.15, 2.8, 0.5])
                            with row_cols[0]:
                                checked = st.checkbox(
                                    "Have at home",
                                    value=bool(have_at_home),
                                    key=f"grocery_cb_{item_id}_{int(have_at_home)}",
                                    label_visibility="collapsed",
                                )
                            with row_cols[1]:
                                css_class = "groceries-item-have" if have_at_home else ""
                                st.markdown(
                                    f'<div class="groceries-item-row {css_class}">{"✓ " if have_at_home else ""}{item_name}</div>',
                                    unsafe_allow_html=True,
                                )
                            with row_cols[2]:
                                if st.button("Remove", key=f"grocery_remove_{item_id}"):
                                    db.delete_grocery_item(item_id)
                                    st.toast("Item removed.")
                                    st.query_params["page"] = "Groceries"
                                    st.rerun()
                            if checked != bool(have_at_home):
                                db.set_grocery_item_have_at_home(item_id, checked)
                                st.toast("Updated.")
                                st.query_params["page"] = "Groceries"
                                st.rerun()

                    if st.button("Delete category", key=f"grocery_del_cat_{cat_id}"):
                        db.delete_grocery_category(cat_id)
                        st.toast(f"Category «{cat_name}» and its items removed.")
                        st.query_params["page"] = "Groceries"
                        st.rerun()

# -------------------
# General Tasks Page (standalone list, no day/time, same look as glance)
# -------------------
elif page == "General Tasks":
    if not hasattr(db, "get_general_tasks"):
        st.error("Database module needs a restart. Stop Streamlit (Ctrl+C) and run it again so the General Tasks feature loads.")
    else:
        st.subheader("General Tasks")
        st.caption("Tasks with no date or time — just a list you can mark done. Add to glance to schedule a day (and optional time) and move it to the Weekly Planner.")
        new_title = st.text_input("New task", placeholder="Add a task…", key="general_new_task")
        if st.button("Add task", key="general_add_btn") and new_title.strip():
            db.add_general_task(new_title.strip())
            st.toast("Task added.")
            st.query_params["page"] = "General Tasks"
            st.rerun()

        all_tasks = db.get_general_tasks()
        undone = [t for t in all_tasks if not t[2]]
        done_list = [t for t in all_tasks if t[2]]
        recent_done = sorted(done_list, key=lambda x: x[0], reverse=True)[:10]
        tasks = undone + recent_done

        if not tasks:
            st.info("No general tasks yet. Add one above.")
        else:
            if len(done_list) > 10:
                st.caption(f"Showing all {len(undone)} to-do and the last 10 completed (of {len(done_list)}).")
            today = date.today()
            week_start = today - datetime.timedelta(days=(today.weekday() + 1) % 7)
            week_end = week_start + datetime.timedelta(days=6)
            week_days = [week_start + datetime.timedelta(days=i) for i in range(7)]

            for (tid, title, done) in tasks:
                done_class = " glance-task-done" if done else ""
                row_cols = st.columns([0.4, 5.2, 0.6])
                with row_cols[0]:
                    checked = st.checkbox("", value=bool(done), key=f"general_cb_{tid}_{done}", label_visibility="collapsed")
                with row_cols[1]:
                    st.markdown(
                        f'<div class="task-tree-item task-tree-task{done_class}">📌 {title}</div>',
                        unsafe_allow_html=True,
                    )
                with row_cols[2]:
                    if st.button("Remove", key=f"general_remove_{tid}"):
                        db.delete_general_task(tid)
                        st.toast("Task removed.")
                        st.query_params["page"] = "General Tasks"
                        st.rerun()

                with st.expander("Add to glance (schedule a day, then move to Weekly Planner)", expanded=False):
                    schedule_day = st.selectbox(
                        "Day this week",
                        options=week_days,
                        key=f"general_glance_day_{tid}",
                        format_func=lambda d: d.strftime("%a %d %b"),
                    )
                    set_time = st.checkbox("Set scheduled time", key=f"general_glance_set_time_{tid}")
                    scheduled_time = None
                    if set_time:
                        t_val = st.time_input("Time", value=datetime.time(9, 0), key=f"general_glance_time_{tid}", label_visibility="collapsed")
                        scheduled_time = t_val.strftime("%H:%M")
                    if st.button("Add to glance", key=f"general_glance_confirm_{tid}"):
                        db.add_planner_task(
                            schedule_day.isoformat(),
                            title,
                            "",
                            "once",
                            packet_id=None,
                            minutes=0,
                            hobby_id=None,
                            points=0,
                            task_id=None,
                            scheduled_time=scheduled_time,
                        )
                        db.delete_general_task(tid)
                        st.toast("Task added to weekly glance. Edit it under Weekly Planner → Existing Tasks → General (no hobby).")
                        st.query_params["page"] = "General Tasks"
                        st.rerun()

                if checked != bool(done):
                    db.set_general_task_done(tid, checked)
                    st.toast("Updated.")
                    st.query_params["page"] = "General Tasks"
                    st.rerun()
