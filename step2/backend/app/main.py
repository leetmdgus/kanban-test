from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.database import Base
from app.database import engine
from app.database import get_db
from app.kanban.models import Board
from app.kanban.models import BoardColumn
from app.kanban.models import Business
from app.kanban.models import Card
from app.kanban.schemas import BoardCreate
from app.kanban.schemas import BoardDetailResponse
from app.kanban.schemas import BoardResponse
from app.kanban.schemas import BoardUpdate
from app.kanban.schemas import BusinessCreate
from app.kanban.schemas import BusinessResponse
from app.kanban.schemas import BusinessUpdate
from app.kanban.schemas import CardCreate
from app.kanban.schemas import CardMove
from app.kanban.schemas import CardResponse
from app.kanban.schemas import CardUpdate
from app.kanban.schemas import ColumnCreate
from app.kanban.schemas import ColumnResponse
from app.kanban.schemas import ColumnUpdate
from app.kanban.seed import seed_data

from app.kanban.routers import router as kanban_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kanban Step 2 API")

app.include_router(kanban_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}
