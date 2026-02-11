"""Entry point for PyInstaller and python -m simplifia."""

import sys
import os

# Add the parent directory to path for imports to work
if getattr(sys, 'frozen', False):
    # Running as compiled
    bundle_dir = sys._MEIPASS
    sys.path.insert(0, bundle_dir)
else:
    # Running as script
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simplifia.cli import app

if __name__ == "__main__":
    app()
