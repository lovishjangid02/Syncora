"""
End-to-End Hackathon Demonstration Scenario Test
Simulates the exact 10-step demo script from Section 11 of the specification:
1. Open dashboard.
2. Show project and team workload.
3. Create a new task.
4. Assign it to a team member.
5. Set priority and deadline.
6. Move from Backlog -> In Progress -> Done.
7. Add a comment and update checklist.
8. Verify dashboard statistics update.
9. Verify SQLite persistence after re-connecting.
10. Export to CSV.
"""

import sys
import os
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import DatabaseManager
from services.project_service import ProjectService
from services.member_service import MemberService
from services.task_service import TaskService
from services.report_service import ReportService


def run_demo_flow():
    print("=" * 60)
    print("Starting Syncora 10-Step Hackathon Demo Scenario")
    print("=" * 60)

    # Use a clean test database
    temp_db = tempfile.mktemp(suffix=".db")
    db = DatabaseManager(db_path=temp_db)
    project_svc = ProjectService(db)
    member_svc = MemberService(db)
    task_svc = TaskService(db)
    report_svc = ReportService(db)

    # Step 1: Open dashboard and seed data
    print("\n[Step 1 & 2] Opening Dashboard & Inspecting Initial Stats...")
    db.seed_demo_data(force=True)
    summary_before = report_svc.get_dashboard_summary()
    print(f"-> Total Projects: {summary_before['total_projects']}")
    print(f"-> Total Tasks: {summary_before['total_tasks']}")
    print(f"-> Initial Completion Rate: {summary_before['completion_rate']}%")
    print(f"-> In Progress: {summary_before['in_progress_tasks']}, Overdue: {summary_before['overdue_tasks']}")

    projects = project_svc.get_all_projects()
    members = member_svc.get_all_members()
    target_project = projects[0]
    target_member = members[1]  # Anshul Verma
    print(f"-> Selected Target Project: '{target_project.name}' (ID: {target_project.id})")
    print(f"-> Selected Assignee: '{target_member.name}' ({target_member.role})")

    # Step 3, 4, 5: Create new task, assign it, set priority and deadline
    print("\n[Step 3, 4, 5] Creating New Task with Assignee, Priority & Due Date...")
    new_task = task_svc.create_task(
        title="Implement WebSocket Live Sync",
        description="Add offline-first real-time synchronization bridge for peer clients.",
        project_id=target_project.id,
        assignee_id=target_member.id,
        status="Backlog",
        priority="High",
        due_date="2026-10-30",
        labels="realtime,backend,networking",
        checklist_items=["Design socket payload", "Write connection handshake", "Test edge reconnection"],
        current_user="Lovish Jangid"
    )
    print(f"-> Created Task ID {new_task.id}: '{new_task.title}'")
    print(f"   Assignee: {new_task.assignee_name}, Status: {new_task.status}, Priority: {new_task.priority}")
    print(f"   Checklist Items: {new_task.checklist_total}")
    assert new_task.id is not None
    assert new_task.status == "Backlog"

    # Step 6: Move from Backlog -> In Progress -> Done
    print("\n[Step 6] Moving Task Across Kanban Columns...")
    task_svc.update_task_status(new_task.id, "In Progress", current_user=target_member.name)
    t1 = task_svc.get_task_by_id(new_task.id)
    print(f"-> Advanced to: {t1.status}")
    assert t1.status == "In Progress"

    task_svc.update_task_status(new_task.id, "Done", current_user=target_member.name)
    t2 = task_svc.get_task_by_id(new_task.id)
    print(f"-> Advanced to: {t2.status}")
    assert t2.status == "Done"

    # Step 7: Add comment and update checklist
    print("\n[Step 7] Updating Checklists and Adding Discussion Comments...")
    chk_items = task_svc.get_checklist_items(new_task.id)
    print(f"-> Initial checklist items count: {len(chk_items)}")
    # Complete step 1 and step 2
    task_svc.toggle_checklist_item(chk_items[0].id, True, current_user=target_member.name)
    task_svc.toggle_checklist_item(chk_items[1].id, True, current_user=target_member.name)
    t_updated = task_svc.get_task_by_id(new_task.id)
    print(f"-> Checklists completed: {t_updated.checklist_completed}/{t_updated.checklist_total} ({t_updated.checklist_progress_pct}%)")
    assert t_updated.checklist_completed == 2

    # Add comment
    comment = task_svc.add_comment(
        task_id=new_task.id,
        author_name="Lovish Jangid",
        content="Excellent work on the connection handshake! Benchmarks look great."
    )
    print(f"-> Posted Comment by '{comment.author_name}': \"{comment.content}\"")
    comments = task_svc.get_comments(new_task.id)
    assert len(comments) >= 1

    # Step 8: Show dashboard statistics updating correctly
    print("\n[Step 8] Verifying Real-Time Dashboard Statistics Update...")
    summary_after = report_svc.get_dashboard_summary()
    print(f"-> Total Tasks: {summary_after['total_tasks']} (was {summary_before['total_tasks']})")
    print(f"-> Completed Tasks: {summary_after['completed_tasks']} (was {summary_before['completed_tasks']})")
    print(f"-> New Completion Rate: {summary_after['completion_rate']}% (was {summary_before['completion_rate']}%)")
    assert summary_after["total_tasks"] == summary_before["total_tasks"] + 1
    assert summary_after["completed_tasks"] == summary_before["completed_tasks"] + 1

    # Step 9: Reconnect / verify SQLite persistence
    print("\n[Step 9] Verifying SQLite Persistence Across New Connections...")
    db_reopened = DatabaseManager(db_path=temp_db)
    task_svc_reopened = TaskService(db_reopened)
    persisted_task = task_svc_reopened.get_task_by_id(new_task.id)
    print(f"-> Re-fetched Task ID {persisted_task.id} from cold SQLite storage:")
    print(f"   Title: '{persisted_task.title}'")
    print(f"   Status: '{persisted_task.status}'")
    print(f"   Assignee: '{persisted_task.assignee_name}'")
    print(f"   Checklist: {persisted_task.checklist_completed}/{persisted_task.checklist_total}")
    assert persisted_task.title == "Implement WebSocket Live Sync"
    assert persisted_task.status == "Done"
    assert persisted_task.checklist_completed == 2

    # Step 10: Export task data to CSV
    print("\n[Step 10] Exporting Complete Project Dataset to CSV...")
    csv_path = tempfile.mktemp(suffix=".csv")
    exported_count = report_svc.export_tasks_to_csv(csv_path)
    print(f"-> Exported {exported_count} tasks to {csv_path}")
    assert exported_count == summary_after["total_tasks"]
    with open(csv_path, "r", encoding="utf-8") as f:
        csv_text = f.read()
        assert "Implement WebSocket Live Sync" in csv_text
        assert "Lovish Jangid" in csv_text
    print("-> CSV file contents verified successfully!")

    # Cleanup temp
    try:
        os.remove(temp_db)
        os.remove(csv_path)
    except Exception:
        pass

    print("\n" + "=" * 60)
    print("SUCCESS: ALL 10 DEMO SCENARIO CHECKS PASSED PERFECTLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_demo_flow()
