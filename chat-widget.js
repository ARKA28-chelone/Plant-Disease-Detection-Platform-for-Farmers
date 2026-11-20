// ---------- Floating Krishi Mitra chat button (shown on every page) ----------
// Needs auth.js loaded first. Opens a small chat window in the bottom-right corner.
(function () {
  // The full assistant page already has its own chat
  if (/assistant\.html$/.test(window.location.pathname)) return;

  const toolNames = {
    lookup_disease: "disease database",
    get_my_recent_scans: "your scans",
    get_my_tracked_plants: "your tracked plants"
  };
  const history = [];

  function build() {
    const launcher = document.createElement("button");
    launcher.type = "button";
    launcher.className = "chat-launcher";
    launcher.setAttribute("aria-label", "Open Krishi Mitra assistant");
    launcher.title = "Ask Krishi Mitra";
    launcher.textContent = "💬";

    const box = document.createElement("div");
    box.className = "chat-widget";
    box.hidden = true;
    box.innerHTML =
      '<div class="chat-widget-head">' +
        "<span><strong>Krishi Mitra</strong><small>Farmer assistant</small></span>" +
        '<button type="button" class="chat-widget-close" aria-label="Close">✕</button>' +
      "</div>" +
      '<div class="chat-widget-log" aria-live="polite"></div>' +
      '<form class="chat-widget-form">' +
        '<input type="text" maxlength="2000" autocomplete="off" placeholder="Ask about your crops...">' +
        '<button type="submit" class="btn">Send</button>' +
      "</form>" +
      '<a class="chat-widget-full" href="assistant.html">Open full assistant →</a>';

    document.body.appendChild(box);
    document.body.appendChild(launcher);

    const log = box.querySelector(".chat-widget-log");
    const form = box.querySelector("form");
    const input = form.querySelector("input");
    const sendBtn = form.querySelector("button");

    function addMessage(role, text, meta) {
      const div = document.createElement("div");
      div.className = "msg " + role;
      const p = document.createElement("p");
      p.textContent = text;
      div.appendChild(p);
      if (meta) {
        const small = document.createElement("small");
        small.textContent = meta;
        div.appendChild(small);
      }
      log.appendChild(div);
      log.scrollTop = log.scrollHeight;
      return div;
    }

    // Greeting depends on whether the farmer is logged in
    if (Auth.getUser()) {
      addMessage("bot", "Namaste! 🌱 Ask me anything about crop diseases, pests or plant care.");
    } else {
      const div = addMessage("bot", "Namaste! 🌱 Please log in to chat with Krishi Mitra.");
      const link = document.createElement("a");
      link.href = "login.html";
      link.textContent = "Log in →";
      div.appendChild(link);
      input.disabled = true;
      sendBtn.disabled = true;
    }

    function toggle(open) {
      box.hidden = !open;
      launcher.classList.toggle("open", open);
      launcher.textContent = open ? "✕" : "💬";
      if (open && !input.disabled) input.focus();
    }

    launcher.addEventListener("click", function () { toggle(box.hidden); });
    box.querySelector(".chat-widget-close").addEventListener("click", function () { toggle(false); });

    // Other pages can open the chat with a question, e.g. "Ask the assistant" on a scan
    window.KrishiChat = {
      ask: function (question) {
        toggle(true);
        if (input.disabled) return;
        input.value = question;
        form.requestSubmit();
      }
    };

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      const question = input.value.trim();
      if (!question) return;
      addMessage("user", question);
      input.value = "";
      sendBtn.disabled = true;
      const thinking = addMessage("bot thinking", "Thinking...");

      Auth.request("/api/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: question,
          history: history,
          language: typeof I18n !== "undefined" ? I18n.getLang() : "en"
        })
      }).then(function (data) {
        thinking.remove();
        const used = Array.from(new Set(data.tools_used || [])).map(function (t) { return toolNames[t] || t; });
        addMessage("bot", data.reply || "Sorry, I couldn't come up with an answer.",
          used.length ? "Checked: " + used.join(", ") : "");
        history.push({ role: "user", content: question }, { role: "assistant", content: data.reply || "" });
      }).catch(function (err) {
        thinking.remove();
        addMessage("bot error", "Sorry, something went wrong: " + err.message);
      }).finally(function () {
        sendBtn.disabled = false;
        input.focus();
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }
})();
