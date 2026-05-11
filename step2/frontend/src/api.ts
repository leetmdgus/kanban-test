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