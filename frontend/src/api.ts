import type { Card, Status } from "./types";

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

export function getCards(): Promise<Card[]> {
  return request<Card[]>("/cards");
}

export function createCard(input: {
  title: string;
  description: string;
  status: Status;
}): Promise<Card> {
  return request<Card>("/cards", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateCard(
  id: string,
  input: Partial<Pick<Card, "title" | "description" | "status" | "order">>,
): Promise<Card> {
  return request<Card>(`/cards/${id}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function moveCard(id: string, status: Status, order: number): Promise<Card> {
  return request<Card>(`/cards/${id}/move`, {
    method: "POST",
    body: JSON.stringify({ status, order }),
  });
}

export function deleteCard(id: string): Promise<void> {
  return request<void>(`/cards/${id}`, {
    method: "DELETE",
  });
}