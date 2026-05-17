(function () {
  "use strict";

  // 5.1 — session_id persistido por aba
  const SESSION_KEY = "t2a_session_id";
  let sessionId = sessionStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    sessionStorage.setItem(SESSION_KEY, sessionId);
  }

  const history = document.getElementById("chat-history");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("message-input");
  const sendBtn = document.getElementById("send-btn");

  // 5.5 — scroll automático para o final
  function scrollToBottom() {
    history.scrollTop = history.scrollHeight;
  }

  function addBubble(text, role) {
    const row = document.createElement("div");
    row.className = `bubble-row ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;

    row.appendChild(bubble);
    history.appendChild(row);
    scrollToBottom();
    return row;
  }

  // 5.3 — indicador de loading
  function addLoading() {
    const row = document.createElement("div");
    row.className = "bubble-row agent";
    row.id = "loading-bubble";

    const bubble = document.createElement("div");
    bubble.className = "bubble loading-dots";
    bubble.innerHTML = "<span></span><span></span><span></span>";

    row.appendChild(bubble);
    history.appendChild(row);
    scrollToBottom();
  }

  function removeLoading() {
    const el = document.getElementById("loading-bubble");
    if (el) el.remove();
  }

  function setLoading(on) {
    input.disabled = on;
    sendBtn.disabled = on;
    if (on) {
      addLoading();
    } else {
      removeLoading();
      input.focus();
    }
  }

  // 5.2 + 5.4 + 5.6 — envio de mensagem
  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return; // 5.2 — evita envio vazio

    input.value = "";
    addBubble(text, "user");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: text }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        const msg = err.detail ?? "Erro desconhecido no servidor.";
        addBubble(`Erro: ${msg}`, "error"); // 5.6
      } else {
        const data = await res.json();
        addBubble(data.response, "agent"); // 5.4
      }
    } catch (e) {
      addBubble("Não foi possível conectar ao servidor. Verifique se ele está rodando.", "error"); // 5.6
    } finally {
      setLoading(false); // 5.4 — reabilita interface
    }
  }

  // 5.7 — vincular eventos
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    sendMessage();
  });

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
})();
