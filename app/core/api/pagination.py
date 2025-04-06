from pydantic.main import BaseModel


class PaginationSchema(BaseModel):
    limit: int = 20
    offset: int = 0
