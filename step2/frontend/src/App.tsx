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