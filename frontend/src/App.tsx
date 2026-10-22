import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { getQuestion, startSession, submitAnswer } from "./api";
import type { ChatMessage, Progress, QuestionResponse, Subject } from "./types";

let nextMessageId = 1;

export default function App() {
  const [name, setName] = useState("");
  const [subject, setSubject] = useState<Subject>("math");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [question, setQuestion] = useState<QuestionResponse | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [showHint, setShowHint] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Keep the newest chat bubble in view
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  function addMessage(from: ChatMessage["from"], text: string) {
    setMessages((prev) => [...prev, { id: nextMessageId++, from, text }]);
  }

  async function loadQuestion(id: string) {
    setLoading(true);
    setError(null);
    setShowHint(false);
    try {
      const q = await getQuestion(id);
      setQuestion(q);
      addMessage("bot", `Level ${q.level} · ${q.topic}\n${q.question}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function handleStart(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const session = await startSession(name.trim() || "Student", subject);
      setSessionId(session.sessionId);
      setProgress(session.progress);
      addMessage("bot", `Hi ${session.name}! Let's practice ${subject}. Get two right in a row and the questions get harder.`);
      await loadQuestion(session.sessionId);
    } catch (err) {
      setError((err as Error).message);
      setLoading(false);
    }
  }

  async function handleAnswer(choiceIndex: number) {
    if (!sessionId || !question) return;
    const answered = question;
    setQuestion(null); // hide the buttons so it can't be answered twice
    addMessage("student", answered.choices[choiceIndex]);
    setLoading(true);
    try {
      const result = await submitAnswer(sessionId, answered.questionId, choiceIndex);
      setProgress(result.progress);
      const lines = [
        result.correct
          ? "Correct! Great job."
          : `Not quite. The answer is: ${answered.choices[result.correctIndex]}`,
        result.explanation,
      ];
      if (result.levelEvent === "level_up") lines.push("Level up! The next one will be a bit harder.");
      if (result.levelEvent === "level_down") lines.push("Let's try an easier one.");
      addMessage("bot", lines.join("\n"));
      await loadQuestion(sessionId);
    } catch (err) {
      setError((err as Error).message);
      setLoading(false);
    }
  }

  function handleRestart() {
    setSessionId(null);
    setProgress(null);
    setQuestion(null);
    setMessages([]);
    setError(null);
  }

  if (!sessionId) {
    return (
      <main className="app">
        <h1>SandStudyMate AI</h1>
        <p className="tagline">Math and Science practice that grows with you.</p>
        <form className="start-form" onSubmit={handleStart}>
          <label>
            Your name
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Sandy" maxLength={30} />
          </label>
          <label>
            Subject
            <select value={subject} onChange={(e) => setSubject(e.target.value as Subject)}>
              <option value="math">Math</option>
              <option value="science">Science</option>
            </select>
          </label>
          <button type="submit" disabled={loading}>
            {loading ? "Starting..." : "Start practicing"}
          </button>
        </form>
        {error && <p className="error">{error}</p>}
      </main>
    );
  }

  return (
    <main className="app">
      <header className="status-bar">
        <span>Level {progress?.level ?? 1} / 5</span>
        <span>Score {progress?.total_correct ?? 0} / {progress?.total_answered ?? 0}</span>
        <button className="link-button" onClick={handleRestart}>New session</button>
      </header>

      <section className="chat">
        {messages.map((m) => (
          <div key={m.id} className={`bubble ${m.from}`}>{m.text}</div>
        ))}
        {loading && <div className="bubble bot thinking">Thinking...</div>}
        <div ref={bottomRef} />
      </section>

      {question && (
        <section className="answers">
          {question.choices.map((choice, i) => (
            <button key={i} onClick={() => handleAnswer(i)}>{choice}</button>
          ))}
          {question.hint &&
            (showHint ? (
              <p className="hint">Hint: {question.hint}</p>
            ) : (
              <button className="link-button" onClick={() => setShowHint(true)}>Show a hint</button>
            ))}
        </section>
      )}

      {error && (
        <p className="error">
          {error}{" "}
          <button className="link-button" onClick={() => loadQuestion(sessionId)}>Try again</button>
        </p>
      )}
    </main>
  );
}
