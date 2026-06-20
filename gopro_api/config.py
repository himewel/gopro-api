"""Environment-backed settings loaded from the environment and ``.env``."""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from the process environment and optional ``.env`` file.

    Values are read at instantiation; use :func:`get_settings` for the token used
    by API clients and the CLI.

    Attributes:
        gp_access_token: GoPro cloud cookie value. Environment variable:
            ``GP_ACCESS_TOKEN``.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gp_access_token: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton.

    The result is memoized. Call ``get_settings.cache_clear()`` before constructing
    a new ``Settings`` instance when tests mutate the environment.

    Returns:
        Parsed :class:`Settings` for the current process.
    """
    return Settings()


def get_token_info() -> tuple[bool, str | None]:
    """Report whether ``GP_ACCESS_TOKEN`` is available and where it came from.

    Returns:
        A pair ``(configured, source)`` where ``source`` is ``"environment"``,
        ``".env"``, or ``None`` when not configured.
    """
    token = get_settings().gp_access_token
    if not token:
        return False, None
    if os.environ.get("GP_ACCESS_TOKEN"):
        return True, "environment"
    return True, ".env"


__all__ = ["Settings", "get_settings", "get_token_info"]
