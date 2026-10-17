"""
Unit & Integration Tests for DatabaseManager
"""

import unittest
import os
import tempfile
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db = DatabaseManager(db_path=self.temp_db_path)

    def tearDown(self):
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except PermissionError:
                pass

    def test_schema_initialization(self):
        """Verify that all required tables and indexes exist."""
        with self.db.connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row["name"] for row in cur.fetchall()]

            self.assertIn("projects", tables)
            self.assertIn("members", tables)
            self.assertIn("tasks", tables)
            self.assertIn("checklist_items", tables)
            self.assertIn("comments", tables)
            self.assertIn("activity_logs", tables)

    def test_foreign_key_cascade(self):
        """Verify ON DELETE CASCADE works when deleting a project."""
        with self.db.transaction() as cur:
            cur.execute("""
                INSERT INTO projects (name, description, owner, status, created_at, updated_at)
                VALUES ('Test Proj', 'Desc', 'Owner', 'Active', '2026-10-16', '2026-10-16')
            """)
            proj_id = cur.lastrowid

            cur.execute("""
                INSERT INTO tasks (title, project_id, status, priority, created_at, updated_at)
                VALUES ('Test Task', ?, 'Backlog', 'High', '2026-10-16', '2026-10-16')
            """, (proj_id,))
            task_id = cur.lastrowid

            cur.execute("""
                INSERT INTO checklist_items (task_id, title, is_completed, created_at)
                VALUES (?, 'Step 1', 0, '2026-10-16')
            """, (task_id,))

        # Delete project
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM projects WHERE id = ?", (proj_id,))

        # Verify task and checklist were cascaded
        with self.db.connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM tasks WHERE id = ?", (task_id,))
            self.assertEqual(cur.fetchone()[0], 0)
            cur.execute("SELECT COUNT(*) FROM checklist_items WHERE task_id = ?", (task_id,))
            self.assertEqual(cur.fetchone()[0], 0)

    def test_seed_demo_data(self):
        """Verify seeding adds projects, members, and tasks."""
        self.assertTrue(self.db.is_empty())
        self.db.seed_demo_data(force=True)
        self.assertFalse(self.db.is_empty())

        with self.db.connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM projects")
            self.assertGreater(cur.fetchone()[0], 0)
            cur.execute("SELECT COUNT(*) FROM tasks")
            self.assertGreater(cur.fetchone()[0], 0)
            cur.execute("SELECT COUNT(*) FROM members")
            self.assertGreater(cur.fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
