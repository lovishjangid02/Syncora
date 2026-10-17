"""
Project Management View
Displays workspace projects with progress bars, task metrics, creation, editing, and deletion.
"""

import customtkinter as ctk
from typing import Optional, Callable
from models.project import Project
from services import project_service
from ui.theme import COLORS, FONTS, RADII, ROLES
from ui.components.badges import StatusBadge
from ui.components.cards import ConfirmDialog


class ProjectView(ctk.CTkFrame):
    """Project management and workspace browser screen."""

    def __init__(
        self,
        master,
        current_user: str = "User",
        user_role: str = "Admin",
        on_open_kanban: Optional[Callable[[int], None]] = None,
        on_create_project: Optional[Callable[[], None]] = None,
        on_edit_project: Optional[Callable[[Project], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.current_user = current_user
        self.user_role = user_role
        self.on_open_kanban = on_open_kanban
        self.on_create_project = on_create_project
        self.on_edit_project = on_edit_project
        self.search_filter = ""

        self._build_ui()

    def refresh(self):
        """Reload project cards."""
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    def _build_ui(self):
        can_create = ROLES.get(self.user_role, {}).get("can_create_project", True)
        can_edit = ROLES.get(self.user_role, {}).get("can_edit_project", True)
        can_delete = ROLES.get(self.user_role, {}).get("can_delete_project", True)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=20)

        # 1. Header Toolbar
        top_bar = ctk.CTkFrame(scroll, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 20))

        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(title_box, text="Project Workspaces", font=FONTS["page_title"], text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Organize team initiatives, track agile milestones, and monitor completion velocity",
            font=FONTS["page_subtitle"],
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        actions_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        actions_box.pack(side="right")

        # Search box
        self.search_entry = ctk.CTkEntry(
            actions_box,
            placeholder_text="🔍 Search projects...",
            font=FONTS["body"],
            width=200,
            height=36,
            corner_radius=RADII["small"]
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._on_search)

        if can_create:
            new_btn = ctk.CTkButton(
                actions_box,
                text="+ New Project",
                font=FONTS["body_bold"],
                fg_color=COLORS["primary"],
                hover_color=COLORS["primary_hover"],
                height=36,
                corner_radius=RADII["small"],
                command=self.on_create_project if self.on_create_project else lambda: None
            )
            new_btn.pack(side="right")

        # 2. Project Cards Grid
        projects = project_service.get_all_projects(include_stats=True)

        if self.search_filter:
            q = self.search_filter.lower()
            projects = [p for p in projects if q in p.name.lower() or q in p.description.lower() or q in p.owner.lower()]

        if not projects:
            empty_card = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=RADII["medium"], border_color=COLORS["border"], border_width=1)
            empty_card.pack(fill="x", pady=40)

            ctk.CTkLabel(
                empty_card,
                text="No projects found matching your search.",
                font=FONTS["card_title"],
                text_color=COLORS["text_muted"],
                pady=30
            ).pack()
            return

        # Render cards
        for p in projects:
            card = ctk.CTkFrame(
                scroll,
                fg_color=COLORS["bg_card"],
                border_color=COLORS["border"],
                border_width=1,
                corner_radius=RADII["medium"]
            )
            card.pack(fill="x", pady=8)

            c_inner = ctk.CTkFrame(card, fg_color="transparent")
            c_inner.pack(fill="both", expand=True, padx=20, pady=16)

            # Top Row: Name + Status Badge + Actions
            c_top = ctk.CTkFrame(c_inner, fg_color="transparent")
            c_top.pack(fill="x", pady=(0, 6))

            name_box = ctk.CTkFrame(c_top, fg_color="transparent")
            name_box.pack(side="left")

            ctk.CTkLabel(name_box, text=p.name, font=FONTS["card_title"], text_color=COLORS["text_primary"]).pack(side="left", padx=(0, 10))

            sb = StatusBadge(name_box, status=p.status)
            sb.pack(side="left")

            act_row = ctk.CTkFrame(c_top, fg_color="transparent")
            act_row.pack(side="right")

            open_btn = ctk.CTkButton(
                act_row,
                text="📋 Open Kanban",
                font=FONTS["small_bold"],
                fg_color=COLORS["primary_light"],
                hover_color=COLORS["primary"],
                text_color=COLORS["primary"],
                height=30,
                corner_radius=RADII["small"],
                command=lambda pid=p.id: self.on_open_kanban(pid) if self.on_open_kanban else None
            )
            open_btn.pack(side="left", padx=(0, 6))

            if can_edit:
                edit_btn = ctk.CTkButton(
                    act_row,
                    text="✏️ Edit",
                    font=FONTS["small"],
                    fg_color=COLORS["bg_card_secondary"],
                    hover_color=COLORS["border"],
                    text_color=COLORS["text_primary"],
                    width=60,
                    height=30,
                    corner_radius=RADII["small"],
                    command=lambda proj=p: self.on_edit_project(proj) if self.on_edit_project else None
                )
                edit_btn.pack(side="left", padx=(0, 6))

            if can_delete:
                del_btn = ctk.CTkButton(
                    act_row,
                    text="🗑️",
                    font=FONTS["small"],
                    fg_color=COLORS["bg_card_secondary"],
                    hover_color=COLORS["danger_light"],
                    text_color=COLORS["danger"],
                    width=32,
                    height=30,
                    corner_radius=RADII["small"],
                    command=lambda proj=p: self._confirm_delete(proj)
                )
                del_btn.pack(side="left")

            # Description
            if p.description:
                desc_lbl = ctk.CTkLabel(
                    c_inner,
                    text=p.description,
                    font=FONTS["body"],
                    text_color=COLORS["text_secondary"],
                    wraplength=800,
                    justify="left",
                    anchor="w"
                )
                desc_lbl.pack(fill="x", pady=(0, 12))

            # Progress Bar & Metrics
            prog_row = ctk.CTkFrame(c_inner, fg_color="transparent")
            prog_row.pack(fill="x", pady=(0, 4))

            ctk.CTkLabel(
                prog_row,
                text=f"Progress: {p.progress_pct}% complete",
                font=FONTS["small_bold"],
                text_color=COLORS["text_primary"]
            ).pack(side="left")

            stat_summary = f"{p.completed_tasks} done • {p.in_progress_tasks} in progress • {p.total_tasks} total"
            if p.overdue_tasks > 0:
                stat_summary += f" • {p.overdue_tasks} overdue"

            ctk.CTkLabel(
                prog_row,
                text=stat_summary,
                font=FONTS["small"],
                text_color=COLORS["danger"] if p.overdue_tasks > 0 else COLORS["text_muted"]
            ).pack(side="right")

            bar = ctk.CTkProgressBar(c_inner, height=8, corner_radius=4)
            bar.set(p.progress_pct / 100.0)
            bar.configure(
                progress_color=COLORS["success"] if p.progress_pct == 100 else COLORS["primary"],
                fg_color=COLORS["bg_card_secondary"]
            )
            bar.pack(fill="x", pady=(0, 10))

            # Metadata Footer
            c_foot = ctk.CTkFrame(c_inner, fg_color="transparent")
            c_foot.pack(fill="x")

            foot_txt = f"Lead: {p.owner}  •  Created: {p.created_at.split()[0]}  •  Target Deadline: {p.deadline or 'Open Ended'}"
            ctk.CTkLabel(c_foot, text=foot_txt, font=FONTS["small"], text_color=COLORS["text_muted"]).pack(side="left")

    def _on_search(self, event=None):
        self.search_filter = self.search_entry.get().strip()
        self.refresh()

    def _confirm_delete(self, project: Project):
        ConfirmDialog(
            self,
            title="Delete Project Workspace",
            message=f"Are you sure you want to permanently delete '{project.name}'?\nThis will also delete all associated tasks, checklists, and comments.",
            confirm_text="Delete Workspace",
            on_confirm=lambda: self._delete_project(project.id)
        )

    def _delete_project(self, project_id: int):
        project_service.delete_project(project_id, current_user=self.current_user)
        self.refresh()
