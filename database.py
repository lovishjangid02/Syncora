"""
Syncora Database Module
Provides robust SQLite connection management, schema initialization,
foreign key enforcement, transaction handling, and realistic demo data seeding.
"""

import sqlite3
import os
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Generator, Optional, List, Dict, Any

logger = logging.getLogger("Syncora.Database")

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "syncora.db")
OLD_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "taskflow.db")
if not os.path.exists(DEFAULT_DB_PATH) and os.path.exists(OLD_DB_PATH):
    try:
        os.rename(OLD_DB_PATH, DEFAULT_DB_PATH)
    except Exception:
        pass


class DatabaseManager:
    """Manages SQLite database connections, schema migrations, and transactions."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._ensure_dir()
        self.initialize_schema()

    def _ensure_dir(self):
        """Ensure the directory for the database file exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Create and return a new SQLite connection with foreign keys and Row factory enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for acquiring a database connection."""
        conn = self.get_connection()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Cursor, None, None]:
        """Context manager for executing operations within a transaction.
        Auto-commits on completion, rolls back on exception.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error("Transaction failed and was rolled back: %s", e)
            raise
        finally:
            conn.close()

    def initialize_schema(self):
        """Create tables, indexes, and constraints if they do not exist."""
        with self.transaction() as cur:
            # Projects table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    owner TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Active',
                    deadline TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # Members table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL DEFAULT 'Member',
                    avatar_color TEXT DEFAULT '#3B82F6',
                    created_at TEXT NOT NULL
                );
            """)

            # Tasks table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    project_id INTEGER NOT NULL,
                    assignee_id INTEGER,
                    status TEXT NOT NULL DEFAULT 'Backlog',
                    priority TEXT NOT NULL DEFAULT 'Medium',
                    due_date TEXT,
                    labels TEXT DEFAULT '',
                    order_index INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (assignee_id) REFERENCES members(id) ON DELETE SET NULL
                );
            """)

            # Checklist items table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS checklist_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    is_completed INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
                );
            """)

            # Comments table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    member_id INTEGER,
                    author_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE SET NULL
                );
            """)

            # Activity logs table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    task_id INTEGER,
                    user_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
                );
            """)

            # Create performance indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_checklist_task ON checklist_items(task_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_comments_task ON comments(task_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_logs(created_at DESC);")

        logger.info("Database schema initialized at %s", self.db_path)

    def is_empty(self) -> bool:
        """Check if database contains any projects."""
        with self.connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM projects")
            count = cur.fetchone()[0]
            return count == 0

    def reset_database(self):
        """Clear all tables and re-seed demo data."""
        with self.transaction() as cur:
            cur.execute("DELETE FROM activity_logs")
            cur.execute("DELETE FROM comments")
            cur.execute("DELETE FROM checklist_items")
            cur.execute("DELETE FROM tasks")
            cur.execute("DELETE FROM members")
            cur.execute("DELETE FROM projects")
        self.seed_demo_data(force=True)

    def seed_demo_data(self, force: bool = False):
        """Seed realistic demo records if database is empty or forced."""
        if not force and not self.is_empty():
            logger.info("Database already contains data; skipping seed.")
            return

        logger.info("Seeding realistic demo data...")
        now = datetime.now()
        iso_now = now.strftime("%Y-%m-%d %H:%M:%S")

        with self.transaction() as cur:
            # 1. Members
            members_data = [
                ("Lovish Jangid", "lovish.jangid@university.edu", "Admin", "#8B5CF6"),
                ("Love Kush", "love.kush@university.edu", "Member", "#3B82F6"),
                ("Lakshay Bhargava", "lakshay.bhargava@university.edu", "Member", "#10B981"),
                ("Manas", "manas@university.edu", "Member", "#F59E0B")
            ]
            member_ids = {}
            for name, email, role, color in members_data:
                cur.execute("""
                    INSERT INTO members (name, email, role, avatar_color, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, email, role, color, iso_now))
                member_ids[name] = cur.lastrowid

            # 2. Projects
            projects_data = [
                (
                    "Syncora Desktop Tracker",
                    "Offline-first collaborative Agile Kanban tracker and task workflow manager built for student engineering teams.",
                    "Lovish Jangid",
                    "Active",
                    (now + timedelta(days=14)).strftime("%Y-%m-%d"),
                    iso_now
                ),
                (
                    "CampusNav Indoor AR",
                    "Augmented reality campus navigation system connecting lecture halls, labs, and student centers.",
                    "Love Kush",
                    "Active",
                    (now + timedelta(days=28)).strftime("%Y-%m-%d"),
                    iso_now
                ),
                (
                    "StudySync Peer Portal",
                    "Intelligent peer tutoring matchmaking portal with automated scheduling and session whiteboards.",
                    "Lakshay Bhargava",
                    "Active",
                    (now + timedelta(days=7)).strftime("%Y-%m-%d"),
                    iso_now
                )
            ]
            project_ids = {}
            for name, desc, owner, status, deadline, created_at in projects_data:
                cur.execute("""
                    INSERT INTO projects (name, description, owner, status, deadline, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (name, desc, owner, status, deadline, created_at, created_at))
                project_ids[name] = cur.lastrowid

            p1 = project_ids["Syncora Desktop Tracker"]
            p2 = project_ids["CampusNav Indoor AR"]
            p3 = project_ids["StudySync Peer Portal"]

            # 3. Tasks
            # Dates: some overdue, some due today/tomorrow, some due next week
            overdue_date1 = (now - timedelta(days=3)).strftime("%Y-%m-%d")
            overdue_date2 = (now - timedelta(days=1)).strftime("%Y-%m-%d")
            soon_date = (now + timedelta(days=2)).strftime("%Y-%m-%d")
            future_date1 = (now + timedelta(days=6)).strftime("%Y-%m-%d")
            future_date2 = (now + timedelta(days=12)).strftime("%Y-%m-%d")

            tasks_data = [
                # Project 1 Tasks
                {
                    "title": "Design Database Schema & Constraints",
                    "desc": "Specify relational tables for projects, tasks, checklists, comments, and audit logs with foreign key cascades.",
                    "proj": p1,
                    "assignee": member_ids["Lakshay Bhargava"],
                    "status": "Done",
                    "priority": "High",
                    "due": overdue_date1,
                    "labels": "database,architecture",
                    "checklists": [
                        ("Draft ER diagram", 1),
                        ("Write table creation DDL", 1),
                        ("Add indexes for performance", 1),
                        ("Validate cascade deletion rules", 1)
                    ],
                    "comments": [
                        (member_ids["Lovish Jangid"], "Lovish Jangid", "Schema looks clean and normalized. Foreign keys verified.")
                    ]
                },
                {
                    "title": "Build Interactive Kanban Board",
                    "desc": "Implement four-column drag/move board with status badges, priority markers, and filter controls.",
                    "proj": p1,
                    "assignee": member_ids["Love Kush"],
                    "status": "In Progress",
                    "priority": "High",
                    "due": soon_date,
                    "labels": "frontend,ui/ux",
                    "checklists": [
                        ("Render Backlog, In Progress, Review, and Done columns", 1),
                        ("Add quick action buttons to shift task status", 1),
                        ("Implement filter toolbar for priority and assignee", 0),
                        ("Add overdue date highlight badges", 1)
                    ],
                    "comments": [
                        (member_ids["Manas"], "Manas", "Card spacing looks great. Let's make sure the badge colors pop in dark mode."),
                        (member_ids["Love Kush"], "Love Kush", "Implementing the quick move arrows right now!")
                    ]
                },
                {
                    "title": "Task Detail Modal with Interactive Checklists",
                    "desc": "Provide pop-up dialog allowing users to toggle checklist items, read/write comments, and review audit trail.",
                    "proj": p1,
                    "assignee": member_ids["Lovish Jangid"],
                    "status": "In Progress",
                    "priority": "Medium",
                    "due": overdue_date2,  # Overdue to demonstrate alert!
                    "labels": "frontend,collaboration",
                    "checklists": [
                        ("Checklist checkboxes with immediate SQLite sync", 1),
                        ("Comment posting stream with author avatars", 1),
                        ("Activity history timeline", 0)
                    ],
                    "comments": [
                        (member_ids["Manas"], "Manas", "Please ensure the checklist completion ratio updates dynamically.")
                    ]
                },
                {
                    "title": "Analytics Dashboard & Matplotlib Charts",
                    "desc": "Render project status donut chart, priority breakdown, member workload distribution, and CSV export.",
                    "proj": p1,
                    "assignee": member_ids["Manas"],
                    "status": "Review",
                    "priority": "Medium",
                    "due": future_date1,
                    "labels": "analytics,reporting",
                    "checklists": [
                        ("Matplotlib chart embedding via FigureCanvasTkAgg", 1),
                        ("Status distribution chart", 1),
                        ("CSV export routine with file picker", 1),
                        ("Dark/light mode chart color synchronization", 1)
                    ],
                    "comments": [
                        (member_ids["Lovish Jangid"], "Lovish Jangid", "Testing CSV export with edge case descriptions. Looks solid!")
                    ]
                },
                {
                    "title": "Implement Role-Based UI Permissions",
                    "desc": "Configure Admin and Member roles to control editing, deleting, and configuration privileges.",
                    "proj": p1,
                    "assignee": member_ids["Lakshay Bhargava"],
                    "status": "Backlog",
                    "priority": "Low",
                    "due": future_date2,
                    "labels": "security,roles",
                    "checklists": [
                        ("Define role permissions matrix", 1),
                        ("Enforce admin privileges for team rosters", 0),
                        ("Add active role switcher pill in top navigation", 0)
                    ],
                    "comments": []
                },
                {
                    "title": "Prepare Automated Unit & Integration Tests",
                    "desc": "Write test suites for SQLite database integrity, service layer calculations, and CSV export accuracy.",
                    "proj": p1,
                    "assignee": member_ids["Manas"],
                    "status": "Done",
                    "priority": "High",
                    "due": overdue_date1,
                    "labels": "testing,quality",
                    "checklists": [
                        ("Database constraint tests", 1),
                        ("CRUD operations test suite", 1),
                        ("Overdue date calculation verification", 1)
                    ],
                    "comments": []
                },

                # Project 2 Tasks (CampusNav)
                {
                    "title": "Map Campus Floorplans into Vector Meshes",
                    "desc": "Convert architectural PDF blueprints into coordinate points for pathfinding graph.",
                    "proj": p2,
                    "assignee": member_ids["Love Kush"],
                    "status": "In Progress",
                    "priority": "High",
                    "due": future_date1,
                    "labels": "mapping,graph",
                    "checklists": [
                        ("Extract Science Building floorplan", 1),
                        ("Plot beacon coordinates", 0)
                    ],
                    "comments": []
                },
                {
                    "title": "A* Pathfinding Algorithm Integration",
                    "desc": "Implement multi-floor shortest path routing considering elevators and accessibility ramps.",
                    "proj": p2,
                    "assignee": member_ids["Lakshay Bhargava"],
                    "status": "Backlog",
                    "priority": "Medium",
                    "due": future_date2,
                    "labels": "algorithm,navigation",
                    "checklists": [
                        ("Implement node graph structure", 0),
                        ("Add elevator transition penalties", 0)
                    ],
                    "comments": []
                },
                {
                    "title": "AR Camera Overlay Viewport",
                    "desc": "Render directional arrows overlaid onto live camera feed using ARKit/ARCore bridge.",
                    "proj": p2,
                    "assignee": member_ids["Lovish Jangid"],
                    "status": "Review",
                    "priority": "High",
                    "due": soon_date,
                    "labels": "ar,camera",
                    "checklists": [
                        ("Camera permission handler", 1),
                        ("Overlay smoothing filter", 1)
                    ],
                    "comments": []
                },

                # Project 3 Tasks (StudySync)
                {
                    "title": "Tutor Availability Calendar Component",
                    "desc": "Interactive weekly slot selection widget for tutors to set their open study hours.",
                    "proj": p3,
                    "assignee": member_ids["Manas"],
                    "status": "Done",
                    "priority": "Medium",
                    "due": overdue_date1,
                    "labels": "frontend,calendar",
                    "checklists": [
                        ("7-day grid view", 1),
                        ("Slot multi-select", 1)
                    ],
                    "comments": []
                },
                {
                    "title": "Automated Session Reminder Notifications",
                    "desc": "Send scheduled alert emails and calendar invites 1 hour before scheduled tutoring sessions.",
                    "proj": p3,
                    "assignee": member_ids["Love Kush"],
                    "status": "Backlog",
                    "priority": "Low",
                    "due": future_date2,
                    "labels": "notifications,backend",
                    "checklists": [],
                    "comments": []
                }
            ]

            for t_idx, t in enumerate(tasks_data):
                cur.execute("""
                    INSERT INTO tasks (title, description, project_id, assignee_id, status, priority, due_date, labels, order_index, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    t["title"],
                    t["desc"],
                    t["proj"],
                    t["assignee"],
                    t["status"],
                    t["priority"],
                    t["due"],
                    t["labels"],
                    t_idx,
                    iso_now,
                    iso_now
                ))
                task_id = cur.lastrowid

                # Checklists
                for c_title, c_done in t["checklists"]:
                    cur.execute("""
                        INSERT INTO checklist_items (task_id, title, is_completed, created_at)
                        VALUES (?, ?, ?, ?)
                    """, (task_id, c_title, c_done, iso_now))

                # Comments
                for author_id, author_name, content in t["comments"]:
                    cur.execute("""
                        INSERT INTO comments (task_id, member_id, author_name, content, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (task_id, author_id, author_name, content, iso_now))

            # 4. Activity Logs
            activities = [
                (p1, None, "Lovish Jangid", "Project Created", "Created project 'Syncora Desktop Tracker'", iso_now),
                (p1, None, "Lakshay Bhargava", "Task Completed", "Completed 'Design Database Schema & Constraints'", iso_now),
                (p1, None, "Love Kush", "Status Change", "Moved 'Build Interactive Kanban Board' to In Progress", iso_now),
                (p1, None, "Manas", "Task Created", "Created 'Analytics Dashboard & Matplotlib Charts'", iso_now),
                (p1, None, "Lovish Jangid", "Comment Added", "Commented on 'Design Database Schema & Constraints'", iso_now),
                (p2, None, "Love Kush", "Project Created", "Created project 'CampusNav Indoor AR'", iso_now),
                (p3, None, "Manas", "Task Completed", "Completed 'Tutor Availability Calendar Component'", iso_now)
            ]
            for proj_id, task_id, user, action, details, created_at in activities:
                cur.execute("""
                    INSERT INTO activity_logs (project_id, task_id, user_name, action, details, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (proj_id, task_id, user, action, details, created_at))

        logger.info("Demo data seeded successfully with %d tasks across 3 projects.", len(tasks_data))


# Singleton instance for general use
db = DatabaseManager()
