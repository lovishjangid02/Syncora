"""
Syncora Main Application Window
Coordinates top navigation, collapsible left sidebar, active role switcher,
screen transitions, modal dialogs, and real-time refresh workflows.
"""

import os
import logging
from typing import Optional, Dict
import customtkinter as ctk
from database import db
from models.task import Task
from models.project import Project
from models.member import Member
from services import project_service, member_service, task_service
from ui.theme import COLORS, FONTS, RADII, ROLES, DEFAULT_APPEARANCE_MODE
from ui.components.badges import RoleBadge, AvatarBadge
from ui.components.cards import ConfirmDialog, ToastNotification
from ui.task_dialog import TaskDialog
from ui.task_detail_dialog import TaskDetailDialog
from ui.project_dialog import ProjectDialog
from ui.member_dialog import MemberDialog
from ui.dashboard_view import DashboardView
from ui.kanban_view import KanbanView
from ui.project_view import ProjectView
from ui.team_view import TeamView
from ui.reports_view import ReportsView

logger = logging.getLogger("Syncora.MainWindow")


class MainWindow(ctk.CTk):
    """Main application shell for Syncora desktop tracker."""

    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("Syncora — Collaborative Agile Project Tracker")
        self.geometry("1400x860")
        self.minsize(1100, 700)

        # Set default appearance
        ctk.set_appearance_mode(DEFAULT_APPEARANCE_MODE)
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=COLORS["bg_main"])

        # Member list for profile selector
        self.members = member_service.get_all_members(include_stats=False)
        self.projects = project_service.get_all_projects(include_stats=False)

        # State management (default to first Admin if available, else first member)
        admin_member = next((m for m in self.members if m.role == "Admin"), None)
        if admin_member:
            self.current_user = admin_member.name
            self.user_role = admin_member.role
        elif self.members:
            self.current_user = self.members[0].name
            self.user_role = self.members[0].role
        else:
            self.current_user = "Mehul Jangid"
            self.user_role = "Admin"
        self.current_project_id: Optional[int] = None
        self.active_view_name = "dashboard"

        # View references cache
        self.views: Dict[str, ctk.CTkFrame] = {}

        self._build_shell()
        self.show_view("dashboard")

    def _build_shell(self):
        # Configure layout: 2 columns (Sidebar: col 0, Main Area: col 1)
        self.grid_columnconfigure(0, weight=0, minsize=240)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Left Sidebar
        self.sidebar = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_sidebar"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=0,
            width=240
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self._build_sidebar()

        # 2. Right Main Container (Top Bar + Dynamic View Container + Status Bar)
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)

        self._build_top_bar()

        # Dynamic View Host
        self.view_host = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_host.grid(row=1, column=0, sticky="nsew")
        self.view_host.grid_columnconfigure(0, weight=1)
        self.view_host.grid_rowconfigure(0, weight=1)

        self._build_status_bar()

    def _build_sidebar(self):
        # Brand Header
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=16, pady=(20, 14))

        logo_row = ctk.CTkFrame(brand_frame, fg_color="transparent")
        logo_row.pack(anchor="w")

        glyph = ctk.CTkLabel(
            logo_row,
            text="⚡",
            font=("Segoe UI", 20, "bold"),
            text_color=COLORS["primary"]
        )
        glyph.pack(side="left", padx=(0, 8))

        b_name = ctk.CTkLabel(
            logo_row,
            text="Syncora",
            font=FONTS["brand_title"],
            text_color=COLORS["text_primary"]
        )
        b_name.pack(side="left")

        b_sub = ctk.CTkLabel(
            brand_frame,
            text="AGILE COLLABORATION SUITE",
            font=FONTS["badge"],
            text_color=COLORS["text_muted"]
        )
        b_sub.pack(anchor="w", pady=(2, 0))

        # Divider
        div1 = ctk.CTkFrame(self.sidebar, fg_color=COLORS["border"], height=1)
        div1.pack(fill="x", padx=14, pady=(10, 14))

        # Navigation Links
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}
        nav_items = [
            ("dashboard", "📊  Dashboard"),
            ("kanban", "📋  Kanban Board"),
            ("projects", "📁  Projects"),
            ("team", "👥  Team & Roles"),
            ("reports", "📈  Reports & Analytics"),
        ]

        for key, label in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                font=FONTS["body_bold"],
                anchor="w",
                fg_color="transparent",
                hover_color=COLORS["bg_card_secondary"],
                text_color=COLORS["text_secondary"],
                height=40,
                corner_radius=RADII["small"],
                command=lambda k=key: self.show_view(k)
            )
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[key] = btn

        # Workspace Project Quick Switcher
        div2 = ctk.CTkFrame(self.sidebar, fg_color=COLORS["border"], height=1)
        div2.pack(fill="x", padx=14, pady=16)

        ws_label = ctk.CTkLabel(
            self.sidebar,
            text="ACTIVE WORKSPACE",
            font=FONTS["badge"],
            text_color=COLORS["text_muted"]
        )
        ws_label.pack(anchor="w", padx=16, pady=(0, 6))

        self.sidebar_proj_options = ["All Workspaces"] + [f"{p.id}: {p.name}" for p in self.projects]
        self.sidebar_proj_combo = ctk.CTkComboBox(
            self.sidebar,
            values=self.sidebar_proj_options,
            command=self._on_sidebar_workspace_select,
            height=32,
            font=FONTS["small"],
            corner_radius=RADII["small"]
        )
        self.sidebar_proj_combo.set("All Workspaces")
        self.sidebar_proj_combo.pack(fill="x", padx=12, pady=(0, 14))

        # Bottom Utilities Container
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=12, pady=16)

        # Quick New Task button
        self.side_new_task_btn = ctk.CTkButton(
            bottom_frame,
            text="+ Quick New Task",
            font=FONTS["body_bold"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            height=36,
            corner_radius=RADII["small"],
            command=lambda: self.open_task_dialog()
        )
        self.side_new_task_btn.pack(fill="x", pady=(0, 8))

        # Reset / Load Demo Data button
        demo_btn = ctk.CTkButton(
            bottom_frame,
            text="↺ Reload Demo Data",
            font=FONTS["small"],
            fg_color=COLORS["bg_card_secondary"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_secondary"],
            height=30,
            corner_radius=RADII["small"],
            command=self._confirm_reload_demo
        )
        demo_btn.pack(fill="x", pady=(0, 10))

        # Theme Switch
        theme_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        theme_row.pack(fill="x", pady=(0, 6))

        is_dark = DEFAULT_APPEARANCE_MODE.lower() == "dark"
        self.theme_label = ctk.CTkLabel(
            theme_row,
            text="Dark Theme" if is_dark else "Light Theme",
            font=FONTS["small"],
            text_color=COLORS["text_muted"]
        )
        self.theme_label.pack(side="left")

        self.theme_switch = ctk.CTkSwitch(
            theme_row,
            text="",
            command=self._toggle_theme,
            width=40,
            height=20
        )
        if is_dark:
            self.theme_switch.select()
        else:
            self.theme_switch.deselect()
        self.theme_switch.pack(side="right")

        # Version stamp
        v_lbl = ctk.CTkLabel(
            bottom_frame,
            text="Syncora v1.0 • Offline SQLite",
            font=FONTS["small"],
            text_color=COLORS["text_muted"]
        )
        v_lbl.pack(pady=(4, 0))

    def _build_top_bar(self):
        self.top_bar = ctk.CTkFrame(
            self.main_container,
            fg_color=COLORS["bg_sidebar"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=0,
            height=60
        )
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.top_bar.grid_propagate(False)

        # Left: Breadcrumb / View Title
        self.title_container = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.title_container.pack(side="left", padx=20, pady=12)

        self.top_title_label = ctk.CTkLabel(
            self.title_container,
            text="Dashboard Overview",
            font=FONTS["card_title"],
            text_color=COLORS["text_primary"]
        )
        self.top_title_label.pack(side="left")

        # Right: User Profile Switcher & Actions
        self.top_right = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.top_right.pack(side="right", padx=20, pady=12)

        # Refresh Data button
        refresh_btn = ctk.CTkButton(
            self.top_right,
            text="↻",
            width=32,
            height=32,
            font=("Segoe UI", 14, "bold"),
            fg_color=COLORS["bg_card_secondary"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            command=self.refresh_current_view
        )
        refresh_btn.pack(side="left", padx=(0, 12))

        # Role switcher pill (Demonstrates Role-Aware UI)
        role_frame = ctk.CTkFrame(self.top_right, fg_color="transparent")
        role_frame.pack(side="left")

        ctk.CTkLabel(role_frame, text="Active Profile:", font=FONTS["small"], text_color=COLORS["text_muted"]).pack(side="left", padx=(0, 6))

        # Profile options format: "Name (Role)"
        profile_options = [f"{m.name} ({m.role})" for m in self.members] if self.members else [f"{self.current_user} ({self.user_role})"]
        default_profile = f"{self.current_user} ({self.user_role})"

        self.profile_combo = ctk.CTkComboBox(
            role_frame,
            values=profile_options,
            command=self._on_profile_switch,
            width=210,
            height=32,
            font=FONTS["small_bold"],
            corner_radius=RADII["pill"],
            state="readonly"
        )
        self.profile_combo.set(default_profile)
        self.profile_combo.pack(side="left")

    def _build_status_bar(self):
        self.status_bar = ctk.CTkFrame(
            self.main_container,
            fg_color=COLORS["bg_sidebar"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=0,
            height=28
        )
        self.status_bar.grid(row=2, column=0, sticky="ew")
        self.status_bar.grid_propagate(False)

        # Status text
        self.status_lbl = ctk.CTkLabel(
            self.status_bar,
            text=f"● SQLite Database Connected: {os.path.basename(db.db_path)}  •  Foreign Keys: ON  •  Ready",
            font=FONTS["small"],
            text_color=COLORS["success"]
        )
        self.status_lbl.pack(side="left", padx=16)

        self.workspace_status_lbl = ctk.CTkLabel(
            self.status_bar,
            text=f"Role: {self.user_role}  •  Workspace: All Workspaces",
            font=FONTS["small"],
            text_color=COLORS["text_muted"]
        )
        self.workspace_status_lbl.pack(side="right", padx=16)

    # ----------------- View Navigation & Management -----------------

    def show_view(self, view_name: str, target_project_id: Optional[int] = None):
        """Switch active main container screen."""
        if target_project_id is not None:
            self.current_project_id = target_project_id

        self.active_view_name = view_name

        # Update sidebar button highlight
        for key, btn in self.nav_buttons.items():
            if key == view_name:
                btn.configure(
                    fg_color=COLORS["primary_light"],
                    text_color=COLORS["primary"]
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["text_secondary"]
                )

        # Update Top Bar Title
        title_map = {
            "dashboard": "Dashboard Overview",
            "kanban": "Interactive Kanban Task Board",
            "projects": "Project Workspaces",
            "team": "Team Members & Role Responsibilities",
            "reports": "Reports & Agile Analytics"
        }
        self.top_title_label.configure(text=title_map.get(view_name, "Syncora"))

        # Destroy current view and create new one
        for child in self.view_host.winfo_children():
            child.destroy()

        if view_name == "dashboard":
            view = DashboardView(
                self.view_host,
                current_user=self.current_user,
                user_role=self.user_role,
                on_navigate=self.show_view,
                on_open_task=self.open_task_detail_by_id,
                on_create_task=lambda: self.open_task_dialog(),
                on_create_project=lambda: self.open_project_dialog()
            )
        elif view_name == "kanban":
            view = KanbanView(
                self.view_host,
                current_project_id=self.current_project_id,
                current_user=self.current_user,
                user_role=self.user_role,
                on_open_task=self.open_task_detail,
                on_create_task=lambda s: self.open_task_dialog(default_status=s)
            )
        elif view_name == "projects":
            view = ProjectView(
                self.view_host,
                current_user=self.current_user,
                user_role=self.user_role,
                on_open_kanban=lambda pid: self.show_view("kanban", pid),
                on_create_project=lambda: self.open_project_dialog(),
                on_edit_project=lambda p: self.open_project_dialog(p)
            )
        elif view_name == "team":
            view = TeamView(
                self.view_host,
                current_user=self.current_user,
                user_role=self.user_role,
                on_add_member=lambda: self.open_member_dialog(),
                on_edit_member=lambda m: self.open_member_dialog(m),
                on_filter_member_tasks=lambda mid: self.show_view("kanban", None)
            )
        elif view_name == "reports":
            view = ReportsView(
                self.view_host,
                current_project_id=self.current_project_id,
                on_open_task=self.open_task_detail_by_id
            )
        else:
            view = ctk.CTkLabel(self.view_host, text="View not found.")

        view.pack(fill="both", expand=True)
        self.views[view_name] = view

        # Update status bar info
        proj_name = "All Workspaces"
        if self.current_project_id:
            proj = project_service.get_project_by_id(self.current_project_id, include_stats=False)
            if proj:
                proj_name = proj.name

        self.workspace_status_lbl.configure(text=f"Role: {self.user_role}  •  Workspace: {proj_name}")

    def refresh_current_view(self):
        """Refresh whatever view is currently active."""
        # Reload projects and members
        self.projects = project_service.get_all_projects(include_stats=False)
        self.members = member_service.get_all_members(include_stats=False)

        # Update sidebar combo values
        self.sidebar_proj_options = ["All Workspaces"] + [f"{p.id}: {p.name}" for p in self.projects]
        self.sidebar_proj_combo.configure(values=self.sidebar_proj_options)

        # Update profile combo values so member renames are instantly reflected
        if hasattr(self, "profile_combo"):
            profile_opts = [f"{m.name} ({m.role})" for m in self.members] if self.members else [f"{self.current_user} ({self.user_role})"]
            self.profile_combo.configure(values=profile_opts)
            cur_profile = f"{self.current_user} ({self.user_role})"
            if cur_profile in profile_opts:
                self.profile_combo.set(cur_profile)
            elif self.members:
                self.current_user = self.members[0].name
                self.user_role = self.members[0].role
                self.profile_combo.set(f"{self.current_user} ({self.user_role})")

        # Re-render active view
        self.show_view(self.active_view_name, self.current_project_id)

    # ----------------- Profile / Role Switcher -----------------

    def _on_profile_switch(self, choice: str):
        """Switch current user and role dynamically."""
        for m in self.members:
            if choice.startswith(m.name):
                self.current_user = m.name
                self.user_role = m.role
                break

        # Update UI permissions
        can_create_task = ROLES.get(self.user_role, {}).get("can_create_task", True)
        self.side_new_task_btn.configure(state="normal" if can_create_task else "disabled")

        self.refresh_current_view()

    # ----------------- Workspace Switcher -----------------

    def _on_sidebar_workspace_select(self, choice: str):
        if choice == "All Workspaces":
            self.current_project_id = None
        else:
            try:
                self.current_project_id = int(choice.split(":")[0])
            except ValueError:
                self.current_project_id = None

        self.show_view(self.active_view_name, self.current_project_id)

    # ----------------- Theme Switcher -----------------

    def _toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("dark")
            self.theme_label.configure(text="Dark Theme")
        else:
            ctk.set_appearance_mode("light")
            self.theme_label.configure(text="Light Theme")
        self.refresh_current_view()

    # ----------------- Reload Demo Data -----------------

    def _confirm_reload_demo(self):
        ConfirmDialog(
            self,
            title="Reset to Demo Data",
            message="Are you sure you want to reset the database?\nThis will re-seed sample projects, team members, tasks, checklists, and activity logs.",
            confirm_text="Reset Data",
            on_confirm=self._do_reload_demo
        )

    def _do_reload_demo(self):
        db.reset_database()
        self.refresh_current_view()
        ToastNotification(self.main_container, message="Demo data reloaded successfully!", level="success").place(relx=0.5, rely=0.08, anchor="center")

    # ----------------- Dialog Openers -----------------

    def open_task_dialog(self, task: Optional[Task] = None, default_status: str = "Backlog"):
        can_create = ROLES.get(self.user_role, {}).get("can_create_task", True)
        if not can_create and not task:
            ToastNotification(self.main_container, message="Viewers do not have permission to create tasks.", level="warning").place(relx=0.5, rely=0.08, anchor="center")
            return

        TaskDialog(
            self,
            task=task,
            default_project_id=self.current_project_id,
            default_status=default_status,
            current_user=self.current_user,
            on_saved=lambda t: self.refresh_current_view()
        )

    def open_task_detail(self, task: Task):
        TaskDetailDialog(
            self,
            task=task,
            current_user=self.current_user,
            user_role=self.user_role,
            on_updated=self.refresh_current_view,
            on_deleted=self.refresh_current_view,
            on_edit_request=lambda t: self.open_task_dialog(t)
        )

    def open_task_detail_by_id(self, task_id: int):
        task = task_service.get_task_by_id(task_id)
        if task:
            self.open_task_detail(task)

    def open_project_dialog(self, project: Optional[Project] = None):
        can_proj = ROLES.get(self.user_role, {}).get("can_create_project", True) if not project else ROLES.get(self.user_role, {}).get("can_edit_project", True)
        if not can_proj:
            ToastNotification(self.main_container, message="Insufficient permissions to manage projects.", level="warning").place(relx=0.5, rely=0.08, anchor="center")
            return

        ProjectDialog(
            self,
            project=project,
            current_user=self.current_user,
            on_saved=lambda p: self.refresh_current_view()
        )

    def open_member_dialog(self, member: Optional[Member] = None):
        can_mem = ROLES.get(self.user_role, {}).get("can_manage_members", True)
        if not can_mem:
            ToastNotification(self.main_container, message="Only Admins can add or edit team members.", level="warning").place(relx=0.5, rely=0.08, anchor="center")
            return

        def _on_saved(saved_member: Member):
            if member and member.name == self.current_user:
                self.current_user = saved_member.name
                self.user_role = saved_member.role
            self.refresh_current_view()

        MemberDialog(
            self,
            member=member,
            current_user=self.current_user,
            on_saved=_on_saved
        )
