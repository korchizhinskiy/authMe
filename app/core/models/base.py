from app.infrastructure.database import Base


class CoreBase(Base):
    __abstract__: bool = True
