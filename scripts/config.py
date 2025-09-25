"""Central configuration for Free Fire logging scripts."""
from __future__ import annotations

DEFAULT_UID = "2805365702"
API_BASE_URL = "https://7ama-info.vercel.app"
API_INFO_ENDPOINT = "/info"


def build_api_url(uid: str) -> str:
    """Return the fully qualified API URL for the given UID."""
    return f"{API_BASE_URL}{API_INFO_ENDPOINT}?uid={uid}"
