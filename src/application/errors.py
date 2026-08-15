class ApplicationError(Exception):
    pass


class NotFoundError(ApplicationError):
    pass


class ConflictError(ApplicationError):
    pass


class InvalidStateError(ApplicationError):
    pass


class BatchValidationError(ApplicationError):
    pass
