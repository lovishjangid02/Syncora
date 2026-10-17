"""
Activity Service
Audit trail and recent event logging for projects and tasks.
"""

from datetime import datetime
from typing import List, Optional
import logging
from database import db, DatabaseManager
from models.task import ActivityLog

logger = logging.getLogger("Syncora.ActivityService")


class ActivityService:
    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager

    def log_activity(
        self,
        action: str,
        user_name: str,
        details: str,
        project_id: Optional[int] = None,
        task_id: Optional[int] = None
    ):
        """Append an activity log entry."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.db.transaction() as cur:
                cur.execute("""
                    INSERT INTO activity_logs (project_id, task_id, user_name, action, details, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (project_id, task_id, user_name, action, details, now_str))
        except Exception as e:
            logger.error("Failed to write activity log: %s", e)

    def get_recent_activities(self, limit: int = 15, project_id: Optional[int] = None) -> List[ActivityLog]:
        """Fetch chronological recent activities, optionally scoped to a project."""
        with self.db.connection() as conn:
            cur = conn.cursor()
            if project_id:
                cur.execute("""
                    SELECT * FROM activity_logs 
                    WHERE project_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (project_id, limit))
            else:
                cur.execute("""
                    SELECT * FROM activity_logs 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))

            rows = cur.fetchall()
            return [ActivityLog.from_row(row) for row in rows]
