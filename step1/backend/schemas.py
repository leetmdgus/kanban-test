from pydantic import BaseModel


class CardBase(BaseModel):
    title: str
    description: str = ""
    status: str = "todo"


class CreateCardRequest(CardBase):
    pass


class UpdateCardRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    order: int | None = None


class CardResponse(CardBase):
    id: str
    order: int

    model_config = {
        "from_attributes": True,
    }