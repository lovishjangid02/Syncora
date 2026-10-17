"""
GUI & Shell Integration Tests for Syncora
Verifies window creation, view transitions, and widget rendering.
"""

import unittest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import db
from ui.main_window import MainWindow


class TestUIIntegration(unittest.TestCase):
    def setUp(self):
        db.seed_demo_data()

    def test_main_window_and_views(self):
        """Test MainWindow initialization and screen transitions."""
        app = MainWindow()
        app.update()

        # Switch to Kanban
        app.show_view("kanban")
        app.update()
        self.assertEqual(app.active_view_name, "kanban")

        # Switch to Projects
        app.show_view("projects")
        app.update()
        self.assertEqual(app.active_view_name, "projects")

        # Switch to Team
        app.show_view("team")
        app.update()
        self.assertEqual(app.active_view_name, "team")

        # Switch to Reports
        app.show_view("reports")
        app.update()
        self.assertEqual(app.active_view_name, "reports")

        # Switch back to Dashboard
        app.show_view("dashboard")
        app.update()
        self.assertEqual(app.active_view_name, "dashboard")

        # Test role switch
        app._on_profile_switch("Love Kush (Member)")
        app.update()
        self.assertEqual(app.current_user, "Love Kush")
        self.assertEqual(app.user_role, "Member")

        app.destroy()


if __name__ == "__main__":
    unittest.main()
