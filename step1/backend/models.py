import uuid

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from database import Base


class Card(Base):
    __tablename__ = "cards"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(100), nullable=False)
    description = Column(String, nullable=False, default="")
    status = Column(String(30), nullable=False, default="todo")
    order = Column(Integer, nullable=False, default=0)