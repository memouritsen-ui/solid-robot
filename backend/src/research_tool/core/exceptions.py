"""Exception hierarchy for Research Tool."""


class ResearchToolError(Exception):
    """Base exception for all Research Tool errors."""

    pass


class ConfigurationError(ResearchToolError):
    """Configuration or setup error."""

    pass


class NetworkError(ResearchToolError):
    """Network-related error."""

    pass


class RateLimitError(NetworkError):
    """Rate limit exceeded."""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        """Initialize with retry information.

        Args:
            message: Error description.
            retry_after: Seconds to wait before retrying.
        """
        super().__init__(message)
        self.retry_after = retry_after


class AccessDeniedError(NetworkError):
    """Access denied (403, login required)."""

    pass


class TimeoutError(NetworkError):
    """Request timeout."""

    pass


class ParseError(ResearchToolError):
    """Failed to parse response."""

    pass


class StorageError(ResearchToolError):
    """Storage operation failed."""

    pass


class ModelError(ResearchToolError):
    """LLM-related error."""

    pass


class ModelUnavailableError(ModelError):
    """Model not available."""

    pass


class ModelOverloadedError(ModelError):
    """Model overloaded."""

    pass


class ResearchError(ResearchToolError):
    """Research process error."""

    pass


class SaturationNotReached(ResearchError):
    """Research stopped before saturation."""

    pass


class SourceExhausted(ResearchError):
    """All sources exhausted."""

    pass
