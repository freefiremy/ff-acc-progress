"""Central configuration for Free Fire logging and automation scripts."""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence

DEFAULT_UIDS: List[str] = ["2805365702", "667352678"]
DEFAULT_UID = DEFAULT_UIDS[0]
API_BASE_URL = "https://7ama-info.vercel.app"
API_INFO_ENDPOINT = "/info"

LIKES_API_BASE_URL = "https://likes.api.freefireofficial.com/api/sg"
DEFAULT_LIKES_UIDS: List[str] = DEFAULT_UIDS.copy()
DEFAULT_LIKES_UID = DEFAULT_LIKES_UIDS[0]
DEFAULT_LIKES_API_KEY = "astute2k3"


def build_api_url(uid: str) -> str:
    """Return the fully qualified profile info API URL for the given UID."""
    return f"{API_BASE_URL}{API_INFO_ENDPOINT}?uid={uid}"


def build_likes_api_url(uid: str, api_key: str) -> str:
    """Return the fully qualified likes API URL for the given UID and API key."""
    return f"{LIKES_API_BASE_URL}/{uid}?key={api_key}"


def parse_uid_list(
    raw: Optional[Iterable[str] | str],
    fallback: Optional[Sequence[str]] = None,
) -> List[str]:
    """Normalise a raw UID collection (iterable or delimited string) into a list."""
    if raw is None:
        base: List[str] = []
    elif isinstance(raw, str):
        raw = raw.replace(";", ",")
        parts = [part.strip() for part in raw.split(",")]
        base = [part for part in parts if part]
    else:
        base = [str(item).strip() for item in raw if str(item).strip()]

    if base:
        return base
    if fallback is None:
        return []
    return [str(item).strip() for item in fallback if str(item).strip()]


def serialise_uid_list(uids: Sequence[str]) -> str:
    """Join a UID list into a comma-separated string suitable for env vars."""
    return ",".join(uid for uid in uids if uid)


def resolve_primary_uid(
    single_value: Optional[str],
    list_value: Optional[Iterable[str] | str],
    fallback: Optional[Sequence[str]] = None,
) -> str:
    """Return the first configured UID from single/list inputs, falling back as needed."""
    if single_value:
        primary = single_value.strip()
        if primary:
            return primary

    uids = parse_uid_list(list_value, fallback)
    if not uids:
        raise ValueError("No UID configured")
    return uids[0]


def default_env_vars() -> Dict[str, str]:
    """Return mapping of environment variable names to their default values."""
    values = {
        "FREEFIRE_UID": DEFAULT_UID,
        "FREEFIRE_UIDS": serialise_uid_list(DEFAULT_UIDS),
        "FREEFIRE_LIKES_UID": DEFAULT_LIKES_UID,
        "FREEFIRE_LIKES_UIDS": serialise_uid_list(DEFAULT_LIKES_UIDS),
        "FREEFIRE_LIKES_KEY": DEFAULT_LIKES_API_KEY,
    }
    return {key: value for key, value in values.items() if value}

