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
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO planner_tasks (date, title, notes, frequency, packet_id, minutes, hobby_id, points, task_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (date_str, title, notes, frequency, packet_id, minutes, hobby_id, points, task_id),
    )
    conn.commit()
    conn.close()


def get_planner_tasks_for_range(start_date_str, end_date_str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, date, title, notes, done, frequency, packet_id, minutes, hobby_id, points, task_id
        FROM planner_tasks
        WHERE date BETWEEN ? AND ?
        ORDER BY date, id
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


def toggle_planner_task_done(task_id, done=True):
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

    cursor.execute(
        "UPDATE planner_tasks SET done = ? WHERE id = ?",
        (1 if done else 0, task_id),
    )

    # If transitioning from not-done -> done
    if (not was_done) and done:
        if linked_task_id is not None:
            # Reuse main task completion logic so it appears in tasks UI and stats
            mark_task_done(linked_task_id, is_subtask=False)
        elif hobby_id is not None:
            # Fallback: log directly into entries
            cursor.execute(
                """
                INSERT INTO entries (hobby_id, date, minutes, notes, points)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    hobby_id,
                    date_str,
                    minutes or 0,
                    f"Weekly plan: {title}" + (f" — {notes}" if notes else ""),
                    points or 0,
                ),
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


def delete_planner_task(task_id: int):
    """
    Remove a single planner task from the weekly planner.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM planner_tasks WHERE id = ?", (task_id,))
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


def mark_task_done(task_id, is_subtask=False):
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

        # If task has subtasks, sum minutes/points ONLY for subtasks
        # that are not yet marked done, to avoid double-counting
        # subtasks that were already logged individually.
        cursor.execute(
            "SELECT SUM(minutes), SUM(points) FROM subtasks WHERE task_id = ? AND done = 0",
            (task_id,),
        )
        sums = cursor.fetchone()
        minutes_to_log = sums[0] if sums[0] else task[1]
        points_to_log = sums[1] if sums[1] else task[2]

        cursor.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
        cursor.execute("""
            INSERT INTO entries (hobby_id, date, minutes, notes, points)
            VALUES (?, ?, ?, ?, ?)
        """, (task[0], str(date.today()), minutes_to_log, f"Task: {task[3]}", points_to_log))

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