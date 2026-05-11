from enum import Enum
from typing import Dict, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Kanban API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Status(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class Card(BaseModel):
    id: str
    title: str
    description: str = ""
    status: Status
    order: int = 0


class CreateCardRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    status: Status = Status.todo


class UpdateCardRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    status: Status | None = None
    order: int | None = None


cards: Dict[str, Card] = {}


def seed_data() -> None:
    initial_cards = [
        Card(id=str(uuid4()), title="요구사항 정리", description="Kanban 기능 범위 정의", status=Status.todo, order=0),
        Card(id=str(uuid4()), title="API 설계", description="CRUD 및 이동 API 작성", status=Status.in_progress, order=0),
        Card(id=str(uuid4()), title="프로젝트 생성", description="Vite/FastAPI 초기 세팅", status=Status.done, order=0),
    ]
    for card in initial_cards:
        cards[card.id] = card


seed_data()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/cards", response_model=List[Card])
def list_cards() -> List[Card]:
    return sorted(cards.values(), key=lambda card: (card.status.value, card.order))


@app.post("/cards", response_model=Card, status_code=201)
def create_card(payload: CreateCardRequest) -> Card:
    status_cards = [card for card in cards.values() if card.status == payload.status]
    next_order = len(status_cards)

    card = Card(
        id=str(uuid4()),
        title=payload.title,
        description=payload.description,
        status=payload.status,
        order=next_order,
    )
    cards[card.id] = card
    return card


@app.patch("/cards/{card_id}", response_model=Card)
def update_card(card_id: str, payload: UpdateCardRequest) -> Card:
    card = cards.get(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    update_data = payload.model_dump(exclude_unset=True)
    updated = card.model_copy(update=update_data)
    cards[card_id] = updated
    return updated


@app.delete("/cards/{card_id}", status_code=204)
def delete_card(card_id: str) -> None:
    if card_id not in cards:
        raise HTTPException(status_code=404, detail="Card not found")
    del cards[card_id]


@app.post("/cards/{card_id}/move", response_model=Card)
def move_card(card_id: str, payload: UpdateCardRequest) -> Card:
    card = cards.get(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if payload.status is None:
        raise HTTPException(status_code=400, detail="status is required")

    same_column_cards = [c for c in cards.values() if c.status == payload.status and c.id != card_id]
    requested_order = payload.order if payload.order is not None else len(same_column_cards)
    safe_order = max(0, min(requested_order, len(same_column_cards)))

    moved = card.model_copy(update={"status": payload.status, "order": safe_order})
    cards[card_id] = moved

    reordered = same_column_cards[:]
    reordered.insert(safe_order, moved)
    for index, item in enumerate(reordered):
        cards[item.id] = item.model_copy(update={"order": index})

    return cards[card_id]