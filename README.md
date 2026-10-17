# Syncora — Advanced Collaborative Task & Agile Project Tracker

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-7C3AED.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![Database](https://img.shields.io/badge/Database-SQLite3%20(Local%20Offline)-003B57.svg)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Hackathon Problem 3**: Collaborative Task & Agile Project Tracker  
> An offline-first, modern desktop application designed for student engineering teams to organize workloads, assign responsibilities, track deadlines, manage interactive Kanban boards, and visualize project health.

---

## 🌟 Key Features

### 1. 📊 Executive Dashboard
- **Dynamic KPI Metrics**: Real-time calculations of Total Projects, Total Tasks, Completed Tasks, In-Progress Tasks, Review Tasks, and Overdue Tasks directly from SQLite.
- **Velocity & Completion Rate**: Live percentage progress bars reflecting actual database task completion.
- **Project Progress Overview**: Workspace health cards showing team leads, target deadlines, and progress ratios.
- **Upcoming Deadlines & Alerts**: Highlights imminent deadlines and flags overdue items in red.
- **Team Workload Breakdown**: Real-time distribution showing active tasks per contributor.
- **Chronological Activity Log**: Audit trail recording project creation, task movements, checklist updates, and comments.

### 2. 📋 Interactive Kanban Board
- **Four Standard Agile Columns**: `Backlog`, `In Progress`, `Review`, and `Done` with accent-coded status badges and item counters.
- **Rich Task Cards**:
  - Priority indicators (`High` ▲, `Medium` ●, `Low` ▼) with custom color styling.
  - Project workspace tags and label badges (e.g., `#frontend`, `#database`, `#ui/ux`).
  - Assignee initials avatar and name.
  - Due date with bright `OVERDUE` alert badge if past due date.
  - Real-time checklist ratio (e.g., `☑ 2/3`) and comment counters (`💬 2`).
  - **Quick-Move Controls**: `◀ Prev` and `Next ▶` buttons right on each card to immediately shift status across columns with instant database persistence.
- **Multi-Criteria Filtering & Live Search**: Filter simultaneously by Project, Assignee, Priority, and keyword search with an instant "Clear Filters" button.

### 3. 📝 Task Creation, Editing & Collaboration
- **Modal Task Form**: Full input validation, title, multiline description, project assignment, member assignment, status, priority, and labels.
- **Quick Date Shortcuts**: Instant `+Today`, `+3d`, `+1w` buttons for rapid deadline entry in standard `YYYY-MM-DD` format.
- **Interactive Checklists**: Checkboxes with immediate SQLite synchronization, dynamic percentage completion calculation, item addition, and item deletion.
- **Discussion Stream**: Timestamped comments with author avatars and names.
- **Task Audit Trail**: History of status movements, edits, and checklist changes.

### 4. 📁 Project Management & Workspaces
- Create, view, edit, and delete multiple project workspaces.
- Computed project progress percentage from associated tasks.
- Cascade deletion handling: deleting a project safely cleans up associated tasks, checklists, and comments in a single database transaction with confirmation modals.

### 5. 👥 Team & Role-Aware Collaboration
- Team member roster with contact emails and customizable avatar colors.
- Individual workload tracking: Assigned, In Progress, Completed, Overdue.
- **Role-Aware Interface Behavior**:
  - **Admin**: Full authority to create, edit, and delete projects, tasks, and team members.
  - **Member**: Can create/edit tasks, update checklists, post comments, and advance task statuses.
  - **Viewer**: Read-only stakeholder/evaluator mode; destructive buttons and form creation are protected.
- **Active Profile Switcher**: One-click dropdown in the top bar to test different roles immediately during judging!

### 6. 📈 Reports & Analytics (Matplotlib Visualizations)
- **Status Distribution**: Donut chart visualizing task ratios across all 4 statuses.
- **Priority Distribution**: Bar chart comparing High, Medium, and Low workloads.
- **Member Workload Allocation**: Horizontal stacked bar chart displaying tasks per team member.
- **Project Progress Comparison**: Multi-project velocity comparison bar chart.
- **Overdue Summary Table**: Detailed tabular breakdown of all overdue tasks with direct "Inspect Task" buttons.
- **CSV Data Export**: One-click native file dialog export of all tasks, assignees, dates, statuses, and checklist metrics to `.csv`.

### 7. 🎨 UI/UX Design System
- **Dark Theme by Default**: Deep navy/charcoal palette (`#0B0F19`, `#161F30`, `#1E293B`) with subtle violet (`#8B5CF6`) and royal blue (`#3B82F6`) accents.
- **Theme Toggle**: Real-time switch between Dark and Light appearance modes.
- **Responsive Layout**: Designed for smooth resizing on 1366×768 and 1920×1080 displays.

---

## 🛠️ Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| **Programming Language** | Python 3.11+ | Clean type hints, modern syntax, cross-platform |
| **Desktop GUI Framework** | CustomTkinter 6.0+ | Modern SaaS aesthetics, rounded corners, dark/light themes |
| **Database Storage** | SQLite 3 | Offline-first, zero-configuration, relational foreign key cascade |
| **Visual Analytics** | Matplotlib (TkAgg backend) | Embedded data visualizations with theme-matched color styling |
| **Image & Icon Support** | Pillow (PIL) | Native image asset scaling |

---

## 📂 Project Architecture

```
TaskFlow/
├── main.py                     # Application entry point & initialization
├── database.py                 # SQLite connection manager, schema & demo data seeder
├── requirements.txt            # Project dependencies
├── README.md                   # Comprehensive documentation & demo guide
├── .gitignore                  # Git exclusion rules
├── models/                     # Data models
│   ├── __init__.py
│   ├── project.py              # Project entity & progress calculations
│   ├── member.py               # Member entity & workload scores
│   └── task.py                 # Task, Checklist, Comment, ActivityLog models
├── services/                   # Business logic layer
│   ├── __init__.py
│   ├── project_service.py      # Project CRUD, validation, and stats
│   ├── member_service.py       # Team roster, roles, and workloads
│   ├── task_service.py         # Task workflows, checklists, comments, filters
│   ├── report_service.py       # Aggregations, metrics, Matplotlib data, CSV export
│   └── activity_service.py     # Audit trail logging
├── ui/                         # User Interface layer
│   ├── __init__.py
│   ├── theme.py                # Colors, fonts, radii, and role permissions
│   ├── main_window.py          # Main application shell (sidebar, topbar, status bar)
│   ├── dashboard_view.py       # Executive dashboard screen
│   ├── kanban_view.py          # Interactive 4-column Kanban board
│   ├── project_view.py         # Project workspaces browser
│   ├── team_view.py            # Team management & role permissions screen
│   ├── reports_view.py         # Visual analytics & CSV export screen
│   ├── task_dialog.py          # Modal task creation/editing form
│   ├── task_detail_dialog.py   # Modal task collaboration, checklists & comments
│   ├── project_dialog.py       # Modal project creation/editing form
│   ├── member_dialog.py        # Modal member creation/editing form
│   └── components/             # Reusable UI widgets
│       ├── __init__.py
│       ├── badges.py           # PriorityBadge, StatusBadge, TagBadge, RoleBadge, AvatarBadge
│       ├── cards.py            # MetricCard, ConfirmDialog, ToastNotification
│       └── task_card.py        # Interactive Kanban TaskCard
└── tests/                      # Automated test suite
    ├── test_database.py        # Database schema & constraint tests
    ├── test_services.py        # Service layer CRUD & calculation tests
    ├── test_ui.py              # UI shell & view transition tests
    └── test_demo_flow.py       # End-to-end 10-step hackathon demo test
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11, 3.12, 3.13, or 3.14.
- Windows, macOS, or Linux.

### 1. Installation
Clone or navigate to the project directory:
```bash
cd TaskFlow
```

Install the dependencies:
```bash
pip install -r requirements.txt
```
*(Dependencies: `customtkinter`, `pillow`, `matplotlib`, `darkdetect`)*

### 2. Launch the Application
Run:
```bash
python main.py
```
On first launch, Syncora automatically initializes `syncora.db` and populates realistic student hackathon demo data.

---

## 🧪 Running Automated Tests

Run the complete test suite:
```bash
python -m unittest discover tests
```

Run the end-to-end 10-step hackathon demo simulation:
```bash
python tests/test_demo_flow.py
```

---

## 🎬 10-Step Live Demo Script for Evaluators

1. **Dashboard Overview**: Launch `python main.py`. Observe the 6 KPI metric cards, project health progress bars, upcoming deadlines, team workload distribution, and chronological activity log.
2. **Interactive Kanban Board**: Click `📋 Kanban Board` in the left sidebar. Notice the 4 columns: `Backlog`, `In Progress`, `Review`, and `Done`.
3. **Filter & Search**: Type `database` in the search box; observe instant real-time filtering. Try the `Priority` or `Assignee` dropdowns, then click `Clear Filters`.
4. **Create a Task**: Click `+ New Task`. Fill in Title, Description, select a Project, Assignee, Priority, Due Date (`+3d` button), and add initial checklist steps. Click `Create Task`.
5. **Kanban Status Transitions**: On the newly created card, click the `Next ▶` button to move it from `Backlog` to `In Progress`, and click `Next ▶` again to move it to `Review` or `Done`.
6. **Task Collaboration & Interactive Checklists**: Click on any task card to open the **Task Detail Dialog**.
   - Check off a checklist item — observe the checklist progress bar update dynamically (e.g. `2/3 (67%)`).
   - Add a new checklist item with `+ Add Step`.
   - Post a discussion comment using the comment box.
7. **Verify Dashboard Reactivity**: Return to `📊 Dashboard` and observe that total tasks, completed tasks, and overall velocity percentage have updated to match SQLite records.
8. **Role-Aware UI Demonstration**: In the top navigation bar, change the **Active Profile** dropdown from `Mehul Jangid (Admin)` to `Prof. Rajesh Sharma (Viewer)`. Notice that creation buttons are protected and destructive actions are restricted for Viewers. Switch back to Admin anytime.
9. **Analytics & Embedded Charts**: Click `📈 Reports & Analytics`. Review the dark-theme embedded Matplotlib charts (Status Donut, Priority Bars, Member Workload, Project Progress).
10. **CSV Data Export & Persistence**:
    - Click `📥 Export Tasks to CSV`, select a destination path, and save. Open the CSV to verify all fields, assignees, dates, and checklist metrics.
    - Close the application and restart `python main.py` to confirm 100% offline persistence in SQLite.

---

## 🔒 Publishing to GitHub

To publish this project to a public GitHub repository:

```bash
# 1. Initialize git
git init

# 2. Add files (.gitignore automatically excludes databases and virtual environments)
git add .

# 3. Commit
git commit -m "feat: complete Syncora agile desktop tracker application"

# 4. Link to GitHub and push
git remote add origin https://github.com/YOUR_USERNAME/TaskFlow.git
git branch -M main
git push -u origin main
```

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
