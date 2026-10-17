"""
Project Creation & Editing Dialog
Provides form inputs, validation, and lifecycle controls for Projects.
"""

import customtkinter as ctk
from datetime import datetime, timedelta
from typing import Optional, Callable
from models.project import Project
from services import project_service, member_service
from ui.theme import COLORS, FONTS, RADII


class ProjectDialog(ctk.CTkToplevel):
    """Modal dialog for creating and editing projects."""

    def __init__(
        self,
        parent,
        project: Optional[Project] = None,
        current_user: str = "User",
        on_saved: Optional[Callable[[Project], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.project = project
        self.current_user = current_user
        self.on_saved = on_saved

        self.title("Edit Project" if self.project else "Create New Project")
        self.geometry("540x580")
        self.minsize(500, 520)
        self.configure(fg_color=COLORS["bg_main"])

        self.transient(parent)
        self.grab_set()

        # Center relative to parent
        self.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() - 540) // 2
            y = parent.winfo_y() + (parent.winfo_height() - 580) // 2
            self.geometry(f"+{max(10, x)}+{max(10, y)}")
        except Exception:
            pass

        self.members = member_service.get_all_members(include_stats=False)
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=60, corner_radius=0)
        header.pack(fill="x", side="top")

        h_title = ctk.CTkLabel(
            header,
            text="📁  Edit Project" if self.project else "🚀  New Project Workspace",
            font=FONTS["card_title"],
            text_color=COLORS["text_primary"],
            padx=20,
            pady=16
        )
        h_title.pack(side="left")

        # Scrollable form
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # Error notification banner
        self.error_banner = ctk.CTkLabel(
            scroll,
            text="",
            font=FONTS["small_bold"],
            text_color=COLORS["danger"],
            fg_color=COLORS["danger_light"],
            corner_radius=RADII["small"],
            height=30
        )

        # 1. Project Name
        name_lbl = ctk.CTkLabel(scroll, text="Project Name *", font=FONTS["body_bold"], text_color=COLORS["text_primary"])
        name_lbl.pack(anchor="w", pady=(10, 4))

        self.name_entry = ctk.CTkEntry(
            scroll,
            placeholder_text="e.g. EcoTrack Sustainability Platform",
            font=FONTS["body"],
            height=38,
            corner_radius=RADII["small"]
        )
        self.name_entry.pack(fill="x", pady=(0, 10))
        if self.project:
            self.name_entry.insert(0, self.project.name)

        # 2. Description
        desc_lbl = ctk.CTkLabel(scroll, text="Description", font=FONTS["body_bold"], text_color=COLORS["text_primary"])
        desc_lbl.pack(anchor="w", pady=(5, 4))

        self.desc_text = ctk.CTkTextbox(
            scroll,
            font=FONTS["body"],
            height=85,
            corner_radius=RADII["small"]
        )
        self.desc_text.pack(fill="x", pady=(0, 10))
        if self.project and self.project.description:
            self.desc_text.insert("1.0", self.project.description)

        # 3. Owner & Status row
        row1 = ctk.CTkFrame(scroll, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 10))

        # Owner
        owner_col = ctk.CTkFrame(row1, fg_color="transparent")
        owner_col.pack(side="left", fill="x", expand=True, padx=(0, 8))

        owner_lbl = ctk.CTkLabel(owner_col, text="Owner / Lead *", font=FONTS["body_bold"], text_color=COLORS["text_primary"])
        owner_lbl.pack(anchor="w", pady=(0, 4))

        owner_options = [m.name for m in self.members] if self.members else ["Lovish Jangid", "Love Kush"]
        default_owner = self.project.owner if self.project else (self.current_user if self.current_user in owner_options else owner_options[0])

        self.owner_combo = ctk.CTkComboBox(
            owner_col,
            values=owner_options,
            height=36,
            corner_radius=RADII["small"],
            font=FONTS["body"]
        )
        self.owner_combo.set(default_owner)
        self.owner_combo.pack(fill="x")

        # Status
        stat_col = ctk.CTkFrame(row1, fg_color="transparent")
        stat_col.pack(side="left", fill="x", expand=True, padx=(8, 0))

        stat_lbl = ctk.CTkLabel(stat_col, text="Status", font=FONTS["body_bold"], text_color=COLORS["text_primary"])
        stat_lbl.pack(anchor="w", pady=(0, 4))

        self.status_combo = ctk.CTkComboBox(
            stat_col,
            values=["Active", "Completed", "On Hold"],
            height=36,
            corner_radius=RADII["small"],
            font=FONTS["body"]
        )
        self.status_combo.set(self.project.status if self.project else "Active")
        self.status_combo.pack(fill="x")

        # 4. Target Deadline
        dead_lbl = ctk.CTkLabel(scroll, text="Target Completion Deadline (YYYY-MM-DD)", font=FONTS["body_bold"], text_color=COLORS["text_primary"])
        dead_lbl.pack(anchor="w", pady=(5, 4))

        dead_row = ctk.CTkFrame(scroll, fg_color="transparent")
        dead_row.pack(fill="x", pady=(0, 12))

        self.dead_entry = ctk.CTkEntry(
            dead_row,
            placeholder_text="YYYY-MM-DD",
            font=FONTS["body"],
            height=36,
            corner_radius=RADII["small"]
        )
        self.dead_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        if self.project and self.project.deadline:
            self.dead_entry.insert(0, self.project.deadline)

        btn_2w = ctk.CTkButton(
            dead_row,
            text="+2 Weeks",
            width=70,
            height=32,
            font=FONTS["small"],
            fg_color=COLORS["bg_card_secondary"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            command=lambda: self._set_quick_date(14)
        )
        btn_2w.pack(side="left", padx=2)

        btn_1m = ctk.CTkButton(
            dead_row,
            text="+1 Month",
            width=70,
            height=32,
            font=FONTS["small"],
            fg_color=COLORS["bg_card_secondary"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            command=lambda: self._set_quick_date(30)
        )
        btn_1m.pack(side="left", padx=2)

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
            text="Save Project" if self.project else "Create Project",
            font=FONTS["body_bold"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=self._save_project,
            width=140,
            height=38,
            corner_radius=RADII["small"]
        )
        save_btn.pack(side="right", pady=14)

    def _set_quick_date(self, days: int):
        target = datetime.now() + timedelta(days=days)
        self.dead_entry.delete(0, "end")
        self.dead_entry.insert(0, target.strftime("%Y-%m-%d"))

    def _save_project(self):
        name = self.name_entry.get().strip()
        desc = self.desc_text.get("1.0", "end-1c").strip()
        owner = self.owner_combo.get().strip()
        status = self.status_combo.get().strip()
        deadline = self.dead_entry.get().strip() or None

        try:
            if self.project:
                saved = project_service.update_project(
                    project_id=self.project.id,
                    name=name,
                    description=desc,
                    owner=owner,
                    deadline=deadline,
                    status=status,
                    current_user=self.current_user
                )
            else:
                saved = project_service.create_project(
                    name=name,
                    description=desc,
                    owner=owner,
                    deadline=deadline,
                    status=status,
                    current_user=self.current_user
                )

            if self.on_saved and saved:
                self.on_saved(saved)

            self.destroy()

        except Exception as e:
            self.error_banner.configure(text=f"⚠  {str(e)}")
            self.error_banner.pack(fill="x", pady=(0, 10), before=self.name_entry)
