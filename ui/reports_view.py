"""
Reports and Analytics View
Embedded Matplotlib charts (Status Donut, Priority Bars, Team Workload, Project Progress),
overdue task summaries, and CSV data export with file dialog.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Optional, Callable
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from services import report_service, project_service, task_service
from ui.theme import COLORS, FONTS, RADII
from ui.components.badges import PriorityBadge
from ui.components.cards import MetricCard, ToastNotification


class ReportsView(ctk.CTkFrame):
    """Analytics dashboard with embedded Matplotlib visualizations and CSV export."""

    def __init__(
        self,
        master,
        current_project_id: Optional[int] = None,
        on_open_task: Optional[Callable[[int], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.current_project_id = current_project_id
        self.on_open_task = on_open_task
        self.canvas_widgets = []

        self._build_ui()

    def set_project(self, project_id: Optional[int]):
        self.current_project_id = project_id
        self.refresh()

    def refresh(self):
        """Reload analytics and re-render charts."""
        for cw in self.canvas_widgets:
            try:
                cw.get_tk_widget().destroy()
            except Exception:
                pass
        self.canvas_widgets.clear()
        plt.close("all")

        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    def _build_ui(self):
        summary = report_service.get_dashboard_summary(self.current_project_id)
        projects = project_service.get_all_projects(include_stats=True)
        overdue_tasks = report_service.get_overdue_tasks(limit=10, project_id=self.current_project_id)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=20)

        # 1. Header Toolbar
        top_bar = ctk.CTkFrame(scroll, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 20))

        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(title_box, text="Reports & Analytics", font=FONTS["page_title"], text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Agile project health, workflow velocity, workload balance, and task reports",
            font=FONTS["page_subtitle"],
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        actions_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        actions_box.pack(side="right")

        # Project Selector
        self.proj_options = ["All Projects"] + [f"{p.id}: {p.name}" for p in projects]
        default_p = "All Projects"
        if self.current_project_id:
            for opt in self.proj_options:
                if opt.startswith(f"{self.current_project_id}:"):
                    default_p = opt
                    break

        self.proj_combo = ctk.CTkComboBox(
            actions_box,
            values=self.proj_options,
            command=self._on_project_change,
            width=180,
            height=36,
            corner_radius=RADII["small"],
            font=FONTS["body"]
        )
        self.proj_combo.set(default_p)
        self.proj_combo.pack(side="left", padx=(0, 10))

        # CSV Export Button
        export_btn = ctk.CTkButton(
            actions_box,
            text="📥  Export Tasks to CSV",
            font=FONTS["body_bold"],
            fg_color=COLORS["secondary"],
            hover_color=COLORS["secondary_hover"],
            height=36,
            corner_radius=RADII["small"],
            command=self._export_csv
        )
        export_btn.pack(side="right")

        # 2. KPI Summary Cards (4 cards)
        kpi_grid = ctk.CTkFrame(scroll, fg_color="transparent")
        kpi_grid.pack(fill="x", pady=(0, 20))
        for ci in range(4):
            kpi_grid.grid_columnconfigure(ci, weight=1)

        kpis = [
            ("Total Tasks", str(summary["total_tasks"]), "Tracked items", "#3B82F6", "📋"),
            ("Completed", str(summary["completed_tasks"]), f"{summary['completion_rate']}% overall velocity", "#10B981", "✓"),
            ("In Progress", str(summary["in_progress_tasks"]), "Active sprints", "#06B6D4", "⚡"),
            ("Overdue Tasks", str(summary["overdue_tasks"]), "Require immediate triage" if summary["overdue_tasks"] > 0 else "0 late tasks", "#EF4444" if summary["overdue_tasks"] > 0 else "#10B981", "⚠" if summary["overdue_tasks"] > 0 else "✓"),
        ]

        for idx, (title, val, sub, col, sym) in enumerate(kpis):
            mc = MetricCard(kpi_grid, title=title, value=val, subtitle=sub, accent_color=col, icon_symbol=sym)
            mc.grid(row=0, column=idx, padx=6, pady=0, sticky="nsew")

        # 3. Embedded Matplotlib Visualizations Grid (2x2)
        charts_container = ctk.CTkFrame(scroll, fg_color="transparent")
        charts_container.pack(fill="x", pady=(0, 24))
        charts_container.grid_columnconfigure(0, weight=1)
        charts_container.grid_columnconfigure(1, weight=1)

        # Chart 1: Status Distribution (Donut Chart)
        c1_card = ctk.CTkFrame(charts_container, fg_color=COLORS["bg_card"], corner_radius=RADII["medium"], border_color=COLORS["border"], border_width=1)
        c1_card.grid(row=0, column=0, padx=(0, 8), pady=8, sticky="nsew")
        self._render_status_donut(c1_card)

        # Chart 2: Priority Distribution (Bar Chart)
        c2_card = ctk.CTkFrame(charts_container, fg_color=COLORS["bg_card"], corner_radius=RADII["medium"], border_color=COLORS["border"], border_width=1)
        c2_card.grid(row=0, column=1, padx=(8, 0), pady=8, sticky="nsew")
        self._render_priority_bars(c2_card)

        # Chart 3: Team Workload (Horizontal Bars)
        c3_card = ctk.CTkFrame(charts_container, fg_color=COLORS["bg_card"], corner_radius=RADII["medium"], border_color=COLORS["border"], border_width=1)
        c3_card.grid(row=1, column=0, padx=(0, 8), pady=8, sticky="nsew")
        self._render_team_workload(c3_card)

        # Chart 4: Project Progress Comparison
        c4_card = ctk.CTkFrame(charts_container, fg_color=COLORS["bg_card"], corner_radius=RADII["medium"], border_color=COLORS["border"], border_width=1)
        c4_card.grid(row=1, column=1, padx=(8, 0), pady=8, sticky="nsew")
        self._render_project_progress(c4_card, projects)

        # 4. Overdue Tasks Table Section
        overdue_container = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=RADII["medium"], border_color=COLORS["border"], border_width=1)
        overdue_container.pack(fill="x", pady=(0, 16))

        od_hdr = ctk.CTkFrame(overdue_container, fg_color="transparent")
        od_hdr.pack(fill="x", padx=18, pady=(16, 12))

        ctk.CTkLabel(od_hdr, text=f"Overdue Tasks Summary ({len(overdue_tasks)})", font=FONTS["section_title"], text_color=COLORS["danger"] if overdue_tasks else COLORS["text_primary"]).pack(side="left")

        if not overdue_tasks:
            ctk.CTkLabel(
                overdue_container,
                text="✓ No overdue tasks found. All deadlines are within schedule!",
                font=FONTS["body_bold"],
                text_color=COLORS["success"],
                pady=24
            ).pack()
        else:
            table_frame = ctk.CTkFrame(overdue_container, fg_color="transparent")
            table_frame.pack(fill="x", padx=16, pady=(0, 14))

            # Header row
            t_hdr = ctk.CTkFrame(table_frame, fg_color=COLORS["bg_card_secondary"], corner_radius=RADII["small"], height=32)
            t_hdr.pack(fill="x", pady=(0, 6))

            ctk.CTkLabel(t_hdr, text="TASK TITLE", font=FONTS["badge"], text_color=COLORS["text_muted"]).pack(side="left", padx=12)
            ctk.CTkLabel(t_hdr, text="ACTION", font=FONTS["badge"], text_color=COLORS["text_muted"]).pack(side="right", padx=12)
            ctk.CTkLabel(t_hdr, text="DUE DATE", font=FONTS["badge"], text_color=COLORS["text_muted"]).pack(side="right", padx=20)
            ctk.CTkLabel(t_hdr, text="ASSIGNEE", font=FONTS["badge"], text_color=COLORS["text_muted"]).pack(side="right", padx=20)
            ctk.CTkLabel(t_hdr, text="PRIORITY", font=FONTS["badge"], text_color=COLORS["text_muted"]).pack(side="right", padx=20)

            for t in overdue_tasks:
                row = ctk.CTkFrame(table_frame, fg_color=COLORS["danger_light"], corner_radius=RADII["small"])
                row.pack(fill="x", pady=3)

                r_inner = ctk.CTkFrame(row, fg_color="transparent")
                r_inner.pack(fill="x", padx=12, pady=6)

                t_lbl = ctk.CTkLabel(
                    r_inner,
                    text=f"⚠  {t.title} ({t.project_name})",
                    font=FONTS["body_bold"],
                    text_color=COLORS["danger"],
                    anchor="w"
                )
                t_lbl.pack(side="left", fill="x", expand=True)

                view_btn = ctk.CTkButton(
                    r_inner,
                    text="Inspect Task",
                    width=90,
                    height=26,
                    font=FONTS["small_bold"],
                    fg_color=COLORS["danger"],
                    hover_color="#DC2626",
                    command=lambda tid=t.id: self.on_open_task(tid) if self.on_open_task else None
                )
                view_btn.pack(side="right", padx=(8, 0))

                due_lbl = ctk.CTkLabel(r_inner, text=t.due_date, font=FONTS["small_bold"], text_color=COLORS["danger"])
                due_lbl.pack(side="right", padx=16)

                ass_lbl = ctk.CTkLabel(r_inner, text=t.assignee_name, font=FONTS["small"], text_color=COLORS["text_primary"])
                ass_lbl.pack(side="right", padx=16)

                pb = PriorityBadge(r_inner, priority=t.priority)
                pb.pack(side="right", padx=16)

    # ----------------- Matplotlib Visualizations -----------------

    def _get_chart_theme(self):
        is_dark = ctk.get_appearance_mode().lower() == "dark"
        return {
            "bg": "#161F30" if is_dark else "#FFFFFF",
            "border": "#27354A" if is_dark else "#E2E8F0",
            "text": "#F8FAFC" if is_dark else "#0F172A",
            "text_muted": "#94A3B8" if is_dark else "#64748B",
            "grid": "#27354A" if is_dark else "#E2E8F0",
            "legend_bg": "#1E293B" if is_dark else "#F8FAFC",
            "legend_border": "#27354A" if is_dark else "#CBD5E1",
        }

    def _render_status_donut(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="Task Status Distribution", font=FONTS["card_title"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(12, 0))

        status_counts = report_service.get_status_distribution(self.current_project_id)
        labels = ["Backlog", "In Progress", "Review", "Done"]
        values = [status_counts.get(s, 0) for s in labels]
        colors = ["#64748B", "#3B82F6", "#8B5CF6", "#10B981"]

        theme = self._get_chart_theme()
        fig, ax = plt.subplots(figsize=(4.2, 3.0), dpi=100)
        fig.patch.set_facecolor(theme["bg"])
        ax.set_facecolor(theme["bg"])

        total = sum(values)
        if total == 0:
            ax.text(0, 0, "No tasks to display", color=theme["text_muted"], ha="center", va="center", fontsize=11)
            ax.axis("off")
        else:
            # Filter non-zero slices for clean rendering
            non_zero = [(lbl, val, col) for lbl, val, col in zip(labels, values, colors) if val > 0]
            nz_labels = [x[0] for x in non_zero]
            nz_vals = [x[1] for x in non_zero]
            nz_cols = [x[2] for x in non_zero]

            wedges, texts, autotexts = ax.pie(
                nz_vals,
                labels=nz_labels,
                autopct="%1.0f%%",
                startangle=140,
                colors=nz_cols,
                wedgeprops=dict(width=0.45, edgecolor=theme["bg"], linewidth=2),
                textprops=dict(color=theme["text"], fontsize=9)
            )
            for autotext in autotexts:
                autotext.set_color("#FFFFFF")
                autotext.set_fontweight("bold")
                autotext.set_fontsize(9)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas_widgets.append(canvas)

    def _render_priority_bars(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="Tasks by Priority Level", font=FONTS["card_title"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(12, 0))

        prio_counts = report_service.get_priority_distribution(self.current_project_id)
        categories = ["Low", "Medium", "High"]
        counts = [prio_counts.get(c, 0) for c in categories]
        bar_colors = ["#06B6D4", "#F59E0B", "#EF4444"]

        theme = self._get_chart_theme()
        fig, ax = plt.subplots(figsize=(4.2, 3.0), dpi=100)
        fig.patch.set_facecolor(theme["bg"])
        ax.set_facecolor(theme["bg"])

        bars = ax.bar(categories, counts, color=bar_colors, width=0.55, edgecolor=theme["border"])

        # Styling
        ax.tick_params(colors=theme["text_muted"], labelsize=9)
        for spine in ax.spines.values():
            spine.set_color(theme["border"])
        ax.grid(axis="y", color=theme["grid"], linestyle="--", alpha=0.6)

        # Bar value labels on top
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{height}",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha="center", va="bottom",
                        color=theme["text"], fontsize=9, fontweight="bold")

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas_widgets.append(canvas)

    def _render_team_workload(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="Member Workload Allocation", font=FONTS["card_title"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(12, 0))

        workload = report_service.get_team_workload_summary()
        names = [m["name"].split()[0] for m in workload]
        in_prog = [m["in_progress"] for m in workload]
        completed = [m["completed"] for m in workload]

        theme = self._get_chart_theme()
        fig, ax = plt.subplots(figsize=(4.2, 3.0), dpi=100)
        fig.patch.set_facecolor(theme["bg"])
        ax.set_facecolor(theme["bg"])

        if not names:
            ax.text(0.5, 0.5, "No members found", color=theme["text_muted"], ha="center", va="center")
            ax.axis("off")
        else:
            y_pos = range(len(names))
            ax.barh(y_pos, completed, color="#10B981", height=0.45, label="Done", edgecolor=theme["border"])
            ax.barh(y_pos, in_prog, left=completed, color="#3B82F6", height=0.45, label="In Progress", edgecolor=theme["border"])

            ax.set_yticks(y_pos)
            ax.set_yticklabels(names, color=theme["text"], fontsize=9)
            ax.tick_params(colors=theme["text_muted"], labelsize=9)
            for spine in ax.spines.values():
                spine.set_color(theme["border"])
            ax.grid(axis="x", color=theme["grid"], linestyle="--", alpha=0.6)
            ax.legend(loc="lower right", facecolor=theme["legend_bg"], edgecolor=theme["legend_border"], labelcolor=theme["text"], fontsize=8)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas_widgets.append(canvas)

    def _render_project_progress(self, parent_frame, projects):
        ctk.CTkLabel(parent_frame, text="Project Completion Comparison", font=FONTS["card_title"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(12, 0))

        p_names = [p.name[:14] + "..." if len(p.name) > 14 else p.name for p in projects]
        pcts = [p.progress_pct for p in projects]

        theme = self._get_chart_theme()
        fig, ax = plt.subplots(figsize=(4.2, 3.0), dpi=100)
        fig.patch.set_facecolor(theme["bg"])
        ax.set_facecolor(theme["bg"])

        if not p_names:
            ax.text(0.5, 0.5, "No projects found", color=theme["text_muted"], ha="center", va="center")
            ax.axis("off")
        else:
            bars = ax.bar(p_names, pcts, color="#8B5CF6", width=0.5, edgecolor=theme["border"])
            ax.set_ylim(0, 100)
            ax.tick_params(colors=theme["text_muted"], labelsize=9)
            for spine in ax.spines.values():
                spine.set_color(theme["border"])
            ax.grid(axis="y", color=theme["grid"], linestyle="--", alpha=0.6)

            for bar in bars:
                h = bar.get_height()
                ax.annotate(f"{h}%",
                            xy=(bar.get_x() + bar.get_width() / 2, h),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha="center", va="bottom",
                            color=theme["text"], fontsize=9, fontweight="bold")

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas_widgets.append(canvas)

    def _on_project_change(self, choice: str):
        if choice == "All Projects":
            self.current_project_id = None
        else:
            try:
                self.current_project_id = int(choice.split(":")[0])
            except ValueError:
                self.current_project_id = None
        self.refresh()

    def _export_csv(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Export Syncora Tasks to CSV",
            initialfile="syncora_tasks_export.csv"
        )
        if file_path:
            try:
                count = report_service.export_tasks_to_csv(file_path, project_id=self.current_project_id)
                messagebox.showinfo(
                    "Export Successful",
                    f"Successfully exported {count} tasks to:\n{file_path}"
                )
            except Exception as e:
                messagebox.showerror("Export Failed", f"An error occurred while exporting: {e}")
