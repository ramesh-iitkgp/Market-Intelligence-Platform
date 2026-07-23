"""Executable Gemini API connectivity check for local development."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.settings import get_settings
from backend.core.exceptions import ConfigurationError, GeminiServiceError
from backend.core.logger import configure_logging, get_logger
from backend.services.gemini_service import GeminiService


def main() -> int:
    """Generate a small response to confirm the configured Gemini connection."""
    try:
        settings = get_settings()
        configure_logging(settings)
        logger = get_logger(__name__)
        logger.info("Testing Gemini connection with model '%s'.", settings.gemini_model)

        response = GeminiService(settings=settings, logger=logger).generate_text(
            "In one sentence, explain the value of market intelligence."
        )
    except ConfigurationError as error:
        print(f"Gemini configuration failed: {error}", file=sys.stderr)
        return 1
    except GeminiServiceError as error:
        print(f"Gemini API connection failed: {error}", file=sys.stderr)
        return 1

    print("Gemini connection verified successfully.")
    print(f"Model: {settings.gemini_model}")
    print(f"Response: {response}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
