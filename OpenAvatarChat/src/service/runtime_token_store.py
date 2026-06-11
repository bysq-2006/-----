import time
from typing import Dict


_token = ""
_expires_at = 0.0


def save_token(token: str, ttl_seconds: int = 60) -> None:
    global _token, _expires_at
    _token = token.strip()
    _expires_at = time.time() + max(1, ttl_seconds)


def get_auth_headers(header_name: str = "Authorization", header_template: str = "Bearer {token}") -> Dict[str, str]:
    if not _token or time.time() >= _expires_at:
        return {}
    return {header_name: header_template.format(token=_token)}
