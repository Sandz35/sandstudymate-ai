document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("quiz-form");
  const questionsContainer = document.getElementById("questions");

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const topic = document.getElementById("topic").value || "general study";
    const difficulty = document.getElementById("difficulty").value;

    const sampleQuestions = [
      `Explain the core idea of ${topic} at a ${difficulty} level.`,
      `List the main factors affecting ${topic}.`,
      `What real-world example best illustrates ${topic}?`,
    ];

    questionsContainer.innerHTML = sampleQuestions
      .map((question) => `<div class="question-card"><p>${question}</p></div>`)
      .join("");
  });
});
