"""
Task Creation & Editing Dialog
Provides form inputs, validation, quick date shortcuts, checklist item additions, and saving.
"""

import customtkinter as ctk
from datetime import datetime, timedelta
from typing import Optional, Callable, List
from models.task import Task
from services import task_service, project_service, member_service
from ui.theme import COLORS, FONTS, RADII


class TaskDialog(ctk.CTkToplevel):
    """Modal dialog for creating and editing tasks."""

    def __init__(
        self,
        parent,
        task: Optional[Task] = None,
        default_project_id: Optional[int] = None,
        default_status: str = "Backlog",
        current_user: str = "User",
        on_saved: Optional[Callable[[Task], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.task = task
        self.default_project_id = default_project_id or (task.project_id if task else None)
        self.default_status = task.status if task else default_status
        self.current_user = current_user
        self.on_saved = on_saved

        self.title("Edit Task" if self.task else "Create New Task")
        self.geometry("620x720")
        self.minsize(580, 650)
        self.configure(fg_color=COLORS["bg_main"])

        self.transient(parent)
        self.grab_set()

        # Center relative to parent
        self.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() - 620) // 2
            y = parent.winfo_y() + (parent.winfo_height() - 720) // 2
            self.geometry(f"+{max(10, x)}+{max(10, y)}")
        except Exception:
            pass

        # Load projects and members
        self.projects = project_service.get_all_projects(include_stats=False)
        self.members = member_service.get_all_members(include_stats=False)

        # Temporary list for new checklist items if creating
        self.temp_checklist_items: List[str] = []

        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=60, corner_radius=0)
        header.pack(fill="x", side="top")

        h_title = ctk.CTkLabel(
            header,
            text="✏️  Edit Task" if self.task else "✨  Create New Task",
            font=FONTS["card_title"],
            text_color=COLORS["text_primary"],
            padx=20,
            pady=16
        )
        h_title.pack(side="left")

        # Scrollable form container
        form_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # Error notification banner (hidden by default)
        self.error_banner = ctk.CTkLabel(
            form_scroll,
            text="",
            font=FONTS["small_bold"],
            text_color=COLORS["danger"],
            fg_color=COLORS["danger_light"],
            corner_radius=RADII["small"],
            height=30
        )

        # 1. Title
        title_lbl = ctk.CTkLabel(form_scroll, text="Task Title *", font=FONTS["body_bold"], text_color=COLORS["text_primary"])
        title_lbl.pack(anchor="w", pady=(10, 4))
        self.title_entry = ctk.CTkEntry(
            form_scroll,
            placeholder_text="e.g., Implement OAuth authentication flow",
            font=FONTS["body"],
            height=38,
            corner_radius=RADII["small"]
        )
        self.title_entry.pack(fill="x", pady=(0, 10))
        if self.task:
            self.title_entry.insert(0, self.task.title)

        # 2. Description
        desc_lbl = ctk.CTkLabel(form_scroll, text="Description", font=FONTS["body_bold"], text_color=COLORS["text_primary"])
        desc_lbl.pack(anchor="w", pady=(5, 4))
        self.desc_text = ctk.CTkTextbox(
            form_scroll,
            font=FONTS["body"],
            height=90,
            corner_radius=RADII["small"]
        )
        self.desc_text.pack(fill="x", pady=(0, 10))
        if self.task and self.task.description:
            self.desc_text.insert("1.0", self.task.description)

        # Row: Project & Assignee
        proj_assign_row = ctk.CTkFrame(form_scroll, fg_color="transparent")
        proj_assign_row.pack(fill="x", pady=(0, 10))

        # Project selection
        proj_col = ctk.CTkFrame(proj_assign_row, fg_color="transparent")
        proj_col.pack(side="left", fill="x", expand=True, padx=(0, 8))

        proj_lbl = ctk.CTkLabel(proj_col, text="Project *", font=FONTS["body_bold"], text_color=COLORS["text_primary"])
        proj_lbl.pack(anchor="w", pady=(0, 4))

        self.project_names = [f"{p.id}: {p.name}" for p in self.projects]
        default_proj_name = self.project_names[0] if self.project_names else "No Projects Available"
        if self.default_project_id:
            for pname in self.project_names:
                if pname.startswith(f"{self.default_project_id}:"):
                    default_proj_name = pname
                    break

        self.project_combo = ctk.CTkComboBox(
            proj_col,
            values=self.project_names if self.project_names else ["No Projects Available"],
            height=36,
            corner_radius=RADII["small"],
            font=FONTS["body"]
        )
        self.project_combo.set(default_proj_name)
        self.project_combo.pack(fill="x")

        # Assignee selection
        assign_col = ctk.CTkFrame(proj_assign_row, fg_color="transparent")
        assign_col.pack(side="left", fill="x", expand=True, padx=(8, 0))

        assign_lbl = ctk.CTkLabel(assign_col, text="Assignee", font=FONTS["body_bold"], text_color=COLORS["text_primary"])
        assign_lbl.pack(anchor="w", pady=(0, 4))

        self.member_options = ["None (Unassigned)"] + [f"{m.id}: {m.name} ({m.role})" for m in self.members]
        default_assign_name = "None (Unassigned)"
        if self.task and self.task.assignee_id:
            for mopt in self.member_options:
                if mopt.startswith(f"{self.task.assignee_id}:"):
                    default_assign_name = mopt
                    break

        self.assignee_combo = ctk.CTkComboBox(
            assign_col,
            values=self.member_options,
            height=36,
            corner_radius=RADII["small"],
            font=FONTS["body"]
        )
        self.assignee_combo.set(default_assign_name)
        self.assignee_combo.pack(fill="x")

        # Row: Status & Priority
        stat_prio_row = ctk.CTkFrame(form_scroll, fg_color="transparent")
        stat_prio_row.pack(fill="x", pady=(0, 10))

        # Status
        stat_col = ctk.CTkFrame(stat_prio_row, fg_color="transparent")
        stat_col.pack(side="left", fill="x", expand=True, padx=(0, 8))

        stat_lbl = ctk.CTkLabel(stat_col, text="Status", font=FONTS["body_bold"], text_color=COLORS["text_primary"])
        stat_lbl.pack(anchor="w", pady=(0, 4))

        self.status_combo = ctk.CTkComboBox(
            stat_col,
            values=["Backlog", "In Progress", "Review", "Done"],
            height=36,
            corner_radius=RADII["small"],
            font=FONTS["body"]
        )
        self.status_combo.set(self.default_status)
        self.status_combo.pack(fill="x")

        # Priority
        prio_col = ctk.CTkFrame(stat_prio_row, fg_color="transparent")
        prio_col.pack(side="left", fill="x", expand=True, padx=(8, 0))

        prio_lbl = ctk.CTkLabel(prio_col, text="Priority", font=FONTS["body_bold"], text_color=COLORS["text_primary"])
        prio_lbl.pack(anchor="w", pady=(0, 4))

        self.priority_combo = ctk.CTkComboBox(
            prio_col,
            values=["Low", "Medium", "High"],
            height=36,
            corner_radius=RADII["small"],
            font=FONTS["body"]
        )
        self.priority_combo.set(self.task.priority if self.task else "Medium")
        self.priority_combo.pack(fill="x")

        # 3. Due Date & Quick shortcuts
        due_lbl = ctk.CTkLabel(form_scroll, text="Due Date (YYYY-MM-DD)", font=FONTS["body_bold"], text_color=COLORS["text_primary"])
        due_lbl.pack(anchor="w", pady=(5, 4))

        due_row = ctk.CTkFrame(form_scroll, fg_color="transparent")
        due_row.pack(fill="x", pady=(0, 10))

        self.due_entry = ctk.CTkEntry(
            due_row,
            placeholder_text="YYYY-MM-DD (e.g. 2026-10-25)",
            font=FONTS["body"],
            height=36,
            corner_radius=RADII["small"]
        )
        self.due_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        if self.task and self.task.due_date:
            self.due_entry.insert(0, self.task.due_date)

        # Quick date buttons
        btn_today = ctk.CTkButton(
            due_row,
            text="+Today",
            width=55,
            height=32,
            font=FONTS["small"],
            fg_color=COLORS["bg_card_secondary"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            command=lambda: self._set_quick_date(0)
        )
        btn_today.pack(side="left", padx=2)

        btn_3d = ctk.CTkButton(
            due_row,
            text="+3d",
            width=48,
            height=32,
            font=FONTS["small"],
            fg_color=COLORS["bg_card_secondary"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            command=lambda: self._set_quick_date(3)
        )
        btn_3d.pack(side="left", padx=2)

        btn_1w = ctk.CTkButton(
            due_row,
            text="+1w",
            width=48,
            height=32,
            font=FONTS["small"],
            fg_color=COLORS["bg_card_secondary"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            command=lambda: self._set_quick_date(7)
        )
        btn_1w.pack(side="left", padx=2)

        # 4. Labels
        label_lbl = ctk.CTkLabel(
            form_scroll,
            text="Labels (comma separated, e.g. frontend, ui, critical)",
            font=FONTS["body_bold"],
            text_color=COLORS["text_primary"]
        )
        label_lbl.pack(anchor="w", pady=(5, 4))

        self.labels_entry = ctk.CTkEntry(
            form_scroll,
            placeholder_text="frontend, database, bug, urgent",
            font=FONTS["body"],
            height=36,
            corner_radius=RADII["small"]
        )
        self.labels_entry.pack(fill="x", pady=(0, 12))
        if self.task and self.task.labels:
            self.labels_entry.insert(0, self.task.labels)

        # 5. Initial Checklist Items (Only for New Task creation)
        if not self.task:
            chk_header = ctk.CTkLabel(
                form_scroll,
                text="Initial Checklist Items (Optional)",
                font=FONTS["body_bold"],
                text_color=COLORS["text_primary"]
            )
            chk_header.pack(anchor="w", pady=(5, 4))

            add_chk_row = ctk.CTkFrame(form_scroll, fg_color="transparent")
            add_chk_row.pack(fill="x", pady=(0, 6))

            self.new_chk_entry = ctk.CTkEntry(
                add_chk_row,
                placeholder_text="Add item (e.g. Write test cases)",
                font=FONTS["body"],
                height=34,
                corner_radius=RADII["small"]
            )
            self.new_chk_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
            self.new_chk_entry.bind("<Return>", lambda e: self._add_temp_chk())

            add_chk_btn = ctk.CTkButton(
                add_chk_row,
                text="+ Add",
                font=FONTS["body_bold"],
                width=70,
                height=34,
                fg_color=COLORS["secondary"],
                hover_color=COLORS["secondary_hover"],
                command=self._add_temp_chk
            )
            add_chk_btn.pack(side="right")

            self.chk_list_frame = ctk.CTkFrame(form_scroll, fg_color=COLORS["bg_card"], corner_radius=RADII["small"])
            self.chk_list_frame.pack(fill="x", pady=(0, 10))
            self._render_temp_chk_items()

        # Bottom Actions Bar
        actions_bar = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=65, corner_radius=0)
        actions_bar.pack(fill="x", side="bottom")

        cancel_btn = ctk.CTkButton(
            actions_bar,
            text="Cancel",
            font=FONTS["body"],
            fg_color=COLORS["bg_card_secondary"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            command=self.destroy,
            width=100,
            height=38,
            corner_radius=RADII["small"]
        )
        cancel_btn.pack(side="right", padx=16, pady=14)

        save_btn = ctk.CTkButton(
            actions_bar,
            text="Save Task" if self.task else "Create Task",
            font=FONTS["body_bold"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=self._save_task,
            width=130,
            height=38,
            corner_radius=RADII["small"]
        )
        save_btn.pack(side="right", pady=14)

    def _set_quick_date(self, days_ahead: int):
        target = datetime.now() + timedelta(days=days_ahead)
        self.due_entry.delete(0, "end")
        self.due_entry.insert(0, target.strftime("%Y-%m-%d"))

    def _add_temp_chk(self):
        text = self.new_chk_entry.get().strip()
        if text:
            self.temp_checklist_items.append(text)
            self.new_chk_entry.delete(0, "end")
            self._render_temp_chk_items()

    def _remove_temp_chk(self, index: int):
        if 0 <= index < len(self.temp_checklist_items):
            self.temp_checklist_items.pop(index)
            self._render_temp_chk_items()

    def _render_temp_chk_items(self):
        for widget in self.chk_list_frame.winfo_children():
            widget.destroy()

        if not self.temp_checklist_items:
            empty = ctk.CTkLabel(
                self.chk_list_frame,
                text="No checklist items added yet.",
                font=FONTS["small"],
                text_color=COLORS["text_muted"],
                pady=10
            )
            empty.pack()
            return

        for idx, item in enumerate(self.temp_checklist_items):
            row = ctk.CTkFrame(self.chk_list_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=3)

            lbl = ctk.CTkLabel(row, text=f"•  {item}", font=FONTS["body"], text_color=COLORS["text_primary"], anchor="w")
            lbl.pack(side="left", fill="x", expand=True)

            del_btn = ctk.CTkButton(
                row,
                text="✕",
                width=24,
                height=24,
                font=FONTS["small"],
                fg_color="transparent",
                hover_color=COLORS["danger_light"],
                text_color=COLORS["danger"],
                command=lambda i=idx: self._remove_temp_chk(i)
            )
            del_btn.pack(side="right")

    def _save_task(self):
        title = self.title_entry.get().strip()
        desc = self.desc_text.get("1.0", "end-1c").strip()
        status = self.status_combo.get()
        priority = self.priority_combo.get()
        due_date = self.due_entry.get().strip() or None
        labels = self.labels_entry.get().strip()

        # Extract project ID
        proj_str = self.project_combo.get()
        if ":" not in proj_str:
            self._show_error("Please create or select a valid project first.")
            return
        try:
            project_id = int(proj_str.split(":")[0])
        except ValueError:
            self._show_error("Invalid project selected.")
            return

        # Extract Assignee ID
        assign_str = self.assignee_combo.get()
        assignee_id = None
        if ":" in assign_str:
            try:
                assignee_id = int(assign_str.split(":")[0])
            except ValueError:
                assignee_id = None

        try:
            if self.task:
                # Update existing
                updated = task_service.update_task(
                    task_id=self.task.id,
                    title=title,
                    description=desc,
                    project_id=project_id,
                    assignee_id=assignee_id,
                    status=status,
                    priority=priority,
                    due_date=due_date,
                    labels=labels,
                    current_user=self.current_user
                )
                saved_task = updated
            else:
                # Create new
                created = task_service.create_task(
                    title=title,
                    description=desc,
                    project_id=project_id,
                    assignee_id=assignee_id,
                    status=status,
                    priority=priority,
                    due_date=due_date,
                    labels=labels,
                    checklist_items=self.temp_checklist_items,
                    current_user=self.current_user
                )
                saved_task = created

            if self.on_saved and saved_task:
                self.on_saved(saved_task)

            self.destroy()

        except Exception as e:
            self._show_error(str(e))

    def _show_error(self, message: str):
        self.error_banner.configure(text=f"⚠  {message}")
        self.error_banner.pack(fill="x", pady=(0, 10), before=self.title_entry)
