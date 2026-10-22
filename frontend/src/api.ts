import type { AnswerResponse, QuestionResponse, SessionResponse, Subject } from "./types";

// Remove a trailing slash so we never call "...com//session"
const API_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

async function post<T>(path: string, body: unknown): Promise<T> {
  if (!API_URL) {
    throw new Error("VITE_API_URL is not set. Check frontend/.env.local and restart npm run dev.");
  }
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error ?? `Request failed (${res.status})`);
  }
  return data as T;
}

export const startSession = (name: string, subject: Subject) =>
  post<SessionResponse>("/session", { name, subject });

export const getQuestion = (sessionId: string) =>
  post<QuestionResponse>("/question", { sessionId });

export const submitAnswer = (sessionId: string, questionId: string, choiceIndex: number) =>
  post<AnswerResponse>("/answer", { sessionId, questionId, choiceIndex });
