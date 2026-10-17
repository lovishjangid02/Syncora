"""
Member Creation & Editing Dialog
Provides form inputs, email validation, role selection, and avatar color customization.
"""

import customtkinter as ctk
from typing import Optional, Callable
from models.member import Member
from services import member_service
from ui.theme import COLORS, FONTS, RADII


class MemberDialog(ctk.CTkToplevel):
    """Modal dialog for creating and editing team members."""

    COLOR_PRESETS = [
        ("#3B82F6", "Blue"),
        ("#8B5CF6", "Purple"),
        ("#10B981", "Emerald"),
        ("#F59E0B", "Amber"),
        ("#EF4444", "Rose"),
        ("#06B6D4", "Cyan")
    ]

    def __init__(
        self,
        parent,
        member: Optional[Member] = None,
        current_user: str = "User",
        on_saved: Optional[Callable[[Member], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.member = member
        self.current_user = current_user
        self.on_saved = on_saved
        self.selected_color = member.avatar_color if member else "#3B82F6"

        self.title("Edit Team Member" if self.member else "Add Team Member")
        self.geometry("480x520")
        self.minsize(440, 480)
        self.configure(fg_color=COLORS["bg_main"])

        self.transient(parent)
        self.grab_set()

        # Center relative to parent
        self.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() - 480) // 2
            y = parent.winfo_y() + (parent.winfo_height() - 520) // 2
            self.geometry(f"+{max(10, x)}+{max(10, y)}")
        except Exception:
            pass

        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=60, corner_radius=0)
        header.pack(fill="x", side="top")

        h_title = ctk.CTkLabel(
            header,
            text="👤  Edit Team Member" if self.member else "👥  Add New Team Member",
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

        # 1. Full Name
        name_lbl = ctk.CTkLabel(scroll, text="Full Name *", font=FONTS["body_bold"], text_color=COLORS["text_primary"])
        name_lbl.pack(anchor="w", pady=(10, 4))

        self.name_entry = ctk.CTkEntry(
            scroll,
            placeholder_text="e.g. Jordan Lee",
            font=FONTS["body"],
            height=38,
            corner_radius=RADII["small"]
        )
        self.name_entry.pack(fill="x", pady=(0, 12))
        if self.member:
            self.name_entry.insert(0, self.member.name)

        # 2. Email Address
        email_lbl = ctk.CTkLabel(scroll, text="Email Address *", font=FONTS["body_bold"], text_color=COLORS["text_primary"])
        email_lbl.pack(anchor="w", pady=(0, 4))

        self.email_entry = ctk.CTkEntry(
            scroll,
            placeholder_text="jordan.lee@university.edu",
            font=FONTS["body"],
            height=38,
            corner_radius=RADII["small"]
        )
        self.email_entry.pack(fill="x", pady=(0, 12))
        if self.member:
            self.email_entry.insert(0, self.member.email)

        # 3. Role
        role_lbl = ctk.CTkLabel(scroll, text="Assigned Role *", font=FONTS["body_bold"], text_color=COLORS["text_primary"])
        role_lbl.pack(anchor="w", pady=(0, 4))

        self.role_combo = ctk.CTkComboBox(
            scroll,
            values=["Admin", "Member", "Viewer"],
            height=38,
            corner_radius=RADII["small"],
            font=FONTS["body"]
        )
        self.role_combo.set(self.member.role if self.member else "Member")
        self.role_combo.pack(fill="x", pady=(0, 12))

        # 4. Avatar Theme Color
        color_lbl = ctk.CTkLabel(scroll, text="Avatar Accent Color", font=FONTS["body_bold"], text_color=COLORS["text_primary"])
        color_lbl.pack(anchor="w", pady=(0, 6))

        color_row = ctk.CTkFrame(scroll, fg_color="transparent")
        color_row.pack(fill="x", pady=(0, 16))

        self.color_buttons = []
        for hex_code, label in self.COLOR_PRESETS:
            btn = ctk.CTkButton(
                color_row,
                text="✓" if hex_code.lower() == self.selected_color.lower() else "",
                width=36,
                height=36,
                corner_radius=18,
                fg_color=hex_code,
                hover_color=hex_code,
                text_color="#FFFFFF",
                font=("Segoe UI", 12, "bold"),
                command=lambda c=hex_code: self._select_color(c)
            )
            btn.pack(side="left", padx=4)
            self.color_buttons.append((hex_code, btn))

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
            text="Save Member" if self.member else "Add Member",
            font=FONTS["body_bold"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=self._save_member,
            width=130,
            height=38,
            corner_radius=RADII["small"]
        )
        save_btn.pack(side="right", pady=14)

    def _select_color(self, hex_code: str):
        self.selected_color = hex_code
        for code, btn in self.color_buttons:
            btn.configure(text="✓" if code.lower() == hex_code.lower() else "")

    def _save_member(self):
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        role = self.role_combo.get().strip()

        try:
            if self.member:
                saved = member_service.update_member(
                    member_id=self.member.id,
                    name=name,
                    email=email,
                    role=role,
                    avatar_color=self.selected_color,
                    current_user=self.current_user
                )
            else:
                saved = member_service.create_member(
                    name=name,
                    email=email,
                    role=role,
                    avatar_color=self.selected_color,
                    current_user=self.current_user
                )

            if self.on_saved and saved:
                self.on_saved(saved)

            self.destroy()

        except Exception as e:
            self.error_banner.configure(text=f"⚠  {str(e)}")
            self.error_banner.pack(fill="x", pady=(0, 10), before=self.name_entry)
