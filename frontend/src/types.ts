export type Status = "todo" | "in_progress" | "done";

export interface Card {
  id: string;
  title: string;
  description: string;
  status: Status;
  order: number;
}

export interface Column {
  id: Status;
  title: string;
}