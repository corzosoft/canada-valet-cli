"""Custom exceptions for canada-valet-cli."""


class ValetApiError(RuntimeError):
    """Base exception for Valet API and CLI failures."""


class ValetHttpError(ValetApiError):
    """Raised when the API returns an unsuccessful HTTP response."""


class ValetResponseError(ValetApiError):
    """Raised when an API response has an unexpected shape."""


class ValetValidationError(ValetApiError):
    """Raised when validation cannot complete."""


class ValetExportError(ValetApiError):
    """Raised when exporting observations fails."""


class ValetCacheError(ValetApiError):
    """Raised when local cache operations fail."""
