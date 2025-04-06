class ApplicationError(Exception):
    message: str = "Unknown error occurred"
    code = 2
