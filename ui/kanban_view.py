"""
Interactive Kanban Board View
Four-column visual workflow (Backlog, In Progress, Review, Done) with real-time status transitions,
multi-criteria filtering, search, and task details integration.
"""

import customtkinter as ctk
from typing import Optional, Callable, Dict, List
from models.task import Task
from services import task_service, project_service, member_service
from ui.theme import COLORS, FONTS, RADII, ROLES
from ui.components.task_card import TaskCard
from ui.components.cards import ConfirmDialog


class KanbanView(ctk.CTkFrame):
    """Interactive 4-column Agile Kanban Board."""

    COLUMNS = [
        ("Backlog", "#64748B", "📋"),
        ("In Progress", "#3B82F6", "⚡"),
        ("Review", "#8B5CF6", "👁"),
        ("Done", "#10B981", "✓")
    ]

    def __init__(
        self,
        master,
        current_project_id: Optional[int] = None,
        current_user: str = "User",
        user_role: str = "Admin",
        on_open_task: Optional[Callable[[Task], None]] = None,
        on_create_task: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.current_project_id = current_project_id
        self.current_user = current_user
        self.user_role = user_role
        self.on_open_task = on_open_task
        self.on_create_task = on_create_task

        # Filter states
        self.selected_assignee_id: Optional[int] = None
        self.selected_priority: str = "All"
        self.selected_label: str = "All"
        self.search_query: str = ""

        # Column card container references
        self.column_containers: Dict[str, ctk.CTkScrollableFrame] = {}
        self.column_badges: Dict[str, ctk.CTkLabel] = {}

        self._build_ui()

    def set_project(self, project_id: Optional[int]):
        """Change the active project filter and reload cards."""
        self.current_project_id = project_id
        self.refresh()

    def refresh(self):
        """Reload all tasks from database and refresh column cards."""
        self._load_cards()

    def _build_ui(self):
        # 1. Filter & Controls Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=62, corner_radius=RADII["medium"], border_color=COLORS["border"], border_width=1)
        toolbar.pack(fill="x", padx=20, pady=(16, 12))

        # Search Entry
        search_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        search_box.pack(side="left", padx=(14, 8), pady=12)

        self.search_entry = ctk.CTkEntry(
            search_box,
            placeholder_text="🔍 Search tasks...",
            font=FONTS["body"],
            width=180,
            height=34,
            corner_radius=RADII["small"]
        )
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search_changed())

        # Project Filter
        projects = project_service.get_all_projects(include_stats=False)
        self.proj_options = ["All Projects"] + [f"{p.id}: {p.name}" for p in projects]
        default_proj = "All Projects"
        if self.current_project_id:
            for opt in self.proj_options:
                if opt.startswith(f"{self.current_project_id}:"):
                    default_proj = opt
                    break

        self.proj_combo = ctk.CTkComboBox(
            toolbar,
            values=self.proj_options,
            command=self._on_project_filter,
            width=170,
            height=34,
            corner_radius=RADII["small"],
            font=FONTS["body"]
        )
        self.proj_combo.set(default_proj)
        self.proj_combo.pack(side="left", padx=4, pady=12)

        # Assignee Filter
        members = member_service.get_all_members(include_stats=False)
        self.member_options = ["All Assignees", "Unassigned"] + [f"{m.id}: {m.name}" for m in members]

        self.assignee_combo = ctk.CTkComboBox(
            toolbar,
            values=self.member_options,
            command=self._on_assignee_filter,
            width=150,
            height=34,
            corner_radius=RADII["small"],
            font=FONTS["body"]
        )
        self.assignee_combo.set("All Assignees")
        self.assignee_combo.pack(side="left", padx=4, pady=12)

        # Priority Filter
        self.prio_combo = ctk.CTkComboBox(
            toolbar,
            values=["All Priorities", "High", "Medium", "Low"],
            command=self._on_priority_filter,
            width=120,
            height=34,
            corner_radius=RADII["small"],
            font=FONTS["body"]
        )
        self.prio_combo.set("All Priorities")
        self.prio_combo.pack(side="left", padx=4, pady=12)

        # Clear Filters Button
        clear_btn = ctk.CTkButton(
            toolbar,
            text="Clear Filters",
            font=FONTS["small"],
            fg_color=COLORS["bg_card_secondary"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_secondary"],
            width=85,
            height=34,
            corner_radius=RADII["small"],
            command=self._clear_filters
        )
        clear_btn.pack(side="left", padx=6, pady=12)

        # Quick Add Task Button
        can_create = ROLES.get(self.user_role, {}).get("can_create_task", True)
        if can_create:
            add_btn = ctk.CTkButton(
                toolbar,
                text="+ New Task",
                font=FONTS["body_bold"],
                fg_color=COLORS["primary"],
                hover_color=COLORS["primary_hover"],
                height=34,
                corner_radius=RADII["small"],
                command=lambda: self.on_create_task("Backlog") if self.on_create_task else None
            )
            add_btn.pack(side="right", padx=14, pady=12)

        # 2. Four Kanban Columns Container
        board_container = ctk.CTkFrame(self, fg_color="transparent")
        board_container.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        for col_idx in range(4):
            board_container.grid_columnconfigure(col_idx, weight=1, uniform="col")
        board_container.grid_rowconfigure(0, weight=1)

        for idx, (status_name, accent_col, icon) in enumerate(self.COLUMNS):
            col_frame = ctk.CTkFrame(
                board_container,
                fg_color=COLORS["bg_card"],
                border_color=COLORS["border"],
                border_width=1,
                corner_radius=RADII["medium"]
            )
            col_frame.grid(row=0, column=idx, padx=6, pady=0, sticky="nsew")

            # Column Header
            col_hdr = ctk.CTkFrame(col_frame, fg_color="transparent")
            col_hdr.pack(fill="x", padx=14, pady=12)

            # Left: Icon + Title
            left_hdr = ctk.CTkFrame(col_hdr, fg_color="transparent")
            left_hdr.pack(side="left")

            dot = ctk.CTkLabel(left_hdr, text=icon, font=("Segoe UI", 12), text_color=accent_col)
            dot.pack(side="left", padx=(0, 6))

            title = ctk.CTkLabel(left_hdr, text=status_name, font=FONTS["card_title"], text_color=COLORS["text_primary"])
            title.pack(side="left")

            # Right: Count Badge + Add Task (+)
            right_hdr = ctk.CTkFrame(col_hdr, fg_color="transparent")
            right_hdr.pack(side="right")

            badge = ctk.CTkLabel(
                right_hdr,
                text="0",
                font=FONTS["badge"],
                fg_color=COLORS["bg_card_secondary"],
                text_color=COLORS["text_secondary"],
                corner_radius=RADII["pill"],
                width=24,
                height=22
            )
            badge.pack(side="left", padx=(0, 6))
            self.column_badges[status_name] = badge

            if can_create:
                quick_add = ctk.CTkButton(
                    right_hdr,
                    text="+",
                    font=FONTS["body_bold"],
                    width=22,
                    height=22,
                    fg_color="transparent",
                    hover_color=COLORS["bg_card_secondary"],
                    text_color=COLORS["text_secondary"],
                    command=lambda s=status_name: self.on_create_task(s) if self.on_create_task else None
                )
                quick_add.pack(side="left")

            # Scrollable card container for this column
            card_scroll = ctk.CTkScrollableFrame(col_frame, fg_color="transparent")
            card_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 10))
            self.column_containers[status_name] = card_scroll

        # Initial card loading
        self._load_cards()

    def _load_cards(self):
        # Clear existing cards in all columns
        for status_name, container in self.column_containers.items():
            for widget in container.winfo_children():
                widget.destroy()

        # Query tasks with current filters
        tasks = task_service.get_tasks(
            project_id=self.current_project_id,
            assignee_id=self.selected_assignee_id,
            priority=self.selected_priority if self.selected_priority != "All Priorities" else None,
            label=self.selected_label if self.selected_label != "All" else None,
            search_query=self.search_query
        )

        can_edit = ROLES.get(self.user_role, {}).get("can_edit_task", True)

        # Partition by column status
        counts = {s[0]: 0 for s in self.COLUMNS}

        for task in tasks:
            if task.status in self.column_containers:
                counts[task.status] += 1
                card = TaskCard(
                    self.column_containers[task.status],
                    task=task,
                    on_click=self._on_card_clicked,
                    on_status_change=self._on_card_status_move,
                    can_edit=can_edit
                )
                card.pack(fill="x", pady=5)

        # Update badge counters and render empty states if column has 0 tasks
        for status_name, count in counts.items():
            if status_name in self.column_badges:
                self.column_badges[status_name].configure(text=str(count))

            if count == 0 and status_name in self.column_containers:
                empty = ctk.CTkLabel(
                    self.column_containers[status_name],
                    text="No tasks in this column",
                    font=FONTS["small"],
                    text_color=COLORS["text_muted"],
                    pady=30
                )
                empty.pack()

    def _on_card_clicked(self, task: Task):
        if self.on_open_task:
            self.on_open_task(task)

    def _on_card_status_move(self, task_id: int, new_status: str):
        try:
            task_service.update_task_status(task_id, new_status, current_user=self.current_user)
            self._load_cards()
        except Exception as e:
            pass

    def _on_search_changed(self):
        self.search_query = self.search_entry.get().strip()
        self._load_cards()

    def _on_project_filter(self, choice: str):
        if choice == "All Projects":
            self.current_project_id = None
        else:
            try:
                self.current_project_id = int(choice.split(":")[0])
            except ValueError:
                self.current_project_id = None
        self._load_cards()

    def _on_assignee_filter(self, choice: str):
        if choice == "All Assignees":
            self.selected_assignee_id = None
        elif choice == "Unassigned":
            self.selected_assignee_id = -1
        else:
            try:
                self.selected_assignee_id = int(choice.split(":")[0])
            except ValueError:
                self.selected_assignee_id = None
        self._load_cards()

    def _on_priority_filter(self, choice: str):
        self.selected_priority = choice
        self._load_cards()

    def _clear_filters(self):
        self.search_entry.delete(0, "end")
        self.search_query = ""
        self.proj_combo.set("All Projects")
        self.current_project_id = None
        self.assignee_combo.set("All Assignees")
        self.selected_assignee_id = None
        self.prio_combo.set("All Priorities")
        self.selected_priority = "All"
        self._load_cards()
