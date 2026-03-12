import sqlite3
import pandas as pd
from datetime import date, timedelta

DB_PATH = "data/hobbies.db"


def get_connection():
    # Increase timeout to avoid locked errors in Streamlit
    return sqlite3.connect(DB_PATH, timeout=10)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # ----------------------
    # Hobbies table
    # ----------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hobbies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """)

    # ----------------------
    # Entries table
    # ----------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hobby_id INTEGER,
        date TEXT,
        minutes INTEGER,
        notes TEXT,
        points INTEGER
    )
    """)

    # ----------------------
    # Tasks table
    # ----------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
                                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                                         hobby_id INTEGER NOT NULL,
                                         name TEXT NOT NULL,
                                         done INTEGER DEFAULT 0,
                                         minutes INTEGER DEFAULT 0,
                                         points INTEGER DEFAULT 0,
                                         FOREIGN KEY(hobby_id) REFERENCES hobbies(id)
    )
    """)

    # ----------------------
    # Subtasks table
    # ----------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subtasks (
                                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                                            task_id INTEGER NOT NULL,
                                            name TEXT NOT NULL,
                                            done INTEGER DEFAULT 0,
                                            minutes INTEGER DEFAULT 0,
                                            points INTEGER DEFAULT 0,
                                            FOREIGN KEY(task_id) REFERENCES tasks(id)
    )
    """)

    # ----------------------
    # Recurring tasks table
    # ----------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recurring_tasks (
                                                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                   hobby_id INTEGER NOT NULL,
                                                   name TEXT NOT NULL,
                                                   minutes INTEGER DEFAULT 0,
                                                   points INTEGER DEFAULT 0,
                                                   frequency TEXT NOT NULL,
                                                   last_created_date TEXT,
                                                   FOREIGN KEY(hobby_id) REFERENCES hobbies(id)
    )
    """)

    # ----------------------
    # Weekly planner tables
    # ----------------------
    # High-level tasks tied to a specific date (for weekly planning)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS planner_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        title TEXT NOT NULL,
        notes TEXT,
        done INTEGER DEFAULT 0,
        frequency TEXT DEFAULT 'once', -- once, daily, weekly
        packet_id INTEGER,
        minutes INTEGER DEFAULT 0,
        hobby_id INTEGER,
        points INTEGER DEFAULT 0,
        task_id INTEGER
    )
    """)

    # Packets (templates) of tasks, e.g. "Self care"
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS planner_packets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS planner_packet_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        packet_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        FOREIGN KEY(packet_id) REFERENCES planner_packets(id)
    )
    """)

    # Ensure newer columns exist in planner_tasks for older DBs
    cursor.execute("PRAGMA table_info(planner_tasks)")
    cols = [row[1] for row in cursor.fetchall()]
    if "minutes" not in cols:
        cursor.execute("ALTER TABLE planner_tasks ADD COLUMN minutes INTEGER DEFAULT 0")
    if "hobby_id" not in cols:
        cursor.execute("ALTER TABLE planner_tasks ADD COLUMN hobby_id INTEGER")
    if "points" not in cols:
        cursor.execute("ALTER TABLE planner_tasks ADD COLUMN points INTEGER DEFAULT 0")
    if "task_id" not in cols:
        cursor.execute("ALTER TABLE planner_tasks ADD COLUMN task_id INTEGER")
    if "scheduled_time" not in cols:
        cursor.execute("ALTER TABLE planner_tasks ADD COLUMN scheduled_time TEXT")

    # ----------------------
    # General tasks (no day, no time – standalone list for General Tasks page)
    # ----------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS general_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        done INTEGER DEFAULT 0
    )
    """)

    # Seed a default "Self care" packet if it doesn't exist yet
    cursor.execute("SELECT id FROM planner_packets WHERE name = ?", ("Self care",))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO planner_packets (name) VALUES (?)", ("Self care",))
        packet_id = cursor.lastrowid
        cursor.executemany(
            "INSERT INTO planner_packet_items (packet_id, title) VALUES (?, ?)",
            [
                (packet_id, "Skin-care"),
                (packet_id, "Shower"),
                (packet_id, "Breakfast"),
                (packet_id, "Meditation"),
            ],
        )

    conn.commit()
    conn.close()


# ----------------------
# Hobbies functions
# ----------------------
def add_hobby(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO hobbies (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()


def get_hobbies():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM hobbies")
    hobbies = cursor.fetchall()
    conn.close()
    return hobbies


def delete_hobby(hobby_id: int):
    """
    Remove a hobby and all associated data (entries, tasks, subtasks, recurring tasks).
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Delete entries linked to the hobby
    cursor.execute("DELETE FROM entries WHERE hobby_id = ?", (hobby_id,))

    # Delete subtasks for all tasks of this hobby
    cursor.execute("SELECT id FROM tasks WHERE hobby_id = ?", (hobby_id,))
    task_ids = [row[0] for row in cursor.fetchall()]
    if task_ids:
        cursor.executemany("DELETE FROM subtasks WHERE task_id = ?", [(tid,) for tid in task_ids])

    # Delete tasks and recurring tasks, then the hobby itself
    cursor.execute("DELETE FROM tasks WHERE hobby_id = ?", (hobby_id,))
    cursor.execute("DELETE FROM recurring_tasks WHERE hobby_id = ?", (hobby_id,))
    cursor.execute("DELETE FROM hobbies WHERE id = ?", (hobby_id,))

    conn.commit()
    conn.close()


# ----------------------
# Entries functions
# ----------------------
def add_entry(hobby_id, date_str, minutes, notes, points):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO entries (hobby_id, date, minutes, notes, points)
        VALUES (?, ?, ?, ?, ?)
    """, (hobby_id, date_str, minutes, notes, points))
    conn.commit()
    conn.close()


def get_entries_for_hobby(hobby_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM entries
        WHERE hobby_id = ?
        ORDER BY date DESC
    """, (hobby_id,))
    entries = cursor.fetchall()
    conn.close()
    return entries


def get_total_minutes_per_hobby():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT h.name AS hobby, SUM(e.minutes) AS total_minutes
        FROM entries e
        JOIN hobbies h ON e.hobby_id = h.id
        GROUP BY h.id
    """, conn)
    conn.close()
    return df


def get_daily_minutes():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT date, SUM(minutes) AS total_minutes
        FROM entries
        GROUP BY date
        ORDER BY date
    """, conn)
    conn.close()
    return df


def get_points_over_time():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT date, SUM(points) AS total_points
        FROM entries
        GROUP BY date
        ORDER BY date
    """, conn)
    conn.close()
    return df


def get_daily_minutes_by_hobby():
    """
    Return a DataFrame with columns:
    - date
    - hobby
    - total_minutes
    """
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT e.date AS date,
               h.name AS hobby,
               SUM(e.minutes) AS total_minutes
        FROM entries e
        JOIN hobbies h ON e.hobby_id = h.id
        GROUP BY e.date, h.id
        ORDER BY e.date
        """,
        conn,
    )
    conn.close()
    return df


def get_task_completion_stats():
    """
    Return a DataFrame with per-hobby task completion stats:
    - hobby
    - total_tasks
    - completed_tasks
    - completion_rate (0-1)
    """
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT h.name AS hobby,
               COUNT(t.id) AS total_tasks,
               SUM(CASE WHEN t.done = 1 THEN 1 ELSE 0 END) AS completed_tasks
        FROM tasks t
        JOIN hobbies h ON t.hobby_id = h.id
        GROUP BY h.id
        """,
        conn,
    )
    conn.close()
    if not df.empty:
        df["completion_rate"] = df["completed_tasks"] / df["total_tasks"]
    return df


def get_weekly_minutes_by_hobby():
    """
    Return a DataFrame with weekly summed minutes per hobby.
    Columns:
    - year_week (e.g. '2026-10')
    - hobby
    - total_minutes
    """
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT strftime('%Y-%W', date) AS year_week,
               h.name AS hobby,
               SUM(e.minutes) AS total_minutes
        FROM entries e
        JOIN hobbies h ON e.hobby_id = h.id
        GROUP BY strftime('%Y-%W', date), h.id
        ORDER BY strftime('%Y-%W', date)
        """,
        conn,
    )
    conn.close()
    return df


def get_minutes_for_hobbies_in_range(start_date_str, end_date_str):
    """
    Aggregate actual minutes from entries per hobby between two dates (inclusive).
    """
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT h.name AS hobby,
               SUM(e.minutes) AS total_minutes
        FROM entries e
        JOIN hobbies h ON e.hobby_id = h.id
        WHERE e.date BETWEEN ? AND ?
        GROUP BY h.id
        """,
        conn,
        params=(start_date_str, end_date_str),
    )
    conn.close()
    return df


def get_completed_count_per_hobby_for_week():
    """
    Count of completed activities (entries) per hobby in the last 7 days.
    Returns DataFrame with columns: hobby, completed_count.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=6)
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT h.name AS hobby,
               COUNT(e.id) AS completed_count
        FROM entries e
        JOIN hobbies h ON e.hobby_id = h.id
        WHERE e.date BETWEEN ? AND ?
        GROUP BY h.id
        ORDER BY completed_count DESC
        """,
        conn,
        params=(start_date.isoformat(), end_date.isoformat()),
    )
    conn.close()
    return df


def get_completed_and_estimated_tasks_per_hobby_for_week(week_start_str: str, week_end_str: str):
    """
    For the given week (Sunday–Saturday), per hobby:
    - completed_count: count of entries (logged completions)
    - estimated_count: count of planner_tasks with that hobby_id in the week (planned tasks)
    Returns DataFrame with columns: hobby, completed_count, estimated_count.
    """
    conn = get_connection()
    # Completed: entries in range
    df_completed = pd.read_sql_query(
        """
        SELECT h.name AS hobby,
               COUNT(e.id) AS completed_count
        FROM entries e
        JOIN hobbies h ON e.hobby_id = h.id
        WHERE e.date BETWEEN ? AND ?
        GROUP BY h.id
        """,
        conn,
        params=(week_start_str, week_end_str),
    )
    # Estimated: planner_tasks with hobby_id in range (one row per planned task occurrence)
    df_estimated = pd.read_sql_query(
        """
        SELECT h.name AS hobby,
               COUNT(p.id) AS estimated_count
        FROM planner_tasks p
        JOIN hobbies h ON p.hobby_id = h.id
        WHERE p.date BETWEEN ? AND ?
        GROUP BY h.id
        """,
        conn,
        params=(week_start_str, week_end_str),
    )
    conn.close()
    if df_completed.empty and df_estimated.empty:
        return pd.DataFrame(columns=["hobby", "completed_count", "estimated_count"])
    # Merge so we have all hobbies that have either completed or estimated
    df = df_completed.merge(
        df_estimated, on="hobby", how="outer"
    ).fillna(0)
    df["completed_count"] = df["completed_count"].astype(int)
    df["estimated_count"] = df["estimated_count"].astype(int)
    df = df.sort_values("completed_count", ascending=False)
    return df


# ----------------------
# Weekly planner helpers
# ----------------------
def add_planner_task(
    date_str,
    title,
    notes="",
    frequency="once",
    packet_id=None,
    minutes=0,
    hobby_id=None,
    points=0,
    task_id=None,
    scheduled_time=None,
):
    """scheduled_time: optional "HH:MM" string for ordering in the glance (tasks with time first, then unscheduled)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO planner_tasks (date, title, notes, frequency, packet_id, minutes, hobby_id, points, task_id, scheduled_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (date_str, title, notes, frequency, packet_id, minutes, hobby_id, points, task_id, scheduled_time),
    )
    conn.commit()
    conn.close()


def get_planner_tasks_for_range(start_date_str, end_date_str):
    """Return planner rows ordered by date, then scheduled_time (NULL last), then id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, date, title, notes, done, frequency, packet_id, minutes, hobby_id, points, task_id, scheduled_time
        FROM planner_tasks
        WHERE date BETWEEN ? AND ?
        ORDER BY date, CASE WHEN scheduled_time IS NULL OR scheduled_time = '' THEN 1 ELSE 0 END, scheduled_time, id
        """,
        (start_date_str, end_date_str),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def update_planner_task_minutes(task_id: int, minutes: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE planner_tasks SET minutes = ? WHERE id = ?",
        (minutes, task_id),
    )
    conn.commit()
    conn.close()


def update_planner_task_scheduled_time(planner_id: int, scheduled_time: str | None):
    """Set scheduled_time for a planner row (e.g. "09:00"). Pass None or "" to clear."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE planner_tasks SET scheduled_time = ? WHERE id = ?",
        (scheduled_time if scheduled_time else None, planner_id),
    )
    conn.commit()
    conn.close()


def update_planner_packet_item_scheduled_time_for_week(
    packet_id: int, title: str, scheduled_time: str | None, start_date_str: str, end_date_str: str
):
    """Set scheduled_time for all planner_tasks in the date range that match this packet item (packet_id + title)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE planner_tasks
        SET scheduled_time = ?
        WHERE packet_id = ? AND title = ? AND date BETWEEN ? AND ?
        """,
        (scheduled_time if scheduled_time else None, packet_id, title, start_date_str, end_date_str),
    )
    conn.commit()
    conn.close()


def set_planner_done_for_linked_task(linked_task_id: int, done: bool = True, minutes=None):
    """Sync: when a task is marked done in the task manager, set linked planner_tasks.done (no new entry). Optionally set minutes too."""
    conn = get_connection()
    cursor = conn.cursor()
    if minutes is not None:
        cursor.execute(
            "UPDATE planner_tasks SET done = ?, minutes = ? WHERE task_id = ?",
            (1 if done else 0, minutes, linked_task_id),
        )
    else:
        cursor.execute(
            "UPDATE planner_tasks SET done = ? WHERE task_id = ?",
            (1 if done else 0, linked_task_id),
        )
    conn.commit()
    conn.close()


def toggle_planner_task_done(task_id, done=True, minutes_override=None):
    """When marking done, minutes_override (if set) is used for the logged entry so UI minutes are used."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date, title, notes, done, minutes, hobby_id, points, task_id FROM planner_tasks WHERE id = ?",
        (task_id,),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return
    date_str, title, notes, was_done, minutes, hobby_id, points, linked_task_id = row

    # If undoing and this row is linked to a task, sync task manager (task + all planner rows for that task)
    if not done and linked_task_id is not None:
        conn.commit()
        conn.close()
        mark_task_undone(linked_task_id)
        return

    # When marking done and row is linked to a task, require all subtasks done (check before updating planner row)
    if (not was_done) and done and linked_task_id is not None:
        cursor.execute(
            "SELECT COUNT(*), SUM(CASE WHEN done = 0 THEN 1 ELSE 0 END) FROM subtasks WHERE task_id = ?",
            (linked_task_id,),
        )
        sub_count, undone_count = cursor.fetchone()
        if (sub_count or 0) > 0 and (undone_count or 0) > 0:
            conn.close()
            return  # do not update planner row or task

    cursor.execute(
        "UPDATE planner_tasks SET done = ? WHERE id = ?",
        (1 if done else 0, task_id),
    )

    # If transitioning from not-done -> done (minutes_override used for entry; app updates planner row separately)
    if (not was_done) and done:
        mins_to_log = int(minutes_override) if minutes_override is not None else (minutes or 0)
        if linked_task_id is not None:
            # Commit and release connection before mark_task_done opens its own (avoids DB lock)
            conn.commit()
            conn.close()
            mark_task_done(linked_task_id, is_subtask=False)
            return
        elif hobby_id is not None:
            cursor.execute(
                """
                INSERT INTO entries (hobby_id, date, minutes, notes, points)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    hobby_id,
                    date_str,
                    mins_to_log,
                    f"Weekly plan: {title}" + (f" — {notes}" if notes else ""),
                    points or 0,
                ),
            )
    conn.commit()
    conn.close()


def set_planner_row_done_only(planner_id: int, done: bool = True, minutes_override=None):
    """Update only this planner row's done state (and log one entry when marking done). Use when the same task appears on multiple days so each day can be toggled independently."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date, title, notes, done, minutes, hobby_id, points FROM planner_tasks WHERE id = ?",
        (planner_id,),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return
    date_str, title, notes, was_done, minutes, hobby_id, points = row

    cursor.execute(
        "UPDATE planner_tasks SET done = ? WHERE id = ?",
        (1 if done else 0, planner_id),
    )
    if (not was_done) and done and hobby_id is not None:
        mins = int(minutes_override) if minutes_override is not None else (minutes or 0)
        cursor.execute(
            """
            INSERT INTO entries (hobby_id, date, minutes, notes, points)
            VALUES (?, ?, ?, ?, ?)
            """,
            (hobby_id, date_str, mins, f"Weekly plan: {title}" + (f" — {notes}" if notes else ""), points or 0),
        )
    conn.commit()
    conn.close()


def get_planner_packets():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM planner_packets ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_planner_packet_items(packet_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title FROM planner_packet_items WHERE packet_id = ? ORDER BY id",
        (packet_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def delete_planner_packet(packet_id):
    """
    Remove a planner packet, its items, and any planner tasks that were created
    with this packet_id.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM planner_tasks WHERE packet_id = ?", (packet_id,))
    cursor.execute("DELETE FROM planner_packet_items WHERE packet_id = ?", (packet_id,))
    cursor.execute("DELETE FROM planner_packets WHERE id = ?", (packet_id,))
    conn.commit()
    conn.close()


def add_planner_packet(name: str) -> int:
    """Create a new packet (if it does not already exist) and return its id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM planner_packets WHERE name = ?", (name,))
    row = cursor.fetchone()
    if row:
        packet_id = row[0]
    else:
        cursor.execute("INSERT INTO planner_packets (name) VALUES (?)", (name,))
        packet_id = cursor.lastrowid
        conn.commit()
    conn.close()
    return packet_id


def add_planner_packet_item(packet_id: int, title: str):
    """Add an item (title) to an existing packet."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO planner_packet_items (packet_id, title) VALUES (?, ?)",
        (packet_id, title),
    )
    conn.commit()
    conn.close()


def update_planner_packet_item(item_id: int, new_title: str):
    """Update a packet item's title and sync planner_tasks that were created from this item."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT packet_id, title FROM planner_packet_items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return
    packet_id, old_title = row
    cursor.execute("UPDATE planner_packet_items SET title = ? WHERE id = ?", (new_title.strip(), item_id))
    cursor.execute(
        "UPDATE planner_tasks SET title = ? WHERE packet_id = ? AND title = ?",
        (new_title.strip(), packet_id, old_title),
    )
    conn.commit()
    conn.close()


def delete_planner_packet_item(item_id: int):
    """Remove a packet item and any planner_tasks in the week that were created from it (same packet_id and title)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT packet_id, title FROM planner_packet_items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return
    packet_id, title = row
    cursor.execute("DELETE FROM planner_tasks WHERE packet_id = ? AND title = ?", (packet_id, title))
    cursor.execute("DELETE FROM planner_packet_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


# ----------------------
# General tasks (standalone list, no day/time)
# ----------------------
def get_general_tasks():
    """Return all general tasks as (id, title, done)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM general_tasks ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return rows


def add_general_task(title: str) -> int:
    """Add a general task; return its id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO general_tasks (title, done) VALUES (?, 0)", (title.strip(),))
    rid = cursor.lastrowid
    conn.commit()
    conn.close()
    return rid


def set_general_task_done(task_id: int, done: bool):
    """Mark a general task done or undone."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE general_tasks SET done = ? WHERE id = ?", (1 if done else 0, task_id))
    conn.commit()
    conn.close()


def delete_general_task(task_id: int):
    """Remove a general task."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM general_tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def update_general_planner_task_title(
    old_title: str, new_title: str, start_date_str: str, end_date_str: str
):
    """Update title for all general (no hobby, no packet) planner rows in the date range with the given title."""
    if not new_title or not new_title.strip():
        return
    conn = get_connection()
    cursor = conn.cursor()
    name = new_title.strip()
    cursor.execute(
        """
        UPDATE planner_tasks
        SET title = ?
        WHERE task_id IS NULL AND (packet_id IS NULL OR packet_id = 0)
          AND title = ? AND date BETWEEN ? AND ?
        """,
        (name, old_title, start_date_str, end_date_str),
    )
    conn.commit()
    conn.close()


def delete_planner_task(planner_id: int):
    """Remove a single planner task row from the weekly planner."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM planner_tasks WHERE id = ?", (planner_id,))
    conn.commit()
    conn.close()


def delete_planner_tasks_for_linked_task(task_id: int):
    """Remove all planner rows linked to this task (removes task from the week in the glance)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM planner_tasks WHERE task_id = ?", (task_id,))
    conn.commit()
    conn.close()


def update_task_name(task_id: int, new_name: str):
    """Update a task's name and sync linked planner_tasks so the glance shows the new title."""
    if not new_name or not new_name.strip():
        return
    conn = get_connection()
    cursor = conn.cursor()
    name = new_name.strip()
    cursor.execute("UPDATE tasks SET name = ? WHERE id = ?", (name, task_id))
    cursor.execute("UPDATE planner_tasks SET title = ? WHERE task_id = ?", (name, task_id))
    conn.commit()
    conn.close()


def delete_task(task_id: int):
    """Remove task from DB: subtasks, planner rows for this task, then the task. Task disappears from Existing tasks and glance."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subtasks WHERE task_id = ?", (task_id,))
    cursor.execute("DELETE FROM planner_tasks WHERE task_id = ?", (task_id,))
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def get_hobby_points_and_minutes():
    """
    Return per-hobby totals of minutes and points, plus points per hour.
    Columns:
    - hobby
    - total_minutes
    - total_points
    - points_per_hour
    """
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT h.name AS hobby,
               SUM(e.minutes) AS total_minutes,
               SUM(e.points) AS total_points
        FROM entries e
        JOIN hobbies h ON e.hobby_id = h.id
        GROUP BY h.id
        """,
        conn,
    )
    conn.close()
    if not df.empty:
        df["points_per_hour"] = df.apply(
            lambda row: (row["total_points"] / (row["total_minutes"] / 60.0))
            if row["total_minutes"] and row["total_minutes"] > 0
            else 0,
            axis=1,
        )
    return df


# ----------------------
# Tasks & Subtasks
# ----------------------
def add_task(hobby_id, name, minutes=0, points=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tasks (hobby_id, name, minutes, points)
        VALUES (?, ?, ?, ?)
    """, (hobby_id, name, minutes, points))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id


def add_subtask(task_id, name, minutes=0, points=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO subtasks (task_id, name, minutes, points)
        VALUES (?, ?, ?, ?)
    """, (task_id, name, minutes, points))
    conn.commit()
    conn.close()


def get_tasks(hobby_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE hobby_id = ?", (hobby_id,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks


def get_subtasks(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subtasks WHERE task_id = ?", (task_id,))
    subtasks = cursor.fetchall()
    conn.close()
    return subtasks


def mark_task_done(task_id, is_subtask=False, actual_minutes_override=None):
    """When marking a main task done, actual_minutes_override (if set) is used for the logged entry. Syncs planner_tasks.done for linked rows."""
    conn = get_connection()
    cursor = conn.cursor()

    if is_subtask:
        cursor.execute("SELECT task_id, minutes, points, name FROM subtasks WHERE id = ?", (task_id,))
        subtask = cursor.fetchone()
        if not subtask:
            conn.close()
            return
        cursor.execute("UPDATE subtasks SET done = 1 WHERE id = ?", (task_id,))
        cursor.execute("SELECT hobby_id FROM tasks WHERE id = ?", (subtask[0],))
        hobby_id = cursor.fetchone()[0]
        cursor.execute("""
            INSERT INTO entries (hobby_id, date, minutes, notes, points)
            VALUES (?, ?, ?, ?, ?)
        """, (hobby_id, str(date.today()), subtask[1], f"Subtask: {subtask[3]}", subtask[2]))
    else:
        cursor.execute("SELECT hobby_id, minutes, points, name FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()
        if not task:
            conn.close()
            return

        # Refuse to mark task done if it has subtasks and not all are done (enforced in DB so all paths obey)
        cursor.execute(
            "SELECT COUNT(*), SUM(CASE WHEN done = 0 THEN 1 ELSE 0 END) FROM subtasks WHERE task_id = ?",
            (task_id,),
        )
        sub_count, undone_count = cursor.fetchone()
        has_subtasks = (sub_count or 0) > 0
        if has_subtasks and (undone_count or 0) > 0:
            conn.close()
            return

        # If task has subtasks, sum minutes/points ONLY for subtasks not yet done (avoid double-counting).
        # When all subtasks are already done, do NOT log again – their time was already logged per subtask.
        cursor.execute(
            "SELECT SUM(minutes), SUM(points) FROM subtasks WHERE task_id = ? AND done = 0",
            (task_id,),
        )
        sums = cursor.fetchone()
        all_subtasks_done = has_subtasks and (sums[0] is None or sums[0] == 0)

        if all_subtasks_done:
            # Time already logged per subtask; do not add again
            minutes_to_log = 0
            points_to_log = 0
        elif actual_minutes_override is not None:
            minutes_to_log = int(actual_minutes_override)
            points_to_log = task[2]
        elif has_subtasks:
            minutes_to_log = int(sums[0]) if sums[0] else 0
            points_to_log = int(sums[1]) if sums[1] else 0
        else:
            minutes_to_log = task[1]
            points_to_log = task[2]

        cursor.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
        if minutes_to_log > 0 or points_to_log > 0:
            cursor.execute("""
                INSERT INTO entries (hobby_id, date, minutes, notes, points)
                VALUES (?, ?, ?, ?, ?)
            """, (task[0], str(date.today()), minutes_to_log, f"Task: {task[3]}", points_to_log))

    conn.commit()
    conn.close()

    # Sync: any planner row linked to this task shows done in weekly glance (and same minutes if provided)
    if not is_subtask:
        set_planner_done_for_linked_task(task_id, done=True, minutes=int(actual_minutes_override) if actual_minutes_override is not None else None)


def mark_task_undone(task_id):
    """Set task to not done and sync all linked planner rows to undone (no entry deletion)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET done = 0 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    set_planner_done_for_linked_task(task_id, done=False)


def mark_subtask_undone(subtask_id: int):
    """Set subtask to not done (no entry deletion)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE subtasks SET done = 0 WHERE id = ?", (subtask_id,))
    conn.commit()
    conn.close()


def delete_subtask(subtask_id: int):
    """Remove a subtask."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subtasks WHERE id = ?", (subtask_id,))
    conn.commit()
    conn.close()


# ----------------------
# Recurring Tasks
# ----------------------
def add_recurring_task(hobby_id, name, minutes=0, points=0, frequency="daily"):
    """
    Create a recurring task template. Actual tasks are generated
    into the tasks table by ensure_recurring_tasks_for_today.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO recurring_tasks (hobby_id, name, minutes, points, frequency)
        VALUES (?, ?, ?, ?, ?)
        """,
        (hobby_id, name, minutes, points, frequency),
    )
    conn.commit()
    conn.close()


def get_recurring_tasks(hobby_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, name, minutes, points, frequency, last_created_date
        FROM recurring_tasks
        WHERE hobby_id = ?
        ORDER BY id DESC
        """,
        (hobby_id,),
    )
    tasks = cursor.fetchall()
    conn.close()
    return tasks


def ensure_recurring_tasks_for_today(hobby_id):
    """
    For the given hobby, ensure that daily/weekly recurring tasks
    have corresponding concrete tasks created for today.
    """
    conn = get_connection()
    cursor = conn.cursor()

    today = date.today()
    today_str = today.isoformat()

    cursor.execute(
        """
        SELECT id, name, minutes, points, frequency, last_created_date
        FROM recurring_tasks
        WHERE hobby_id = ?
        """,
        (hobby_id,),
    )
    templates = cursor.fetchall()

    for r_id, name, minutes, points, frequency, last_created in templates:
        create_task = False

        if frequency == "daily":
            if last_created != today_str:
                create_task = True
        elif frequency == "weekly":
            # Create at most one task per calendar week, on the day
            # the user visits the page.
            if not last_created:
                create_task = True
            else:
                last_date = date.fromisoformat(last_created)
                # Compare week starts (Monday) to avoid multiple per week
                last_week_start = last_date - timedelta(days=last_date.weekday())
                this_week_start = today - timedelta(days=today.weekday())
                if last_week_start < this_week_start:
                    create_task = True

        if create_task:
            cursor.execute(
                """
                INSERT INTO tasks (hobby_id, name, minutes, points)
                VALUES (?, ?, ?, ?)
                """,
                (hobby_id, name, minutes, points),
            )
            cursor.execute(
                "UPDATE recurring_tasks SET last_created_date = ? WHERE id = ?",
                (today_str, r_id),
            )

    conn.commit()
    conn.close()