"""
Report and Analytics Service
Generates aggregations, workload calculations, overdue summaries, and CSV exports.
"""

from datetime import datetime, date
from typing import Dict, List, Any, Optional
import csv
import logging
from database import db, DatabaseManager
from models.task import Task

logger = logging.getLogger("Syncora.ReportService")


class ReportService:
    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager

    def get_dashboard_summary(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        """Calculate high-level summary KPIs for dashboard metrics."""
        with self.db.connection() as conn:
            cur = conn.cursor()

            # Total projects
            cur.execute("SELECT COUNT(*) FROM projects")
            total_projects = cur.fetchone()[0]

            # Task aggregates
            query = """
                SELECT 
                    COUNT(t.id) as total_tasks,
                    SUM(CASE WHEN t.status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN t.status = 'In Progress' THEN 1 ELSE 0 END) as in_progress_tasks,
                    SUM(CASE WHEN t.status = 'Review' THEN 1 ELSE 0 END) as review_tasks,
                    SUM(CASE WHEN t.status = 'Backlog' THEN 1 ELSE 0 END) as backlog_tasks,
                    SUM(CASE WHEN t.status != 'Done' AND t.due_date IS NOT NULL AND date(t.due_date) < date('now') THEN 1 ELSE 0 END) as overdue_tasks
                FROM tasks t
                WHERE 1=1
            """
            params = []
            if project_id and project_id > 0:
                query += " AND t.project_id = ?"
                params.append(project_id)

            cur.execute(query, params)
            row = cur.fetchone()

            total_tasks = row["total_tasks"] or 0
            completed_tasks = row["completed_tasks"] or 0
            in_progress_tasks = row["in_progress_tasks"] or 0
            review_tasks = row["review_tasks"] or 0
            backlog_tasks = row["backlog_tasks"] or 0
            overdue_tasks = row["overdue_tasks"] or 0

            completion_rate = int(round((completed_tasks / total_tasks * 100))) if total_tasks > 0 else 0

            return {
                "total_projects": total_projects,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "in_progress_tasks": in_progress_tasks,
                "review_tasks": review_tasks,
                "backlog_tasks": backlog_tasks,
                "overdue_tasks": overdue_tasks,
                "completion_rate": completion_rate
            }

    def get_status_distribution(self, project_id: Optional[int] = None) -> Dict[str, int]:
        """Return task count breakdown per status (Backlog, In Progress, Review, Done)."""
        counts = {"Backlog": 0, "In Progress": 0, "Review": 0, "Done": 0}
        with self.db.connection() as conn:
            cur = conn.cursor()
            query = "SELECT status, COUNT(*) as count FROM tasks WHERE 1=1"
            params = []
            if project_id and project_id > 0:
                query += " AND project_id = ?"
                params.append(project_id)
            query += " GROUP BY status"
            cur.execute(query, params)
            for row in cur.fetchall():
                if row["status"] in counts:
                    counts[row["status"]] = row["count"]
        return counts

    def get_priority_distribution(self, project_id: Optional[int] = None) -> Dict[str, int]:
        """Return task count breakdown per priority (Low, Medium, High)."""
        counts = {"Low": 0, "Medium": 0, "High": 0}
        with self.db.connection() as conn:
            cur = conn.cursor()
            query = "SELECT priority, COUNT(*) as count FROM tasks WHERE 1=1"
            params = []
            if project_id and project_id > 0:
                query += " AND project_id = ?"
                params.append(project_id)
            query += " GROUP BY priority"
            cur.execute(query, params)
            for row in cur.fetchall():
                if row["priority"] in counts:
                    counts[row["priority"]] = row["count"]
        return counts

    def get_team_workload_summary(self) -> List[Dict[str, Any]]:
        """Return workload statistics per team member."""
        with self.db.connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    m.id,
                    m.name,
                    m.role,
                    m.avatar_color,
                    COUNT(t.id) as total_assigned,
                    SUM(CASE WHEN t.status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
                    SUM(CASE WHEN t.status = 'Done' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN t.status = 'Review' THEN 1 ELSE 0 END) as review,
                    SUM(CASE WHEN t.status = 'Backlog' THEN 1 ELSE 0 END) as backlog,
                    SUM(CASE WHEN t.status != 'Done' AND t.due_date IS NOT NULL AND date(t.due_date) < date('now') THEN 1 ELSE 0 END) as overdue
                FROM members m
                LEFT JOIN tasks t ON m.id = t.assignee_id
                GROUP BY m.id
                ORDER BY total_assigned DESC, m.name ASC
            """)
            rows = cur.fetchall()
            workload = []
            for r in rows:
                total = r["total_assigned"] or 0
                done = r["completed"] or 0
                pct = int(round((done / total * 100))) if total > 0 else 0
                workload.append({
                    "id": r["id"],
                    "name": r["name"],
                    "role": r["role"],
                    "avatar_color": r["avatar_color"] or "#3B82F6",
                    "total_assigned": total,
                    "in_progress": r["in_progress"] or 0,
                    "completed": done,
                    "review": r["review"] or 0,
                    "backlog": r["backlog"] or 0,
                    "overdue": r["overdue"] or 0,
                    "completion_pct": pct
                })
            return workload

    def get_upcoming_deadlines(self, limit: int = 6, project_id: Optional[int] = None) -> List[Task]:
        """Fetch tasks with upcoming deadlines or overdue status that are not completed."""
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
                WHERE t.status != 'Done' AND t.due_date IS NOT NULL AND t.due_date != ''
            """
            params = []
            if project_id and project_id > 0:
                query += " AND t.project_id = ?"
                params.append(project_id)

            query += " ORDER BY t.due_date ASC LIMIT ?"
            params.append(limit)

            cur.execute(query, params)
            return [Task.from_row(row) for row in cur.fetchall()]

    def get_overdue_tasks(self, limit: int = 10, project_id: Optional[int] = None) -> List[Task]:
        """Fetch overdue tasks ordered by how far overdue they are."""
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
                WHERE t.status != 'Done' 
                  AND t.due_date IS NOT NULL 
                  AND date(t.due_date) < date('now')
            """
            params = []
            if project_id and project_id > 0:
                query += " AND t.project_id = ?"
                params.append(project_id)

            query += " ORDER BY t.due_date ASC LIMIT ?"
            params.append(limit)

            cur.execute(query, params)
            return [Task.from_row(row) for row in cur.fetchall()]

    def export_tasks_to_csv(self, filepath: str, project_id: Optional[int] = None) -> int:
        """Export task records to standard CSV file format."""
        with self.db.connection() as conn:
            cur = conn.cursor()
            query = """
                SELECT 
                    t.id,
                    t.title,
                    t.description,
                    p.name as project_name,
                    COALESCE(m.name, 'Unassigned') as assignee_name,
                    COALESCE(m.email, '') as assignee_email,
                    t.status,
                    t.priority,
                    COALESCE(t.due_date, '') as due_date,
                    CASE 
                        WHEN t.status != 'Done' AND t.due_date IS NOT NULL AND date(t.due_date) < date('now') THEN 'YES' 
                        ELSE 'NO' 
                    END as is_overdue,
                    t.labels,
                    (SELECT COUNT(*) FROM checklist_items c WHERE c.task_id = t.id) as checklist_total,
                    (SELECT COUNT(*) FROM checklist_items c WHERE c.task_id = t.id AND c.is_completed = 1) as checklist_completed,
                    (SELECT COUNT(*) FROM comments cm WHERE cm.task_id = t.id) as comment_count,
                    t.created_at,
                    t.updated_at
                FROM tasks t
                JOIN projects p ON t.project_id = p.id
                LEFT JOIN members m ON t.assignee_id = m.id
                WHERE 1=1
            """
            params = []
            if project_id and project_id > 0:
                query += " AND t.project_id = ?"
                params.append(project_id)
            query += " ORDER BY p.name ASC, t.id ASC"

            cur.execute(query, params)
            rows = cur.fetchall()

        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Header
            writer.writerow([
                "Task ID", "Title", "Description", "Project", "Assignee", "Assignee Email",
                "Status", "Priority", "Due Date", "Is Overdue", "Labels",
                "Checklist Total", "Checklist Completed", "Comments Count",
                "Created At", "Updated At"
            ])
            for r in rows:
                writer.writerow([
                    r["id"],
                    r["title"],
                    r["description"],
                    r["project_name"],
                    r["assignee_name"],
                    r["assignee_email"],
                    r["status"],
                    r["priority"],
                    r["due_date"],
                    r["is_overdue"],
                    r["labels"],
                    r["checklist_total"],
                    r["checklist_completed"],
                    r["comment_count"],
                    r["created_at"],
                    r["updated_at"]
                ])

        logger.info("Exported %d tasks to %s", len(rows), filepath)
        return len(rows)
