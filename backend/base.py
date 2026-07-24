"""Base classes and interfaces for LLM provider implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

JsonObject = dict[str, Any]
JsonValue = JsonObject | list[Any]


class LLMProvider(ABC):
    """Abstract base class for all LLM provider implementations."""

    @property
    @abstractmethod
    def tokenizer(self) -> Tokenizer:
        """The provider-specific tokenizer instance."""
        ...

    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        *,
        schema: Mapping[str, Any] | None = None,
        temperature: float | None = 0.0,
    ) -> JsonValue:
        """
        Generate and parse a JSON response, optionally constrained by schema.
        """
        ...