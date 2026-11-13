export type Subject = "math" | "science";

export interface Progress {
  level: number;
  correct_streak: number;
  wrong_streak: number;
  total_answered: number;
  total_correct: number;
}

export interface SessionResponse {
  sessionId: string;
  name: string;
  subject: Subject;
  progress: Progress;
}

export interface QuestionResponse {
  questionId: string;
  topic: string;
  level: number;
  question: string;
  choices: string[];
  hint: string;
  grounded: boolean;
}

export interface AnswerResponse {
  correct: boolean;
  correctIndex: number;
  explanation: string;
  levelEvent: "level_up" | "level_down" | "same";
  progress: Progress;
}

export interface ChatMessage {
  id: number;
  from: "bot" | "student";
  text: string;
}

export interface ChatResponse {
  type: "topic_set" | "redirect" | "blocked" | "unclear";
  reply: string;
  topic?: string;
  subject?: Subject;
  question?: QuestionResponse;
}
