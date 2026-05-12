from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.database import Base
from app.database import engine
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
