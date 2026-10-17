"""
Project Data Model
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import sqlite3


@dataclass
class Project:
    id: int
    name: str
    description: str
    owner: str
    status: str  # 'Active', 'Completed', 'On Hold'
    deadline: Optional[str]
    created_at: str
    updated_at: str
    # Computed stats (optional)
    total_tasks: int = 0
    completed_tasks: int = 0
    in_progress_tasks: int = 0
    overdue_tasks: int = 0

    @property
    def progress_pct(self) -> int:
        """Percentage of completed tasks (0 - 100)."""
        if self.total_tasks == 0:
            return 0
        return int(round((self.completed_tasks / self.total_tasks) * 100))

    @classmethod
    def from_row(cls, row: sqlite3.Row, **extra) -> "Project":
        return cls(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            owner=row["owner"],
            status=row["status"],
            deadline=row["deadline"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            total_tasks=extra.get("total_tasks", 0),
            completed_tasks=extra.get("completed_tasks", 0),
            in_progress_tasks=extra.get("in_progress_tasks", 0),
            overdue_tasks=extra.get("overdue_tasks", 0)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner": self.owner,
            "status": self.status,
            "deadline": self.deadline,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "in_progress_tasks": self.in_progress_tasks,
            "overdue_tasks": self.overdue_tasks,
            "progress_pct": self.progress_pct
        }
