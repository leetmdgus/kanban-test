<img width="1911" height="858" alt="image" src="https://github.com/user-attachments/assets/d82d51da-42d3-4bdd-8c61-252a7977ee7c" />

# Step 2 — PostgreSQL + 정규화 Kanban

기존 Step 1은 SQLite 단일 `cards` 테이블 기반이었습니다.

Step 2에서는 PostgreSQL을 사용하고, Kanban 데이터를 여러 테이블로 분리합니다.

핵심 목표는 다음과 같습니다.

- SQLite → PostgreSQL 전환
- 단일 `cards` 테이블 → N개 테이블 정규화
- 사업별, 보드별, 컬럼별, 카드별 데이터 분리
- SQLAlchemy ORM 관계 설정
- FastAPI CRUD API 재구성
- Docker Compose로 PostgreSQL 실행

------

# 1. Step 2 데이터 구조

## ERD

```mermaid
erDiagram
  BUSINESSES ||--o{ BOARDS : has
  BOARDS ||--o{ BOARD_COLUMNS : has
  BOARD_COLUMNS ||--o{ CARDS : has

  BUSINESSES {
    uuid id PK
    string name
    string description
    datetime created_at
    datetime updated_at
  }

  BOARDS {
    uuid id PK
    uuid business_id FK
    string name
    string description
    datetime created_at
    datetime updated_at
  }

  BOARD_COLUMNS {
    uuid id PK
    uuid board_id FK
    string title
    int position
    datetime created_at
    datetime updated_at
  }

  CARDS {
    uuid id PK
    uuid column_id FK
    string title
    text description
    string priority
    date due_date
    int position
    datetime created_at
    datetime updated_at
  }
```

## 관계

```txt
businesses 1 : N boards
boards 1 : N board_columns
board_columns 1 : N cards
```

------

# 2. Backend 프로젝트 구조

```txt
backend/
  app/
    __init__.py
    main.py
    database.py
    models.py
    schemas.py
    seed.py
  requirements.txt
  docker-compose.yml
  .env
```

------

# 3. docker-compose.yml

```yaml
services:
  postgres:
    image: postgres:16
    container_name: kanban-postgres
    restart: always
    environment:
      POSTGRES_USER: kanban
      POSTGRES_PASSWORD: kanban1234
      POSTGRES_DB: kanban_db
    ports:
      - "5432:5432"
    volumes:
      - kanban_postgres_data:/var/lib/postgresql/data

volumes:
  kanban_postgres_data:
```

실행:

```bash
docker compose up -d
```

------

# 4. .env

```env
DATABASE_URL=postgresql+psycopg2://kanban:kanban1234@localhost:5432/kanban_db
```

------

# 5. requirements.txt

```txt
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
psycopg2-binary==2.9.10
pydantic==2.10.4
python-dotenv==1.0.1
```

설치:

```bash
pip install -r requirements.txt
```

------

# 6. app/database.py

```python
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://kanban:kanban1234@localhost:5432/kanban_db",
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

------

# 7. app/models.py

```python
import uuid
from datetime import datetime

from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database import Base


def uuid_string() -> str:
    return str(uuid.uuid4())


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_string)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    boards: Mapped[list["Board"]] = relationship(
        "Board",
        back_populates="business",
        cascade="all, delete-orphan",
    )


class Board(Base):
    __tablename__ = "boards"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_string)
    business_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    business: Mapped[Business] = relationship("Business", back_populates="boards")
    columns: Mapped[list["BoardColumn"]] = relationship(
        "BoardColumn",
        back_populates="board",
        cascade="all, delete-orphan",
        order_by="BoardColumn.position",
    )


class BoardColumn(Base):
    __tablename__ = "board_columns"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_string)
    board_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    board: Mapped[Board] = relationship("Board", back_populates="columns")
    cards: Mapped[list["Card"]] = relationship(
        "Card",
        back_populates="column",
        cascade="all, delete-orphan",
        order_by="Card.position",
    )


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_string)
    column_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("board_columns.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    due_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    column: Mapped[BoardColumn] = relationship("BoardColumn", back_populates="cards")
```

------

# 8. app/schemas.py

```python
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
```

------

# 9. app/seed.py

```python
from sqlalchemy.orm import Session

from app.models import Board
from app.models import BoardColumn
from app.models import Business
from app.models import Card


def seed_data(db: Session) -> None:
    exists = db.query(Business).first()
    if exists:
        return

    business = Business(
        name="샘플 사업",
        description="Step 2 PostgreSQL Kanban 샘플 사업",
    )
    db.add(business)
    db.flush()

    board = Board(
        business_id=business.id,
        name="개발 보드",
        description="기본 Kanban 보드",
    )
    db.add(board)
    db.flush()

    todo = BoardColumn(board_id=board.id, title="To Do", position=0)
    progress = BoardColumn(board_id=board.id, title="In Progress", position=1)
    done = BoardColumn(board_id=board.id, title="Done", position=2)

    db.add_all([todo, progress, done])
    db.flush()

    db.add_all(
        [
            Card(
                column_id=todo.id,
                title="요구사항 정리",
                description="Step 2 범위 정의",
                priority="high",
                position=0,
            ),
            Card(
                column_id=progress.id,
                title="DB 정규화",
                description="사업, 보드, 컬럼, 카드 테이블 분리",
                priority="medium",
                position=0,
            ),
            Card(
                column_id=done.id,
                title="PostgreSQL 연결",
                description="Docker Compose 기반 DB 실행",
                priority="low",
                position=0,
            ),
        ]
    )

    db.commit()
```

------

# 10. app/main.py

```python
from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.database import Base
from app.database import engine
from app.database import get_db
from app.models import Board
from app.models import BoardColumn
from app.models import Business
from app.models import Card
from app.schemas import BoardCreate
from app.schemas import BoardDetailResponse
from app.schemas import BoardResponse
from app.schemas import BoardUpdate
from app.schemas import BusinessCreate
from app.schemas import BusinessResponse
from app.schemas import BusinessUpdate
from app.schemas import CardCreate
from app.schemas import CardMove
from app.schemas import CardResponse
from app.schemas import CardUpdate
from app.schemas import ColumnCreate
from app.schemas import ColumnResponse
from app.schemas import ColumnUpdate
from app.seed import seed_data

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kanban Step 2 API")

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


# Businesses
@app.get("/businesses", response_model=list[BusinessResponse])
def list_businesses(db: Session = Depends(get_db)):
    return db.query(Business).order_by(Business.created_at.desc()).all()


@app.post("/businesses", response_model=BusinessResponse, status_code=201)
def create_business(payload: BusinessCreate, db: Session = Depends(get_db)):
    business = Business(name=payload.name, description=payload.description)
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


@app.patch("/businesses/{business_id}", response_model=BusinessResponse)
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


@app.delete("/businesses/{business_id}")
def delete_business(business_id: str, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    db.delete(business)
    db.commit()
    return {"message": "deleted"}


# Boards
@app.get("/boards", response_model=list[BoardResponse])
def list_boards(db: Session = Depends(get_db)):
    return db.query(Board).order_by(Board.created_at.desc()).all()


@app.get("/boards/{board_id}", response_model=BoardDetailResponse)
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


@app.post("/boards", response_model=BoardResponse, status_code=201)
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


@app.patch("/boards/{board_id}", response_model=BoardResponse)
def update_board(board_id: str, payload: BoardUpdate, db: Session = Depends(get_db)):
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(board, key, value)

    db.commit()
    db.refresh(board)
    return board


@app.delete("/boards/{board_id}")
def delete_board(board_id: str, db: Session = Depends(get_db)):
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    db.delete(board)
    db.commit()
    return {"message": "deleted"}


# Columns
@app.get("/boards/{board_id}/columns", response_model=list[ColumnResponse])
def list_columns(board_id: str, db: Session = Depends(get_db)):
    return (
        db.query(BoardColumn)
        .filter(BoardColumn.board_id == board_id)
        .order_by(BoardColumn.position)
        .all()
    )


@app.post("/columns", response_model=ColumnResponse, status_code=201)
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


@app.patch("/columns/{column_id}", response_model=ColumnResponse)
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


@app.delete("/columns/{column_id}")
def delete_column(column_id: str, db: Session = Depends(get_db)):
    column = db.query(BoardColumn).filter(BoardColumn.id == column_id).first()
    if not column:
        raise HTTPException(status_code=404, detail="Column not found")

    db.delete(column)
    db.commit()
    return {"message": "deleted"}


# Cards
@app.get("/columns/{column_id}/cards", response_model=list[CardResponse])
def list_cards(column_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Card)
        .filter(Card.column_id == column_id)
        .order_by(Card.position)
        .all()
    )


@app.get("/boards/{board_id}/cards", response_model=list[CardResponse])
def list_board_cards(board_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Card)
        .join(BoardColumn, Card.column_id == BoardColumn.id)
        .filter(BoardColumn.board_id == board_id)
        .order_by(BoardColumn.position, Card.position)
        .all()
    )


@app.post("/cards", response_model=CardResponse, status_code=201)
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


@app.patch("/cards/{card_id}", response_model=CardResponse)
def update_card(card_id: str, payload: CardUpdate, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(card, key, value)

    db.commit()
    db.refresh(card)
    return card


@app.post("/cards/{card_id}/move", response_model=CardResponse)
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


@app.delete("/cards/{card_id}")
def delete_card(card_id: str, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    db.delete(card)
    db.commit()
    return {"message": "deleted"}
```

------

# 11. 실행 방법

## 1. PostgreSQL 실행

```bash
cd backend
docker compose up -d
```

## 2. 백엔드 가상환경 생성

```bash
python -m venv .venv
```

## 3. 가상환경 활성화

macOS / Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 4. 패키지 설치

```bash
pip install -r requirements.txt
```

## 5. FastAPI 실행

```bash
uvicorn app.main:app --reload --port 8000
```

## 6. Swagger 확인

```txt
http://localhost:8000/docs
```

------

# 12. API 사용 순서

## 1. 사업 조회

```http
GET /businesses
```

## 2. 보드 조회

```http
GET /boards
```

## 3. 특정 보드 컬럼 조회

```http
GET /boards/{board_id}/columns
```

## 4. 특정 보드 카드 조회

```http
GET /boards/{board_id}/cards
```

## 5. 카드 생성

```http
POST /cards
Content-Type: application/json

{
  "column_id": "컬럼 UUID",
  "title": "신규 업무",
  "description": "업무 설명",
  "priority": "medium",
  "due_date": null
}
```

## 6. 카드 이동

```http
POST /cards/{card_id}/move
Content-Type: application/json

{
  "column_id": "이동할 컬럼 UUID",
  "position": 0
}
```

------

# 13. Frontend 전체 코드

Step 2 프런트엔드는 `status`가 아니라 `column_id`를 기준으로 카드를 관리합니다.

------

## Frontend 프로젝트 생성

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

------

## frontend/package.json

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@vitejs/plugin-react": "latest",
    "vite": "latest",
    "typescript": "latest",
    "react": "latest",
    "react-dom": "latest"
  },
  "devDependencies": {}
}
```

------

## frontend/src/types.ts

```ts
export type Priority = "low" | "medium" | "high";

export interface Business {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface Board {
  id: string;
  business_id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface BoardColumn {
  id: string;
  board_id: string;
  title: string;
  position: number;
  created_at: string;
  updated_at: string;
}

export interface Card {
  id: string;
  column_id: string;
  title: string;
  description: string;
  priority: Priority;
  due_date: string | null;
  position: number;
  created_at: string;
  updated_at: string;
}
```

------

## frontend/src/api.ts

```ts
import type { Board, BoardColumn, Card, Priority } from "./types";

const API_BASE_URL = "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "API request failed");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function getBoards(): Promise<Board[]> {
  return request<Board[]>("/boards");
}

export function getColumns(boardId: string): Promise<BoardColumn[]> {
  return request<BoardColumn[]>(`/boards/${boardId}/columns`);
}

export function getBoardCards(boardId: string): Promise<Card[]> {
  return request<Card[]>(`/boards/${boardId}/cards`);
}

export function createCard(input: {
  column_id: string;
  title: string;
  description: string;
  priority: Priority;
  due_date?: string | null;
}): Promise<Card> {
  return request<Card>("/cards", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateCard(
  id: string,
  input: Partial<Pick<Card, "title" | "description" | "priority" | "due_date" | "position">>,
): Promise<Card> {
  return request<Card>(`/cards/${id}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function moveCard(id: string, columnId: string, position: number): Promise<Card> {
  return request<Card>(`/cards/${id}/move`, {
    method: "POST",
    body: JSON.stringify({ column_id: columnId, position }),
  });
}

export function deleteCard(id: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/cards/${id}`, {
    method: "DELETE",
  });
}
```

------

## frontend/src/main.tsx

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./App.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

------

## frontend/src/App.tsx

```tsx
import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  createCard,
  deleteCard,
  getBoardCards,
  getBoards,
  getColumns,
  moveCard,
  updateCard,
} from "./api";
import type { Board, BoardColumn, Card, Priority } from "./types";

interface CardFormState {
  title: string;
  description: string;
  priority: Priority;
  due_date: string;
  column_id: string;
}

const emptyForm: CardFormState = {
  title: "",
  description: "",
  priority: "medium",
  due_date: "",
  column_id: "",
};

function App() {
  const [boards, setBoards] = useState<Board[]>([]);
  const [selectedBoardId, setSelectedBoardId] = useState<string>("");
  const [columns, setColumns] = useState<BoardColumn[]>([]);
  const [cards, setCards] = useState<Card[]>([]);
  const [form, setForm] = useState<CardFormState>(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const selectedBoard = boards.find((board) => board.id === selectedBoardId);

  const groupedCards = useMemo(() => {
    const result: Record<string, Card[]> = {};

    columns.forEach((column) => {
      result[column.id] = cards
        .filter((card) => card.column_id === column.id)
        .sort((a, b) => a.position - b.position);
    });

    return result;
  }, [cards, columns]);

  async function loadBoards() {
    const data = await getBoards();
    setBoards(data);

    if (data.length > 0) {
      setSelectedBoardId(data[0].id);
    }
  }

  async function loadBoardData(boardId: string) {
    const [columnData, cardData] = await Promise.all([
      getColumns(boardId),
      getBoardCards(boardId),
    ]);

    const sortedColumns = [...columnData].sort((a, b) => a.position - b.position);

    setColumns(sortedColumns);
    setCards(cardData);

    setForm((prev) => ({
      ...prev,
      column_id: sortedColumns[0]?.id ?? "",
    }));
  }

  useEffect(() => {
    async function init() {
      try {
        setError(null);
        await loadBoards();
      } catch (err) {
        setError(err instanceof Error ? err.message : "보드 목록을 불러오지 못했습니다.");
      } finally {
        setLoading(false);
      }
    }

    void init();
  }, []);

  useEffect(() => {
    if (!selectedBoardId) {
      return;
    }

    async function load() {
      try {
        setError(null);
        await loadBoardData(selectedBoardId);
      } catch (err) {
        setError(err instanceof Error ? err.message : "보드 데이터를 불러오지 못했습니다.");
      }
    }

    void load();
  }, [selectedBoardId]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!form.title.trim()) {
      setError("카드 제목을 입력해주세요.");
      return;
    }

    if (!form.column_id) {
      setError("컬럼을 선택해주세요.");
      return;
    }

    try {
      setError(null);

      if (editingId) {
        const updated = await updateCard(editingId, {
          title: form.title.trim(),
          description: form.description.trim(),
          priority: form.priority,
          due_date: form.due_date || null,
        });

        setCards((prev) => prev.map((card) => (card.id === updated.id ? updated : card)));
      } else {
        const created = await createCard({
          column_id: form.column_id,
          title: form.title.trim(),
          description: form.description.trim(),
          priority: form.priority,
          due_date: form.due_date || null,
        });

        setCards((prev) => [...prev, created]);
      }

      setEditingId(null);
      setForm({
        ...emptyForm,
        column_id: columns[0]?.id ?? "",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "카드 저장에 실패했습니다.");
    }
  }

  function handleEdit(card: Card) {
    setEditingId(card.id);
    setForm({
      title: card.title,
      description: card.description,
      priority: card.priority,
      due_date: card.due_date ?? "",
      column_id: card.column_id,
    });
  }

  async function handleDelete(cardId: string) {
    try {
      setError(null);
      await deleteCard(cardId);
      setCards((prev) => prev.filter((card) => card.id !== cardId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "카드 삭제에 실패했습니다.");
    }
  }

  function handleDragStart(event: React.DragEvent<HTMLElement>, cardId: string) {
    event.dataTransfer.setData("text/plain", cardId);
  }

  function handleDragOver(event: React.DragEvent<HTMLElement>) {
    event.preventDefault();
  }

  async function handleDrop(event: React.DragEvent<HTMLElement>, columnId: string) {
    event.preventDefault();

    const cardId = event.dataTransfer.getData("text/plain");
    const targetCard = cards.find((card) => card.id === cardId);

    if (!targetCard || targetCard.column_id === columnId) {
      return;
    }

    const nextPosition = groupedCards[columnId]?.length ?? 0;
    const previousCards = cards;

    setCards((prev) =>
      prev.map((card) =>
        card.id === cardId
          ? { ...card, column_id: columnId, position: nextPosition }
          : card,
      ),
    );

    try {
      await moveCard(cardId, columnId, nextPosition);
      await loadBoardData(selectedBoardId);
    } catch (err) {
      setCards(previousCards);
      setError(err instanceof Error ? err.message : "카드 이동에 실패했습니다.");
    }
  }

  if (loading) {
    return <main className="app">불러오는 중...</main>;
  }

  return (
    <main className="app">
      <header className="header">
        <div>
          <p className="eyebrow">Step 2 PostgreSQL Kanban</p>
          <h1>Kanban Board</h1>
          {selectedBoard && <p className="description">{selectedBoard.description}</p>}
        </div>

        <select
          className="board-select"
          value={selectedBoardId}
          onChange={(event) => setSelectedBoardId(event.target.value)}
        >
          {boards.map((board) => (
            <option key={board.id} value={board.id}>
              {board.name}
            </option>
          ))}
        </select>
      </header>

      <section className="panel">
        <form className="card-form" onSubmit={handleSubmit}>
          <input
            value={form.title}
            onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
            placeholder="카드 제목"
          />

          <input
            value={form.description}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, description: event.target.value }))
            }
            placeholder="설명"
          />

          <select
            value={form.priority}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, priority: event.target.value as Priority }))
            }
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>

          <input
            type="date"
            value={form.due_date}
            onChange={(event) => setForm((prev) => ({ ...prev, due_date: event.target.value }))}
          />

          <select
            value={form.column_id}
            onChange={(event) => setForm((prev) => ({ ...prev, column_id: event.target.value }))}
          >
            {columns.map((column) => (
              <option key={column.id} value={column.id}>
                {column.title}
              </option>
            ))}
          </select>

          <button type="submit">{editingId ? "수정" : "추가"}</button>

          {editingId && (
            <button
              type="button"
              className="secondary"
              onClick={() => {
                setEditingId(null);
                setForm({ ...emptyForm, column_id: columns[0]?.id ?? "" });
              }}
            >
              취소
            </button>
          )}
        </form>

        {error && <p className="error">{error}</p>}
      </section>

      <section className="board">
        {columns.map((column) => (
          <section
            key={column.id}
            className="column"
            onDragOver={handleDragOver}
            onDrop={(event) => void handleDrop(event, column.id)}
          >
            <div className="column-header">
              <h2>{column.title}</h2>
              <span>{groupedCards[column.id]?.length ?? 0}</span>
            </div>

            <div className="cards">
              {(groupedCards[column.id] ?? []).map((card) => (
                <article
                  key={card.id}
                  className="kanban-card"
                  draggable
                  onDragStart={(event) => handleDragStart(event, card.id)}
                >
                  <div className="card-top">
                    <h3>{card.title}</h3>
                    <span className={`priority ${card.priority}`}>{card.priority}</span>
                  </div>

                  {card.description && <p>{card.description}</p>}

                  {card.due_date && <p className="due-date">마감일: {card.due_date}</p>}

                  <div className="card-actions">
                    <button type="button" onClick={() => handleEdit(card)}>
                      수정
                    </button>
                    <button type="button" onClick={() => void handleDelete(card.id)}>
                      삭제
                    </button>
                  </div>
                </article>
              ))}
            </div>
          </section>
        ))}
      </section>
    </main>
  );
}

export default App;
```

------

## frontend/src/App.css

```css
:root {
  color: #172033;
  background: #f4f6fb;
  font-family:
    Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
    sans-serif;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
}

button,
input,
select {
  font: inherit;
}

button {
  border: 0;
  border-radius: 10px;
  background: #1f2937;
  color: white;
  cursor: pointer;
  padding: 10px 14px;
  font-weight: 700;
}

button:hover {
  opacity: 0.9;
}

button.secondary {
  background: #e5e7eb;
  color: #111827;
}

.app {
  min-height: 100vh;
  padding: 40px;
}

.header {
  align-items: center;
  display: flex;
  gap: 20px;
  justify-content: space-between;
  margin-bottom: 24px;
}

.eyebrow {
  color: #667085;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.08em;
  margin: 0 0 8px;
  text-transform: uppercase;
}

h1 {
  font-size: 42px;
  margin: 0;
}

.description {
  color: #667085;
  margin: 8px 0 0;
}

.board-select {
  min-width: 220px;
}

.panel {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
  margin-bottom: 24px;
  padding: 20px;
}

.card-form {
  display: grid;
  gap: 12px;
  grid-template-columns: 1fr 1fr 140px 160px 180px auto auto;
}

input,
select {
  border: 1px solid #d0d5dd;
  border-radius: 10px;
  padding: 10px 12px;
}

.error {
  color: #b42318;
  font-weight: 700;
  margin: 14px 0 0;
}

.board {
  display: grid;
  gap: 20px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.column {
  background: #eef2f7;
  border: 1px solid #dbe1ea;
  border-radius: 22px;
  min-height: 520px;
  padding: 16px;
}

.column-header {
  align-items: center;
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.column-header h2 {
  font-size: 18px;
  margin: 0;
}

.column-header span {
  background: white;
  border-radius: 999px;
  color: #475467;
  font-size: 13px;
  font-weight: 700;
  padding: 4px 10px;
}

.cards {
  display: grid;
  gap: 12px;
}

.kanban-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
  cursor: grab;
  padding: 16px;
}

.kanban-card:active {
  cursor: grabbing;
}

.card-top {
  align-items: flex-start;
  display: flex;
  gap: 12px;
  justify-content: space-between;
}

.kanban-card h3 {
  font-size: 16px;
  margin: 0 0 8px;
}

.kanban-card p {
  color: #667085;
  line-height: 1.5;
  margin: 0 0 14px;
}

.due-date {
  font-size: 13px;
}

.priority {
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  padding: 4px 8px;
  text-transform: uppercase;
}

.priority.low {
  background: #ecfdf3;
  color: #027a48;
}

.priority.medium {
  background: #fffaeb;
  color: #b54708;
}

.priority.high {
  background: #fef3f2;
  color: #b42318;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.card-actions button {
  background: #f2f4f7;
  color: #344054;
  padding: 8px 10px;
}

@media (max-width: 1200px) {
  .card-form {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 920px) {
  .app {
    padding: 24px;
  }

  .header {
    align-items: stretch;
    flex-direction: column;
  }

  .card-form,
  .board {
    grid-template-columns: 1fr;
  }
}
```

------

# 14. Frontend 실행

```bash
cd frontend
npm install
npm run dev
```

접속:

```txt
http://localhost:5173
```

------

# 15. Step 2 체크리스트

- PostgreSQL Docker 실행
- `.env` 생성
- SQLAlchemy PostgreSQL 연결
- `businesses` 테이블 생성
- `boards` 테이블 생성
- `board_columns` 테이블 생성
- `cards` 테이블 생성
- 샘플 데이터 자동 생성
- Swagger에서 API 테스트
- 프런트엔드 `status` 제거
- 프런트엔드 `column_id` 기반으로 수정

------

# 16. Step 2 완료 기준

다음이 가능하면 Step 2 완료입니다.

```txt
1. 사업을 만들 수 있다.
2. 사업 안에 보드를 만들 수 있다.
3. 보드 안에 컬럼을 만들 수 있다.
4. 컬럼 안에 카드를 만들 수 있다.
5. 카드를 다른 컬럼으로 이동할 수 있다.
6. 서버를 재시작해도 PostgreSQL에 데이터가 남아 있다.
```

------

# 17. 다음 Step 3 예고

Step 3에서는 인증/인가를 추가합니다.

예상 추가 테이블:

```txt
users
workspace_members
board_members
refresh_tokens
```

예상 기능:

```txt
회원가입
로그인
JWT 인증
보드별 권한
담당자 지정
```
