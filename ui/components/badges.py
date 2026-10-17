"""
Syncora Badge Components
Reusable chip badges for Status, Priority, Labels, Roles, and Member Avatars.
"""

import customtkinter as ctk
from typing import Optional
from ui.theme import COLORS, FONTS, RADII, ROLES


class PriorityBadge(ctk.CTkFrame):
    """Visual priority badge (High, Medium, Low) with tailored styling."""

    def __init__(self, master, priority: str, **kwargs):
        priority_key = priority.lower() if priority.lower() in ("high", "medium", "low") else "medium"
        fg_color = COLORS.get(f"priority_{priority_key}_bg", ("#3B2A10", "#FEF3C7"))
        border_color = COLORS.get(f"priority_{priority_key}", ("#F59E0B", "#D97706"))

        super().__init__(
            master,
            fg_color=fg_color,
            border_color=border_color,
            border_width=1,
            corner_radius=RADII["pill"],
            height=22,
            **kwargs
        )
        text_color = COLORS.get(f"priority_{priority_key}", ("#F59E0B", "#D97706"))

        icon = "▲ " if priority_key == "high" else ("● " if priority_key == "medium" else "▼ ")
        self.label = ctk.CTkLabel(
            self,
            text=f"{icon}{priority.upper()}",
            font=FONTS["badge"],
            text_color=text_color,
            padx=8,
            pady=1
        )
        self.label.pack(expand=True)


class StatusBadge(ctk.CTkFrame):
    """Visual status badge (Backlog, In Progress, Review, Done)."""

    STATUS_CONFIG = {
        "Backlog": (("#252E3E", "#E2E8F0"), ("#94A3B8", "#64748B")),
        "In Progress": (("#1E2E4B", "#DBEAFE"), ("#60A5FA", "#2563EB")),
        "Review": (("#2E234B", "#EDE9FE"), ("#C084FC", "#7C3AED")),
        "Done": (("#13382E", "#D1FAE5"), ("#34D399", "#059669"))
    }

    def __init__(self, master, status: str, **kwargs):
        cfg = self.STATUS_CONFIG.get(status, self.STATUS_CONFIG["Backlog"])
        super().__init__(
            master,
            fg_color=cfg[0],
            border_color=cfg[1],
            border_width=1,
            corner_radius=RADII["pill"],
            height=22,
            **kwargs
        )
        self.label = ctk.CTkLabel(
            self,
            text=status.upper(),
            font=FONTS["badge"],
            text_color=cfg[1],
            padx=8,
            pady=1
        )
        self.label.pack(expand=True)


class TagBadge(ctk.CTkFrame):
    """Small tag badge for labels (e.g., #frontend, #api)."""

    def __init__(self, master, text: str, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card_secondary"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=RADII["small"],
            height=20,
            **kwargs
        )
        clean_text = text if text.startswith("#") else f"#{text}"
        self.label = ctk.CTkLabel(
            self,
            text=clean_text,
            font=FONTS["small"],
            text_color=COLORS["text_secondary"],
            padx=6,
            pady=0
        )
        self.label.pack(expand=True)


class RoleBadge(ctk.CTkFrame):
    """Team member role indicator badge."""

    def __init__(self, master, role: str, **kwargs):
        color = ROLES.get(role, {}).get("badge_color", "#64748B")
        super().__init__(
            master,
            fg_color="transparent",
            border_color=color,
            border_width=1,
            corner_radius=RADII["pill"],
            height=22,
            **kwargs
        )
        self.label = ctk.CTkLabel(
            self,
            text=role.upper(),
            font=FONTS["badge"],
            text_color=color,
            padx=8,
            pady=1
        )
        self.label.pack(expand=True)


class AvatarBadge(ctk.CTkFrame):
    """Circular/pill initials badge for user profiles and assignees."""

    def __init__(self, master, name: str, color: Optional[str] = None, size: int = 28, **kwargs):
        parts = name.strip().split() if name else []
        initials = (f"{parts[0][0]}{parts[1][0]}" if len(parts) >= 2 else (parts[0][:2] if parts else "?")).upper()
        bg_col = color if color else "#3B82F6"

        super().__init__(
            master,
            fg_color=bg_col,
            corner_radius=size // 2,
            width=size,
            height=size,
            **kwargs
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        self.label = ctk.CTkLabel(
            self,
            text=initials,
            font=("Segoe UI", int(size * 0.38), "bold"),
            text_color="#FFFFFF"
        )
        self.label.place(relx=0.5, rely=0.5, anchor="center")
