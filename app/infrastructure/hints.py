from pydantic.main import BaseModel


class ErrorType(BaseModel):
    code: int
    message: str


class ErrorResponseType(BaseModel):
    error: ErrorType
