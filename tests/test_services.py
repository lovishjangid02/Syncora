"""
Unit & Integration Tests for Syncora Services (Project, Task, Member, Reports)
"""

import unittest
import os
import tempfile
import sys
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import DatabaseManager
from services.project_service import ProjectService
from services.member_service import MemberService
from services.task_service import TaskService
from services.report_service import ReportService
from services.activity_service import ActivityService


class TestServices(unittest.TestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db = DatabaseManager(db_path=self.temp_db_path)
        self.db.seed_demo_data(force=True)

        self.project_svc = ProjectService(self.db)
        self.member_svc = MemberService(self.db)
        self.task_svc = TaskService(self.db)
        self.report_svc = ReportService(self.db)
        self.activity_svc = ActivityService(self.db)

    def tearDown(self):
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except PermissionError:
                pass

    def test_project_crud(self):
        """Test Project creation, read, update, stats, and delete."""
        proj = self.project_svc.create_project(
            name="Alpha Project",
            description="Alpha test project",
            owner="Mehul Jangid",
            deadline="2026-12-31",
            status="Active"
        )
        self.assertIsNotNone(proj)
        self.assertEqual(proj.name, "Alpha Project")

        # Update
        updated = self.project_svc.update_project(
            project_id=proj.id,
            name="Alpha Project Updated",
            description="Updated desc",
            owner="Mehul Jangid",
            deadline="2027-01-15",
            status="Completed"
        )
        self.assertEqual(updated.name, "Alpha Project Updated")
        self.assertEqual(updated.status, "Completed")

        # Delete
        success = self.project_svc.delete_project(proj.id)
        self.assertTrue(success)
        self.assertIsNone(self.project_svc.get_project_by_id(proj.id))

    def test_member_crud(self):
        """Test Member creation, validation, unique email, update, delete."""
        member = self.member_svc.create_member(
            name="Sam Wilson",
            email="sam.wilson@univ.edu",
            role="Member",
            avatar_color="#8B5CF6"
        )
        self.assertIsNotNone(member)
        self.assertEqual(member.name, "Sam Wilson")

        # Duplicate email should fail
        with self.assertRaises(ValueError):
            self.member_svc.create_member("Duplicate", "sam.wilson@univ.edu", "Member")

        # Update
        updated = self.member_svc.update_member(
            member_id=member.id,
            name="Sam Wilson Jr.",
            email="sam.jr@univ.edu",
            role="Admin"
        )
        self.assertEqual(updated.name, "Sam Wilson Jr.")
        self.assertEqual(updated.role, "Admin")

        # Delete
        self.assertTrue(self.member_svc.delete_member(member.id))

    def test_task_workflow_and_statuses(self):
        """Test task status progression across Backlog, In Progress, Review, and Done."""
        projects = self.project_svc.get_all_projects()
        p_id = projects[0].id

        task = self.task_svc.create_task(
            title="Workflow Test Task",
            description="Testing four column Kanban status movement",
            project_id=p_id,
            status="Backlog",
            priority="High",
            due_date="2026-11-20",
            labels="test,agile",
            checklist_items=["Step 1", "Step 2"]
        )
        self.assertEqual(task.status, "Backlog")

        # Advance to In Progress
        self.assertTrue(self.task_svc.update_task_status(task.id, "In Progress"))
        t_prog = self.task_svc.get_task_by_id(task.id)
        self.assertEqual(t_prog.status, "In Progress")

        # Advance to Review
        self.assertTrue(self.task_svc.update_task_status(task.id, "Review"))
        t_rev = self.task_svc.get_task_by_id(task.id)
        self.assertEqual(t_rev.status, "Review")

        # Advance to Done
        self.assertTrue(self.task_svc.update_task_status(task.id, "Done"))
        t_done = self.task_svc.get_task_by_id(task.id)
        self.assertEqual(t_done.status, "Done")

    def test_checklists_and_comments(self):
        """Test checklist additions, toggles, and comments stream."""
        tasks = self.task_svc.get_tasks()
        task = tasks[0]

        # Add checklist item
        item = self.task_svc.add_checklist_item(task.id, "Verify documentation")
        self.assertFalse(item.is_completed)

        # Toggle item
        self.assertTrue(self.task_svc.toggle_checklist_item(item.id, True))
        items = self.task_svc.get_checklist_items(task.id)
        matching = [i for i in items if i.id == item.id]
        self.assertTrue(matching[0].is_completed)

        # Add comment
        comment = self.task_svc.add_comment(task.id, "Mehul Jangid", "Looks good for release!")
        self.assertEqual(comment.content, "Looks good for release!")

        comments = self.task_svc.get_comments(task.id)
        self.assertIn("Looks good for release!", [c.content for c in comments])

    def test_overdue_calculation(self):
        """Test overdue task detection."""
        projects = self.project_svc.get_all_projects()
        p_id = projects[0].id
        past_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

        task = self.task_svc.create_task(
            title="Overdue Test Task",
            description="Testing overdue detection",
            project_id=p_id,
            status="In Progress",
            priority="High",
            due_date=past_date
        )
        self.assertTrue(task.is_overdue)

        # If moved to Done, it should not be overdue
        self.task_svc.update_task_status(task.id, "Done")
        t_done = self.task_svc.get_task_by_id(task.id)
        self.assertFalse(t_done.is_overdue)

    def test_csv_export(self):
        """Test exporting tasks to CSV."""
        temp_csv = tempfile.mktemp(suffix=".csv")
        try:
            count = self.report_svc.export_tasks_to_csv(temp_csv)
            self.assertGreater(count, 0)
            self.assertTrue(os.path.exists(temp_csv))

            with open(temp_csv, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("Task ID,Title,Description", content)
                self.assertIn("Design Database Schema & Constraints", content)
        finally:
            if os.path.exists(temp_csv):
                os.remove(temp_csv)


if __name__ == "__main__":
    unittest.main()
