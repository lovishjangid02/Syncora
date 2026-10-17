"""
Member Data Model
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import sqlite3


@dataclass
class Member:
    id: int
    name: str
    email: str
    role: str  # 'Admin', 'Member', 'Viewer'
    avatar_color: str
    created_at: str
    # Computed stats (optional)
    assigned_tasks: int = 0
    in_progress_tasks: int = 0
    completed_tasks: int = 0
    overdue_tasks: int = 0

    @property
    def initials(self) -> str:
        parts = self.name.strip().split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        elif parts:
            return parts[0][:2].upper()
        return "??"

    @property
    def workload_score(self) -> int:
        """Workload load score: In Progress counts 2x, Backlog/Review counts 1x."""
        return self.in_progress_tasks * 2 + (self.assigned_tasks - self.completed_tasks - self.in_progress_tasks)

    @classmethod
    def from_row(cls, row: sqlite3.Row, **extra) -> "Member":
        return cls(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            role=row["role"],
            avatar_color=row["avatar_color"] or "#3B82F6",
            created_at=row["created_at"],
            assigned_tasks=extra.get("assigned_tasks", 0),
            in_progress_tasks=extra.get("in_progress_tasks", 0),
            completed_tasks=extra.get("completed_tasks", 0),
            overdue_tasks=extra.get("overdue_tasks", 0)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "avatar_color": self.avatar_color,
            "created_at": self.created_at,
            "assigned_tasks": self.assigned_tasks,
            "in_progress_tasks": self.in_progress_tasks,
            "completed_tasks": self.completed_tasks,
            "overdue_tasks": self.overdue_tasks,
            "initials": self.initials
        }
