"""Structured application logging configuration."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from backend.config.settings import Settings, get_settings


LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def configure_logging(settings: Settings | None = None) -> None:
    """Configure timestamped console and rotating file log handlers once."""
    current_settings = settings or get_settings()
    log_directory: Path = current_settings.log_directory
    log_directory.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(current_settings.log_level)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    for handler in root_logger.handlers:
        if getattr(handler, "_market_intelligence_handler", False):
            return

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler._market_intelligence_handler = True  # type: ignore[attr-defined]

    file_handler = RotatingFileHandler(
        log_directory / "market_intelligence.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler._market_intelligence_handler = True  # type: ignore[attr-defined]

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger after configuring the application handlers."""
    configure_logging()
    return logging.getLogger(name)
