"""Centralized, environment-backed application settings."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv

from backend.core.exceptions import ConfigurationError


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"


def _as_bool(value: str) -> bool:
    """Parse a conventional environment boolean value."""
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigurationError(f"Expected a boolean value, received {value!r}.")


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable runtime settings loaded from the environment."""

    environment: str
    debug: bool
    log_level: str
    log_directory: Path
    gemini_api_key: str
    gemini_model: str
    gemini_timeout_seconds: float

    @classmethod
    def from_environment(cls, env_file: Path | None = DEFAULT_ENV_FILE) -> "Settings":
        """Build settings from a dotenv file and the process environment.

        Process-level environment variables take precedence over the dotenv file,
        which supports secure deployment-time configuration overrides.
        """
        if env_file is not None:
            load_dotenv(env_file, override=False)

        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise ConfigurationError(
                "GEMINI_API_KEY is required. Add it to .env or the runtime environment."
            )

        timeout_raw = os.getenv("GEMINI_TIMEOUT_SECONDS", "30")
        try:
            timeout = float(timeout_raw)
        except ValueError as error:
            raise ConfigurationError(
                "GEMINI_TIMEOUT_SECONDS must be a positive number."
            ) from error
        if timeout <= 0:
            raise ConfigurationError("GEMINI_TIMEOUT_SECONDS must be greater than zero.")

        log_directory = Path(os.getenv("LOG_DIRECTORY", PROJECT_ROOT / "logs"))
        return cls(
            environment=os.getenv("ENVIRONMENT", "development").strip(),
            debug=_as_bool(os.getenv("DEBUG", "false")),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper().strip(),
            log_directory=log_directory,
            gemini_api_key=api_key,
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip(),
            gemini_timeout_seconds=timeout,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings.from_environment()
