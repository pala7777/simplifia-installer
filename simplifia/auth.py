"""SimplifIA CLI - Authentication management."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def _auth_dir() -> Path:
    """Get auth directory (~/.simplifia)."""
    return Path.home() / ".simplifia"


def auth_path() -> Path:
    """Get auth file path."""
    return _auth_dir() / "auth.json"


@dataclass
class AuthState:
    """Current authentication state."""
    session_token: str
    entitlements: list[str]
    product: Optional[str] = None
    niche: Optional[str] = None
    created_at: Optional[str] = None


def load_auth() -> Optional[AuthState]:
    """Load authentication state from disk."""
    p = auth_path()
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        st = data.get("session_token")
        if not st:
            return None
        return AuthState(
            session_token=st,
            entitlements=list(data.get("entitlements") or []),
            product=data.get("product"),
            niche=data.get("niche"),
            created_at=data.get("created_at"),
        )
    except Exception:
        return None


def save_auth(
    session_token: str,
    entitlements: list[str],
    product: str | None,
    niche: str | None
) -> None:
    """Save authentication state to disk."""
    d = _auth_dir()
    d.mkdir(parents=True, exist_ok=True)
    
    payload: dict[str, Any] = {
        "session_token": session_token,
        "entitlements": entitlements,
        "product": product,
        "niche": niche,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    
    # Atomic write
    p = auth_path()
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)


def clear_auth() -> None:
    """Clear authentication state."""
    p = auth_path()
    if p.exists():
        p.unlink()
