"""
Syncora — Advanced Collaborative Task & Agile Project Tracker
Main entry point for the desktop application.
"""

import sys
import os
import logging

# Ensure root project directory is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Syncora")


def main():
    logger.info("Starting Syncora Application...")

    # 1. Initialize SQLite Database & Auto-Seed Demo Data if empty
    from database import db
    if db.is_empty():
        logger.info("First launch detected: Seeding realistic demo data...")
        db.seed_demo_data()

    # 2. Launch GUI Application Shell
    from ui.main_window import MainWindow
    app = MainWindow()
    logger.info("Syncora window rendered. Entering main event loop.")
    app.mainloop()


if __name__ == "__main__":
    main()


