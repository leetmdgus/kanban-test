from datetime import date
from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from pydantic import Field

Priority = Literal["low", "medium", "high"]


class BusinessCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""


class BusinessUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None


class BusinessResponse(BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BoardCreate(BaseModel):
    business_id: str
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""


class BoardUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None


class BoardResponse(BaseModel):
    id: str
    business_id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ColumnCreate(BaseModel):
    board_id: str
    title: str = Field(..., min_length=1, max_length=100)
    position: int = 0


class ColumnUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    position: int | None = None


class ColumnResponse(BaseModel):
    id: str
    board_id: str
    title: str
    position: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CardCreate(BaseModel):
    column_id: str
    title: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    priority: Priority = "medium"
    due_date: date | None = None


class CardUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    priority: Priority | None = None
    due_date: date | None = None
    position: int | None = None


class CardMove(BaseModel):
    column_id: str
    position: int


class CardResponse(BaseModel):
    id: str
    column_id: str
    title: str
    description: str
    priority: str
    due_date: date | None
    position: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BoardDetailResponse(BoardResponse):
    columns: list[ColumnResponse]