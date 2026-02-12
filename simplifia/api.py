"""SimplifIA CLI - API client."""
from __future__ import annotations

import os
import platform
import uuid
from dataclasses import dataclass
from typing import Any, Optional

import httpx

DEFAULT_API_BASE = "https://simplifia.com.br/api/v1"


def api_base() -> str:
    return os.getenv("SIMPLIFIA_API_BASE", DEFAULT_API_BASE).rstrip("/")


def default_fingerprint() -> str:
    """Generate minimal, non-invasive device fingerprint."""
    node = uuid.getnode()
    return f"{platform.system()}-{platform.release()}-{node}"


@dataclass
class ActivateResponse:
    """Response from token activation."""
    entitlements: list[str]
    session_token: str
    product: Optional[str] = None
    niche: Optional[str] = None


class ApiError(RuntimeError):
    """API call failed."""
    pass


def activate_token(
    token: str,
    device_fingerprint: Optional[str] = None,
    timeout_s: float = 20.0
) -> ActivateResponse:
    """
    Exchange a Telegram token for a session token.
    
    Args:
        token: The activation token from Telegram bot
        device_fingerprint: Optional device fingerprint
        timeout_s: Request timeout in seconds
        
    Returns:
        ActivateResponse with session_token
        
    Raises:
        ApiError: If activation fails
    """
    url = f"{api_base()}/cli/activate-token"
    body: dict[str, Any] = {"token": token}
    
    if device_fingerprint:
        body["device_fingerprint"] = device_fingerprint
    
    with httpx.Client(timeout=timeout_s) as client:
        r = client.post(url, json=body, headers={"Content-Type": "application/json"})
        
        if r.status_code >= 400:
            # Try to get error message from response
            try:
                data = r.json()
                msg = data.get("error", f"HTTP {r.status_code}")
            except Exception:
                msg = f"HTTP {r.status_code}"
            raise ApiError(f"Activation failed: {msg}")
        
        data = r.json()
        
        if not data.get("ok"):
            raise ApiError(data.get("error", "Activation failed"))
        
        st = data.get("session_token")
        if not st:
            raise ApiError("Activation failed: missing session_token")
        
        return ActivateResponse(
            entitlements=list(data.get("entitlements") or []),
            session_token=st,
            product=data.get("product"),
            niche=data.get("niche"),
        )


def get_manifest(session_token: str, timeout_s: float = 20.0) -> dict[str, Any]:
    """
    Fetch the pack manifest for the authenticated user.
    
    Args:
        session_token: JWT session token
        timeout_s: Request timeout in seconds
        
    Returns:
        Manifest data with entitlements and packs
        
    Raises:
        ApiError: If request fails (UNAUTHORIZED for 401/403)
    """
    url = f"{api_base()}/cli/manifest"
    
    with httpx.Client(timeout=timeout_s) as client:
        r = client.get(url, headers={"Authorization": f"Bearer {session_token}"})
        
        if r.status_code in (401, 403):
            raise ApiError("UNAUTHORIZED")
        
        if r.status_code >= 400:
            raise ApiError(f"Manifest failed ({r.status_code})")
        
        return r.json()


# ============================================================
# DEVICE LINK API
# ============================================================

@dataclass
class LinkStartResponse:
    """Response from link start."""
    link_code: str
    expires_at: str
    url: str


@dataclass
class LinkStatusResponse:
    """Response from link status."""
    linked: bool
    device_id: Optional[str] = None
    claimed_at: Optional[str] = None
    device_fingerprint: Optional[str] = None
    link_code_last4: Optional[str] = None


def start_device_link(
    session_token: str,
    device_fingerprint: Optional[str] = None,
    cli_version: Optional[str] = None,
    os_name: Optional[str] = None,
    timeout_s: float = 20.0
) -> LinkStartResponse:
    """
    Start device link flow - get a link code.
    
    Args:
        session_token: JWT session token
        device_fingerprint: Optional device fingerprint
        cli_version: Optional CLI version
        os_name: Optional OS name
        timeout_s: Request timeout
        
    Returns:
        LinkStartResponse with link_code and expires_at
        
    Raises:
        ApiError: If request fails
    """
    url = f"{api_base()}/link/start"
    body: dict[str, Any] = {}
    
    if device_fingerprint:
        body["device_fingerprint"] = device_fingerprint
    if cli_version:
        body["cli_version"] = cli_version
    if os_name:
        body["os"] = os_name
    
    with httpx.Client(timeout=timeout_s) as client:
        r = client.post(
            url,
            json=body,
            headers={
                "Authorization": f"Bearer {session_token}",
                "Content-Type": "application/json"
            }
        )
        
        if r.status_code == 401:
            raise ApiError("UNAUTHORIZED")
        if r.status_code == 429:
            raise ApiError("RATE_LIMITED")
        if r.status_code >= 400:
            try:
                data = r.json()
                msg = data.get("error", f"HTTP {r.status_code}")
            except Exception:
                msg = f"HTTP {r.status_code}"
            raise ApiError(msg)
        
        data = r.json()
        
        if not data.get("ok"):
            raise ApiError(data.get("error", "Link start failed"))
        
        return LinkStartResponse(
            link_code=data["link_code"],
            expires_at=data["expires_at"],
            url=data["url"],
        )


def get_link_status(
    session_token: str,
    timeout_s: float = 20.0
) -> LinkStatusResponse:
    """
    Get device link status.
    
    Args:
        session_token: JWT session token
        timeout_s: Request timeout
        
    Returns:
        LinkStatusResponse with linked status
        
    Raises:
        ApiError: If request fails
    """
    url = f"{api_base()}/link/status"
    
    with httpx.Client(timeout=timeout_s) as client:
        r = client.get(
            url,
            headers={"Authorization": f"Bearer {session_token}"}
        )
        
        if r.status_code == 401:
            raise ApiError("UNAUTHORIZED")
        if r.status_code >= 400:
            try:
                data = r.json()
                msg = data.get("error", f"HTTP {r.status_code}")
            except Exception:
                msg = f"HTTP {r.status_code}"
            raise ApiError(msg)
        
        data = r.json()
        
        if not data.get("ok"):
            raise ApiError(data.get("error", "Link status failed"))
        
        return LinkStatusResponse(
            linked=data.get("linked", False),
            device_id=data.get("device_id"),
            claimed_at=data.get("claimed_at"),
            device_fingerprint=data.get("device_fingerprint"),
            link_code_last4=data.get("link_code_last4"),
        )


# ============================================================
# WHATSAPP GOLD API
# ============================================================

@dataclass
class WhatsAppConfig:
    """WhatsApp Gold configuration from server."""
    profile_id: str
    config_version: str
    applied_at: str
    config: dict[str, Any]
    instructions: list[str]


def get_whatsapp_config(
    session_token: str,
    device_id: str,
    profile_id: str,
    timeout_s: float = 30.0
) -> WhatsAppConfig:
    """
    Get WhatsApp Gold config (calls /apply to generate machine-ready config).
    
    Args:
        session_token: JWT session token
        device_id: Device link ID
        profile_id: WhatsApp profile ID
        timeout_s: Request timeout
        
    Returns:
        WhatsAppConfig with full machine config
        
    Raises:
        ApiError: If request fails
    """
    url = f"{api_base()}/whatsapp/apply"
    
    with httpx.Client(timeout=timeout_s) as client:
        r = client.post(
            url,
            json={"device_id": device_id, "profile_id": profile_id},
            headers={
                "Authorization": f"Bearer {session_token}",
                "Content-Type": "application/json"
            }
        )
        
        if r.status_code == 401:
            raise ApiError("UNAUTHORIZED")
        if r.status_code == 404:
            raise ApiError("NOT_FOUND")
        if r.status_code >= 400:
            try:
                data = r.json()
                msg = data.get("error", f"HTTP {r.status_code}")
            except Exception:
                msg = f"HTTP {r.status_code}"
            raise ApiError(msg)
        
        data = r.json()
        
        if not data.get("ok"):
            raise ApiError(data.get("error", "Config fetch failed"))
        
        return WhatsAppConfig(
            profile_id=profile_id,
            config_version=data["config_version"],
            applied_at=data["applied_at"],
            config=data["config"],
            instructions=data.get("instructions", []),
        )


def get_whatsapp_profile(
    session_token: str,
    device_id: str,
    timeout_s: float = 20.0
) -> Optional[dict[str, Any]]:
    """
    Get WhatsApp profile for device.
    
    Args:
        session_token: JWT session token
        device_id: Device link ID
        timeout_s: Request timeout
        
    Returns:
        Profile dict or None if not found
        
    Raises:
        ApiError: If request fails
    """
    url = f"{api_base()}/whatsapp/profile?device_id={device_id}"
    
    with httpx.Client(timeout=timeout_s) as client:
        r = client.get(
            url,
            headers={"Authorization": f"Bearer {session_token}"}
        )
        
        if r.status_code == 401:
            raise ApiError("UNAUTHORIZED")
        if r.status_code >= 400:
            try:
                data = r.json()
                msg = data.get("error", f"HTTP {r.status_code}")
            except Exception:
                msg = f"HTTP {r.status_code}"
            raise ApiError(msg)
        
        data = r.json()
        
        if not data.get("ok"):
            raise ApiError(data.get("error", "Profile fetch failed"))
        
        return data.get("profile")
