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
}