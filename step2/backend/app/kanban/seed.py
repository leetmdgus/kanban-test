from sqlalchemy.orm import Session

from app.kanban.models import Board
from app.kanban.models import BoardColumn
from app.kanban.models import Business
from app.kanban.models import Card


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