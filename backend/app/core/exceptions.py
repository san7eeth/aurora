"""Application errors raised by services and translated by the API layer."""


class AuroraError(Exception):
    """Base error for Aurora. `status_code` is the HTTP status the API should return."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ConfigurationError(AuroraError):
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class DatabaseError(AuroraError):
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class OllamaUnavailableError(AuroraError):
    def __init__(self, message: str = "Ollama is not reachable"):
        super().__init__(message, status_code=503)


class NotFoundError(AuroraError):
    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class ValidationError(AuroraError):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)
