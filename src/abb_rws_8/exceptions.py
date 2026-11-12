class RWS8Exception(Exception):
    """The base exception for all RWS8 exceptions"""


class RWSConnectionError(RWS8Exception):
    """Raised when a connection to the controller cannot be established."""


class RWSTimeoutError(RWS8Exception):
    """Raised when a request exceeds a network operation timeout."""


class RWSHTTPError(RWS8Exception):
    """Raised when the controller returns an unsuccessful HTTP status."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(message)
