import sys
from pathlib import Path

# Ensure project root is on path (e.g. when running streamlit from another directory)
_project_root = Path(__file__).resolve().parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import streamlit as st
try:
    import data.database as db
except (ModuleNotFoundError, KeyError):
    # Fallback for environments where namespace package resolution intermittently fails.
    _data_dir = _project_root / "data"
    if str(_data_dir) not in sys.path:
        sys.path.insert(0, str(_data_dir))
    import database as db

from datetime import date
from itertools import groupby
import pandas as pd
import datetime
import altair as alt

# Initialize database once per server process (not on every rerun)
@st.cache_resource
def _init_db_once():
    db.init_db()
    return True

_init_db_once()

# OpenAI client — initialized once, None if key not configured
@st.cache_resource
def _get_openai_client():
    try:
        key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        key = ""
    if not key or key.startswith("sk-your"):
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=key)
    except ImportError:
        return None

# Basic theming / styling
st.set_page_config(page_title="Hobby Tracker", page_icon="🎯", layout="wide")

st.markdown(
    """
    <style>
    /* Import playful handwritten + clean body fonts (Amatic SC covers Hebrew script) */
    @import url('https://fonts.googleapis.com/css2?family=Amatic+SC:wght@400;700&family=Caveat:wght@500;600&family=Nunito:wght@400;600;700&display=swap');

    /* Apply background to full Streamlit app with layered, subtle orange theme */
    .stApp {
        background:
            radial-gradient(circle at 12% 0%, rgba(254, 215, 170, 0.9) 0, rgba(254, 249, 195, 0.0) 55%),
            radial-gradient(circle at 90% 8%, rgba(254, 226, 226, 0.85) 0, rgba(254, 226, 226, 0.0) 55%),
            linear-gradient(180deg, #fffaf3 0%, #fde7c7 45%, #fed7aa 80%, #fef3c7 100%) !important;
        color: #1f2933;
        font-family: 'Caveat', 'Amatic SC', 'Nunito', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    }
    /* Hebrew text → Amatic SC handwriting (upscaled: Amatic SC is narrower than Caveat) */
    :lang(he), :lang(iw), [dir="rtl"] {
        font-family: 'Amatic SC', 'Caveat', cursive !important;
        font-size: 2em !important;
        font-weight: 900 !important;
        -webkit-text-stroke: 1px currentColor;
        letter-spacing: 0.03em;
        line-height: 1.5;
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
        font-family: 'Caveat', 'Amatic SC', 'Nunito', system-ui, sans-serif !important;
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
        font-family: 'Caveat', 'Amatic SC', 'Nunito', system-ui, sans-serif !important;
    }
    /* Sidebar app title */
    .sidebar-app-title {
        font-family: 'Caveat', 'Amatic SC', cursive;
        font-size: 1.6rem;
        font-weight: 600;
        color: #7c2d12;
        margin-bottom: 0.75rem;
        letter-spacing: 0.04em;
    }
    /* Kitchen section divider in sidebar */
    .sidebar-kitchen-divider {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 0.85rem 0 0.5rem 0;
        color: #166534;
        font-family: 'Caveat', 'Amatic SC', cursive;
        font-size: 1.1rem;
        font-weight: 600;
    }
    .sidebar-kitchen-divider::before,
    .sidebar-kitchen-divider::after {
        content: "";
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(22,101,52,0.45), transparent);
    }

    /* Global headers use handwritten font (override Streamlit defaults) */
    h1, h2, h3,
    .block-container h1,
    .block-container h2,
    .block-container h3,
    [data-testid="stHeader"] h1 {
        font-family: 'Caveat', 'Amatic SC', 'Nunito', system-ui, sans-serif !important;
        color: #7c2d12 !important;
    }

    /* Handwritten-style main title and section titles */
    .hobby-title {
        font-family: 'Caveat', 'Amatic SC', 'Nunito', system-ui, sans-serif;
        font-size: 3rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: none;
        color: #7c2d12;
        margin-bottom: 0.3rem;
    }
    .hobby-subtitle-main {
        font-family: 'Caveat', 'Amatic SC', 'Nunito', system-ui, sans-serif;
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
        font-family: 'Caveat', 'Amatic SC', 'Nunito', system-ui, sans-serif;
        font-weight: 600;
        font-size: 1.7rem;
        color: #7c2d12;
        margin-bottom: 0.4rem;
    }
    .stats-title {
        font-family: 'Caveat', 'Amatic SC', 'Nunito', system-ui, sans-serif;
        font-weight: 600;
        font-size: 2rem;
        margin: 0.8rem 0 0.4rem 0;
        color: #7c2d12;
    }

    /* Enlarge tab labels like "Overview", "By Hobby", etc. */
    .stTabs button[role="tab"] {
        font-family: 'Caveat', 'Amatic SC', 'Nunito', system-ui, sans-serif !important;
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
        font-family: 'Caveat', 'Amatic SC', 'Nunito', system-ui, sans-serif;
    }
    .hobby-pill-label {
        margin-right: 0.5rem;
    }
    .hobby-pill-delete button {
        background: transparent !important;
        color: #fecaca !important;
        font-family: 'Caveat', 'Amatic SC', 'Nunito', system-ui, sans-serif;
    }

    /* All checkbox labels in handwriting */
    div.stCheckbox label {
        font-family: 'Caveat', 'Amatic SC', 'Nunito', system-ui, sans-serif !important;
        font-size: 1.15rem !important;
        color: #7c2d12 !important;
    }
    /* Only the tree-view checkbox tick in blue */
    div.stCheckbox input[id^="tree_view_toggle"] {
        accent-color: #3b82f6 !important;
    }

    /* Task tree styling */
    .task-tree {
        font-family: 'Caveat', 'Amatic SC', 'Nunito', system-ui, sans-serif;
        font-size: 1.05rem;
        padding-left: 0.4rem;
    }
    .task-tree-item {
        margin: 0.1rem 0;
    }
    .task-tree-task {
        color: #7c2d12;
        font-weight: 600;
        font-family: 'Caveat', 'Amatic SC', cursive, system-ui, sans-serif !important;
        font-size: 1.4rem !important;
    }
    /* Packet tasks: pin icon tinted amber/orange to distinguish from regular task pin */
    .task-tree-task .pin-packet {
        display: inline;
        filter: sepia(1) saturate(3) hue-rotate(15deg);
    }
    .task-tree-sub-active {
        color: #1f2933;
        font-family: 'Caveat', 'Amatic SC', cursive, system-ui, sans-serif !important;
    }
    .task-tree-sub-done {
        color: #15803d;
        text-decoration: line-through;
        opacity: 0.9;
        font-family: 'Caveat', 'Amatic SC', cursive, system-ui, sans-serif !important;
        animation: subtaskDone 0.4s ease-out;
    }
    @keyframes subtaskDone {
        from { opacity: 0.5; transform: scale(0.98); }
        to { opacity: 0.9; transform: scale(1); }
    }
    .glance-task-done {
        color: #15803d !important;
        text-decoration: line-through;
        font-family: 'Caveat', 'Amatic SC', cursive, system-ui, sans-serif !important;
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
        font-family: 'Caveat', 'Amatic SC', cursive, system-ui, sans-serif !important;
    }
    .planner-glance-sub {
        margin: 0.25rem 0;
        font-size: 1.2rem;
        line-height: 1.35;
        font-family: 'Caveat', 'Amatic SC', cursive, system-ui, sans-serif !important;
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
        font-family: 'Caveat', 'Amatic SC', cursive, system-ui, sans-serif !important;
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

    /* ═══════════════════════════════════════════════════════
       Groceries page — market / garden aesthetic
    ═══════════════════════════════════════════════════════ */
    .groceries-hero {
        font-family: 'Caveat', 'Amatic SC', cursive;
        font-size: 3rem;
        font-weight: 700;
        color: #14532d;
        margin-bottom: 0.15rem;
        letter-spacing: 0.04em;
        text-shadow: 1px 2px 0 rgba(255,255,255,0.55);
    }
    /* Shopping-list note card */
    .groceries-missing-card {
        background: linear-gradient(160deg, #fefce8 0%, #fef9c3 55%, #fde68a 100%);
        border: none;
        border-left: 5px solid #ca8a04;
        border-radius: 0 0.85rem 0.85rem 0;
        padding: 1.1rem 1.4rem 1.1rem 1.6rem;
        margin-bottom: 1.6rem;
        box-shadow: 3px 4px 14px rgba(0,0,0,0.10), inset 0 1px 0 rgba(255,255,255,0.7);
        position: relative;
    }
    .groceries-missing-card::before {
        content: "📌";
        position: absolute;
        top: -0.55rem;
        left: 1.2rem;
        font-size: 1.4rem;
        filter: drop-shadow(0 1px 1px rgba(0,0,0,0.2));
    }
    .groceries-missing-title {
        font-family: 'Caveat', 'Amatic SC', cursive;
        font-size: 1.6rem;
        font-weight: 700;
        color: #78350f;
        margin-bottom: 0.6rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .groceries-missing-list {
        font-family: 'Amatic SC', 'Caveat', cursive;
        font-size: 1.6rem;
        font-weight: 700;
        -webkit-text-stroke: 0.5px currentColor;
        color: #1c1917;
        line-height: 1.75;
    }
    .groceries-missing-list span {
        display: inline-block;
        margin-right: 0.5rem;
        margin-bottom: 0.25rem;
    }
    /* Category cards — produce-crate look */
    .groceries-category-card {
        background: linear-gradient(180deg, rgba(240,253,244,0.85) 0%, rgba(220,252,231,0.5) 100%);
        border: 1.5px solid rgba(22, 101, 52, 0.25);
        border-radius: 0.85rem;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(22, 101, 52, 0.08);
    }
    .groceries-category-name {
        font-family: 'Caveat', 'Amatic SC', cursive;
        font-size: 1.5rem;
        font-weight: 700;
        color: #14532d;
        margin-bottom: 0.5rem;
        letter-spacing: 0.03em;
    }
    /* Item rows — handwritten checklist */
    .groceries-item-row {
        font-family: 'Amatic SC', 'Caveat', cursive !important;
        font-size: 1.6rem;
        font-weight: 700;
        -webkit-text-stroke: 0.5px currentColor;
        color: #1f2933;
        padding: 0.3rem 0;
        border-bottom: 1px dashed rgba(22, 101, 52, 0.12);
        line-height: 1.5;
    }
    .groceries-item-row:last-child { border-bottom: none; }
    .groceries-item-have {
        color: #15803d;
        text-decoration: line-through;
        opacity: 0.75;
        font-family: 'Amatic SC', 'Caveat', cursive !important;
        font-size: 1.6rem;
        font-weight: 700;
        -webkit-text-stroke: 0.5px currentColor;
    }
    .groceries-empty-msg {
        font-family: 'Amatic SC', 'Caveat', cursive;
        font-size: 1.3rem;
        font-weight: 700;
        color: #78716c;
        font-style: italic;
        padding: 0.75rem 0;
    }
    .groceries-cat-label {
        font-family: 'Amatic SC', 'Caveat', cursive !important;
        font-size: 1.5rem;
        font-weight: 700;
        -webkit-text-stroke: 0.4px currentColor;
        color: #14532d;
        margin: 0.5rem 0 0.2rem 0;
        padding: 0.2rem 0.6rem;
        background: rgba(22,101,52,0.08);
        border-radius: 0.35rem;
        display: inline-block;
    }
    .groceries-section-head {
        font-family: 'Amatic SC', 'Caveat', cursive !important;
        font-size: 1.9rem;
        font-weight: 700;
        -webkit-text-stroke: 0.4px currentColor;
        color: #14532d;
        letter-spacing: 0.03em;
        margin: 0.5rem 0 0.75rem 0;
    }
    /* Style grocery category expanders: green market crate */
    [data-testid="stSidebar"] ~ * details[data-testid="stExpander"],
    details[data-testid="stExpander"]:has(> summary > div[data-testid="stExpanderToggleIcon"]) {
        border-radius: 0.7rem;
    }
    /* ═══════════════════════════════════════════════════════
       Recipes page — cookbook / recipe-card aesthetic
    ═══════════════════════════════════════════════════════ */
    .recipes-hero {
        font-family: 'Caveat', 'Amatic SC', cursive;
        font-size: 3.2rem;
        font-weight: 700;
        color: #7c2d12;
        margin-bottom: 0.15rem;
        letter-spacing: 0.04em;
        text-shadow: 1px 2px 0 rgba(255,255,255,0.55);
    }
    /* "Possible to cook" banner — satisfying green glow */
    .recipes-possible-card {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 60%, #bbf7d0 100%);
        border: none;
        border-left: 5px solid #16a34a;
        border-radius: 0 1rem 1rem 0;
        padding: 1.1rem 1.5rem;
        margin-bottom: 1.4rem;
        box-shadow: 0 2px 14px rgba(22, 101, 52, 0.18), inset 0 1px 0 rgba(255,255,255,0.7);
    }
    .recipes-possible-title {
        font-family: 'Caveat', 'Amatic SC', cursive;
        font-size: 1.7rem;
        font-weight: 700;
        color: #14532d;
        margin-bottom: 0.5rem;
    }
    .recipes-list-item { font-family: 'Caveat', 'Amatic SC', cursive; font-size: 1.4rem; font-weight: 700; color: #1f2933; }
    .recipes-badge-possible {
        background: linear-gradient(135deg, #166534, #15803d);
        color: #f0fdf4;
        padding: 0.2rem 0.6rem;
        border-radius: 0.5rem;
        font-size: 0.85rem;
        box-shadow: 0 1px 3px rgba(22,101,52,0.3);
    }
    .recipes-badge-missing {
        background: linear-gradient(135deg, #92400e, #b45309);
        color: #fff7ed;
        padding: 0.2rem 0.6rem;
        border-radius: 0.5rem;
        font-size: 0.85rem;
    }

    /* Recipe cards — recipe index card feel */
    .recipes-glance-wrap { margin-top: 1rem; }
    .recipe-card {
        margin-bottom: 1.4rem;
        border-radius: 0.85rem;
        border: 1px solid rgba(124, 45, 18, 0.18);
        border-top: 3px solid rgba(124, 45, 18, 0.35);
        background: linear-gradient(160deg, #fffdf7 0%, #fefce8 50%, #fdf6e3 100%);
        padding: 0;
        overflow: hidden;
        box-shadow: 0 3px 12px rgba(124, 45, 18, 0.12), 0 0 0 1px rgba(255,255,255,0.6) inset;
    }
    .recipe-card-header {
        font-family: 'Caveat', 'Amatic SC', cursive;
        font-weight: 700;
        font-size: 1.7rem;
        color: #7c2d12;
        padding: 0.65rem 1rem 0.5rem 1rem;
        border-bottom: 2px dashed rgba(124, 45, 18, 0.15);
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.5rem;
        background: rgba(254, 243, 199, 0.4);
    }
    .recipe-card-meta { font-size: 0.95rem; color: rgba(124, 45, 18, 0.7); font-weight: 400; }
    .recipe-ingredients-tree {
        margin: 0.5rem 0 0.75rem 0;
        padding-left: 1.25rem;
        margin-left: 1rem;
        border-left: 3px solid rgba(124, 45, 18, 0.2);
        font-size: 1.6rem;
        font-weight: 700;
        line-height: 1.5;
        font-family: 'Amatic SC', 'Caveat', cursive !important;
    }
    .recipe-ingredient {
        margin: 0.3rem 0;
        font-size: 1.6rem;
        font-weight: 700;
        -webkit-text-stroke: 0.4px currentColor;
        line-height: 1.45;
        padding: 0.3rem 0.75rem;
        border-radius: 0.5rem;
        border: 1px solid transparent;
        display: flex;
        align-items: center;
        gap: 0.4rem;
        flex-wrap: wrap;
        font-family: 'Amatic SC', 'Caveat', cursive !important;
    }
    .recipe-ingredient-have {
        color: #15803d;
        background: rgba(22, 101, 52, 0.09);
        border-color: rgba(22, 101, 52, 0.2);
    }
    .recipe-ingredient-missing {
        color: #92400e;
        background: rgba(180, 83, 9, 0.09);
        border-color: rgba(146, 64, 14, 0.2);
    }
    .recipe-ingredient-emoji { font-size: 1.2em; }
    .recipe-divider {
        margin: 0.9rem 0 0.5rem 0;
        padding-bottom: 0;
        border: none;
        border-top: 1px dashed rgba(124, 45, 18, 0.22);
        font-size: 0;
        height: 0;
    }
    .recipe-section-label {
        font-family: 'Caveat', 'Amatic SC', cursive;
        font-weight: 700;
        font-size: 1.6rem;
        color: #7c2d12;
        margin: 0.85rem 0 0.4rem 0;
    }
    /* Expanders in recipe list — index-card feel */
    .recipes-glance-wrap details {
        border-radius: 0.85rem;
        border: 1px solid rgba(124, 45, 18, 0.18);
        border-top: 3px solid rgba(124, 45, 18, 0.3);
        background: linear-gradient(160deg, #fffdf7 0%, #fefce8 60%, #fdf6e3 100%);
        box-shadow: 0 3px 10px rgba(124, 45, 18, 0.10);
        margin-bottom: 1rem;
        overflow: hidden;
    }
    .recipes-glance-wrap details summary {
        font-family: 'Caveat', 'Amatic SC', cursive !important;
        font-weight: 700 !important;
        font-size: 1.7rem !important;
        color: #7c2d12 !important;
        padding: 0.75rem 1rem !important;
        background: rgba(254, 243, 199, 0.35);
        transition: background 0.15s ease;
    }
    .recipes-glance-wrap details summary:hover {
        background: rgba(254, 243, 199, 0.65) !important;
    }
    .recipes-glance-wrap details[open] summary {
        border-bottom: 2px dashed rgba(124, 45, 18, 0.15);
        background: rgba(254, 243, 199, 0.55);
    }
    .recipes-glance-wrap .recipe-card { border: none; border-radius: 0; background: transparent; box-shadow: none; padding: 0 1rem 1rem 1rem; }

    /* Recipes at a Glance */
    .glance-recipes-marker { display: block !important; height: 0 !important; margin: 0 !important; padding: 0 !important; overflow: hidden !important; }
    .glance-recipe-badge {
        font-size: 0.85rem;
        margin-bottom: 0.4rem;
        padding: 0.2rem 0.55rem;
        border-radius: 0.4rem;
        background: rgba(22, 101, 52, 0.13);
        color: #14532d;
        font-family: 'Nunito', system-ui, sans-serif;
        font-weight: 700;
    }
    .glance-recipe-badge.glance-recipe-missing { background: rgba(146, 64, 14, 0.13); color: #92400e; }
    .glance-recipe-ing {
        margin: 0.2rem 0;
        font-size: 1.4rem;
        font-weight: 700;
        line-height: 1.35;
        padding: 0.2rem 0;
        font-family: 'Amatic SC', 'Caveat', cursive !important;
    }
    .glance-recipe-ing.recipe-ingredient-have { color: #15803d; }
    .glance-recipe-ing.recipe-ingredient-missing { color: #92400e; }
    @media (max-width: 768px) {
        .glance-recipes-marker + [data-testid="stHorizontalBlock"] { display: flex !important; flex-wrap: nowrap !important; overflow-x: auto !important; -webkit-overflow-scrolling: touch; scrollbar-width: thin; margin-left: -0.5rem !important; margin-right: -0.5rem !important; padding: 0.25rem 0.5rem !important; }
        .glance-recipes-marker + [data-testid="stHorizontalBlock"] [data-testid="column"] { flex: 0 0 auto !important; min-width: 110px !important; }
        .glance-recipes-marker + [data-testid="stHorizontalBlock"] .section-title { font-size: 0.95rem !important; white-space: nowrap !important; }
    }

    /* ═══════════════════════════════════════════════════════
       Chef AI page
    ═══════════════════════════════════════════════════════ */
    .chef-hero {
        font-family: 'Caveat', 'Amatic SC', cursive;
        font-size: 3rem;
        font-weight: 700;
        color: #1e3a5f;
        letter-spacing: 0.04em;
        text-shadow: 1px 2px 0 rgba(255,255,255,0.6);
        margin-bottom: 0.1rem;
    }
    .chef-subtitle {
        font-family: 'Caveat', 'Amatic SC', cursive;
        font-size: 1.4rem;
        color: #334e68;
        margin-bottom: 1.2rem;
        opacity: 0.9;
    }
    /* Welcome banner */
    .chef-welcome {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 55%, #bfdbfe 100%);
        border-left: 5px solid #3b82f6;
        border-radius: 0 1rem 1rem 0;
        padding: 1.1rem 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 12px rgba(59,130,246,0.13), inset 0 1px 0 rgba(255,255,255,0.7);
    }
    .chef-welcome-title {
        font-family: 'Caveat', 'Amatic SC', cursive;
        font-size: 1.55rem;
        font-weight: 700;
        color: #1e40af;
        margin-bottom: 0.35rem;
    }
    .chef-welcome-tips {
        font-family: 'Caveat', 'Amatic SC', cursive;
        font-size: 1.25rem;
        color: #1e3a5f;
        line-height: 1.7;
    }
    /* Recipe suggestion card */
    .chef-recipe-card {
        background: linear-gradient(160deg, #fffdf7 0%, #fefce8 50%, #fdf6e3 100%);
        border: 1px solid rgba(124, 45, 18, 0.18);
        border-top: 3px solid #f59e0b;
        border-radius: 0.85rem;
        padding: 1.25rem 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 3px 14px rgba(245,158,11,0.13);
    }
    .chef-recipe-card-title {
        font-family: 'Caveat', 'Amatic SC', cursive;
        font-size: 1.9rem;
        font-weight: 700;
        color: #92400e;
        margin-bottom: 0.6rem;
        letter-spacing: 0.02em;
    }
    .chef-ing-row {
        font-family: 'Amatic SC', 'Caveat', cursive;
        font-size: 1.4rem;
        font-weight: 700;
        padding: 0.2rem 0;
    }
    .chef-ing-existing { color: #15803d; }
    .chef-ing-new { color: #92400e; }
    /* Clear chat button */
    .chef-clear-btn button {
        background: transparent !important;
        border: 1px solid rgba(59,130,246,0.3) !important;
        color: #3b82f6 !important;
        font-family: 'Caveat', 'Amatic SC', cursive !important;
        font-size: 1rem !important;
        padding: 0.2rem 0.75rem !important;
        border-radius: 0.5rem !important;
    }
    .chef-clear-btn button:hover {
        background: rgba(59,130,246,0.08) !important;
        border-color: #3b82f6 !important;
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

# Sidebar navigation — main + kitchen subsection
nav_main = ["Add Hobby", "Statistics", "Weekly Planner", "General Tasks"]
nav_kitchen = ["Groceries", "Recipes", "Chef AI"]
all_nav = nav_main + nav_kitchen

current_page = st.query_params.get("page", nav_main[0])
if current_page not in all_nav:
    current_page = nav_main[0]

# Track previous radio values to detect which group the user clicked
_prev_main = st.session_state.get("_nav_main_sel")
_prev_kitchen = st.session_state.get("_nav_kitchen_sel")

main_idx = nav_main.index(current_page) if current_page in nav_main else None
kitchen_idx = nav_kitchen.index(current_page) if current_page in nav_kitchen else None

st.sidebar.markdown('<div class="sidebar-app-title">🎯 Hobby Tracker</div>', unsafe_allow_html=True)
_main_sel = st.sidebar.radio("", nav_main, index=main_idx, key="sidebar_main", label_visibility="collapsed")
st.sidebar.markdown('<div class="sidebar-kitchen-divider">🛒 Kitchen</div>', unsafe_allow_html=True)
_kitchen_sel = st.sidebar.radio("", nav_kitchen, index=kitchen_idx, key="sidebar_kitchen", label_visibility="collapsed")

st.session_state["_nav_main_sel"] = _main_sel
st.session_state["_nav_kitchen_sel"] = _kitchen_sel

# Detect navigation: whichever selection changed from the previous run is the new page
if _main_sel is not None and _main_sel != _prev_main:
    page = _main_sel
elif _kitchen_sel is not None and _kitchen_sel != _prev_kitchen:
    page = _kitchen_sel
else:
    page = current_page

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

    # Persist weekly time from entries and show full history
    if hasattr(db, "sync_weekly_hobby_time_from_entries"):
        db.sync_weekly_hobby_time_from_entries()
    st.markdown(
        '<div class="section-title">⏱️ Time spent per hobby (saved by week)</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Totals are stored per calendar week (Sunday–Saturday) from your logged entries. "
        "They update whenever you open Statistics."
    )
    df_wh = db.get_weekly_hobby_time_history() if hasattr(db, "get_weekly_hobby_time_history") else None
    df_wt = db.get_weekly_total_minutes_history() if hasattr(db, "get_weekly_total_minutes_history") else None
    if df_wh is not None and not df_wh.empty:
        def _week_label(ws: str) -> str:
            try:
                sun = datetime.datetime.strptime(ws, "%Y-%m-%d").date()
                sat = sun + datetime.timedelta(days=6)
                return f"{sun.strftime('%d %b')} – {sat.strftime('%d %b %Y')}"
            except (ValueError, TypeError):
                return str(ws)

        df_wh = df_wh.copy()
        df_wh["week_label"] = df_wh["week_start"].map(_week_label)
        week_order = sorted(df_wh["week_start"].unique().tolist())
        label_map = {ws: _week_label(ws) for ws in week_order}
        week_labels_ordered = [label_map[ws] for ws in week_order]

        try:
            chart_stack = (
                alt.Chart(df_wh, width=700, height=320)
                .mark_bar()
                .encode(
                    x=alt.X("week_label:N", title="Week", sort=week_labels_ordered),
                    y=alt.Y("minutes:Q", title="Minutes"),
                    color=alt.Color("hobby:N", title="Hobby"),
                    tooltip=["week_label", "hobby", "minutes"],
                )
            )
        except (AttributeError, TypeError):
            chart_stack = (
                alt.Chart(df_wh, width=600, height=320)
                .mark_bar()
                .encode(
                    x=alt.X("week_label:N", title="Week", sort=week_labels_ordered),
                    y=alt.Y("minutes:Q", title="Minutes"),
                    color=alt.Color("hobby:N", title="Hobby"),
                    tooltip=["week_label", "hobby", "minutes"],
                )
            )
        st.altair_chart(chart_stack, use_container_width=True)

        if df_wt is not None and not df_wt.empty:
            df_wt = df_wt.copy()
            df_wt["week_label"] = df_wt["week_start"].map(_week_label)
            try:
                chart_total = (
                    alt.Chart(df_wt, width=700, height=240)
                    .mark_line(point=True, strokeWidth=3)
                    .encode(
                        x=alt.X("week_label:N", title="Week", sort=week_labels_ordered),
                        y=alt.Y("total_minutes:Q", title="Total minutes (all hobbies)"),
                        tooltip=["week_label", "total_minutes"],
                    )
                    .properties(title="Total time across all hobbies per week")
                )
            except (AttributeError, TypeError):
                chart_total = (
                    alt.Chart(df_wt, width=600, height=240)
                    .mark_bar()
                    .encode(
                        x=alt.X("week_label:N", title="Week", sort=week_labels_ordered),
                        y=alt.Y("total_minutes:Q", title="Total minutes (all hobbies)"),
                        tooltip=["week_label", "total_minutes"],
                    )
                )
            st.altair_chart(chart_total, use_container_width=True)
    else:
        st.info("No weekly time history yet. Log minutes on hobbies (entries) and open Statistics again to build the graph.")

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
    with st.expander("Plan a new weekly task", expanded=False, key="planner_add_task_exp"):
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
    with st.expander("Create / edit packets", expanded=False, key="planner_packets_exp"):
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
        with st.expander("Add packet to week", expanded=False, key="planner_add_packet_week_exp"):
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
                with st.expander(f"{done_status} {title}", expanded=False, key=f"gen_task_exp_{first_id}"):
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
                with st.expander(f"{done_status} {pkt_name}: {item_title}", expanded=False, key=f"pkt_task_exp_{first_planner_id}"):
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
                with st.expander(f"{done_status} {t[2]} • {total_minutes} min", expanded=False, key=f"task_exp_{t_id}"):
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
            # One-shot: only expand a category on the run immediately after add/remove/update (so no category opens by default on fresh load).
            expand_cat_id = st.session_state.pop("grocery_keep_open_cat_id", None)
            for cat_id, cat_name, _ in categories:
                items = db.get_grocery_items(cat_id)
                if expand_cat_id is not None and expand_cat_id == cat_id:
                    st.session_state[f"grocery_cat_{cat_id}"] = True
                with st.expander(f"**{cat_name}** ({len(items)} items)", expanded=False, key=f"grocery_cat_{cat_id}"):
                    new_item = st.text_input("Add item", placeholder="New item…", key=f"grocery_new_{cat_id}", label_visibility="collapsed")
                    add_col, _ = st.columns([1, 4])
                    with add_col:
                        if st.button("Add", key=f"grocery_add_item_{cat_id}") and new_item.strip():
                            new_id = db.add_grocery_item(cat_id, new_item.strip())
                            if new_id is None:
                                st.error("An ingredient with this name already exists.")
                            else:
                                st.session_state["grocery_keep_open_cat_id"] = cat_id
                                st.query_params["page"] = "Groceries"
                                st.toast(f"Added to {cat_name}.")
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
                                    st.session_state["grocery_keep_open_cat_id"] = cat_id
                                    st.query_params["page"] = "Groceries"
                                    st.toast("Item removed.")
                                    st.rerun()
                            if checked != bool(have_at_home):
                                db.set_grocery_item_have_at_home(item_id, checked)
                                st.session_state["grocery_keep_open_cat_id"] = cat_id
                                st.query_params["page"] = "Groceries"
                                st.toast("Updated.")
                                st.rerun()

                    if st.button("Delete category", key=f"grocery_del_cat_{cat_id}"):
                        db.delete_grocery_category(cat_id)
                        if st.session_state.get("grocery_keep_open_cat_id") == cat_id:
                            del st.session_state["grocery_keep_open_cat_id"]
                        st.toast(f"Category «{cat_name}» and its items removed.")
                        st.query_params["page"] = "Groceries"
                        st.rerun()

# -------------------
# Recipes Page
# -------------------
elif page == "Recipes":
    if not hasattr(db, "get_recipes"):
        st.error("Recipes feature is not loaded. Redeploy or restart the app so the latest database module is used.")
    else:
        st.markdown('<div class="recipes-hero">📖 Recipes</div>', unsafe_allow_html=True)
        st.caption("Build recipes from your grocery list. A recipe is possible to cook when you have all its ingredients at home.")

        possible = db.get_recipes_possible_to_cook() if hasattr(db, "get_recipes_possible_to_cook") else []

        # Add recipe
        with st.expander("➕ Add new recipe", expanded=False, key="recipe_add_exp"):
            new_name = st.text_input("Recipe name", key="recipe_new_name", placeholder="e.g. Pasta carbonara")
            new_instructions = st.text_area("Instructions (optional)", key="recipe_new_instructions", placeholder="Steps…", height=100)
            if st.button("Create recipe", key="recipe_create_btn") and new_name.strip():
                rid = db.add_recipe(new_name.strip(), new_instructions.strip())
                if rid is None:
                    st.error("A recipe with this name already exists.")
                else:
                    st.session_state["recipe_expanded_id"] = rid
                    st.toast("Recipe created. Add ingredients below.")
                    st.query_params["page"] = "Recipes"
                    st.rerun()

        all_recipes = db.get_recipes()
        if not all_recipes:
            st.info("No recipes yet. Create one in «Add new recipe» above, then add ingredients from your grocery list.")
        else:
            all_items = db.get_all_grocery_items() if hasattr(db, "get_all_grocery_items") else []
            possible_ids = {r[0] for r in possible}

            # Recipes at a Glance (same layout as Weekly Planner – columns per recipe)
            st.subheader("Recipes at a Glance")
            st.markdown('<div class="glance-recipes-marker" aria-hidden="true"></div>', unsafe_allow_html=True)
            n_glance = min(len(all_recipes), 7)
            glance_recipes = all_recipes[:n_glance]
            glance_cols = st.columns(n_glance)
            for i, (rid, rname, rinstructions) in enumerate(glance_recipes):
                with glance_cols[i]:
                    st.markdown(
                        f"<div class='section-title'>🍳 {rname}</div>",
                        unsafe_allow_html=True,
                    )
                    ing_list = db.get_recipe_ingredients(rid)
                    is_possible = rid in possible_ids and len(ing_list) > 0
                    if is_possible:
                        st.markdown('<div class="glance-recipe-badge">✅ Possible to cook</div>', unsafe_allow_html=True)
                    elif ing_list:
                        missing_count = sum(1 for _ in (x for x in ing_list if not x[4]))
                        st.markdown(f'<div class="glance-recipe-badge glance-recipe-missing">🛒 Missing {missing_count}</div>', unsafe_allow_html=True)
                    if not ing_list:
                        st.caption("No ingredients yet")
                    ing_label = f"🥗 Ingredients ({len(ing_list)})" if ing_list else "🥗 Ingredients"
                    glance_expanded = st.session_state.get(f"glance_ing_{rid}", False)
                    with st.expander(ing_label, expanded=glance_expanded, key=f"glance_ing_{rid}"):
                        if ing_list:
                            max_ing = 12
                            for _, _gi, iname, cname, have in ing_list[:max_ing]:
                                klass = "recipe-ingredient-have" if have else "recipe-ingredient-missing"
                                icon = "✅" if have else "🛒"
                                st.markdown(
                                    f'<div class="glance-recipe-ing {klass}">{icon} {iname} <span style="color:rgba(124,45,18,0.6);font-size:0.85em;">({cname})</span></div>',
                                    unsafe_allow_html=True,
                                )
                            if len(ing_list) > max_ing:
                                st.caption(f"… +{len(ing_list) - max_ing} more")
                        else:
                            st.caption("Add ingredients in the list below.")
            if len(all_recipes) > n_glance:
                st.caption(f"First {n_glance} recipes above; expand any recipe below to edit.")

            st.markdown('<div class="section-title">📋 Your recipes</div>', unsafe_allow_html=True)
            st.markdown('<div class="recipes-glance-wrap">', unsafe_allow_html=True)
            keep_expanded = st.session_state.get("recipe_expanded_id")
            for rid, rname, rinstructions in all_recipes:
                ing_list = db.get_recipe_ingredients(rid)
                missing_count = sum(1 for _ in (x for x in ing_list if not x[4]))
                is_possible = rid in possible_ids and len(ing_list) > 0
                badge = " · ✅ Possible to cook" if is_possible else (f" · ⚠️ Missing {missing_count} ingredient(s)" if ing_list and missing_count > 0 else "")
                ing_count = f" — 📝 {len(ing_list)} ingredients" if ing_list else " — 📝 no ingredients yet"
                expander_label = f"🍳 {rname}{ing_count}{badge}"
                if keep_expanded == rid:
                    st.session_state[f"recipe_exp_{rid}"] = True
                with st.expander(expander_label, expanded=False, key=f"recipe_exp_{rid}"):
                    st.markdown('<div class="recipe-card">', unsafe_allow_html=True)
                    st.markdown('<div class="recipe-section-label">🥗 Ingredients</div>', unsafe_allow_html=True)
                    if ing_list:
                        st.markdown('<div class="recipe-ingredients-tree">', unsafe_allow_html=True)
                        for _, _gi, iname, cname, have in ing_list:
                            klass = "recipe-ingredient-have" if have else "recipe-ingredient-missing"
                            icon = "✅" if have else "🛒"
                            st.markdown(f'<div class="recipe-ingredient {klass}"><span class="recipe-ingredient-emoji">{icon}</span> {iname} <span style="color:rgba(124,45,18,0.6);font-size:0.9em;">({cname})</span></div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        if not is_possible and missing_count > 0:
                            st.caption(f"🛒 Missing {missing_count} ingredient(s) — check them off in Groceries.")
                    else:
                        st.caption("➕ Add ingredients below so this recipe appears in «Possible to cook» when you have them all.")

                    st.markdown('<div class="recipe-divider">—</div>', unsafe_allow_html=True)
                    st.markdown('<div class="recipe-section-label">➕ Add ingredient</div>', unsafe_allow_html=True)
                    if all_items:
                        task_search = st.text_input("Search ingredients", placeholder="Filter by name...", key=f"recipe_ing_search_{rid}")
                        current_ing_ids = db.get_recipe_ingredient_ids(rid)
                        search_lower = (task_search or "").strip().lower()
                        if search_lower:
                            filtered = [(item_id, iname, cname) for item_id, iname, _cid, cname, _ in all_items if item_id not in current_ing_ids and (search_lower in iname.lower() or search_lower in cname.lower())]
                        else:
                            filtered = []
                        if not filtered:
                            if search_lower:
                                st.markdown("🔍 *No ingredients match your search, or they’re already in this recipe.")
                            else:
                                st.markdown("⌨️ *Type above to search for ingredients to add.*")
                        else:
                            for item_id, iname, cname in filtered[:30]:
                                row_cols = st.columns([3, 0.6])
                                with row_cols[0]:
                                    st.markdown(f"🥬 **{iname}** *({cname})*")
                                with row_cols[1]:
                                    if st.button("Add", key=f"recipe_add_ing_{rid}_{item_id}"):
                                        db.add_recipe_ingredient(rid, item_id)
                                        st.session_state["recipe_expanded_id"] = rid
                                        st.toast(f"Added {iname}.")
                                        st.query_params["page"] = "Recipes"
                                        st.rerun()
                            if len(filtered) > 30:
                                st.caption(f"… and {len(filtered) - 30} more. Refine your search to narrow.")

                    st.markdown('<div class="recipe-divider">—</div>', unsafe_allow_html=True)
                    st.markdown('<div class="recipe-section-label">🆕 Ingredient not in the list? Add it and link to a category</div>', unsafe_allow_html=True)
                    new_ing_name = st.text_input("New ingredient name", key=f"recipe_new_ing_name_{rid}", placeholder="e.g. Parmesan")
                    categories = db.get_grocery_categories()
                    cat_options = [(cid, cname) for cid, cname, _ in categories]
                    if cat_options:
                        new_ing_cat = st.selectbox("Category", options=range(len(cat_options)), format_func=lambda i: cat_options[i][1], key=f"recipe_new_ing_cat_{rid}")
                        if st.button("Add ingredient to groceries and to this recipe", key=f"recipe_new_ing_btn_{rid}") and new_ing_name.strip():
                            cid = cat_options[new_ing_cat][0]
                            new_id = db.add_grocery_item(cid, new_ing_name.strip())
                            if new_id is None:
                                st.error("An ingredient with this name already exists.")
                            else:
                                db.add_recipe_ingredient(rid, new_id)
                                st.session_state["recipe_expanded_id"] = rid
                                st.toast(f"Added «{new_ing_name.strip()}» to groceries and to recipe.")
                                st.query_params["page"] = "Recipes"
                                st.rerun()
                    else:
                        st.caption("Create at least one category in Groceries first.")

                    st.markdown('<div class="recipe-divider">—</div>', unsafe_allow_html=True)
                    st.markdown('<div class="recipe-section-label">✂️ Remove ingredient</div>', unsafe_allow_html=True)
                    for ri_id, gi_id, iname, cname, _ in ing_list:
                        if st.button(f"🗑️ Remove {iname}", key=f"recipe_remove_ing_{rid}_{gi_id}"):
                            db.remove_recipe_ingredient(rid, gi_id)
                            st.session_state["recipe_expanded_id"] = rid
                            st.toast("Removed.")
                            st.query_params["page"] = "Recipes"
                            st.rerun()

                    if st.button("🗑️ Delete recipe", key=f"recipe_del_{rid}"):
                        db.delete_recipe(rid)
                        if st.session_state.get("recipe_expanded_id") == rid:
                            del st.session_state["recipe_expanded_id"]
                        st.toast(f"Recipe «{rname}» deleted.")
                        st.query_params["page"] = "Recipes"
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

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

                with st.expander("Add to glance (schedule a day, then move to Weekly Planner)", expanded=False, key=f"general_glance_exp_{tid}"):
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

# -------------------
# Chef AI Page
# -------------------
elif page == "Chef AI":
    import json

    oai = _get_openai_client()

    # ── hero ───────────────────────────────────────────────────────────
    st.markdown('<div class="chef-hero">🤖 Chef AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="chef-subtitle">Your personal AI cooking assistant — always ready to inspire!</div>', unsafe_allow_html=True)

    if oai is None:
        st.warning(
            "🔑 **OpenAI API key not configured.** "
            "Add your key to `.streamlit/secrets.toml` as `OPENAI_API_KEY = \"sk-...\"`, "
            "then restart the app. On Streamlit Cloud, add it via **App Settings → Secrets**."
        )
    else:
        # ── session state ──────────────────────────────────────────────
        if "chef_messages" not in st.session_state:
            st.session_state["chef_messages"] = []
        if "chef_pending_recipe" not in st.session_state:
            st.session_state["chef_pending_recipe"] = None

        # ── welcome banner (only when chat is empty) ───────────────────
        if not st.session_state["chef_messages"] and not st.session_state["chef_pending_recipe"]:
            st.markdown(
                """
                <div class="chef-welcome">
                  <div class="chef-welcome-title">👨‍🍳 Hi! I'm Chef AI — what shall we cook today?</div>
                  <div class="chef-welcome-tips">
                    Here are some things you can ask me:<br>
                    🍝 &nbsp;<em>Suggest a quick weeknight pasta</em><br>
                    🥗 &nbsp;<em>Give me a healthy salad with what I have</em><br>
                    🧁 &nbsp;<em>What can I bake with eggs, flour and butter?</em><br>
                    🔄 &nbsp;<em>What's a substitute for heavy cream?</em><br>
                    🌶️ &nbsp;<em>Make last week's chicken recipe spicier</em>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ── tool definition ────────────────────────────────────────────
        SUGGEST_TOOL = {
            "type": "function",
            "function": {
                "name": "suggest_recipe",
                "description": "Propose a recipe to add to the user's recipe book.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Recipe name"},
                        "instructions": {"type": "string", "description": "Concise step-by-step cooking instructions"},
                        "ingredients": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "category": {"type": "string", "description": "Grocery category (e.g. Dairy, Produce, Meat)"}
                                },
                                "required": ["name", "category"]
                            }
                        }
                    },
                    "required": ["name", "instructions", "ingredients"]
                }
            }
        }

        def _build_system_prompt():
            cats = db.get_grocery_categories()
            items = db.get_all_grocery_items() if hasattr(db, "get_all_grocery_items") else []
            cat_list = ", ".join(c[1] for c in cats) if cats else "none yet"
            item_list = ", ".join(i[1] for i in items[:80]) if items else "none yet"
            return (
                "You are Chef AI, a warm, enthusiastic, and creative cooking assistant embedded in a personal recipe tracker. "
                "Use a friendly, encouraging tone. Include a fun food emoji or two in your replies. "
                "Keep responses concise and practical — no long essays.\n\n"
                f"The user's existing grocery categories: {cat_list}\n"
                f"The user's existing grocery ingredients: {item_list}\n\n"
                "When the user asks for a recipe suggestion (or when it's natural to offer one), "
                "call the suggest_recipe() function with the full structured recipe. "
                "Prefer reusing existing ingredient names and categories where sensible. "
                "You may also chat freely — answer cooking questions, give substitution tips, discuss flavor ideas — without calling the function."
            )

        def _call_openai(user_message: str):
            messages = [{"role": "system", "content": _build_system_prompt()}]
            messages += st.session_state["chef_messages"]
            messages.append({"role": "user", "content": user_message})
            response = oai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=[SUGGEST_TOOL],
                tool_choice="auto",
            )
            return response.choices[0].message

        # ── chat history ───────────────────────────────────────────────
        for m in st.session_state["chef_messages"]:
            if m["role"] in ("user", "assistant") and isinstance(m.get("content"), str):
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

        # ── pending recipe card ────────────────────────────────────────
        pending = st.session_state.get("chef_pending_recipe")
        if pending:
            all_items = db.get_all_grocery_items() if hasattr(db, "get_all_grocery_items") else []
            existing_lower = {i[1].strip().lower(): (i[0], i[2], i[3]) for i in all_items}
            all_cats = db.get_grocery_categories()
            cat_options = [(c[0], c[1]) for c in all_cats]
            cat_names = [c[1] for c in cat_options]

            new_ingredients, existing_links = [], []
            for ing in pending["ingredients"]:
                key = ing["name"].strip().lower()
                if key in existing_lower:
                    existing_links.append(existing_lower[key][0])
                else:
                    new_ingredients.append(ing)

            st.markdown(
                f'<div class="chef-recipe-card"><div class="chef-recipe-card-title">🍽️ {pending["name"]}</div></div>',
                unsafe_allow_html=True,
            )

            with st.form("chef_add_recipe_form"):
                col_l, col_r = st.columns([3, 2])
                with col_l:
                    st.markdown("**✏️ Recipe name**")
                    recipe_name = st.text_input("Recipe name", value=pending["name"], label_visibility="collapsed", key="chef_recipe_name")
                with col_r:
                    st.markdown(f"**🥗 Ingredients: {len(existing_links)} existing · {len(new_ingredients)} new**")

                st.markdown("**📋 Instructions**")
                recipe_instructions = st.text_area("Instructions", value=pending.get("instructions", ""), label_visibility="collapsed", key="chef_recipe_instructions", height=130)

                if existing_links:
                    st.markdown(f"**✅ Already in your grocery list** — will be linked automatically:")
                    for item_id in existing_links:
                        match = next((i for i in all_items if i[0] == item_id), None)
                        if match:
                            st.markdown(f'<div class="chef-ing-row chef-ing-existing">✅ &nbsp;{match[1]} <span style="opacity:0.6;font-size:0.85em;">({match[3]})</span></div>', unsafe_allow_html=True)

                NEW_CAT_OPTION = "➕ New category…"
                cat_sel_inputs, new_cats_inputs = {}, {}
                if new_ingredients:
                    st.markdown("**🆕 New ingredients — pick a category for each:**")
                    hdr_col, hdr_cat = st.columns([2, 3])
                    hdr_col.caption("🧂 Ingredient")
                    hdr_cat.caption("📂 Category")
                    for ing in new_ingredients:
                        suggested = ing.get("category", "")
                        default_idx = len(cat_names)  # NEW_CAT_OPTION
                        for ci, cname in enumerate(cat_names):
                            if suggested.strip().lower() == cname.strip().lower():
                                default_idx = ci
                                break
                        col_name, col_cat = st.columns([2, 3])
                        with col_name:
                            st.markdown(f'<div class="chef-ing-row chef-ing-new">🆕 &nbsp;{ing["name"]}</div>', unsafe_allow_html=True)
                            st.text_input("Ingredient", value=ing["name"], key=f"chef_ing_name_{ing['name']}", label_visibility="collapsed")
                        with col_cat:
                            st.selectbox("Category", options=cat_names + [NEW_CAT_OPTION], index=default_idx, key=f"chef_ing_cat_{ing['name']}", label_visibility="collapsed")
                            st.text_input("New category name", value=suggested if default_idx == len(cat_names) else "", placeholder="e.g. Spices & Herbs…", key=f"chef_newcat_{ing['name']}", label_visibility="collapsed")
                        cat_sel_inputs[ing["name"]] = f"chef_ing_cat_{ing['name']}"
                        new_cats_inputs[ing["name"]] = f"chef_newcat_{ing['name']}"

                sub_col, dis_col = st.columns([2, 1])
                with sub_col:
                    submitted = st.form_submit_button("🍳 Add to my recipes", type="primary", use_container_width=True)
                with dis_col:
                    dismissed = st.form_submit_button("✖ Dismiss", use_container_width=True)

            if dismissed:
                st.session_state["chef_pending_recipe"] = None
                st.rerun()

            if submitted:
                errors = []
                resolved_item_ids = list(existing_links)
                created_cats = {}

                for ing in new_ingredients:
                    ing_name_final = st.session_state.get(f"chef_ing_name_{ing['name']}", ing["name"]).strip()
                    cat_sel = st.session_state.get(f"chef_ing_cat_{ing['name']}", "")

                    if cat_sel == NEW_CAT_OPTION:
                        new_cat_name = st.session_state.get(f"chef_newcat_{ing['name']}", "").strip()
                        if not new_cat_name:
                            errors.append(f"⚠️ Please enter a category name for **{ing_name_final}**.")
                            continue
                        nc_key = new_cat_name.lower()
                        if nc_key not in created_cats:
                            existing_cat = next((c[0] for c in all_cats if c[1].strip().lower() == nc_key), None)
                            if existing_cat:
                                created_cats[nc_key] = existing_cat
                            else:
                                db.add_grocery_category(new_cat_name)
                                fresh_cats = db.get_grocery_categories()
                                new_id = next((c[0] for c in fresh_cats if c[1].strip().lower() == nc_key), None)
                                created_cats[nc_key] = new_id
                        cat_id = created_cats[nc_key]
                    else:
                        cat_id = next((c[0] for c in cat_options if c[1] == cat_sel), None)
                        if cat_id is None:
                            errors.append(f"⚠️ Could not find category for **{ing_name_final}**.")
                            continue

                    new_item_id = db.add_grocery_item(cat_id, ing_name_final)
                    if new_item_id is None:
                        fresh_items = db.get_all_grocery_items() if hasattr(db, "get_all_grocery_items") else []
                        new_item_id = next((i[0] for i in fresh_items if i[1].strip().lower() == ing_name_final.lower()), None)
                    if new_item_id:
                        resolved_item_ids.append(new_item_id)

                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    rname_final = recipe_name.strip() or pending["name"]
                    rid = db.add_recipe(rname_final, recipe_instructions.strip())
                    if rid is None:
                        st.error(f"A recipe named **{rname_final}** already exists. Rename it above.")
                    else:
                        for item_id in resolved_item_ids:
                            db.add_recipe_ingredient(rid, item_id)
                        st.session_state["chef_pending_recipe"] = None
                        st.session_state["recipe_expanded_id"] = rid
                        st.toast(f"🎉 «{rname_final}» added with {len(resolved_item_ids)} ingredients!")
                        st.query_params["page"] = "Recipes"
                        st.rerun()

        # ── chat input + clear button ──────────────────────────────────
        if st.session_state["chef_messages"]:
            st.markdown('<div class="chef-clear-btn">', unsafe_allow_html=True)
            if st.button("🗑️ Clear conversation", key="chef_clear"):
                st.session_state["chef_messages"] = []
                st.session_state["chef_pending_recipe"] = None
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        user_input = st.chat_input("💬 Ask for a recipe, tips, substitutions…")
        if user_input:
            st.session_state["chef_messages"].append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("👨‍🍳 Chef AI is cooking up an answer…"):
                    try:
                        msg = _call_openai(user_input)
                    except Exception as e:
                        st.error(f"OpenAI error: {e}")
                        st.stop()

            if msg.tool_calls:
                tool_call = msg.tool_calls[0]
                if tool_call.function.name == "suggest_recipe":
                    try:
                        recipe_data = json.loads(tool_call.function.arguments)
                        st.session_state["chef_pending_recipe"] = recipe_data
                    except Exception:
                        recipe_data = {"name": "Recipe"}
                    reply_text = msg.content or f"🍽️ Here's my suggestion for **{recipe_data.get('name', 'this recipe')}**! Review the ingredients below, tweak anything you like, then hit **Add to my recipes**."
                    st.session_state["chef_messages"].append({"role": "assistant", "content": reply_text})
                    with st.chat_message("assistant"):
                        st.markdown(reply_text)
            elif msg.content:
                st.session_state["chef_messages"].append({"role": "assistant", "content": msg.content})
                with st.chat_message("assistant"):
                    st.markdown(msg.content)

            st.rerun()
