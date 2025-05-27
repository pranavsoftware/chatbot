document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("prompt");
  const chatWindow = document.getElementById("chat-window");

  form.onsubmit = async (e) => {
    e.preventDefault();
    const prompt = input.value.trim();
    if (!prompt) return;

    // Show user input
    chatWindow.innerHTML += `<div class="chat-bubble user">${prompt}</div>`;

    // Send to backend
    const res = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: `prompt=${encodeURIComponent(prompt)}`,
    });

    const data = await res.json();

    chatWindow.innerHTML += `<div class="chat-bubble bot">${data.response}</div>`;
    chatWindow.scrollTop = chatWindow.scrollHeight;
    input.value = "";
  };
});
