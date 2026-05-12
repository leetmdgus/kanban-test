from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.kanban.models import Business, Board, BoardColumn, Card
from app.kanban.schemas import (
    BusinessCreate,
    BusinessUpdate,
    BusinessResponse,
    BoardCreate,
    BoardUpdate,
    BoardResponse,
    BoardDetailResponse,
    ColumnCreate,
    ColumnUpdate,
    ColumnResponse,
    CardCreate,
    CardUpdate,
    CardMove,
    CardResponse,
)

router = APIRouter(tags=["Kanban"])


# Businesses
@router.get("/businesses", response_model=list[BusinessResponse])
def list_businesses(db: Session = Depends(get_db)):
    return db.query(Business).order_by(Business.created_at.desc()).all()


@router.post("/businesses", response_model=BusinessResponse, status_code=201)
def create_business(payload: BusinessCreate, db: Session = Depends(get_db)):
    business = Business(name=payload.name, description=payload.description)
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


@router.patch("/businesses/{business_id}", response_model=BusinessResponse)
def update_business(
    business_id: str,
    payload: BusinessUpdate,
    db: Session = Depends(get_db),
):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(business, key, value)

    db.commit()
    db.refresh(business)
    return business


@router.delete("/businesses/{business_id}")
def delete_business(business_id: str, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    db.delete(business)
    db.commit()
    return {"message": "deleted"}


# Boards
@router.get("/boards", response_model=list[BoardResponse])
def list_boards(db: Session = Depends(get_db)):
    return db.query(Board).order_by(Board.created_at.desc()).all()


@router.get("/boards/{board_id}", response_model=BoardDetailResponse)
def get_board(board_id: str, db: Session = Depends(get_db)):
    board = (
        db.query(Board)
        .options(selectinload(Board.columns))
        .filter(Board.id == board_id)
        .first()
    )

    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    return board


@router.post("/boards", response_model=BoardResponse, status_code=201)
def create_board(payload: BoardCreate, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == payload.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    board = Board(
        business_id=payload.business_id,
        name=payload.name,
        description=payload.description,
    )

    db.add(board)
    db.commit()
    db.refresh(board)
    return board


@router.patch("/boards/{board_id}", response_model=BoardResponse)
def update_board(board_id: str, payload: BoardUpdate, db: Session = Depends(get_db)):
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(board, key, value)

    db.commit()
    db.refresh(board)
    return board


@router.delete("/boards/{board_id}")
def delete_board(board_id: str, db: Session = Depends(get_db)):
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    db.delete(board)
    db.commit()
    return {"message": "deleted"}


# Columns
@router.get("/boards/{board_id}/columns", response_model=list[ColumnResponse])
def list_columns(board_id: str, db: Session = Depends(get_db)):
    return (
        db.query(BoardColumn)
        .filter(BoardColumn.board_id == board_id)
        .order_by(BoardColumn.position)
        .all()
    )


@router.post("/columns", response_model=ColumnResponse, status_code=201)
def create_column(payload: ColumnCreate, db: Session = Depends(get_db)):
    board = db.query(Board).filter(Board.id == payload.board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    column = BoardColumn(
        board_id=payload.board_id,
        title=payload.title,
        position=payload.position,
    )

    db.add(column)
    db.commit()
    db.refresh(column)
    return column


@router.patch("/columns/{column_id}", response_model=ColumnResponse)
def update_column(
    column_id: str,
    payload: ColumnUpdate,
    db: Session = Depends(get_db),
):
    column = db.query(BoardColumn).filter(BoardColumn.id == column_id).first()
    if not column:
        raise HTTPException(status_code=404, detail="Column not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(column, key, value)

    db.commit()
    db.refresh(column)
    return column


@router.delete("/columns/{column_id}")
def delete_column(column_id: str, db: Session = Depends(get_db)):
    column = db.query(BoardColumn).filter(BoardColumn.id == column_id).first()
    if not column:
        raise HTTPException(status_code=404, detail="Column not found")

    db.delete(column)
    db.commit()
    return {"message": "deleted"}


# Cards
@router.get("/columns/{column_id}/cards", response_model=list[CardResponse])
def list_cards(column_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Card)
        .filter(Card.column_id == column_id)
        .order_by(Card.position)
        .all()
    )


@router.get("/boards/{board_id}/cards", response_model=list[CardResponse])
def list_board_cards(board_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Card)
        .join(BoardColumn, Card.column_id == BoardColumn.id)
        .filter(BoardColumn.board_id == board_id)
        .order_by(BoardColumn.position, Card.position)
        .all()
    )


@router.post("/cards", response_model=CardResponse, status_code=201)
def create_card(payload: CardCreate, db: Session = Depends(get_db)):
    column = db.query(BoardColumn).filter(BoardColumn.id == payload.column_id).first()
    if not column:
        raise HTTPException(status_code=404, detail="Column not found")

    position = db.query(Card).filter(Card.column_id == payload.column_id).count()

    card = Card(
        column_id=payload.column_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        due_date=payload.due_date,
        position=position,
    )

    db.add(card)
    db.commit()
    db.refresh(card)
    return card


@router.patch("/cards/{card_id}", response_model=CardResponse)
def update_card(card_id: str, payload: CardUpdate, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(card, key, value)

    db.commit()
    db.refresh(card)
    return card


@router.post("/cards/{card_id}/move", response_model=CardResponse)
def move_card(card_id: str, payload: CardMove, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    target_column = db.query(BoardColumn).filter(BoardColumn.id == payload.column_id).first()
    if not target_column:
        raise HTTPException(status_code=404, detail="Target column not found")

    card.column_id = payload.column_id
    card.position = payload.position

    db.commit()
    db.refresh(card)
    return card


@router.delete("/cards/{card_id}")
def delete_card(card_id: str, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    db.delete(card)
    db.commit()
    return {"message": "deleted"}