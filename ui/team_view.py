"""
Team Management View
Displays team roster, roles, member workload metrics, task assignments, and member CRUD.
"""

import customtkinter as ctk
from typing import Optional, Callable
from models.member import Member
from services import member_service, task_service
from ui.theme import COLORS, FONTS, RADII, ROLES
from ui.components.badges import RoleBadge, AvatarBadge, StatusBadge, PriorityBadge
from ui.components.cards import ConfirmDialog


class TeamView(ctk.CTkFrame):
    """Team roster and workload management screen."""

    def __init__(
        self,
        master,
        current_user: str = "User",
        user_role: str = "Admin",
        on_add_member: Optional[Callable[[], None]] = None,
        on_edit_member: Optional[Callable[[Member], None]] = None,
        on_filter_member_tasks: Optional[Callable[[int], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.current_user = current_user
        self.user_role = user_role
        self.on_add_member = on_add_member
        self.on_edit_member = on_edit_member
        self.on_filter_member_tasks = on_filter_member_tasks
        self.search_filter = ""

        self._build_ui()

    def refresh(self):
        """Reload team members."""
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    def _build_ui(self):
        can_manage = ROLES.get(self.user_role, {}).get("can_manage_members", True)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=20)

        # 1. Header Toolbar
        top_bar = ctk.CTkFrame(scroll, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 16))

        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(title_box, text="Team & Roles", font=FONTS["page_title"], text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Manage project contributors, role privileges, and track balance of responsibilities",
            font=FONTS["page_subtitle"],
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        actions_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        actions_box.pack(side="right")

        self.search_entry = ctk.CTkEntry(
            actions_box,
            placeholder_text="🔍 Search members...",
            font=FONTS["body"],
            width=180,
            height=36,
            corner_radius=RADII["small"]
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._on_search)

        if can_manage:
            add_btn = ctk.CTkButton(
                actions_box,
                text="+ Add Member",
                font=FONTS["body_bold"],
                fg_color=COLORS["primary"],
                hover_color=COLORS["primary_hover"],
                height=36,
                corner_radius=RADII["small"],
                command=self.on_add_member if self.on_add_member else lambda: None
            )
            add_btn.pack(side="right")

        # 2. Role Overview Banner
        role_banner = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=RADII["medium"], border_color=COLORS["border"], border_width=1)
        role_banner.pack(fill="x", pady=(0, 20))

        rb_inner = ctk.CTkFrame(role_banner, fg_color="transparent")
        rb_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(rb_inner, text="🔐 Role-Aware Permission Matrix (Local Prototype)", font=FONTS["card_title"], text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 6))

        matrix_txt = (
            "• Admin: Full authority to create, edit, and delete projects, tasks, and team rosters.\n"
            "• Member: Active contributor able to create/update tasks, complete checklist steps, and post discussion comments.\n"
            "• Viewer: Read-only access for academic evaluators and stakeholders. Destructive actions and form edits are disabled."
        )
        ctk.CTkLabel(rb_inner, text=matrix_txt, font=FONTS["small"], text_color=COLORS["text_secondary"], justify="left").pack(anchor="w")

        # 3. Members List
        members = member_service.get_all_members(include_stats=True)

        if self.search_filter:
            q = self.search_filter.lower()
            members = [m for m in members if q in m.name.lower() or q in m.email.lower() or q in m.role.lower()]

        for m in members:
            m_card = ctk.CTkFrame(
                scroll,
                fg_color=COLORS["bg_card"],
                border_color=COLORS["border"],
                border_width=1,
                corner_radius=RADII["medium"]
            )
            m_card.pack(fill="x", pady=8)

            c_inner = ctk.CTkFrame(m_card, fg_color="transparent")
            c_inner.pack(fill="both", expand=True, padx=20, pady=16)

            # Top Row: Avatar + Name + Email + Role + Edit/Delete
            top_row = ctk.CTkFrame(c_inner, fg_color="transparent")
            top_row.pack(fill="x", pady=(0, 12))

            # Left: Avatar + Details
            left_info = ctk.CTkFrame(top_row, fg_color="transparent")
            left_info.pack(side="left")

            av = AvatarBadge(left_info, name=m.name, color=m.avatar_color, size=44)
            av.pack(side="left", padx=(0, 14))

            details = ctk.CTkFrame(left_info, fg_color="transparent")
            details.pack(side="left")

            name_row = ctk.CTkFrame(details, fg_color="transparent")
            name_row.pack(anchor="w")

            ctk.CTkLabel(name_row, text=m.name, font=FONTS["card_title"], text_color=COLORS["text_primary"]).pack(side="left", padx=(0, 8))
            rb = RoleBadge(name_row, role=m.role)
            rb.pack(side="left")

            ctk.CTkLabel(details, text=f"✉ {m.email}", font=FONTS["body"], text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(2, 0))

            # Right: Actions
            right_act = ctk.CTkFrame(top_row, fg_color="transparent")
            right_act.pack(side="right")

            view_tasks_btn = ctk.CTkButton(
                right_act,
                text="View Assigned Board →",
                font=FONTS["small_bold"],
                fg_color=COLORS["primary_light"],
                hover_color=COLORS["primary"],
                text_color=COLORS["primary"],
                height=32,
                corner_radius=RADII["small"],
                command=lambda mid=m.id: self.on_filter_member_tasks(mid) if self.on_filter_member_tasks else None
            )
            view_tasks_btn.pack(side="left", padx=(0, 8))

            if can_manage:
                edit_btn = ctk.CTkButton(
                    right_act,
                    text="✏️",
                    font=FONTS["small"],
                    fg_color=COLORS["bg_card_secondary"],
                    hover_color=COLORS["border"],
                    text_color=COLORS["text_primary"],
                    width=34,
                    height=32,
                    corner_radius=RADII["small"],
                    command=lambda mem=m: self.on_edit_member(mem) if self.on_edit_member else None
                )
                edit_btn.pack(side="left", padx=(0, 6))

                del_btn = ctk.CTkButton(
                    right_act,
                    text="🗑️",
                    font=FONTS["small"],
                    fg_color=COLORS["bg_card_secondary"],
                    hover_color=COLORS["danger_light"],
                    text_color=COLORS["danger"],
                    width=34,
                    height=32,
                    corner_radius=RADII["small"],
                    command=lambda mem=m: self._confirm_delete(mem)
                )
                del_btn.pack(side="left")

            # Workload Metrics Bar
            m_metrics = ctk.CTkFrame(c_inner, fg_color=COLORS["bg_card_secondary"], corner_radius=RADII["small"])
            m_metrics.pack(fill="x", pady=(0, 10))

            m_grid = ctk.CTkFrame(m_metrics, fg_color="transparent")
            m_grid.pack(fill="x", padx=16, pady=10)

            total = m.assigned_tasks
            done = m.completed_tasks
            in_prog = m.in_progress_tasks
            overdue = m.overdue_tasks
            pct = int(round((done / total * 100))) if total > 0 else 0

            # 4 columns for stats
            for c_i in range(4):
                m_grid.grid_columnconfigure(c_i, weight=1)

            ctk.CTkLabel(m_grid, text="ASSIGNED", font=FONTS["badge"], text_color=COLORS["text_muted"]).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(m_grid, text=str(total), font=FONTS["card_title"], text_color=COLORS["text_primary"]).grid(row=1, column=0, sticky="w")

            ctk.CTkLabel(m_grid, text="IN PROGRESS", font=FONTS["badge"], text_color=COLORS["text_muted"]).grid(row=0, column=1, sticky="w")
            ctk.CTkLabel(m_grid, text=str(in_prog), font=FONTS["card_title"], text_color=COLORS["secondary"]).grid(row=1, column=1, sticky="w")

            ctk.CTkLabel(m_grid, text="COMPLETED", font=FONTS["badge"], text_color=COLORS["text_muted"]).grid(row=0, column=2, sticky="w")
            ctk.CTkLabel(m_grid, text=f"{done} ({pct}%)", font=FONTS["card_title"], text_color=COLORS["success"]).grid(row=1, column=2, sticky="w")

            ctk.CTkLabel(m_grid, text="OVERDUE", font=FONTS["badge"], text_color=COLORS["text_muted"]).grid(row=0, column=3, sticky="w")
            ctk.CTkLabel(
                m_grid,
                text=str(overdue),
                font=FONTS["card_title"],
                text_color=COLORS["danger"] if overdue > 0 else COLORS["text_secondary"]
            ).grid(row=1, column=3, sticky="w")

            # Progress bar
            bar = ctk.CTkProgressBar(c_inner, height=6, corner_radius=3)
            bar.set(pct / 100.0)
            bar.configure(
                progress_color=COLORS["success"] if pct == 100 else COLORS["primary"],
                fg_color=COLORS["bg_card_secondary"]
            )
            bar.pack(fill="x")

    def _on_search(self, event=None):
        self.search_filter = self.search_entry.get().strip()
        self.refresh()

    def _confirm_delete(self, member: Member):
        ConfirmDialog(
            self,
            title="Remove Team Member",
            message=f"Are you sure you want to remove '{member.name}' from the team?\nTheir assigned tasks will become 'Unassigned'.",
            confirm_text="Remove Member",
            on_confirm=lambda: self._delete_member(member.id)
        )

    def _delete_member(self, member_id: int):
        member_service.delete_member(member_id, current_user=self.current_user)
        self.refresh()
