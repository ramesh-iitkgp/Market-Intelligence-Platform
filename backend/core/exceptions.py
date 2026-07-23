"""Domain-specific exceptions for the backend."""


class MarketIntelligenceError(Exception):
    """Base exception for expected platform errors."""


class ConfigurationError(MarketIntelligenceError):
    """Raised when required application configuration is invalid or absent."""


class ExternalServiceError(MarketIntelligenceError):
    """Raised when an external dependency cannot satisfy a request."""


class GeminiServiceError(ExternalServiceError):
    """Raised when the Gemini API request or response handling fails."""


class GeminiResponseError(GeminiServiceError):
    """Raised when Gemini returns an unusable or malformed response."""


class RepositoryError(MarketIntelligenceError):
    """Raised when a persistence operation fails."""
