"""
Task Service
Comprehensive task management: CRUD, status workflows, checklists, comments, and filtering.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any, Tuple
import logging
from database import db, DatabaseManager
from models.task import Task, ChecklistItem, Comment, ActivityLog

logger = logging.getLogger("Syncora.TaskService")

VALID_STATUSES = ["Backlog", "In Progress", "Review", "Done"]
VALID_PRIORITIES = ["Low", "Medium", "High"]


class TaskService:
    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager

    def validate_task_data(
        self,
        title: str,
        project_id: int,
        status: str = "Backlog",
        priority: str = "Medium",
        due_date: Optional[str] = None
    ) -> List[str]:
        """Validate task data fields."""
        errors = []
        if not title or len(title.strip()) < 2:
            errors.append("Task title must be at least 2 characters.")
        if len(title.strip()) > 150:
            errors.append("Task title cannot exceed 150 characters.")
        if not project_id:
            errors.append("A project must be selected.")
        if status not in VALID_STATUSES:
            errors.append(f"Status must be one of: {', '.join(VALID_STATUSES)}.")
        if priority not in VALID_PRIORITIES:
            errors.append(f"Priority must be one of: {', '.join(VALID_PRIORITIES)}.")
        if due_date and due_date.strip():
            try:
                datetime.strptime(due_date.strip(), "%Y-%m-%d")
            except ValueError:
                errors.append("Due date must be in YYYY-MM-DD format.")
        return errors

    def get_tasks(
        self,
        project_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        label: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[Task]:
        """Query tasks with dynamic multi-criteria filtering."""
        with self.db.connection() as conn:
            cur = conn.cursor()
            query = """
                SELECT 
                    t.*,
                    p.name as project_name,
                    COALESCE(m.name, 'Unassigned') as assignee_name,
                    COALESCE(m.avatar_color, '#64748B') as assignee_color,
                    (SELECT COUNT(*) FROM checklist_items c WHERE c.task_id = t.id) as checklist_total,
                    (SELECT COUNT(*) FROM checklist_items c WHERE c.task_id = t.id AND c.is_completed = 1) as checklist_completed,
                    (SELECT COUNT(*) FROM comments cm WHERE cm.task_id = t.id) as comment_count
                FROM tasks t
                JOIN projects p ON t.project_id = p.id
                LEFT JOIN members m ON t.assignee_id = m.id
                WHERE 1=1
            """
            params: List[Any] = []

            if project_id is not None and project_id != 0:
                query += " AND t.project_id = ?"
                params.append(project_id)

            if assignee_id is not None and assignee_id != 0:
                if assignee_id == -1:  # Sentinel for unassigned
                    query += " AND t.assignee_id IS NULL"
                else:
                    query += " AND t.assignee_id = ?"
                    params.append(assignee_id)

            if status and status != "All":
                query += " AND t.status = ?"
                params.append(status)

            if priority and priority != "All":
                query += " AND t.priority = ?"
                params.append(priority)

            if label and label != "All":
                query += " AND (',' || t.labels || ',') LIKE ?"
                params.append(f"%,{label.strip()},%")

            if search_query and search_query.strip():
                clean_query = f"%{search_query.strip()}%"
                query += " AND (t.title LIKE ? OR t.description LIKE ? OR t.labels LIKE ?)"
                params.extend([clean_query, clean_query, clean_query])

            query += " ORDER BY t.order_index ASC, t.created_at DESC"

            cur.execute(query, params)
            rows = cur.fetchall()
            return [Task.from_row(row) for row in rows]

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Fetch a single task by ID with project and assignee details."""
        with self.db.connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    t.*,
                    p.name as project_name,
                    COALESCE(m.name, 'Unassigned') as assignee_name,
                    COALESCE(m.avatar_color, '#64748B') as assignee_color,
                    (SELECT COUNT(*) FROM checklist_items c WHERE c.task_id = t.id) as checklist_total,
                    (SELECT COUNT(*) FROM checklist_items c WHERE c.task_id = t.id AND c.is_completed = 1) as checklist_completed,
                    (SELECT COUNT(*) FROM comments cm WHERE cm.task_id = t.id) as comment_count
                FROM tasks t
                JOIN projects p ON t.project_id = p.id
                LEFT JOIN members m ON t.assignee_id = m.id
                WHERE t.id = ?
            """, (task_id,))
            row = cur.fetchone()
            return Task.from_row(row) if row else None

    def create_task(
        self,
        title: str,
        description: str,
        project_id: int,
        assignee_id: Optional[int] = None,
        status: str = "Backlog",
        priority: str = "Medium",
        due_date: Optional[str] = None,
        labels: str = "",
        checklist_items: Optional[List[str]] = None,
        current_user: str = "User"
    ) -> Task:
        """Create a new task with optional initial checklist items."""
        errors = self.validate_task_data(title, project_id, status, priority, due_date)
        if errors:
            raise ValueError("; ".join(errors))

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clean_due = due_date.strip() if due_date and due_date.strip() else None
        clean_labels = ",".join([lbl.strip() for lbl in labels.split(",") if lbl.strip()]) if labels else ""

        with self.db.transaction() as cur:
            cur.execute("""
                INSERT INTO tasks (
                    title, description, project_id, assignee_id, status, priority, due_date, labels, order_index, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """, (
                title.strip(),
                description.strip(),
                project_id,
                assignee_id if assignee_id and assignee_id > 0 else None,
                status,
                priority,
                clean_due,
                clean_labels,
                now_str,
                now_str
            ))
            task_id = cur.lastrowid

            # Add initial checklist items
            if checklist_items:
                for item_text in checklist_items:
                    if item_text and item_text.strip():
                        cur.execute("""
                            INSERT INTO checklist_items (task_id, title, is_completed, created_at)
                            VALUES (?, ?, 0, ?)
                        """, (task_id, item_text.strip(), now_str))

            # Audit log
            cur.execute("""
                INSERT INTO activity_logs (project_id, task_id, user_name, action, details, created_at)
                VALUES (?, ?, ?, 'Task Created', ?, ?)
            """, (project_id, task_id, current_user, f"Created task '{title.strip()}' in status '{status}'", now_str))

        logger.info("Task ID %d created by %s", task_id, current_user)
        return self.get_task_by_id(task_id)

    def update_task(
        self,
        task_id: int,
        title: str,
        description: str,
        project_id: int,
        assignee_id: Optional[int] = None,
        status: str = "Backlog",
        priority: str = "Medium",
        due_date: Optional[str] = None,
        labels: str = "",
        current_user: str = "User"
    ) -> Optional[Task]:
        """Update task properties."""
        errors = self.validate_task_data(title, project_id, status, priority, due_date)
        if errors:
            raise ValueError("; ".join(errors))

        old_task = self.get_task_by_id(task_id)
        if not old_task:
            return None

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clean_due = due_date.strip() if due_date and due_date.strip() else None
        clean_labels = ",".join([lbl.strip() for lbl in labels.split(",") if lbl.strip()]) if labels else ""
        valid_assignee = assignee_id if assignee_id and assignee_id > 0 else None

        changes = []
        if old_task.status != status:
            changes.append(f"status: {old_task.status} -> {status}")
        if old_task.priority != priority:
            changes.append(f"priority: {old_task.priority} -> {priority}")
        if old_task.assignee_id != valid_assignee:
            changes.append("assignee updated")

        detail_text = f"Updated task '{title.strip()}'" + (f" ({', '.join(changes)})" if changes else "")

        with self.db.transaction() as cur:
            cur.execute("""
                UPDATE tasks
                SET title = ?, description = ?, project_id = ?, assignee_id = ?, status = ?, priority = ?, due_date = ?, labels = ?, updated_at = ?
                WHERE id = ?
            """, (
                title.strip(),
                description.strip(),
                project_id,
                valid_assignee,
                status,
                priority,
                clean_due,
                clean_labels,
                now_str,
                task_id
            ))

            cur.execute("""
                INSERT INTO activity_logs (project_id, task_id, user_name, action, details, created_at)
                VALUES (?, ?, ?, 'Task Updated', ?, ?)
            """, (project_id, task_id, current_user, detail_text, now_str))

        return self.get_task_by_id(task_id)

    def update_task_status(self, task_id: int, new_status: str, current_user: str = "User") -> bool:
        """Quick status change for Kanban movements."""
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}")

        task = self.get_task_by_id(task_id)
        if not task:
            return False

        if task.status == new_status:
            return True

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaction() as cur:
            cur.execute("UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?", (new_status, now_str, task_id))
            cur.execute("""
                INSERT INTO activity_logs (project_id, task_id, user_name, action, details, created_at)
                VALUES (?, ?, ?, 'Status Change', ?, ?)
            """, (task.project_id, task_id, current_user, f"Moved '{task.title}' from {task.status} to {new_status}", now_str))

        logger.info("Task %d status moved from %s to %s by %s", task_id, task.status, new_status, current_user)
        return True

    def delete_task(self, task_id: int, current_user: str = "User") -> bool:
        """Delete task and its associated items."""
        task = self.get_task_by_id(task_id)
        if not task:
            return False

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            cur.execute("""
                INSERT INTO activity_logs (project_id, task_id, user_name, action, details, created_at)
                VALUES (?, NULL, ?, 'Task Deleted', ?, ?)
            """, (task.project_id, current_user, f"Deleted task '{task.title}'", now_str))

        logger.info("Task %d deleted by %s", task_id, current_user)
        return True

    # ----------------- Checklists -----------------

    def get_checklist_items(self, task_id: int) -> List[ChecklistItem]:
        """Fetch all checklist items for a task."""
        with self.db.connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM checklist_items WHERE task_id = ? ORDER BY id ASC", (task_id,))
            return [ChecklistItem.from_row(row) for row in cur.fetchall()]

    def add_checklist_item(self, task_id: int, title: str, current_user: str = "User") -> ChecklistItem:
        """Add a new checklist item to a task."""
        if not title or len(title.strip()) < 1:
            raise ValueError("Checklist item text cannot be empty.")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task = self.get_task_by_id(task_id)

        with self.db.transaction() as cur:
            cur.execute("""
                INSERT INTO checklist_items (task_id, title, is_completed, created_at)
                VALUES (?, ?, 0, ?)
            """, (task_id, title.strip(), now_str))
            item_id = cur.lastrowid

            if task:
                cur.execute("""
                    INSERT INTO activity_logs (project_id, task_id, user_name, action, details, created_at)
                    VALUES (?, ?, ?, 'Checklist Added', ?, ?)
                """, (task.project_id, task_id, current_user, f"Added checklist item '{title.strip()}'", now_str))

        with self.db.connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM checklist_items WHERE id = ?", (item_id,))
            return ChecklistItem.from_row(cur.fetchone())

    def toggle_checklist_item(self, item_id: int, is_completed: bool, current_user: str = "User") -> bool:
        """Toggle checklist item completion."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaction() as cur:
            cur.execute("""
                SELECT c.*, t.project_id, t.title as task_title 
                FROM checklist_items c 
                JOIN tasks t ON c.task_id = t.id 
                WHERE c.id = ?
            """, (item_id,))
            row = cur.fetchone()
            if not row:
                return False

            new_val = 1 if is_completed else 0
            cur.execute("UPDATE checklist_items SET is_completed = ? WHERE id = ?", (new_val, item_id))

            state_desc = "checked" if is_completed else "unchecked"
            cur.execute("""
                INSERT INTO activity_logs (project_id, task_id, user_name, action, details, created_at)
                VALUES (?, ?, ?, 'Checklist Updated', ?, ?)
            """, (row["project_id"], row["task_id"], current_user, f"Marked '{row['title']}' as {state_desc}", now_str))

        return True

    def delete_checklist_item(self, item_id: int, current_user: str = "User") -> bool:
        """Remove a checklist item."""
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM checklist_items WHERE id = ?", (item_id,))
            return cur.rowcount > 0

    # ----------------- Comments -----------------

    def get_comments(self, task_id: int) -> List[Comment]:
        """Fetch all comments for a task ordered chronologically."""
        with self.db.connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM comments WHERE task_id = ? ORDER BY created_at ASC", (task_id,))
            return [Comment.from_row(row) for row in cur.fetchall()]

    def add_comment(
        self,
        task_id: int,
        author_name: str,
        content: str,
        member_id: Optional[int] = None
    ) -> Comment:
        """Post a comment on a task."""
        if not content or len(content.strip()) < 1:
            raise ValueError("Comment text cannot be empty.")
        if not author_name or len(author_name.strip()) < 1:
            author_name = "User"

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task = self.get_task_by_id(task_id)

        with self.db.transaction() as cur:
            cur.execute("""
                INSERT INTO comments (task_id, member_id, author_name, content, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (task_id, member_id, author_name.strip(), content.strip(), now_str))
            comment_id = cur.lastrowid

            if task:
                cur.execute("""
                    INSERT INTO activity_logs (project_id, task_id, user_name, action, details, created_at)
                    VALUES (?, ?, ?, 'Comment Added', ?, ?)
                """, (task.project_id, task_id, author_name.strip(), f"Commented on '{task.title}'", now_str))

        with self.db.connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM comments WHERE id = ?", (comment_id,))
            return Comment.from_row(cur.fetchone())

    def get_task_activity(self, task_id: int) -> List[ActivityLog]:
        """Fetch activity logs related to a specific task."""
        with self.db.connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM activity_logs 
                WHERE task_id = ? 
                ORDER BY created_at DESC
            """, (task_id,))
            return [ActivityLog.from_row(row) for row in cur.fetchall()]
