import sqlite3
import pandas as pd
from datetime import date

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
    conn.commit()
    conn.close()


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

        # If task has subtasks, sum their minutes/points
        cursor.execute("SELECT SUM(minutes), SUM(points) FROM subtasks WHERE task_id = ?", (task_id,))
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