"""
Task and Related Data Models (Checklists, Comments, Activity Logs)
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import sqlite3


@dataclass
class ChecklistItem:
    id: int
    task_id: int
    title: str
    is_completed: bool
    created_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "ChecklistItem":
        return cls(
            id=row["id"],
            task_id=row["task_id"],
            title=row["title"],
            is_completed=bool(row["is_completed"]),
            created_at=row["created_at"]
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "title": self.title,
            "is_completed": self.is_completed,
            "created_at": self.created_at
        }


@dataclass
class Comment:
    id: int
    task_id: int
    member_id: Optional[int]
    author_name: str
    content: str
    created_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Comment":
        return cls(
            id=row["id"],
            task_id=row["task_id"],
            member_id=row["member_id"],
            author_name=row["author_name"],
            content=row["content"],
            created_at=row["created_at"]
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "member_id": self.member_id,
            "author_name": self.author_name,
            "content": self.content,
            "created_at": self.created_at
        }


@dataclass
class ActivityLog:
    id: int
    project_id: Optional[int]
    task_id: Optional[int]
    user_name: str
    action: str
    details: str
    created_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "ActivityLog":
        return cls(
            id=row["id"],
            project_id=row["project_id"],
            task_id=row["task_id"],
            user_name=row["user_name"],
            action=row["action"],
            details=row["details"] or "",
            created_at=row["created_at"]
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "task_id": self.task_id,
            "user_name": self.user_name,
            "action": self.action,
            "details": self.details,
            "created_at": self.created_at
        }


@dataclass
class Task:
    id: int
    title: str
    description: str
    project_id: int
    assignee_id: Optional[int]
    status: str  # 'Backlog', 'In Progress', 'Review', 'Done'
    priority: str  # 'Low', 'Medium', 'High'
    due_date: Optional[str]  # 'YYYY-MM-DD'
    labels: str  # comma separated
    order_index: int
    created_at: str
    updated_at: str
    # Joined extra data
    project_name: str = ""
    assignee_name: str = "Unassigned"
    assignee_color: str = "#64748B"
    checklist_total: int = 0
    checklist_completed: int = 0
    comment_count: int = 0

    @property
    def label_list(self) -> List[str]:
        if not self.labels:
            return []
        return [lbl.strip() for lbl in self.labels.split(",") if lbl.strip()]

    @property
    def is_overdue(self) -> bool:
        if self.status == "Done" or not self.due_date:
            return False
        try:
            due = datetime.strptime(self.due_date, "%Y-%m-%d").date()
            return due < date.today()
        except ValueError:
            return False

    @property
    def days_remaining(self) -> Optional[int]:
        if not self.due_date:
            return None
        try:
            due = datetime.strptime(self.due_date, "%Y-%m-%d").date()
            delta = due - date.today()
            return delta.days
        except ValueError:
            return None

    @property
    def checklist_progress_pct(self) -> int:
        if self.checklist_total == 0:
            return 0
        return int(round((self.checklist_completed / self.checklist_total) * 100))

    @classmethod
    def from_row(cls, row: sqlite3.Row, **extra) -> "Task":
        return cls(
            id=row["id"],
            title=row["title"],
            description=row["description"] or "",
            project_id=row["project_id"],
            assignee_id=row["assignee_id"],
            status=row["status"],
            priority=row["priority"],
            due_date=row["due_date"],
            labels=row["labels"] or "",
            order_index=row["order_index"] if "order_index" in row.keys() else 0,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            project_name=extra.get("project_name", row["project_name"] if "project_name" in row.keys() else ""),
            assignee_name=extra.get("assignee_name", row["assignee_name"] if "assignee_name" in row.keys() else "Unassigned"),
            assignee_color=extra.get("assignee_color", row["assignee_color"] if "assignee_color" in row.keys() else "#64748B"),
            checklist_total=extra.get("checklist_total", row["checklist_total"] if "checklist_total" in row.keys() else 0),
            checklist_completed=extra.get("checklist_completed", row["checklist_completed"] if "checklist_completed" in row.keys() else 0),
            comment_count=extra.get("comment_count", row["comment_count"] if "comment_count" in row.keys() else 0)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "project_id": self.project_id,
            "project_name": self.project_name,
            "assignee_id": self.assignee_id,
            "assignee_name": self.assignee_name,
            "assignee_color": self.assignee_color,
            "status": self.status,
            "priority": self.priority,
            "due_date": self.due_date,
            "is_overdue": self.is_overdue,
            "days_remaining": self.days_remaining,
            "labels": self.label_list,
            "order_index": self.order_index,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "checklist_total": self.checklist_total,
            "checklist_completed": self.checklist_completed,
            "checklist_progress_pct": self.checklist_progress_pct,
            "comment_count": self.comment_count
        }
