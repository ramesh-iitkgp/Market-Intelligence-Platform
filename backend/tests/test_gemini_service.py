"""Unit tests for the Gemini service without external API calls."""

from __future__ import annotations

from dataclasses import replace
import logging
from pathlib import Path
from typing import Any

import pytest

from google import genai
from backend.config.settings import Settings
from backend.core.exceptions import GeminiResponseError, GeminiServiceError
from backend.services.llm.gemini import GeminiProvider


class FakeModels:
    """Record generation requests and return a configured fake response."""

    def __init__(self, response: Any = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def generate_content(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


class FakeClient:
    """Minimal substitute for the GenAI client."""

    def __init__(self, response: Any = None, error: Exception | None = None) -> None:
        self.models = FakeModels(response=response, error=error)


class FakeResponse:
    """Simple response fixture with SDK-compatible attributes."""

    def __init__(self, text: str | None = None, parsed: Any = None) -> None:
        self.text = text
        self.parsed = parsed


@pytest.fixture
def settings() -> Settings:
    """Create non-secret settings suitable for unit tests."""
    return Settings(
        environment="test",
        debug=False,
        log_level="INFO",
        log_directory=Path("/tmp/market-intelligence-tests"),
        gemini_api_key="test-key",
        gemini_model="test-model",
        gemini_timeout_seconds=10.0,
    )


def build_service(response: FakeResponse, settings: Settings) -> GeminiProvider:
    """Create a service backed by a deterministic fake client."""
    return GeminiProvider(
        settings=replace(settings),
        client=FakeClient(response=response),
        logger=logging.getLogger("test.gemini"),
    )


def test_generate_text_returns_stripped_response(settings: Settings) -> None:
    """Text generation should normalize surrounding whitespace."""
    service = build_service(FakeResponse(text="  useful result  "), settings)

    assert service.generate_text("test prompt") == "useful result"


def test_generate_json_uses_parsed_payload(settings: Settings) -> None:
    """Structured generation should prefer the SDK-parsed response."""
    service = build_service(FakeResponse(parsed={"signal": "positive"}), settings)

    assert service.generate_json("test prompt") == {"signal": "positive"}


def test_extract_entities_returns_entities(settings: Settings) -> None:
    """Entity extraction should unpack the service-specific payload."""
    service = build_service(
        FakeResponse(parsed={"entities": [{"name": "Acme", "type": "organization"}]}),
        settings,
    )

    assert service.extract_entities("Acme announced earnings.") == [
        {"name": "Acme", "type": "organization"}
    ]


def test_invalid_json_response_raises_domain_error(settings: Settings) -> None:
    """Malformed structured output should be translated to a domain error."""
    service = build_service(FakeResponse(text="not-json"), settings)

    with pytest.raises(GeminiResponseError):
        service.generate_json("test prompt")


def test_provider_failure_raises_domain_error(settings: Settings) -> None:
    """Provider exceptions should not leak through the service boundary."""
    service = GeminiProvider(
        settings=settings,
        client=FakeClient(error=genai.APIError("network error")),
        logger=logging.getLogger("test.gemini"),
    )

    with pytest.raises(GeminiServiceError):
        service.generate_text("test prompt")
