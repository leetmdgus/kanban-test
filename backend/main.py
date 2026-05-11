from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base
from database import SessionLocal
from database import engine
from models import Card
from schemas import CardResponse
from schemas import CreateCardRequest
from schemas import UpdateCardRequest

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kanban API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.get("/cards", response_model=list[CardResponse])
def get_cards(db: Session = Depends(get_db)):
    return db.query(Card).order_by(Card.status, Card.order).all()


@app.post("/cards", response_model=CardResponse)
def create_card(payload: CreateCardRequest, db: Session = Depends(get_db)):
    count = db.query(Card).filter(Card.status == payload.status).count()

    card = Card(
        title=payload.title,
        description=payload.description,
        status=payload.status,
        order=count,
    )

    db.add(card)
    db.commit()
    db.refresh(card)

    return card

@app.patch("/cards/{card_id}", response_model=CardResponse)
def update_card(
    card_id: str,
    payload: UpdateCardRequest,
    db: Session = Depends(get_db),
):
    card = db.query(Card).filter(Card.id == card_id).first()

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    update_data = payload.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(card, key, value)

    db.commit()
    db.refresh(card)

    return card


@app.delete("/cards/{card_id}")
def delete_card(card_id: str, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    db.delete(card)
    db.commit()

    return {"message": "deleted"}


@app.post("/cards/{card_id}/move", response_model=CardResponse)
def move_card(
    card_id: str,
    payload: UpdateCardRequest,
    db: Session = Depends(get_db),
):
    card = db.query(Card).filter(Card.id == card_id).first()

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if payload.status is not None:
        card.status = payload.status

    if payload.order is not None:
        card.order = payload.order

    db.commit()
    db.refresh(card)

    return card