"""
Syncora Design System & Theme Constants
Provides unified color palettes, typography, status badges, and styling constants.
"""

# Theme Modes: 'dark', 'light'
DEFAULT_APPEARANCE_MODE = "light"
DEFAULT_COLOR_THEME = "blue"

# Color Palette (Tuple for Dark / Light mode: (Dark Color, Light Color))
COLORS = {
    # Backgrounds
    "bg_main": ("#0B0F19", "#F8FAFC"),
    "bg_sidebar": ("#0F172A", "#FFFFFF"),
    "bg_card": ("#161F30", "#FFFFFF"),
    "bg_card_secondary": ("#1E293B", "#F1F5F9"),
    "bg_card_hover": ("#223048", "#E2E8F0"),
    "border": ("#27354A", "#E2E8F0"),
    "border_focus": ("#8B5CF6", "#7C3AED"),

    # Typography
    "text_primary": ("#F8FAFC", "#0F172A"),
    "text_secondary": ("#94A3B8", "#475569"),
    "text_muted": ("#64748B", "#94A3B8"),
    "text_on_accent": ("#FFFFFF", "#FFFFFF"),

    # Primary Accents (Purple / Violet)
    "primary": ("#8B5CF6", "#7C3AED"),
    "primary_hover": ("#7C3AED", "#6D28D9"),
    "primary_light": ("#2E234B", "#EDE9FE"),

    # Secondary Accents (Blue)
    "secondary": ("#3B82F6", "#2563EB"),
    "secondary_hover": ("#2563EB", "#1D4ED8"),
    "secondary_light": ("#1E2E4B", "#DBEAFE"),

    # Functional / Feedback
    "success": ("#10B981", "#059669"),
    "success_light": ("#13382E", "#D1FAE5"),
    "warning": ("#F59E0B", "#D97706"),
    "warning_light": ("#3D2D14", "#FEF3C7"),
    "danger": ("#EF4444", "#DC2626"),
    "danger_light": ("#3D1919", "#FEE2E2"),
    "info": ("#06B6D4", "#0891B2"),
    "info_light": ("#13313D", "#CFFAFE"),

    # Status Column Accents
    "status_backlog": ("#64748B", "#64748B"),
    "status_in_progress": ("#3B82F6", "#2563EB"),
    "status_review": ("#8B5CF6", "#7C3AED"),
    "status_done": ("#10B981", "#059669"),

    # Priority Badges
    "priority_high": ("#EF4444", "#DC2626"),
    "priority_high_bg": ("#421A1A", "#FEE2E2"),
    "priority_medium": ("#F59E0B", "#D97706"),
    "priority_medium_bg": ("#3B2A10", "#FEF3C7"),
    "priority_low": ("#06B6D4", "#0891B2"),
    "priority_low_bg": ("#102E38", "#CFFAFE"),
}

# Typography definitions
FONTS = {
    "brand_title": ("Segoe UI", 19, "bold"),
    "brand_subtitle": ("Segoe UI", 10),
    "page_title": ("Segoe UI", 20, "bold"),
    "page_subtitle": ("Segoe UI", 11),
    "section_title": ("Segoe UI", 14, "bold"),
    "card_title": ("Segoe UI", 13, "bold"),
    "metric_value": ("Segoe UI", 24, "bold"),
    "metric_label": ("Segoe UI", 11),
    "body": ("Segoe UI", 12),
    "body_bold": ("Segoe UI", 12, "bold"),
    "small": ("Segoe UI", 10),
    "small_bold": ("Segoe UI", 10, "bold"),
    "badge": ("Segoe UI", 9, "bold"),
    "code": ("Consolas", 10),
}

# Spacing & Radii
RADII = {
    "small": 6,
    "medium": 10,
    "large": 14,
    "pill": 20
}

# Role definitions & access rules
ROLES = {
    "Admin": {
        "can_create_project": True,
        "can_edit_project": True,
        "can_delete_project": True,
        "can_manage_members": True,
        "can_create_task": True,
        "can_edit_task": True,
        "can_delete_task": True,
        "can_comment": True,
        "badge_color": "#8B5CF6"
    },
    "Member": {
        "can_create_project": False,
        "can_edit_project": False,
        "can_delete_project": False,
        "can_manage_members": False,
        "can_create_task": True,
        "can_edit_task": True,
        "can_delete_task": True,
        "can_comment": True,
        "badge_color": "#3B82F6"
    },
    "Viewer": {
        "can_create_project": False,
        "can_edit_project": False,
        "can_delete_project": False,
        "can_manage_members": False,
        "can_create_task": False,
        "can_edit_task": False,
        "can_delete_task": False,
        "can_comment": False,
        "badge_color": "#64748B"
    }
}
