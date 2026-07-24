"""Gemini provider implementation for the LLM interface."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import logging
from typing import Any

from google.api_core import exceptions as google_exceptions
from google import genai
from google.genai import types

from backend.config import Settings, get_settings
from backend.core.exceptions import GeminiResponseError, GeminiServiceError
from backend.services.llm.base import JsonValue, LLMProvider
from backend.services.llm.tokenizer import GeminiTokenizer, Tokenizer


class GeminiProvider(LLMProvider):
    """Encapsulate Gemini generation behind a focused, testable interface."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: genai.Client | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the service with injected dependencies when supplied."""
        self._settings = settings or get_settings()
        self._client = client or genai.Client(api_key=self._settings.gemini_api_key)
        self._model = self._client.models.get(f"models/{self._settings.gemini_model}")
        self._logger = logger or logging.getLogger(__name__)
        self._tokenizer = GeminiTokenizer(self._model)

    @property
    def tokenizer(self) -> Tokenizer:
        """Return the provider-specific tokenizer."""
        return self._tokenizer

    def generate_text(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> str:
        """Generate plain text for a prompt using the configured Gemini model."""
        config = self._build_config(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        response = self._request(prompt, config)
        text = getattr(response, "text", None)
        if not isinstance(text, str) or not text.strip():
            raise GeminiResponseError("Gemini returned an empty text response.")
        return text.strip()

    def generate_json(
        self,
        prompt: str,
        *,
        schema: Mapping[str, Any] | None = None,
        system_instruction: str | None = None,
        temperature: float | None = 0.0,
    ) -> JsonValue:
        """Generate and parse a JSON response, optionally constrained by schema."""
        config_values: dict[str, Any] = {
            "response_mime_type": "application/json",
            "temperature": temperature,
        }
        if system_instruction:
            config_values["system_instruction"] = system_instruction
        if schema:
            config_values["response_json_schema"] = dict(schema)

        response = self._request(prompt, config_values)
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, (dict, list)):
            return parsed

        text = getattr(response, "text", None)
        if not isinstance(text, str):
            raise GeminiResponseError("Gemini returned no JSON content.")
        try:
            return json.loads(text)
        except json.JSONDecodeError as error:
            raise GeminiResponseError("Gemini returned invalid JSON content.") from error

    def summarize(self, content: str, *, max_words: int = 150) -> str:
        """Produce a concise, factual market-intelligence summary."""
        if max_words < 1:
            raise ValueError("max_words must be at least 1.")
        return self.generate_text(
            f"Summarize the following market intelligence in at most {max_words} words. "
            "Preserve material facts, figures, companies, and uncertainty.\n\n"
            f"{content}",
            system_instruction="You write concise, factual market research summaries.",
            temperature=0.2,
        )

    def classify_event(
        self, content: str, categories: Sequence[str]
    ) -> JsonObject:
        """Classify a market event into one supplied category with rationale."""
        if not categories:
            raise ValueError("categories must contain at least one value.")
        category_list = list(categories)
        schema: JsonObject = {
            "type": "object",
            "required": ["category", "confidence", "rationale"],
            "properties": {
                "category": {"type": "string", "enum": category_list},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "rationale": {"type": "string"},
            },
        }
        result = self.generate_json(
            f"Classify this market event into exactly one provided category.\n"
            f"Categories: {', '.join(category_list)}\n\nEvent:\n{content}",
            schema=schema,
            system_instruction="You are a precise market-event classification analyst.",
        )
        if not isinstance(result, dict):
            raise GeminiResponseError("Event classification must be a JSON object.")
        return result

    def extract_entities(self, content: str) -> list[JsonObject]:
        """Extract normalized organizations, instruments, places, and people."""
        schema: JsonObject = {
            "type": "object",
            "required": ["entities"],
            "properties": {
                "entities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "type"],
                        "properties": {
                            "name": {"type": "string"},
                            "type": {
                                "type": "string",
                                "enum": [
                                    "organization",
                                    "instrument",
                                    "country",
                                    "person",
                                    "commodity",
                                    "other",
                                ],
                            },
                            "ticker": {"type": ["string", "null"]},
                        },
                    },
                }
            },
        }
        result = self.generate_json(
            f"Extract market-relevant named entities from this content.\n\n{content}",
            schema=schema,
            system_instruction="Extract only entities directly supported by the supplied text.",
        )
        if not isinstance(result, dict) or not isinstance(result.get("entities"), list):
            raise GeminiResponseError("Entity extraction response is missing an entities list.")
        entities = result["entities"]
        if not all(isinstance(entity, dict) for entity in entities):
            raise GeminiResponseError("Entity extraction response contains an invalid entity.")
        return entities

    def _request(self, prompt: str, config: dict[str, Any]) -> Any:
        """Execute a Gemini request and consistently translate provider failures."""
        if not prompt.strip():
            raise ValueError("prompt must not be empty.")
        
        try:
            return self._model.generate_content(
                contents=prompt,
                config=config,
                request_options={"timeout": self._settings.gemini_timeout_seconds},
            )
        except (google_exceptions.GoogleAPICallError, google_exceptions.RetryError) as error:
            self._logger.exception("Gemini API call failed after retries")
            raise GeminiServiceError("Gemini API call failed.") from error
        except Exception as error:
            self._logger.exception("Gemini generation request failed")
            raise GeminiServiceError("Gemini generation request failed.") from error

    @staticmethod
    def _build_config(
        *,
        system_instruction: str | None,
        temperature: float | None,
        max_output_tokens: int | None,
    ) -> dict[str, Any]:
        """Construct a GenerationConfig without passing null overrides."""
        values: dict[str, Any] = {}
        if system_instruction:
            values["system_instruction"] = system_instruction
        if temperature is not None:
            values["temperature"] = temperature
        if max_output_tokens is not None:
            values["max_output_tokens"] = max_output_tokens
        return values
