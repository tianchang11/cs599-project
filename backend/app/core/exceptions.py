class AppError(Exception):
    def __init__(self, message: str, code: str, status_code: int):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, resource: str, id: str):
        super().__init__(f"{resource} not found: {id}", "NOT_FOUND", 404)


class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", 422)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, "UNAUTHORIZED", 401)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, "FORBIDDEN", 403)


class ServiceUnavailableError(AppError):
    def __init__(self, message: str = "Service unavailable"):
        super().__init__(message, "SERVICE_UNAVAILABLE", 503)


class RateLimitError(AppError):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, "RATE_LIMIT_EXCEEDED", 429)


class TaskError(AppError):
    def __init__(self, message: str):
        super().__init__(message, "TASK_ERROR", 500)
