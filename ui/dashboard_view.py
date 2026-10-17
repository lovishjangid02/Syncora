"""
Dashboard View
Presents top-level KPIs, project progress cards, upcoming deadlines, team workload, and live activity feed.
"""

import customtkinter as ctk
from typing import Optional, Callable
from services import report_service, project_service, activity_service
from ui.theme import COLORS, FONTS, RADII, ROLES
from ui.components.badges import PriorityBadge, AvatarBadge
from ui.components.cards import MetricCard


class DashboardView(ctk.CTkFrame):
    """Primary overview dashboard with real SQLite aggregations."""

    def __init__(
        self,
        master,
        current_user: str = "User",
        user_role: str = "Admin",
        on_navigate: Optional[Callable[[str, Optional[int]], None]] = None,
        on_open_task: Optional[Callable[[int], None]] = None,
        on_create_task: Optional[Callable[[], None]] = None,
        on_create_project: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.current_user = current_user
        self.user_role = user_role
        self.on_navigate = on_navigate
        self.on_open_task = on_open_task
        self.on_create_task = on_create_task
        self.on_create_project = on_create_project

        self._build_ui()

    def refresh(self):
        """Reload all metrics and re-render dashboard cards."""
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    def _build_ui(self):
        summary = report_service.get_dashboard_summary()
        projects = project_service.get_all_projects(include_stats=True)
        deadlines = report_service.get_upcoming_deadlines(limit=5)
        workload = report_service.get_team_workload_summary()
        activities = activity_service.get_recent_activities(limit=8)

        can_create_task = ROLES.get(self.user_role, {}).get("can_create_task", True)
        can_create_proj = ROLES.get(self.user_role, {}).get("can_create_project", True)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=20)

        # 1. Header Toolbar: Greeting & Quick Action Buttons
        top_row = ctk.CTkFrame(scroll, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 20))

        welcome_box = ctk.CTkFrame(top_row, fg_color="transparent")
        welcome_box.pack(side="left")

        w_title = ctk.CTkLabel(
            welcome_box,
            text=f"Welcome back, {self.current_user} 👋",
            font=FONTS["page_title"],
            text_color=COLORS["text_primary"]
        )
        w_title.pack(anchor="w")

        w_sub = ctk.CTkLabel(
            welcome_box,
            text=f"Project Health: {summary['completion_rate']}% of tasks completed • {summary['overdue_tasks']} overdue items requiring attention",
            font=FONTS["page_subtitle"],
            text_color=COLORS["text_secondary"]
        )
        w_sub.pack(anchor="w", pady=(2, 0))

        actions_box = ctk.CTkFrame(top_row, fg_color="transparent")
        actions_box.pack(side="right")

        if can_create_task:
            new_task_btn = ctk.CTkButton(
                actions_box,
                text="+ New Task",
                font=FONTS["body_bold"],
                fg_color=COLORS["primary"],
                hover_color=COLORS["primary_hover"],
                height=36,
                corner_radius=RADII["small"],
                command=self.on_create_task if self.on_create_task else lambda: None
            )
            new_task_btn.pack(side="right", padx=(8, 0))

        if can_create_proj:
            new_proj_btn = ctk.CTkButton(
                actions_box,
                text="+ New Project",
                font=FONTS["body_bold"],
                fg_color=COLORS["secondary"],
                hover_color=COLORS["secondary_hover"],
                height=36,
                corner_radius=RADII["small"],
                command=self.on_create_project if self.on_create_project else lambda: None
            )
            new_proj_btn.pack(side="right")

        # 2. KPI Metrics Grid (6 cards)
        kpi_grid = ctk.CTkFrame(scroll, fg_color="transparent")
        kpi_grid.pack(fill="x", pady=(0, 24))
        for col_idx in range(6):
            kpi_grid.grid_columnconfigure(col_idx, weight=1)

        cards_data = [
            ("Projects", str(summary["total_projects"]), "Active workspaces", "#8B5CF6", "📁"),
            ("Total Tasks", str(summary["total_tasks"]), "Across all boards", "#3B82F6", "📋"),
            ("Completed", str(summary["completed_tasks"]), f"{summary['completion_rate']}% overall velocity", "#10B981", "✓"),
            ("In Progress", str(summary["in_progress_tasks"]), "Active development", "#06B6D4", "⚡"),
            ("In Review", str(summary["review_tasks"]), "Pending verification", "#A855F7", "👁"),
            ("Overdue", str(summary["overdue_tasks"]), "Action required" if summary["overdue_tasks"] > 0 else "All on track", "#EF4444" if summary["overdue_tasks"] > 0 else "#10B981", "⚠" if summary["overdue_tasks"] > 0 else "✓"),
        ]

        for idx, (title, val, sub, color, sym) in enumerate(cards_data):
            card = MetricCard(
                kpi_grid,
                title=title,
                value=val,
                subtitle=sub,
                accent_color=color,
                icon_symbol=sym
            )
            card.grid(row=0, column=idx, padx=5, pady=0, sticky="nsew")

        # 3. Middle Section: Project Progress (Left 60%) & Upcoming Deadlines (Right 40%)
        mid_row = ctk.CTkFrame(scroll, fg_color="transparent")
        mid_row.pack(fill="x", pady=(0, 24))
        mid_row.grid_columnconfigure(0, weight=6)
        mid_row.grid_columnconfigure(1, weight=4)

        # Left Column: Project Progress Overview
        proj_container = ctk.CTkFrame(mid_row, fg_color=COLORS["bg_card"], corner_radius=RADII["medium"], border_color=COLORS["border"], border_width=1)
        proj_container.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        p_hdr = ctk.CTkFrame(proj_container, fg_color="transparent")
        p_hdr.pack(fill="x", padx=18, pady=(16, 12))

        ctk.CTkLabel(p_hdr, text="Project Workspaces", font=FONTS["section_title"], text_color=COLORS["text_primary"]).pack(side="left")
        view_all_p = ctk.CTkButton(
            p_hdr,
            text="Manage Projects →",
            font=FONTS["small_bold"],
            fg_color="transparent",
            hover_color=COLORS["bg_card_secondary"],
            text_color=COLORS["primary"],
            command=lambda: self.on_navigate("projects", None) if self.on_navigate else None
        )
        view_all_p.pack(side="right")

        # List of Projects
        for p in projects:
            p_card = ctk.CTkFrame(proj_container, fg_color=COLORS["bg_card_secondary"], corner_radius=RADII["small"])
            p_card.pack(fill="x", padx=16, pady=6)

            p_top = ctk.CTkFrame(p_card, fg_color="transparent")
            p_top.pack(fill="x", padx=14, pady=(10, 4))

            p_name = ctk.CTkLabel(p_top, text=p.name, font=FONTS["card_title"], text_color=COLORS["text_primary"])
            p_name.pack(side="left")

            p_stat = ctk.CTkLabel(
                p_top,
                text=f"{p.completed_tasks}/{p.total_tasks} tasks ({p.progress_pct}%)",
                font=FONTS["small_bold"],
                text_color=COLORS["primary"]
            )
            p_stat.pack(side="right")

            # Progress bar
            bar = ctk.CTkProgressBar(p_card, height=6, corner_radius=3)
            bar.set(p.progress_pct / 100.0)
            bar.configure(
                progress_color=COLORS["success"] if p.progress_pct == 100 else COLORS["primary"],
                fg_color=COLORS["bg_card_secondary"]
            )
            bar.pack(fill="x", padx=14, pady=(0, 8))

            p_foot = ctk.CTkFrame(p_card, fg_color="transparent")
            p_foot.pack(fill="x", padx=14, pady=(0, 10))

            owner_lbl = ctk.CTkLabel(
                p_foot,
                text=f"Lead: {p.owner}  •  Due: {p.deadline or 'Flexible'}",
                font=FONTS["small"],
                text_color=COLORS["text_muted"]
            )
            owner_lbl.pack(side="left")

            open_board = ctk.CTkButton(
                p_foot,
                text="Open Board",
                font=FONTS["small_bold"],
                fg_color=COLORS["bg_card"],
                hover_color=COLORS["border"],
                text_color=COLORS["text_secondary"],
                width=85,
                height=24,
                corner_radius=RADII["small"],
                command=lambda pid=p.id: self.on_navigate("kanban", pid) if self.on_navigate else None
            )
            open_board.pack(side="right")

        # Right Column: Upcoming Deadlines & Overdue Alerts
        dead_container = ctk.CTkFrame(mid_row, fg_color=COLORS["bg_card"], corner_radius=RADII["medium"], border_color=COLORS["border"], border_width=1)
        dead_container.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        d_hdr = ctk.CTkFrame(dead_container, fg_color="transparent")
        d_hdr.pack(fill="x", padx=18, pady=(16, 12))
        ctk.CTkLabel(d_hdr, text="Upcoming Deadlines", font=FONTS["section_title"], text_color=COLORS["text_primary"]).pack(side="left")

        if not deadlines:
            ctk.CTkLabel(
                dead_container,
                text="No upcoming task deadlines. You're all caught up!",
                font=FONTS["body"],
                text_color=COLORS["text_muted"],
                pady=20
            ).pack()
        else:
            for task in deadlines:
                d_row = ctk.CTkFrame(dead_container, fg_color=COLORS["bg_card_secondary"], corner_radius=RADII["small"])
                d_row.pack(fill="x", padx=16, pady=5)

                r_inner = ctk.CTkFrame(d_row, fg_color="transparent")
                r_inner.pack(fill="x", padx=12, pady=8)

                # Overdue icon or calendar icon
                icon_txt = "⚠ " if task.is_overdue else "📅 "
                icon_col = COLORS["danger"] if task.is_overdue else COLORS["text_muted"]

                date_lbl = ctk.CTkLabel(
                    r_inner,
                    text=f"{icon_txt}{task.due_date}",
                    font=FONTS["small_bold"],
                    text_color=icon_col
                )
                date_lbl.pack(side="right")

                t_lbl = ctk.CTkLabel(
                    r_inner,
                    text=task.title,
                    font=FONTS["body_bold"],
                    text_color=COLORS["text_primary"],
                    wraplength=220,
                    justify="left",
                    anchor="w"
                )
                t_lbl.pack(fill="x", pady=(0, 2))

                sub_row = ctk.CTkFrame(r_inner, fg_color="transparent")
                sub_row.pack(fill="x")

                pb = PriorityBadge(sub_row, priority=task.priority)
                pb.pack(side="left", padx=(0, 8))

                ass_lbl = ctk.CTkLabel(
                    sub_row,
                    text=f"👤 {task.assignee_name.split()[0]}",
                    font=FONTS["small"],
                    text_color=COLORS["text_muted"]
                )
                ass_lbl.pack(side="left")

                view_btn = ctk.CTkButton(
                    sub_row,
                    text="View",
                    width=45,
                    height=20,
                    font=FONTS["small"],
                    fg_color=COLORS["bg_card"],
                    hover_color=COLORS["border"],
                    text_color=COLORS["primary"],
                    command=lambda tid=task.id: self.on_open_task(tid) if self.on_open_task else None
                )
                view_btn.pack(side="right")

        # 4. Bottom Section: Team Workload (Left 50%) & Recent Activity Feed (Right 50%)
        bot_row = ctk.CTkFrame(scroll, fg_color="transparent")
        bot_row.pack(fill="x", pady=(0, 10))
        bot_row.grid_columnconfigure(0, weight=1)
        bot_row.grid_columnconfigure(1, weight=1)

        # Team Workload
        team_container = ctk.CTkFrame(bot_row, fg_color=COLORS["bg_card"], corner_radius=RADII["medium"], border_color=COLORS["border"], border_width=1)
        team_container.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        t_hdr = ctk.CTkFrame(team_container, fg_color="transparent")
        t_hdr.pack(fill="x", padx=18, pady=(16, 12))
        ctk.CTkLabel(t_hdr, text="Team Workload Distribution", font=FONTS["section_title"], text_color=COLORS["text_primary"]).pack(side="left")

        for m in workload:
            m_row = ctk.CTkFrame(team_container, fg_color=COLORS["bg_card_secondary"], corner_radius=RADII["small"])
            m_row.pack(fill="x", padx=16, pady=5)

            m_inner = ctk.CTkFrame(m_row, fg_color="transparent")
            m_inner.pack(fill="x", padx=12, pady=8)

            av = AvatarBadge(m_inner, name=m["name"], color=m["avatar_color"], size=24)
            av.pack(side="left", padx=(0, 8))

            name_box = ctk.CTkFrame(m_inner, fg_color="transparent")
            name_box.pack(side="left")

            ctk.CTkLabel(name_box, text=m["name"], font=FONTS["body_bold"], text_color=COLORS["text_primary"]).pack(anchor="w")
            ctk.CTkLabel(name_box, text=m["role"], font=FONTS["small"], text_color=COLORS["text_muted"]).pack(anchor="w")

            stat_box = ctk.CTkFrame(m_inner, fg_color="transparent")
            stat_box.pack(side="right")

            stat_txt = f"{m['in_progress']} in progress • {m['completed']} done"
            if m["overdue"] > 0:
                stat_txt += f" • {m['overdue']} overdue"

            ctk.CTkLabel(
                stat_box,
                text=stat_txt,
                font=FONTS["small_bold"],
                text_color=COLORS["danger"] if m["overdue"] > 0 else COLORS["text_secondary"]
            ).pack(anchor="e")

        # Activity Feed
        act_container = ctk.CTkFrame(bot_row, fg_color=COLORS["bg_card"], corner_radius=RADII["medium"], border_color=COLORS["border"], border_width=1)
        act_container.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        a_hdr = ctk.CTkFrame(act_container, fg_color="transparent")
        a_hdr.pack(fill="x", padx=18, pady=(16, 12))
        ctk.CTkLabel(a_hdr, text="Recent Activity Audit Log", font=FONTS["section_title"], text_color=COLORS["text_primary"]).pack(side="left")

        if not activities:
            ctk.CTkLabel(act_container, text="No recent activity logged.", font=FONTS["body"], text_color=COLORS["text_muted"], pady=20).pack()
        else:
            for act in activities:
                a_row = ctk.CTkFrame(act_container, fg_color="transparent")
                a_row.pack(fill="x", padx=16, pady=3)

                dot = ctk.CTkLabel(a_row, text="●", font=("Segoe UI", 8), text_color=COLORS["primary"])
                dot.pack(side="left", padx=(0, 8))

                act_lbl = ctk.CTkLabel(
                    a_row,
                    text=f"{act.user_name} — {act.details}",
                    font=FONTS["body"],
                    text_color=COLORS["text_secondary"],
                    wraplength=340,
                    justify="left",
                    anchor="w"
                )
                act_lbl.pack(side="left", fill="x", expand=True)

                time_lbl = ctk.CTkLabel(
                    a_row,
                    text=act.created_at.split()[1] if " " in act.created_at else act.created_at,
                    font=FONTS["small"],
                    text_color=COLORS["text_muted"]
                )
                time_lbl.pack(side="right")
