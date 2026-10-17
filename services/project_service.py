"""
Project Service
Handles CRUD operations, statistical summaries, validation, and lifecycle management for Projects.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
import logging
from database import db, DatabaseManager
from models.project import Project

logger = logging.getLogger("Syncora.ProjectService")


class ProjectService:
    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager

    def validate_project_data(self, name: str, owner: str, deadline: Optional[str] = None, status: str = "Active") -> List[str]:
        """Validate project fields and return list of error messages (empty if valid)."""
        errors = []
        if not name or len(name.strip()) < 2:
            errors.append("Project name must be at least 2 characters.")
        if len(name.strip()) > 100:
            errors.append("Project name cannot exceed 100 characters.")
        if not owner or len(owner.strip()) < 2:
            errors.append("Project owner is required.")
        if status not in ("Active", "Completed", "On Hold"):
            errors.append("Invalid project status. Must be 'Active', 'Completed', or 'On Hold'.")
        if deadline:
            try:
                datetime.strptime(deadline.strip(), "%Y-%m-%d")
            except ValueError:
                errors.append("Deadline must be in YYYY-MM-DD format.")
        return errors

    def get_all_projects(self, include_stats: bool = True) -> List[Project]:
        """Fetch all projects, optionally calculating task progress and overdue stats."""
        with self.db.connection() as conn:
            cur = conn.cursor()
            if not include_stats:
                cur.execute("SELECT * FROM projects ORDER BY created_at DESC")
                return [Project.from_row(row) for row in cur.fetchall()]

            # Fetch projects with aggregated task counts
            cur.execute("""
                SELECT 
                    p.*,
                    COUNT(t.id) as total_tasks,
                    SUM(CASE WHEN t.status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN t.status = 'In Progress' THEN 1 ELSE 0 END) as in_progress_tasks,
                    SUM(CASE WHEN t.status != 'Done' AND t.due_date IS NOT NULL AND date(t.due_date) < date('now') THEN 1 ELSE 0 END) as overdue_tasks
                FROM projects p
                LEFT JOIN tasks t ON p.id = t.project_id
                GROUP BY p.id
                ORDER BY p.status = 'Active' DESC, p.created_at DESC
            """)
            rows = cur.fetchall()
            projects = []
            for row in rows:
                projects.append(Project.from_row(
                    row,
                    total_tasks=row["total_tasks"] or 0,
                    completed_tasks=row["completed_tasks"] or 0,
                    in_progress_tasks=row["in_progress_tasks"] or 0,
                    overdue_tasks=row["overdue_tasks"] or 0
                ))
            return projects

    def get_project_by_id(self, project_id: int, include_stats: bool = True) -> Optional[Project]:
        """Fetch a single project by ID."""
        with self.db.connection() as conn:
            cur = conn.cursor()
            if not include_stats:
                cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
                row = cur.fetchone()
                return Project.from_row(row) if row else None

            cur.execute("""
                SELECT 
                    p.*,
                    COUNT(t.id) as total_tasks,
                    SUM(CASE WHEN t.status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN t.status = 'In Progress' THEN 1 ELSE 0 END) as in_progress_tasks,
                    SUM(CASE WHEN t.status != 'Done' AND t.due_date IS NOT NULL AND date(t.due_date) < date('now') THEN 1 ELSE 0 END) as overdue_tasks
                FROM projects p
                LEFT JOIN tasks t ON p.id = t.project_id
                WHERE p.id = ?
                GROUP BY p.id
            """, (project_id,))
            row = cur.fetchone()
            if not row:
                return None
            return Project.from_row(
                row,
                total_tasks=row["total_tasks"] or 0,
                completed_tasks=row["completed_tasks"] or 0,
                in_progress_tasks=row["in_progress_tasks"] or 0,
                overdue_tasks=row["overdue_tasks"] or 0
            )

    def create_project(
        self,
        name: str,
        description: str,
        owner: str,
        deadline: Optional[str] = None,
        status: str = "Active",
        current_user: str = "User"
    ) -> Project:
        """Create a new project and log the activity."""
        errors = self.validate_project_data(name, owner, deadline, status)
        if errors:
            raise ValueError("; ".join(errors))

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clean_deadline = deadline.strip() if deadline and deadline.strip() else None

        with self.db.transaction() as cur:
            cur.execute("""
                INSERT INTO projects (name, description, owner, status, deadline, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name.strip(), description.strip(), owner.strip(), status, clean_deadline, now_str, now_str))
            project_id = cur.lastrowid

            # Log activity
            cur.execute("""
                INSERT INTO activity_logs (project_id, task_id, user_name, action, details, created_at)
                VALUES (?, NULL, ?, 'Project Created', ?, ?)
            """, (project_id, current_user, f"Created project '{name.strip()}'", now_str))

        logger.info("Project '%s' (ID %d) created by %s", name, project_id, current_user)
        return self.get_project_by_id(project_id)

    def update_project(
        self,
        project_id: int,
        name: str,
        description: str,
        owner: str,
        deadline: Optional[str] = None,
        status: str = "Active",
        current_user: str = "User"
    ) -> Optional[Project]:
        """Update an existing project and log the modification."""
        errors = self.validate_project_data(name, owner, deadline, status)
        if errors:
            raise ValueError("; ".join(errors))

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clean_deadline = deadline.strip() if deadline and deadline.strip() else None

        with self.db.transaction() as cur:
            cur.execute("""
                UPDATE projects 
                SET name = ?, description = ?, owner = ?, status = ?, deadline = ?, updated_at = ?
                WHERE id = ?
            """, (name.strip(), description.strip(), owner.strip(), status, clean_deadline, now_str, project_id))

            if cur.rowcount == 0:
                return None

            # Log activity
            cur.execute("""
                INSERT INTO activity_logs (project_id, task_id, user_name, action, details, created_at)
                VALUES (?, NULL, ?, 'Project Updated', ?, ?)
            """, (project_id, current_user, f"Updated project '{name.strip()}'", now_str))

        return self.get_project_by_id(project_id)

    def delete_project(self, project_id: int, current_user: str = "User") -> bool:
        """Delete project. Foreign keys handle task cascade."""
        proj = self.get_project_by_id(project_id, include_stats=False)
        if not proj:
            return False

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaction() as cur:
            # Delete project (ON DELETE CASCADE in SQLite removes tasks, checklists, comments)
            cur.execute("DELETE FROM projects WHERE id = ?", (project_id,))

            # General activity log entry (project_id is NULL since project is gone)
            cur.execute("""
                INSERT INTO activity_logs (project_id, task_id, user_name, action, details, created_at)
                VALUES (NULL, NULL, ?, 'Project Deleted', ?, ?)
            """, (current_user, f"Deleted project '{proj.name}'", now_str))

        logger.info("Project ID %d deleted by %s", project_id, current_user)
        return True
