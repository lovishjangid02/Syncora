"""
Kanban Task Card Component
Renders an interactive task card with priority, status badges, checklist counts,
assignee info, quick-move action controls, and click-to-view details.
"""

import customtkinter as ctk
from typing import Callable, Optional
from models.task import Task
from ui.theme import COLORS, FONTS, RADII
from ui.components.badges import PriorityBadge, TagBadge, AvatarBadge


class TaskCard(ctk.CTkFrame):
    """Interactive card representation of a task inside a Kanban column."""

    STATUS_ORDER = ["Backlog", "In Progress", "Review", "Done"]

    def __init__(
        self,
        master,
        task: Task,
        on_click: Optional[Callable[[Task], None]] = None,
        on_status_change: Optional[Callable[[int, str], None]] = None,
        on_edit: Optional[Callable[[Task], None]] = None,
        on_delete: Optional[Callable[[Task], None]] = None,
        can_edit: bool = True,
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=RADII["medium"],
            **kwargs
        )
        self.task = task
        self.on_click = on_click
        self.on_status_change = on_status_change
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.can_edit = can_edit

        # Hover state
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        self._build_card()

    def _build_card(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=12, pady=10)

        # Row 1: Priority Badge + Due Date / Overdue Indicator
        header_row = ctk.CTkFrame(container, fg_color="transparent")
        header_row.pack(fill="x", side="top", pady=(0, 6))

        # Priority
        p_badge = PriorityBadge(header_row, priority=self.task.priority)
        p_badge.pack(side="left")

        # Due Date / Overdue
        if self.task.due_date:
            due_frame = ctk.CTkFrame(header_row, fg_color="transparent")
            due_frame.pack(side="right")

            if self.task.is_overdue:
                overdue_badge = ctk.CTkFrame(
                    due_frame,
                    fg_color=COLORS["danger_light"],
                    border_color=COLORS["danger"],
                    border_width=1,
                    corner_radius=RADII["small"],
                    height=20
                )
                overdue_badge.pack(side="right", padx=(4, 0))
                lbl = ctk.CTkLabel(
                    overdue_badge,
                    text="OVERDUE",
                    font=FONTS["badge"],
                    text_color=COLORS["danger"],
                    padx=5
                )
                lbl.pack()

            date_str = self.task.due_date
            date_lbl = ctk.CTkLabel(
                due_frame,
                text=f"📅 {date_str}",
                font=FONTS["small"],
                text_color=COLORS["danger"] if self.task.is_overdue else COLORS["text_muted"]
            )
            date_lbl.pack(side="right")

        # Row 2: Project tag
        if self.task.project_name:
            proj_lbl = ctk.CTkLabel(
                container,
                text=self.task.project_name.upper(),
                font=FONTS["badge"],
                text_color=COLORS["primary"],
                anchor="w"
            )
            proj_lbl.pack(fill="x", pady=(0, 2))

        # Row 3: Task Title
        title_lbl = ctk.CTkLabel(
            container,
            text=self.task.title,
            font=FONTS["card_title"],
            text_color=COLORS["text_primary"],
            wraplength=230,
            justify="left",
            anchor="w"
        )
        title_lbl.pack(fill="x", pady=(0, 6))
        title_lbl.bind("<Button-1>", lambda e: self._handle_click())

        # Row 4: Labels
        if self.task.label_list:
            labels_frame = ctk.CTkFrame(container, fg_color="transparent")
            labels_frame.pack(fill="x", pady=(0, 8))
            for lbl in self.task.label_list[:3]:  # show up to 3 labels
                tb = TagBadge(labels_frame, text=lbl)
                tb.pack(side="left", padx=(0, 4))
                tb.bind("<Button-1>", lambda e: self._handle_click())

        # Divider line
        div = ctk.CTkFrame(container, fg_color=COLORS["border"], height=1)
        div.pack(fill="x", pady=(2, 8))

        # Row 5: Footer (Assignee + Checklist/Comment Counters + Quick Move Controls)
        footer = ctk.CTkFrame(container, fg_color="transparent")
        footer.pack(fill="x", side="bottom")

        # Left side: Assignee
        left_foot = ctk.CTkFrame(footer, fg_color="transparent")
        left_foot.pack(side="left")

        avatar = AvatarBadge(
            left_foot,
            name=self.task.assignee_name,
            color=self.task.assignee_color,
            size=22
        )
        avatar.pack(side="left", padx=(0, 4))

        assignee_lbl = ctk.CTkLabel(
            left_foot,
            text=self.task.assignee_name.split()[0] if self.task.assignee_name != "Unassigned" else "Unassigned",
            font=FONTS["small_bold"],
            text_color=COLORS["text_secondary"]
        )
        assignee_lbl.pack(side="left")

        # Right side: Checklist & Comment counters
        indicators = ctk.CTkFrame(footer, fg_color="transparent")
        indicators.pack(side="right")

        if self.task.checklist_total > 0:
            chk_color = COLORS["success"] if self.task.checklist_completed == self.task.checklist_total else COLORS["text_muted"]
            chk_lbl = ctk.CTkLabel(
                indicators,
                text=f"☑ {self.task.checklist_completed}/{self.task.checklist_total}",
                font=FONTS["small_bold"],
                text_color=chk_color
            )
            chk_lbl.pack(side="left", padx=(0, 6))

        if self.task.comment_count > 0:
            comm_lbl = ctk.CTkLabel(
                indicators,
                text=f"💬 {self.task.comment_count}",
                font=FONTS["small"],
                text_color=COLORS["text_muted"]
            )
            comm_lbl.pack(side="left", padx=(0, 6))

        # Row 6: Quick Movement Arrows & Actions (if allowed)
        if self.can_edit:
            action_row = ctk.CTkFrame(container, fg_color="transparent")
            action_row.pack(fill="x", pady=(6, 0))

            # Current index in STATUS_ORDER
            cur_idx = self.STATUS_ORDER.index(self.task.status) if self.task.status in self.STATUS_ORDER else 0

            # Move left button
            if cur_idx > 0:
                prev_status = self.STATUS_ORDER[cur_idx - 1]
                left_btn = ctk.CTkButton(
                    action_row,
                    text=f"◀ {prev_status}",
                    font=("Segoe UI", 9),
                    fg_color=COLORS["bg_card_secondary"],
                    hover_color=COLORS["border"],
                    text_color=COLORS["text_secondary"],
                    width=65,
                    height=22,
                    corner_radius=RADII["small"],
                    command=lambda: self._move_status(prev_status)
                )
                left_btn.pack(side="left")

            # Move right button
            if cur_idx < len(self.STATUS_ORDER) - 1:
                next_status = self.STATUS_ORDER[cur_idx + 1]
                right_btn = ctk.CTkButton(
                    action_row,
                    text=f"{next_status} ▶",
                    font=("Segoe UI", 9, "bold"),
                    fg_color=COLORS["primary_light"],
                    hover_color=COLORS["primary"],
                    text_color=COLORS["primary"],
                    width=75,
                    height=22,
                    corner_radius=RADII["small"],
                    command=lambda: self._move_status(next_status)
                )
                right_btn.pack(side="right")

        # Make entire card clickable
        for child in [container, header_row]:
            child.bind("<Button-1>", lambda e: self._handle_click())

    def _move_status(self, target_status: str):
        if self.on_status_change:
            self.on_status_change(self.task.id, target_status)

    def _handle_click(self):
        if self.on_click:
            self.on_click(self.task)

    def _on_enter(self, event):
        self.configure(border_color=COLORS["border_focus"])

    def _on_leave(self, event):
        self.configure(border_color=COLORS["border"])
