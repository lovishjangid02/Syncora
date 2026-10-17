"""
Task Detail & Collaboration Dialog
Displays complete task metadata, interactive checklist checkboxes with real-time SQLite sync,
comment stream with author avatars, and chronological audit history.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Optional, Callable
from models.task import Task
from services import task_service
from ui.theme import COLORS, FONTS, RADII, ROLES
from ui.components.badges import PriorityBadge, StatusBadge, TagBadge, AvatarBadge
from ui.components.cards import ConfirmDialog


class TaskDetailDialog(ctk.CTkToplevel):
    """Rich modal window for reviewing and collaborating on a task."""

    def __init__(
        self,
        parent,
        task: Task,
        current_user: str = "User",
        user_role: str = "Admin",
        on_updated: Optional[Callable[[], None]] = None,
        on_deleted: Optional[Callable[[], None]] = None,
        on_edit_request: Optional[Callable[[Task], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.task_id = task.id
        self.current_user = current_user
        self.user_role = user_role
        self.on_updated = on_updated
        self.on_deleted = on_deleted
        self.on_edit_request = on_edit_request

        self.title(f"Task: {task.title}")
        self.geometry("740x800")
        self.minsize(680, 700)
        self.configure(fg_color=COLORS["bg_main"])

        self.transient(parent)
        self.grab_set()

        # Center dialog
        self.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() - 740) // 2
            y = parent.winfo_y() + (parent.winfo_height() - 800) // 2
            self.geometry(f"+{max(10, x)}+{max(10, y)}")
        except Exception:
            pass

        self._load_data()
        self._build_ui()

    def _load_data(self):
        self.task = task_service.get_task_by_id(self.task_id)
        if not self.task:
            self.destroy()
            return
        self.checklist_items = task_service.get_checklist_items(self.task_id)
        self.comments = task_service.get_comments(self.task_id)
        self.activities = task_service.get_task_activity(self.task_id)

    def _refresh_view(self):
        self._load_data()
        for w in self.winfo_children():
            w.destroy()
        self._build_ui()
        if self.on_updated:
            self.on_updated()

    def _build_ui(self):
        can_edit = ROLES.get(self.user_role, {}).get("can_edit_task", True)
        can_comment = ROLES.get(self.user_role, {}).get("can_comment", True)

        # Header bar
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=65, corner_radius=0)
        header.pack(fill="x", side="top")

        h_left = ctk.CTkFrame(header, fg_color="transparent")
        h_left.pack(side="left", padx=20, pady=12)

        proj_badge = ctk.CTkLabel(
            h_left,
            text=f"📁 {self.task.project_name.upper()}",
            font=FONTS["badge"],
            text_color=COLORS["primary"]
        )
        proj_badge.pack(anchor="w")

        p_row = ctk.CTkFrame(header, fg_color="transparent")
        p_row.pack(side="right", padx=20, pady=12)

        # Priority Badge
        p_badge = PriorityBadge(p_row, priority=self.task.priority)
        p_badge.pack(side="left", padx=(0, 10))

        # Status Selector
        if can_edit:
            self.status_var = ctk.StringVar(value=self.task.status)
            self.status_menu = ctk.CTkOptionMenu(
                p_row,
                values=["Backlog", "In Progress", "Review", "Done"],
                variable=self.status_var,
                command=self._on_status_select,
                width=120,
                height=28,
                corner_radius=RADII["small"],
                font=FONTS["badge"]
            )
            self.status_menu.pack(side="left")
        else:
            s_badge = StatusBadge(p_row, status=self.task.status)
            s_badge.pack(side="left")

        # Scrollable content area
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # Overdue alert banner if applicable
        if self.task.is_overdue:
            overdue_banner = ctk.CTkFrame(
                scroll,
                fg_color=COLORS["danger_light"],
                border_color=COLORS["danger"],
                border_width=1,
                corner_radius=RADII["small"]
            )
            overdue_banner.pack(fill="x", pady=(0, 12))

            ob_lbl = ctk.CTkLabel(
                overdue_banner,
                text=f"⚠  This task was due on {self.task.due_date} and is currently OVERDUE!",
                font=FONTS["body_bold"],
                text_color=COLORS["danger"],
                padx=12,
                pady=8
            )
            ob_lbl.pack(anchor="w")

        # Task Title
        title_lbl = ctk.CTkLabel(
            scroll,
            text=self.task.title,
            font=FONTS["page_title"],
            text_color=COLORS["text_primary"],
            wraplength=660,
            justify="left",
            anchor="w"
        )
        title_lbl.pack(fill="x", pady=(0, 12))

        # Metadata Card (Assignee, Due Date, Created)
        meta_card = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=RADII["small"])
        meta_card.pack(fill="x", pady=(0, 16))

        meta_grid = ctk.CTkFrame(meta_card, fg_color="transparent")
        meta_grid.pack(fill="x", padx=16, pady=12)

        # Assignee
        ass_box = ctk.CTkFrame(meta_grid, fg_color="transparent")
        ass_box.pack(side="left", padx=(0, 30))

        ass_lbl = ctk.CTkLabel(ass_box, text="ASSIGNEE", font=FONTS["small_bold"], text_color=COLORS["text_muted"])
        ass_lbl.pack(anchor="w")

        ass_row = ctk.CTkFrame(ass_box, fg_color="transparent")
        ass_row.pack(anchor="w", pady=(2, 0))

        av = AvatarBadge(ass_row, name=self.task.assignee_name, color=self.task.assignee_color, size=24)
        av.pack(side="left", padx=(0, 6))

        ass_name = ctk.CTkLabel(ass_row, text=self.task.assignee_name, font=FONTS["body_bold"], text_color=COLORS["text_primary"])
        ass_name.pack(side="left")

        # Due Date
        due_box = ctk.CTkFrame(meta_grid, fg_color="transparent")
        due_box.pack(side="left", padx=(0, 30))

        due_head = ctk.CTkLabel(due_box, text="DUE DATE", font=FONTS["small_bold"], text_color=COLORS["text_muted"])
        due_head.pack(anchor="w")

        due_val_text = self.task.due_date if self.task.due_date else "No deadline set"
        due_val = ctk.CTkLabel(
            due_box,
            text=f"📅 {due_val_text}",
            font=FONTS["body_bold"],
            text_color=COLORS["danger"] if self.task.is_overdue else COLORS["text_primary"]
        )
        due_val.pack(anchor="w", pady=(2, 0))

        # Labels
        if self.task.label_list:
            lbl_box = ctk.CTkFrame(meta_grid, fg_color="transparent")
            lbl_box.pack(side="left")

            lbl_head = ctk.CTkLabel(lbl_box, text="LABELS", font=FONTS["small_bold"], text_color=COLORS["text_muted"])
            lbl_head.pack(anchor="w")

            lbl_chips = ctk.CTkFrame(lbl_box, fg_color="transparent")
            lbl_chips.pack(anchor="w", pady=(2, 0))
            for l_text in self.task.label_list:
                tb = TagBadge(lbl_chips, text=l_text)
                tb.pack(side="left", padx=(0, 4))

        # Description Section
        desc_head = ctk.CTkLabel(scroll, text="Description", font=FONTS["section_title"], text_color=COLORS["text_primary"])
        desc_head.pack(anchor="w", pady=(0, 6))

        desc_content = self.task.description if self.task.description else "No description provided for this task."
        desc_card = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=RADII["small"])
        desc_card.pack(fill="x", pady=(0, 16))

        desc_text = ctk.CTkLabel(
            desc_card,
            text=desc_content,
            font=FONTS["body"],
            text_color=COLORS["text_secondary"],
            wraplength=640,
            justify="left",
            anchor="w",
            padx=14,
            pady=12
        )
        desc_text.pack(fill="x")

        # Checklist Section
        chk_header_row = ctk.CTkFrame(scroll, fg_color="transparent")
        chk_header_row.pack(fill="x", pady=(0, 6))

        total_chk = len(self.checklist_items)
        done_chk = sum(1 for c in self.checklist_items if c.is_completed)
        chk_pct = int(round((done_chk / total_chk * 100))) if total_chk > 0 else 0

        chk_title = ctk.CTkLabel(
            chk_header_row,
            text=f"Checklist  ({done_chk}/{total_chk} — {chk_pct}%)",
            font=FONTS["section_title"],
            text_color=COLORS["text_primary"]
        )
        chk_title.pack(side="left")

        # Progress bar
        chk_bar = ctk.CTkProgressBar(scroll, height=8, corner_radius=4)
        chk_bar.set(chk_pct / 100.0)
        chk_bar.configure(
            progress_color=COLORS["success"] if chk_pct == 100 else COLORS["primary"],
            fg_color=COLORS["bg_card_secondary"]
        )
        chk_bar.pack(fill="x", pady=(0, 10))

        # Checklist Items Frame
        chk_card = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=RADII["small"])
        chk_card.pack(fill="x", pady=(0, 16))

        if not self.checklist_items:
            empty_chk = ctk.CTkLabel(
                chk_card,
                text="No checklist items yet. Add sub-tasks below.",
                font=FONTS["small"],
                text_color=COLORS["text_muted"],
                pady=10
            )
            empty_chk.pack()
        else:
            for item in self.checklist_items:
                i_row = ctk.CTkFrame(chk_card, fg_color="transparent")
                i_row.pack(fill="x", padx=12, pady=4)

                var = ctk.BooleanVar(value=item.is_completed)
                cb = ctk.CTkCheckBox(
                    i_row,
                    text=item.title,
                    variable=var,
                    font=FONTS["body"],
                    text_color=COLORS["text_muted"] if item.is_completed else COLORS["text_primary"],
                    fg_color=COLORS["success"],
                    hover_color=COLORS["success_light"],
                    state="normal" if can_edit else "disabled",
                    command=lambda i=item, v=var: self._toggle_chk(i.id, v.get())
                )
                cb.pack(side="left", fill="x", expand=True)

                if can_edit:
                    d_btn = ctk.CTkButton(
                        i_row,
                        text="✕",
                        width=22,
                        height=22,
                        font=FONTS["small"],
                        fg_color="transparent",
                        hover_color=COLORS["danger_light"],
                        text_color=COLORS["text_muted"],
                        command=lambda i_id=item.id: self._delete_chk(i_id)
                    )
                    d_btn.pack(side="right")

        # Add Checklist Item Input
        if can_edit:
            add_chk_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            add_chk_frame.pack(fill="x", pady=(0, 16))

            self.new_chk_input = ctk.CTkEntry(
                add_chk_frame,
                placeholder_text="Add a new checklist step...",
                font=FONTS["body"],
                height=34,
                corner_radius=RADII["small"]
            )
            self.new_chk_input.pack(side="left", fill="x", expand=True, padx=(0, 8))
            self.new_chk_input.bind("<Return>", lambda e: self._add_new_chk())

            add_chk_btn = ctk.CTkButton(
                add_chk_frame,
                text="+ Add Step",
                font=FONTS["body_bold"],
                width=90,
                height=34,
                fg_color=COLORS["secondary"],
                hover_color=COLORS["secondary_hover"],
                command=self._add_new_chk
            )
            add_chk_btn.pack(side="right")

        # Collaboration & Comments Section
        comm_head = ctk.CTkLabel(
            scroll,
            text=f"Discussion & Comments ({len(self.comments)})",
            font=FONTS["section_title"],
            text_color=COLORS["text_primary"]
        )
        comm_head.pack(anchor="w", pady=(0, 8))

        comm_card = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=RADII["small"])
        comm_card.pack(fill="x", pady=(0, 16))

        if not self.comments:
            empty_comm = ctk.CTkLabel(
                comm_card,
                text="No comments yet. Start the conversation below!",
                font=FONTS["small"],
                text_color=COLORS["text_muted"],
                pady=14
            )
            empty_comm.pack()
        else:
            for c in self.comments:
                c_box = ctk.CTkFrame(comm_card, fg_color=COLORS["bg_card_secondary"], corner_radius=RADII["small"])
                c_box.pack(fill="x", padx=12, pady=6)

                c_header = ctk.CTkFrame(c_box, fg_color="transparent")
                c_header.pack(fill="x", padx=10, pady=(8, 2))

                c_av = AvatarBadge(c_header, name=c.author_name, size=20)
                c_av.pack(side="left", padx=(0, 6))

                c_author = ctk.CTkLabel(c_header, text=c.author_name, font=FONTS["small_bold"], text_color=COLORS["text_primary"])
                c_author.pack(side="left")

                c_time = ctk.CTkLabel(c_header, text=c.created_at, font=FONTS["small"], text_color=COLORS["text_muted"])
                c_time.pack(side="right")

                c_body = ctk.CTkLabel(
                    c_box,
                    text=c.content,
                    font=FONTS["body"],
                    text_color=COLORS["text_secondary"],
                    wraplength=600,
                    justify="left",
                    anchor="w",
                    padx=10,
                    pady=(0, 8)
                )
                c_body.pack(fill="x")

        # Post Comment Input
        if can_comment:
            comment_box = ctk.CTkFrame(scroll, fg_color="transparent")
            comment_box.pack(fill="x", pady=(0, 16))

            self.comment_input = ctk.CTkTextbox(
                comment_box,
                height=65,
                font=FONTS["body"],
                corner_radius=RADII["small"]
            )
            self.comment_input.pack(fill="x", pady=(0, 6))

            post_btn = ctk.CTkButton(
                comment_box,
                text="💬  Post Comment",
                font=FONTS["body_bold"],
                fg_color=COLORS["primary"],
                hover_color=COLORS["primary_hover"],
                width=140,
                height=32,
                corner_radius=RADII["small"],
                command=self._post_comment
            )
            post_btn.pack(side="right")

        # Bottom Bar: Edit / Delete / Close
        actions = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=60, corner_radius=0)
        actions.pack(fill="x", side="bottom")

        close_btn = ctk.CTkButton(
            actions,
            text="Close",
            font=FONTS["body"],
            fg_color=COLORS["bg_card_secondary"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            command=self.destroy,
            width=90,
            height=36,
            corner_radius=RADII["small"]
        )
        close_btn.pack(side="right", padx=16, pady=12)

        if can_edit:
            edit_btn = ctk.CTkButton(
                actions,
                text="✏️  Edit Task",
                font=FONTS["body_bold"],
                fg_color=COLORS["secondary"],
                hover_color=COLORS["secondary_hover"],
                command=self._request_edit,
                width=110,
                height=36,
                corner_radius=RADII["small"]
            )
            edit_btn.pack(side="right", padx=(0, 8), pady=12)

            del_btn = ctk.CTkButton(
                actions,
                text="🗑️  Delete",
                font=FONTS["body"],
                fg_color=COLORS["danger_light"],
                hover_color=COLORS["danger"],
                text_color=COLORS["danger"],
                command=self._confirm_delete,
                width=90,
                height=36,
                corner_radius=RADII["small"]
            )
            del_btn.pack(side="left", padx=16, pady=12)

    def _on_status_select(self, new_status: str):
        task_service.update_task_status(self.task_id, new_status, current_user=self.current_user)
        self._refresh_view()

    def _toggle_chk(self, item_id: int, is_completed: bool):
        task_service.toggle_checklist_item(item_id, is_completed, current_user=self.current_user)
        self._refresh_view()

    def _delete_chk(self, item_id: int):
        task_service.delete_checklist_item(item_id, current_user=self.current_user)
        self._refresh_view()

    def _add_new_chk(self):
        text = self.new_chk_input.get().strip()
        if text:
            task_service.add_checklist_item(self.task_id, text, current_user=self.current_user)
            self._refresh_view()

    def _post_comment(self):
        text = self.comment_input.get("1.0", "end-1c").strip()
        if text:
            task_service.add_comment(
                task_id=self.task_id,
                author_name=self.current_user,
                content=text
            )
            self._refresh_view()

    def _request_edit(self):
        task_copy = self.task
        self.destroy()
        if self.on_edit_request:
            self.on_edit_request(task_copy)

    def _confirm_delete(self):
        ConfirmDialog(
            self,
            title="Delete Task",
            message=f"Are you sure you want to permanently delete task '{self.task.title}'? All checklist items and comments will be erased.",
            confirm_text="Delete Task",
            on_confirm=self._do_delete
        )

    def _do_delete(self):
        task_service.delete_task(self.task_id, current_user=self.current_user)
        self.destroy()
        if self.on_deleted:
            self.on_deleted()
