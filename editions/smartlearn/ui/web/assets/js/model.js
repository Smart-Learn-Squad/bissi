(() => {
  "use strict";

  const S = {
    bissi: null,
    busy: false,
    activeAiNode: null,
    activeAiRaw: "",
    welcomeHtml: "",
    parserFrameQueued: false,
    parserInFlight: false,
    parserLastRequestedRaw: "",
  };

  const $ = (sel) => document.querySelector(sel);
  const esc = (s) => String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  function init() {
    const welcome = $("#welcome");
    if (welcome) S.welcomeHtml = welcome.outerHTML;
    hydrateSidebarUser();
    warmFromResumeFlow();
    connectBridge(0);
  }

  function hydrateSidebarUser() {
    if (!window.SmartLearnShell) return;
    const user = window.SmartLearnShell.readStoredUser?.() || {
      prenom: "Etudiant",
      filiere: "SmartLearn",
      email: "local@bissi",
    };
    window.SmartLearnShell.setSidebarUser?.(user);
  }

  function warmFromResumeFlow() {
    const params = new URLSearchParams(window.location.search);
    if (params.get("flow") !== "resume") return;

    const title = sessionStorage.getItem("sl_titre_cours") || "ce chapitre";
    const resume = sessionStorage.getItem("sl_resume_cours") || "";
    const points = sessionStorage.getItem("sl_points_cours") || "";
    const matiere = sessionStorage.getItem("sl_matiere_cours") || "General";
    const prompt = [
      `Tu es SmartLearn. Genere un quiz progressif sur "${title}" (${matiere}).`,
      "Format:",
      "1) 5 questions QCM faciles",
      "2) 3 questions intermediaires",
      "3) 2 questions de synthese",
      "Pour chaque question: donne la bonne reponse avec une explication courte.",
      resume ? `Resume du chapitre: ${resume}` : "",
      points ? `Points essentiels:\n${points}` : "",
    ].filter(Boolean).join("\n");

    const input = $("#messageInput");
    if (input) {
      input.value = prompt;
      autoResize(input);
      input.focus();
    }
    const bar = $("#comprehensionBar");
    bar?.classList.add("show");
    const titleNode = $("#compChapterTitle");
    if (titleNode) titleNode.textContent = title;
  }

  function connectBridge(tries) {
    if (typeof qt !== "undefined" && typeof QWebChannel !== "undefined") {
      new QWebChannel(qt.webChannelTransport, (channel) => {
        S.bissi = channel.objects.bissi;
        wireSignals();
        loadInitial();
      });
      return;
    }
    if (tries < 20) {
      setTimeout(() => connectBridge(tries + 1), 100);
      return;
    }
    pushSystem("Mode local: QWebChannel indisponible.");
  }

  function wireSignals() {
    S.bissi.tokenReceived.connect(onToken);
    S.bissi.responseFinished.connect(onFinished);
    S.bissi.errorOccurred.connect(onError);
    S.bissi.interrupted.connect(onInterrupted);
    S.bissi.conversationUpdated.connect((raw) => {
      try {
        renderConversations(JSON.parse(raw));
      } catch (_) {}
    });
  }

  function loadInitial() {
    if (!S.bissi?.getInitialData) return;
    S.bissi.getInitialData((raw) => {
      try {
        const data = JSON.parse(raw);
        renderConversations(Array.isArray(data.conversations) ? data.conversations : []);
      } catch (_) {}
    });
  }

  function setSendBtnState(sending) {
    const btn = document.querySelector(".send-btn");
    if (!btn) return;
    if (sending) {
      btn.title = "Arrêter";
      btn.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>';
      btn.onclick = () => {
        if (S.bissi && S.bissi.stopGeneration) S.bissi.stopGeneration();
        else onInterrupted();
      };
      btn.disabled = false;
    } else {
      btn.title = "Envoyer";
      btn.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>';
      btn.onclick = sendMessage;
      btn.disabled = false;
    }
  }

  function lockInput() {
    S.busy = true;
    const input = $("#messageInput");
    if (input) input.disabled = true;
    setSendBtnState(true);
  }

  function unlockInput() {
    S.busy = false;
    const input = $("#messageInput");
    if (input) {
      input.disabled = false;
      input.focus();
    }
    setSendBtnState(false);
  }

  function hideWelcome() {
    const w = $("#welcome");
    if (w) w.style.display = "none";
  }

  function addUserMessage(text) {
    hideWelcome();
    const wrap = document.createElement("div");
    wrap.className = "msg user";
    wrap.innerHTML = `
      <div class="msg-av">E</div>
      <div class="msg-content">${esc(text)}</div>
    `;
    $("#messages")?.appendChild(wrap);
    scrollToBottom();
  }

  function addAiBubble() {
    hideWelcome();
    const wrap = document.createElement("div");
    wrap.className = "msg ai";
    wrap.innerHTML = `
      <div class="msg-av">∞</div>
      <div class="msg-content"><div class="tw-text"><span class="typing-cursor">▌</span></div></div>
    `;
    $("#messages")?.appendChild(wrap);
    S.activeAiNode = wrap.querySelector(".tw-text");
    S.activeAiRaw = "";
    scrollToBottom();
  }

  function renderMarkdown(text) {
    const parts = [];
    let last = 0;
    const codeRe = /```(\w*)\r?\n?([\s\S]*?)```/g;
    let m;
    while ((m = codeRe.exec(text)) !== null) {
      if (m.index > last) parts.push({ t: "text", s: text.slice(last, m.index) });
      parts.push({ t: "code", lang: m[1], s: m[2] });
      last = m.index + m[0].length;
    }
    if (last < text.length) parts.push({ t: "text", s: text.slice(last) });

    return parts.map((part) => {
      if (part.t === "code") {
        return `<pre class="code-block" data-lang="${esc(part.lang)}"><code>${esc(part.s)}</code></pre>`;
      }
      return renderBlock(part.s);
    }).join("");
  }

  function isTableSeparator(line) {
    return /^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$/.test(line);
  }

  function splitTableRow(line) {
    let row = line.trim();
    if (row.startsWith("|")) row = row.slice(1);
    if (row.endsWith("|")) row = row.slice(0, -1);
    return row.split("|").map((cell) => cell.trim());
  }

  function inl(text) {
    let s = esc(text);
    s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/\*(.+?)\*/g, "<em>$1</em>");
    s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
    s = s.replace(/~~(.+?)~~/g, "<del>$1</del>");
    return s;
  }

  function renderTable(headers, rows) {
    const width = Math.max(headers.length, ...rows.map((r) => r.length), 1);
    const h = headers.slice();
    while (h.length < width) h.push("");
    const bodyRows = rows.map((r) => {
      const cells = r.slice();
      while (cells.length < width) cells.push("");
      return cells;
    });

    const thStyle = "padding:7px 9px;border-bottom:1px solid #e8e8e8;background:#f4f4f7;text-align:left;font-weight:600;color:#2C2C2A;vertical-align:top;";
    const tdStyle = "padding:7px 9px;border-top:1px solid #e8e8e8;vertical-align:top;word-break:break-word;";
    const tableStyle = "width:100%;border-collapse:collapse;border:1px solid #e8e8e8;border-radius:6px;overflow:hidden;margin:8px 0;font-family:Inter,Segoe UI,Helvetica Neue,Arial,sans-serif;font-size:12px;line-height:1.5;";

    const head = h.map((cell) => `<th style="${thStyle}">${inl(cell)}</th>`).join("");
    const body = bodyRows.map((row) =>
      `<tr>${row.map((cell) => `<td style="${tdStyle}">${inl(cell)}</td>`).join("")}</tr>`
    ).join("");

    return `<table style="${tableStyle}"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
  }

  function renderBlock(text) {
    const out = [];
    let inUl = false, inOl = false;

    const lines = text.split("\n");
    for (let i = 0; i < lines.length; ) {
      const line = lines[i];
      const isUl = /^[-*+] /.test(line);
      const isOl = /^\d+\. /.test(line);

      if (!isUl && inUl) { out.push("</ul>"); inUl = false; }
      if (!isOl && inOl) { out.push("</ol>"); inOl = false; }

      if (i + 1 < lines.length && line.includes("|") && isTableSeparator(lines[i + 1])) {
        const headers = splitTableRow(line);
        i += 2;
        const rows = [];
        while (i < lines.length) {
          const rowLine = lines[i];
          if (!rowLine.trim() || !rowLine.includes("|")) break;
          rows.push(splitTableRow(rowLine));
          i += 1;
        }
        out.push(renderTable(headers, rows));
        continue;
      }

      if      (/^#### /.test(line)) out.push(`<h4>${inl(line.slice(5))}</h4>`);
      else if (/^### /.test(line))  out.push(`<h3>${inl(line.slice(4))}</h3>`);
      else if (/^## /.test(line))   out.push(`<h2>${inl(line.slice(3))}</h2>`);
      else if (/^# /.test(line))    out.push(`<h1>${inl(line.slice(2))}</h1>`);
      else if (/^---+$/.test(line.trim())) out.push("<hr>");
      else if (isUl) {
        if (!inUl) { out.push("<ul>"); inUl = true; }
        out.push(`<li>${inl(line.replace(/^[-*+] /, ""))}</li>`);
      } else if (isOl) {
        if (!inOl) { out.push("<ol>"); inOl = true; }
        out.push(`<li>${inl(line.replace(/^\d+\. /, ""))}</li>`);
      } else if (line.trim() === "") {
        out.push("<br>");
      } else {
        out.push(`<p>${inl(line)}</p>`);
      }
      i += 1;
    }
    if (inUl) out.push("</ul>");
    if (inOl) out.push("</ol>");
    return out.join("");
  }

  function setAiHtml(html, withCursor) {
    if (!S.activeAiNode) return;
    S.activeAiNode.innerHTML = withCursor
      ? `${html}<span class="typing-cursor">▌</span>`
      : html;
    enhanceRenderedContent(S.activeAiNode);
    scrollToBottom();
  }

  function enhanceRenderedContent(root) {
    if (!root) return;
    if (typeof hljs !== "undefined") {
      root.querySelectorAll("pre code").forEach((block) => {
        try { hljs.highlightElement(block); } catch (_) {}
      });
    }
    if (window._katexReady && typeof renderMathInElement !== "undefined") {
      try {
        renderMathInElement(root, {
          delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "$", right: "$", display: false },
            { left: "\\[", right: "\\]", display: true },
            { left: "\\(", right: "\\)", display: false },
          ],
          throwOnError: false,
        });
      } catch (_) {}
    }
  }

  function parseStreamingWithBridge(raw, done) {
    if (!S.bissi?.parseStreaming) {
      done(renderMarkdown(raw), false);
      return;
    }
    S.bissi.parseStreaming(raw, (payloadRaw) => {
      try {
        const payload = JSON.parse(payloadRaw);
        done(payload.html || renderMarkdown(raw), true);
      } catch (_) {
        done(renderMarkdown(raw), false);
      }
    });
  }

  function parseFinalWithBridge(raw, done) {
    if (!S.bissi?.parseMarkdown) {
      done(renderMarkdown(raw), false);
      return;
    }
    S.bissi.parseMarkdown(raw, (payloadRaw) => {
      try {
        const payload = JSON.parse(payloadRaw);
        done(payload.html || renderMarkdown(raw), true);
      } catch (_) {
        done(renderMarkdown(raw), false);
      }
    });
  }

  function scheduleStreamingRender() {
    if (S.parserFrameQueued) return;
    S.parserFrameQueued = true;
    requestAnimationFrame(() => {
      S.parserFrameQueued = false;
      if (!S.activeAiNode) return;
      if (S.parserInFlight) return;

      const snapshot = S.activeAiRaw;
      S.parserInFlight = true;
      S.parserLastRequestedRaw = snapshot;
      parseStreamingWithBridge(snapshot, (html, fromBridge) => {
        S.parserInFlight = false;
        if (!S.activeAiNode) return;
        // Drop stale parser results when newer tokens already arrived.
        if (snapshot !== S.activeAiRaw) {
          scheduleStreamingRender();
          return;
        }
        setAiHtml(html, true);
        // Keep one extra pass queued when parser fallback was used.
        if (!fromBridge && snapshot !== S.activeAiRaw) scheduleStreamingRender();
      });
    });
  }

  function onToken(token) {
    if (!S.activeAiNode) addAiBubble();
    S.activeAiRaw += token;
    scheduleStreamingRender();
  }

  function onFinished(raw) {
    const node = S.activeAiNode;
    const finalRaw = (() => {
      try {
        const payload = JSON.parse(raw);
        return payload?.full || S.activeAiRaw;
      } catch (_) {
        return S.activeAiRaw;
      }
    })();

    const cleanup = () => {
      S.activeAiNode = null;
      S.activeAiRaw = "";
      S.parserFrameQueued = false;
      S.parserInFlight = false;
      S.parserLastRequestedRaw = "";
      unlockInput();
    };

    if (!node) {
      cleanup();
      return;
    }

    parseFinalWithBridge(finalRaw, (html) => {
      node.innerHTML = html;
      enhanceRenderedContent(node);
      scrollToBottom();
      cleanup();
    });
  }

  function onError(message) {
    pushSystem(`Erreur: ${message}`);
    S.activeAiNode = null;
    S.activeAiRaw = "";
    S.parserFrameQueued = false;
    S.parserInFlight = false;
    S.parserLastRequestedRaw = "";
    unlockInput();
  }

  function onInterrupted() {
    pushSystem("Generation interrompue.");
    S.activeAiNode = null;
    S.activeAiRaw = "";
    S.parserFrameQueued = false;
    S.parserInFlight = false;
    S.parserLastRequestedRaw = "";
    unlockInput();
  }

  function pushSystem(text) {
    const n = document.createElement("div");
    n.className = "msg ai";
    n.innerHTML = `<div class="msg-av">•</div><div class="msg-content">${esc(text)}</div>`;
    $("#messages")?.appendChild(n);
    scrollToBottom();
  }

  function renderConversations(conversations) {
    const list = $("#conversationsList");
    if (!list) return;
    list.innerHTML = "";
    if (!conversations.length) {
      const empty = document.createElement("div");
      empty.className = "hist-item";
      empty.innerHTML = `<span class="hi-icon">💬</span><span class="hi-text">Nouvelle session</span>`;
      list.appendChild(empty);
      return;
    }

    let firstItem = null;
    conversations.forEach((c, idx) => {
      const item = document.createElement("div");
      item.className = `hist-item${idx === 0 ? " active" : ""}`;
      item.dataset.convId = c.id;
      const title = c.title || c.first_message || `Session ${idx + 1}`;
      item.innerHTML = `
        <span class="hi-icon">💬</span>
        <span class="hi-text">${esc(title)}</span>
      `;

      // Load conversation when clicked
      item.addEventListener('click', () => {
        // mark active
        list.querySelectorAll('.hist-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');

        const convId = parseInt(item.dataset.convId, 10);
        if (!S.bissi?.loadConversation) return;

        S.bissi.loadConversation(convId, (raw) => {
          try {
            const history = JSON.parse(raw);
            if (history.error) {
              pushSystem(`Erreur: ${history.error}`);
              return;
            }

            const hasMessages = Array.isArray(history) && history.length > 0;
            const messagesEl = $("#messages");
            if (messagesEl) messagesEl.innerHTML = hasMessages ? "" : (S.welcomeHtml || "");
            S.activeAiNode = null;
            S.activeAiRaw = "";

            if (!hasMessages) {
              pushSystem("Conversation prête");
              return;
            }

            // Render each message
            history.forEach((msg) => {
              if (msg.role === "user") {
                addUserMessage(msg.content);
              } else if (msg.role === "assistant") {
                // Use Python parser for rich rendering when available
                parseFinalWithBridge(msg.content, (html) => {
                  const wrap = document.createElement("div");
                  wrap.className = "msg ai";
                  wrap.innerHTML = `<div class="msg-av">∞</div><div class="msg-content">${html}</div>`;
                  $("#messages")?.appendChild(wrap);
                  enhanceRenderedContent(wrap);
                  scrollToBottom();
                });
              }
            });
          } catch (e) {
            console.error("loadConversation parse error", e);
          }
        });
      });

      list.appendChild(item);
      if (idx === 0) firstItem = item;
    });

    // Auto-load the first conversation if welcome screen is visible or messages empty
    const msgs = $("#messages");
    const welcome = $("#welcome");
    if (firstItem && msgs) {
      const showWelcome = welcome && welcome.style.display !== "none";
      if (showWelcome || msgs.children.length === 0) {
        firstItem.click();
      }
    }
  }

  function scrollToBottom() {
    const msgs = $("#messages");
    if (!msgs) return;
    msgs.scrollTop = msgs.scrollHeight;
  }

  function autoResize(textarea) {
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 140)}px`;
  }

  function sendMessage() {
    if (S.busy) return;
    const input = $("#messageInput");
    if (!input) return;
    const text = input.value.trim();
    if (!text) return;

    addUserMessage(text);
    input.value = "";
    autoResize(input);
    lockInput();

    if (S.bissi?.sendMessage) {
      S.bissi.sendMessage(text);
      return;
    }

    setTimeout(() => onToken("SmartLearn en mode demonstration locale."), 200);
    setTimeout(() => onFinished(JSON.stringify({ full: "SmartLearn en mode demonstration locale." })), 500);
  }

  function useSuggestion(text) {
    const input = $("#messageInput");
    if (!input) return;
    input.value = text;
    autoResize(input);
    sendMessage();
  }

  function nouvelleConversation() {
    if (S.bissi?.newConversation) S.bissi.newConversation();
    const messages = $("#messages");
    if (messages && S.welcomeHtml) messages.innerHTML = S.welcomeHtml;
    S.activeAiNode = null;
    S.activeAiRaw = "";
    unlockInput();
  }

  function repondreCompris(compris) {
    const bar = $("#comprehensionBar");
    bar?.classList.remove("show");
    useSuggestion(
      compris
        ? "Super. Donne-moi maintenant 3 exercices progressifs pour m'entrainer."
        : "Reexplique-moi ce chapitre plus simplement, avec analogies et exemples concrets."
    );
  }

  function proposerQuiz() {
    useSuggestion("Genere un quiz progressif de 10 questions sur notre dernier chapitre.");
  }

  window.autoResize = autoResize;
  window.sendMessage = sendMessage;
  window.useSuggestion = useSuggestion;
  window.nouvelleConversation = nouvelleConversation;
  window.repondreCompris = repondreCompris;
  window.proposerQuiz = proposerQuiz;

  document.addEventListener("DOMContentLoaded", init);
})();
