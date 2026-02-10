"""State management - tracks installed packs."""

import json
import os
from pathlib import Path
from typing import Dict, Optional

from .doctor import get_simplifia_path

def get_state_file() -> Path:
    """Get path to installed.json."""
    return get_simplifia_path() / "installed.json"

def get_installed_packs() -> Dict[str, dict]:
    """Get all installed packs."""
    state_file = get_state_file()
    if not state_file.exists():
        return {}
    
    try:
        return json.loads(state_file.read_text())
    except (json.JSONDecodeError, IOError):
        return {}

def mark_installed(pack_id: str, info: dict):
    """Mark a pack as installed."""
    installed = get_installed_packs()
    installed[pack_id] = info
    
    state_file = get_state_file()
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(installed, indent=2))

def mark_uninstalled(pack_id: str):
    """Mark a pack as uninstalled."""
    installed = get_installed_packs()
    if pack_id in installed:
        del installed[pack_id]
        state_file = get_state_file()
        state_file.write_text(json.dumps(installed, indent=2))

def get_pack_status(pack_id: str) -> str:
    """Get status string for a pack."""
    # TODO: check if files exist, db is healthy, etc.
    return "✓ OK"
