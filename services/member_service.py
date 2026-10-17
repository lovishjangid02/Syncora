"""
Member Service
Handles team member CRUD operations, role assignment, and individual workload metrics.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import re
import logging
from database import db, DatabaseManager
from models.member import Member

logger = logging.getLogger("Syncora.MemberService")

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class MemberService:
    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager

    def validate_member_data(self, name: str, email: str, role: str, member_id: Optional[int] = None) -> List[str]:
        """Validate member input data and check email uniqueness."""
        errors = []
        if not name or len(name.strip()) < 2:
            errors.append("Member name must be at least 2 characters.")
        if not email or not EMAIL_REGEX.match(email.strip()):
            errors.append("A valid email address is required (e.g., student@university.edu).")
        if role not in ("Admin", "Member", "Viewer"):
            errors.append("Role must be one of: Admin, Member, Viewer.")

        # Check for unique email
        with self.db.connection() as conn:
            cur = conn.cursor()
            if member_id:
                cur.execute("SELECT id FROM members WHERE LOWER(email) = LOWER(?) AND id != ?", (email.strip(), member_id))
            else:
                cur.execute("SELECT id FROM members WHERE LOWER(email) = LOWER(?)", (email.strip(),))
            if cur.fetchone():
                errors.append(f"A member with email '{email.strip()}' already exists.")

        return errors

    def get_all_members(self, include_stats: bool = True) -> List[Member]:
        """Fetch all team members with their task workload distribution."""
        with self.db.connection() as conn:
            cur = conn.cursor()
            if not include_stats:
                cur.execute("SELECT * FROM members ORDER BY name ASC")
                return [Member.from_row(row) for row in cur.fetchall()]

            cur.execute("""
                SELECT 
                    m.*,
                    COUNT(t.id) as assigned_tasks,
                    SUM(CASE WHEN t.status = 'In Progress' THEN 1 ELSE 0 END) as in_progress_tasks,
                    SUM(CASE WHEN t.status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN t.status != 'Done' AND t.due_date IS NOT NULL AND date(t.due_date) < date('now') THEN 1 ELSE 0 END) as overdue_tasks
                FROM members m
                LEFT JOIN tasks t ON m.id = t.assignee_id
                GROUP BY m.id
                ORDER BY m.name ASC
            """)
            rows = cur.fetchall()
            members = []
            for row in rows:
                members.append(Member.from_row(
                    row,
                    assigned_tasks=row["assigned_tasks"] or 0,
                    in_progress_tasks=row["in_progress_tasks"] or 0,
                    completed_tasks=row["completed_tasks"] or 0,
                    overdue_tasks=row["overdue_tasks"] or 0
                ))
            return members

    def get_member_by_id(self, member_id: int, include_stats: bool = True) -> Optional[Member]:
        """Fetch single member by ID."""
        with self.db.connection() as conn:
            cur = conn.cursor()
            if not include_stats:
                cur.execute("SELECT * FROM members WHERE id = ?", (member_id,))
                row = cur.fetchone()
                return Member.from_row(row) if row else None

            cur.execute("""
                SELECT 
                    m.*,
                    COUNT(t.id) as assigned_tasks,
                    SUM(CASE WHEN t.status = 'In Progress' THEN 1 ELSE 0 END) as in_progress_tasks,
                    SUM(CASE WHEN t.status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN t.status != 'Done' AND t.due_date IS NOT NULL AND date(t.due_date) < date('now') THEN 1 ELSE 0 END) as overdue_tasks
                FROM members m
                LEFT JOIN tasks t ON m.id = t.assignee_id
                WHERE m.id = ?
                GROUP BY m.id
            """, (member_id,))
            row = cur.fetchone()
            if not row:
                return None
            return Member.from_row(
                row,
                assigned_tasks=row["assigned_tasks"] or 0,
                in_progress_tasks=row["in_progress_tasks"] or 0,
                completed_tasks=row["completed_tasks"] or 0,
                overdue_tasks=row["overdue_tasks"] or 0
            )

    def create_member(
        self,
        name: str,
        email: str,
        role: str = "Member",
        avatar_color: str = "#3B82F6",
        current_user: str = "User"
    ) -> Member:
        """Create a new team member and record activity."""
        errors = self.validate_member_data(name, email, role)
        if errors:
            raise ValueError("; ".join(errors))

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaction() as cur:
            cur.execute("""
                INSERT INTO members (name, email, role, avatar_color, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (name.strip(), email.strip(), role, avatar_color, now_str))
            member_id = cur.lastrowid

            cur.execute("""
                INSERT INTO activity_logs (project_id, task_id, user_name, action, details, created_at)
                VALUES (NULL, NULL, ?, 'Member Added', ?, ?)
            """, (current_user, f"Added team member {name.strip()} ({role})", now_str))

        logger.info("Team member '%s' (ID %d) created", name, member_id)
        return self.get_member_by_id(member_id)

    def update_member(
        self,
        member_id: int,
        name: str,
        email: str,
        role: str = "Member",
        avatar_color: str = "#3B82F6",
        current_user: str = "User"
    ) -> Optional[Member]:
        """Update existing team member."""
        errors = self.validate_member_data(name, email, role, member_id=member_id)
        if errors:
            raise ValueError("; ".join(errors))

        old_member = self.get_member_by_id(member_id, include_stats=False)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaction() as cur:
            cur.execute("""
                UPDATE members
                SET name = ?, email = ?, role = ?, avatar_color = ?
                WHERE id = ?
            """, (name.strip(), email.strip(), role, avatar_color, member_id))

            if cur.rowcount == 0:
                return None

            if old_member and old_member.name != name.strip():
                cur.execute("UPDATE projects SET owner = ? WHERE owner = ?", (name.strip(), old_member.name))

            cur.execute("""
                INSERT INTO activity_logs (project_id, task_id, user_name, action, details, created_at)
                VALUES (NULL, NULL, ?, 'Member Updated', ?, ?)
            """, (current_user, f"Updated team member {name.strip()}", now_str))

        return self.get_member_by_id(member_id)

    def delete_member(self, member_id: int, current_user: str = "User") -> bool:
        """Delete member; assigned tasks will have their assignee_id set to NULL automatically."""
        mem = self.get_member_by_id(member_id, include_stats=False)
        if not mem:
            return False

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM members WHERE id = ?", (member_id,))
            cur.execute("""
                INSERT INTO activity_logs (project_id, task_id, user_name, action, details, created_at)
                VALUES (NULL, NULL, ?, 'Member Removed', ?, ?)
            """, (current_user, f"Removed team member {mem.name}", now_str))

        logger.info("Member ID %d deleted", member_id)
        return True
