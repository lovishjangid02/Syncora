"""
Syncora Card Components & Dialogs
Includes Metric Cards, Confirmation Dialogs, and Toast Notifications.
"""

import customtkinter as ctk
from typing import Optional, Callable
from ui.theme import COLORS, FONTS, RADII


class MetricCard(ctk.CTkFrame):
    """Modern dashboard KPI card with value, label, accent indicator, and subtitle."""

    def __init__(
        self,
        master,
        title: str,
        value: str,
        subtitle: str = "",
        accent_color: str = "#8B5CF6",
        icon_symbol: str = "◆",
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=RADII["medium"],
            **kwargs
        )
        self.accent_color = accent_color

        # Accent top bar
        self.accent_bar = ctk.CTkFrame(
            self,
            fg_color=accent_color,
            height=3,
            corner_radius=0
        )
        self.accent_bar.pack(fill="x", side="top")

        # Container for inner padding
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=16, pady=12)

        # Header row: Title + Icon
        self.header_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.header_frame.pack(fill="x", side="top")

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text=title.upper(),
            font=FONTS["metric_label"],
            text_color=COLORS["text_secondary"]
        )
        self.title_label.pack(side="left")

        self.icon_label = ctk.CTkLabel(
            self.header_frame,
            text=icon_symbol,
            font=("Segoe UI", 12, "bold"),
            text_color=accent_color
        )
        self.icon_label.pack(side="right")

        # Value
        self.value_label = ctk.CTkLabel(
            self.container,
            text=str(value),
            font=FONTS["metric_value"],
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        self.value_label.pack(fill="x", pady=(4, 0))

        # Subtitle
        if subtitle:
            self.sub_label = ctk.CTkLabel(
                self.container,
                text=subtitle,
                font=FONTS["small"],
                text_color=COLORS["text_muted"],
                anchor="w"
            )
            self.sub_label.pack(fill="x", pady=(2, 0))

    def update_value(self, new_value: str, subtitle: Optional[str] = None):
        """Dynamically update card metrics."""
        self.value_label.configure(text=str(new_value))
        if subtitle is not None and hasattr(self, "sub_label"):
            self.sub_label.configure(text=subtitle)


class ConfirmDialog(ctk.CTkToplevel):
    """Modal confirmation dialog for destructive actions."""

    def __init__(
        self,
        parent,
        title: str,
        message: str,
        confirm_text: str = "Confirm Delete",
        confirm_color: str = "#EF4444",
        on_confirm: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.title(title)
        self.geometry("420x220")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_card"])

        self.on_confirm = on_confirm
        self.result = False

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center dialog relative to parent
        self.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() - 420) // 2
            y = parent.winfo_y() + (parent.winfo_height() - 220) // 2
            self.geometry(f"+{max(10, x)}+{max(10, y)}")
        except Exception:
            pass

        # Content frame
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        # Title & Warning Icon
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        icon = ctk.CTkLabel(
            header,
            text="⚠",
            font=("Segoe UI", 24, "bold"),
            text_color=confirm_color
        )
        icon.pack(side="left", padx=(0, 10))

        title_lbl = ctk.CTkLabel(
            header,
            text=title,
            font=FONTS["card_title"],
            text_color=COLORS["text_primary"]
        )
        title_lbl.pack(side="left", fill="x")

        # Message
        msg_lbl = ctk.CTkLabel(
            container,
            text=message,
            font=FONTS["body"],
            text_color=COLORS["text_secondary"],
            wraplength=370,
            justify="left"
        )
        msg_lbl.pack(fill="both", expand=True, pady=(0, 15))

        # Button row
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom")

        cancel_btn = ctk.CTkButton(
            btn_row,
            text="Cancel",
            font=FONTS["body"],
            fg_color=COLORS["bg_card_secondary"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            command=self._cancel,
            width=110,
            height=36,
            corner_radius=RADII["small"]
        )
        cancel_btn.pack(side="right", padx=(8, 0))

        confirm_btn = ctk.CTkButton(
            btn_row,
            text=confirm_text,
            font=FONTS["body_bold"],
            fg_color=confirm_color,
            hover_color="#DC2626",
            text_color="#FFFFFF",
            command=self._confirm,
            width=140,
            height=36,
            corner_radius=RADII["small"]
        )
        confirm_btn.pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _confirm(self):
        self.result = True
        self.destroy()
        if self.on_confirm:
            self.on_confirm()

    def _cancel(self):
        self.result = False
        self.destroy()


class ToastNotification(ctk.CTkFrame):
    """Temporary toast banner surfaced inside the window container."""

    def __init__(self, master, message: str, level: str = "success", duration_ms: int = 3500, **kwargs):
        color_map = {
            "success": (COLORS["success"], COLORS["success_light"]),
            "error": (COLORS["danger"], COLORS["danger_light"]),
            "warning": (COLORS["warning"], COLORS["warning_light"]),
            "info": (COLORS["info"], COLORS["info_light"]),
        }
        accent, bg = color_map.get(level, color_map["info"])

        super().__init__(
            master,
            fg_color=bg,
            border_color=accent,
            border_width=1,
            corner_radius=RADII["medium"],
            **kwargs
        )
        icon_map = {"success": "✓", "error": "✕", "warning": "⚠", "info": "ℹ"}

        self.label = ctk.CTkLabel(
            self,
            text=f"{icon_map.get(level, 'ℹ')}  {message}",
            font=FONTS["body_bold"],
            text_color=accent,
            padx=16,
            pady=8
        )
        self.label.pack(side="left", fill="both", expand=True)

        close_btn = ctk.CTkButton(
            self,
            text="✕",
            width=24,
            height=24,
            font=FONTS["small"],
            fg_color="transparent",
            hover_color=COLORS["border"],
            text_color=accent,
            command=self.dismiss
        )
        close_btn.pack(side="right", padx=(0, 8))

        if duration_ms > 0:
            self.after(duration_ms, self.dismiss)

    def dismiss(self):
        try:
            self.destroy()
        except Exception:
            pass
