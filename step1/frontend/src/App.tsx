import { FormEvent, useEffect, useMemo, useState } from "react";
import { createCard, deleteCard, getCards, moveCard, updateCard } from "./api";
import type { Card, Column, Status } from "./types";

const columns: Column[] = [
  { id: "todo", title: "To Do" },
  { id: "in_progress", title: "In Progress" },
  { id: "done", title: "Done" },
];

const emptyForm = {
  title: "",
  description: "",
  status: "todo" as Status,
};

function App() {
  const [cards, setCards] = useState<Card[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const groupedCards = useMemo(() => {
    return columns.reduce<Record<Status, Card[]>>(
      (acc, column) => {
        acc[column.id] = cards
          .filter((card) => card.status === column.id)
          .sort((a, b) => a.order - b.order);
        return acc;
      },
      { todo: [], in_progress: [], done: [] },
    );
  }, [cards]);

  async function loadCards() {
    try {
      setError(null);
      const data = await getCards();
      setCards(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "카드를 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadCards();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!form.title.trim()) {
      setError("제목을 입력해주세요.");
      return;
    }

    try {
      setError(null);

      if (editingId) {
        const updated = await updateCard(editingId, {
          title: form.title.trim(),
          description: form.description.trim(),
          status: form.status,
        });
        setCards((prev) => prev.map((card) => (card.id === updated.id ? updated : card)));
      } else {
        const created = await createCard({
          title: form.title.trim(),
          description: form.description.trim(),
          status: form.status,
        });
        setCards((prev) => [...prev, created]);
      }

      setEditingId(null);
      setForm(emptyForm);
    } catch (err) {
      setError(err instanceof Error ? err.message : "저장에 실패했습니다.");
    }
  }

  function handleEdit(card: Card) {
    setEditingId(card.id);
    setForm({
      title: card.title,
      description: card.description,
      status: card.status,
    });
  }

  async function handleDelete(id: string) {
    try {
      setError(null);
      await deleteCard(id);
      setCards((prev) => prev.filter((card) => card.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "삭제에 실패했습니다.");
    }
  }

  function handleDragStart(event: React.DragEvent<HTMLDivElement>, cardId: string) {
    event.dataTransfer.setData("text/plain", cardId);
  }

  function handleDragOver(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();
  }

  async function handleDrop(event: React.DragEvent<HTMLDivElement>, status: Status) {
    event.preventDefault();
    const cardId = event.dataTransfer.getData("text/plain");
    const card = cards.find((item) => item.id === cardId);

    if (!card || card.status === status) {
      return;
    }

    const nextOrder = groupedCards[status].length;

    const previousCards = cards;
    setCards((prev) =>
      prev.map((item) =>
        item.id === cardId ? { ...item, status, order: nextOrder } : item,
      ),
    );

    try {
      await moveCard(cardId, status, nextOrder);
      await loadCards();
    } catch (err) {
      setCards(previousCards);
      setError(err instanceof Error ? err.message : "이동에 실패했습니다.");
    }
  }

  return (
    <main className="app">
      <header className="header">
        <div>
          <p className="eyebrow">React + TypeScript + Vite + FastAPI</p>
          <h1>Kanban Board</h1>
        </div>
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
            onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))}
            placeholder="설명"
          />
          <select
            value={form.status}
            onChange={(event) => setForm((prev) => ({ ...prev, status: event.target.value as Status }))}
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
                setForm(emptyForm);
              }}
            >
              취소
            </button>
          )}
        </form>
        {error && <p className="error">{error}</p>}
      </section>

      {loading ? (
        <p className="loading">불러오는 중...</p>
      ) : (
        <section className="board">
          {columns.map((column) => (
            <div
              key={column.id}
              className="column"
              onDragOver={handleDragOver}
              onDrop={(event) => void handleDrop(event, column.id)}
            >
              <div className="column-header">
                <h2>{column.title}</h2>
                <span>{groupedCards[column.id].length}</span>
              </div>

              <div className="cards">
                {groupedCards[column.id].map((card) => (
                  <article
                    key={card.id}
                    className="kanban-card"
                    draggable
                    onDragStart={(event) => handleDragStart(event, card.id)}
                  >
                    <h3>{card.title}</h3>
                    {card.description && <p>{card.description}</p>}
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
            </div>
          ))}
        </section>
      )}
    </main>
  );
}

export default App;