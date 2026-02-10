"""OpenClawd integration helpers."""

import os
import shutil
from pathlib import Path
from typing import Optional

from .doctor import get_openclawd_path

def check_openclawd_installed() -> bool:
    """Check if OpenClawd is installed."""
    return get_openclawd_path().exists()

def get_workflows_path() -> Path:
    """Get OpenClawd workflows directory."""
    return get_openclawd_path() / "workflows"

def get_rules_path() -> Path:
    """Get OpenClawd rules directory."""
    return get_openclawd_path() / "rules"

def get_assets_path() -> Path:
    """Get OpenClawd assets directory."""
    return get_openclawd_path() / "assets"

def ensure_simplifia_dirs():
    """Ensure SIMPLIFIA directories exist in OpenClawd."""
    paths = [
        get_workflows_path() / "simplifia",
        get_rules_path() / "simplifia",
        get_assets_path() / "simplifia",
    ]
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)

def detect_openclawd_import_command() -> Optional[str]:
    """
    Detect if OpenClawd has an import command.
    Returns the command string if found, None otherwise.
    """
    # Check common locations for openclawd CLI
    openclawd_cli = shutil.which("openclawd")
    if openclawd_cli:
        # TODO: Check if 'openclawd import' exists
        return "openclawd import"
    return None
