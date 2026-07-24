"""Abstract and concrete implementations for LLM tokenizers."""

from __future__ import annotations

from abc import ABC, abstractmethod

import tiktoken
from google.generativeai import GenerativeModel


class Tokenizer(ABC):
    """Abstract base class for a provider-specific tokenizer."""

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Counts the number of tokens in a given text string."""
        ...


class GeminiTokenizer(Tokenizer):
    """Tokenizer for Google Gemini models."""

    def __init__(self, model: GenerativeModel):
        self._model = model

    def count_tokens(self, text: str) -> int:
        """Counts tokens using the Gemini model's specific counter."""
        return self._model.count_tokens(text).total_tokens


class TiktokenTokenizer(Tokenizer):
    """Tokenizer for OpenAI models using the tiktoken library."""

    def __init__(self, encoding_name: str = "cl100k_base"):
        self._encoding = tiktoken.get_encoding(encoding_name)

    def count_tokens(self, text: str) -> int:
        """Counts tokens using the specified tiktoken encoding."""
        return len(self._encoding.encode(text))