## Hobby Tracker

This is a small Streamlit web app for tracking hobbies, tasks, and time spent, with a colorful handwritten-style interface.

### Features

- **Hobbies**
  - Add new hobbies (duplicates are prevented).
  - See your existing hobbies as colorful “pills”.
  - Remove a hobby (and all its tasks, subtasks, recurring tasks, and entries) in one click.

- **Activity logging**
  - Log minutes, notes, and points for any hobby on any date.
  - View a per-hobby history of your entries.

- **Tasks and subtasks**
  - Create one-off tasks and recurring tasks (daily or weekly) per hobby.
  - Add subtasks to break down bigger tasks.
  - Mark tasks and subtasks as done; completion automatically logs an entry with minutes and points.
  - Only the 10 most recent completed tasks are shown; older ones are hidden from the list.
  - A tree view shows active tasks and subtasks in a handwritten-style overview.

- **Statistics**
  - Total minutes per hobby.
  - Points per hobby and over time.
  - Minutes per hobby over time.
  - Daily activity heatmap.
  - Weekly hours per hobby.
  - Task completion stats (per hobby).

### Requirements

- Python 3.10+ (Python 3.12 is known to work).
- `pip` to install dependencies.

### Setup

From the project root (this directory):

1. **Create and activate a virtual environment (optional but recommended)**

```bash
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
```

2. **Install dependencies**

If you already have a `requirements.txt`, you can run:

```bash
pip install -r requirements.txt
```

Otherwise, the minimum set of packages needed for this app is:

```bash
pip install streamlit pandas seaborn matplotlib
```

3. **Make sure the database folder exists**

The SQLite database is stored under `data/hobbies.db`. If the `data` folder does not exist yet, create it:

```bash
mkdir -p data
```

The app will create the database and tables on first run.

### Running the app

From the project root:

```bash
streamlit run app.py
```

Then open the URL that Streamlit prints in the terminal (usually `http://localhost:8501`) in your browser.

### Pages overview

- **Add Hobby**
  - Add a new hobby and see all existing hobbies as nice pills.
  - Remove a hobby and all of its related data.

- **Log Activity**
  - Manually log minutes, notes, and points for a hobby on a given date.

- **View Hobby Activity**
  - Browse past entries for a selected hobby.

- **Statistics**
  - Explore overview, per-hobby trends, daily heatmap, weekly hours, and task completion.

- **Tasks**
  - Create one-off and recurring tasks per hobby.
  - Add, edit, and complete subtasks.
  - See an active task/subtask tree with visual indicators for completed subtasks.

# hobby-tracker
