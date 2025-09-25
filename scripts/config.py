"""Central configuration for Free Fire logging and automation scripts."""
from __future__ import annotations

DEFAULT_UID = "2805365702"
API_BASE_URL = "https://7ama-info.vercel.app"
API_INFO_ENDPOINT = "/info"

LIKES_API_BASE_URL = "https://likes.api.freefireofficial.com/api/sg"
DEFAULT_LIKES_UID = "923824741"
DEFAULT_LIKES_API_KEY = "astute2k3"


def build_api_url(uid: str) -> str:
    """Return the fully qualified profile info API URL for the given UID."""
    return f"{API_BASE_URL}{API_INFO_ENDPOINT}?uid={uid}"


def build_likes_api_url(uid: str, api_key: str) -> str:
    """Return the fully qualified likes API URL for the given UID and API key."""
    return f"{LIKES_API_BASE_URL}/{uid}?key={api_key}"
