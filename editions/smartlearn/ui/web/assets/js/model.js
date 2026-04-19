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
    quizRequestActive: false,
  };

  const $ = (sel) => document.querySelector(sel);
  const esc = (s) => String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  const PROGRESS_KEY = "bissi_smartlearn_progress";

  function loadProgress() {
    try {
      const raw = localStorage.getItem(PROGRESS_KEY);
      if (!raw) return { chapitres: [], quizCompleted: 0, totalTemps: 0 };
      const parsed = JSON.parse(raw);
      return {
        chapitres: Array.isArray(parsed?.chapitres) ? parsed.chapitres : [],
        quizCompleted: Number(parsed?.quizCompleted || 0),
        totalTemps: Number(parsed?.totalTemps || 0),
      };
    } catch (_) {
      return { chapitres: [], quizCompleted: 0, totalTemps: 0 };
    }
  }

  function saveProgress(progress) {
    localStorage.setItem(PROGRESS_KEY, JSON.stringify(progress));
  }

  function recordQuizResult(scorePercent) {
    const progress = loadProgress();
    const titre = (sessionStorage.getItem("sl_titre_cours") || "Conversation").trim();
    const now = new Date().toISOString();
    const idx = progress.chapitres.findIndex((c) => String(c?.titre || "").trim().toLowerCase() === titre.toLowerCase());
    if (idx >= 0) {
      const prev = Number(progress.chapitres[idx].score || 0);
      progress.chapitres[idx] = {
        titre,
        score: Math.round((prev + scorePercent) / 2),
        date: now,
      };
    } else {
      progress.chapitres.unshift({ titre, score: scorePercent, date: now });
    }
    progress.quizCompleted = Number(progress.quizCompleted || 0) + 1;
    const slTemps = Number(localStorage.getItem("sl_temps_etude") || 0);
    progress.totalTemps = Math.max(Number(progress.totalTemps || 0), slTemps);
    saveProgress(progress);
  }

  function parseStrictQuizJson(raw) {
    const txt = String(raw || "").replace(/```json|```/gi, "").trim();
    const start = txt.indexOf("{");
    const end = txt.lastIndexOf("}");
    if (start < 0 || end <= start) throw new Error("Réponse quiz invalide");
    const data = JSON.parse(txt.slice(start, end + 1));
    if (!Array.isArray(data?.questions) || !data.questions.length) {
      throw new Error("Aucune question reçue");
    }
    return {
      questions: data.questions.slice(0, 3).map((q, i) => ({
        q: String(q?.q || `Question ${i + 1}`),
        options: Array.isArray(q?.options) ? q.options.map((o) => String(o)) : [],
        answer: q?.answer,
      })).filter((q) => q.options.length >= 2),
    };
  }

  function answerIndex(question) {
    if (typeof question.answer === "number") return question.answer;
    if (typeof question.answer === "string") {
      const letter = question.answer.trim().toUpperCase();
      if (/^[A-D]$/.test(letter)) return letter.charCodeAt(0) - 65;
      const idx = question.options.findIndex((o) => o.trim().toLowerCase() === question.answer.trim().toLowerCase());
      if (idx >= 0) return idx;
    }
    return -1;
  }

  function requestQuizFromAgent(prompt) {
    if (!S.bissi?.sendMessage) return Promise.reject(new Error("Bridge unavailable"));
    return new Promise((resolve, reject) => {
      const onDone = (raw) => {
        cleanup();
        try {
          const payload = JSON.parse(raw);
          resolve(payload?.full || "");
        } catch (_) {
          resolve(String(raw || ""));
        }
      };
      const onErr = (msg) => {
        cleanup();
        reject(new Error(String(msg || "Erreur quiz")));
      };
      const cleanup = () => {
        S.quizRequestActive = false;
        try { S.bissi.responseFinished.disconnect(onDone); } catch (_) {}
        try { S.bissi.errorOccurred.disconnect(onErr); } catch (_) {}
        unlockInput();
      };
      S.quizRequestActive = true;
      lockInput();
      S.bissi.responseFinished.connect(onDone);
      S.bissi.errorOccurred.connect(onErr);
      S.bissi.sendMessage(prompt);
    });
  }

  function renderQuizCard(quiz) {
    hideWelcome();
    const wrap = document.createElement("div");
    wrap.className = "msg ai";
    wrap.innerHTML = `
      <div class="msg-av">∞</div>
      <div class="msg-content">
        <div style="border:1px solid #1f2a44;border-radius:12px;padding:12px;background:#0f1424;">
          <div style="font-weight:700;color:#cfd8ff;margin-bottom:10px">🎯 Quiz SmartLearn</div>
          <div id="quizQuestion" style="font-weight:600;margin-bottom:10px"></div>
          <div id="quizOptions" style="display:grid;gap:8px"></div>
          <div id="quizMeta" style="margin-top:10px;color:#9fb0d8;font-size:12px"></div>
        </div>
      </div>`;
    $("#messages")?.appendChild(wrap);
    const qNode = wrap.querySelector("#quizQuestion");
    const oNode = wrap.querySelector("#quizOptions");
    const mNode = wrap.querySelector("#quizMeta");
    if (!qNode || !oNode || !mNode) return;

    let index = 0;
    let score = 0;
    const total = quiz.questions.length;

    const show = () => {
      const q = quiz.questions[index];
      qNode.textContent = `Q${index + 1}/${total} — ${q.q}`;
      oNode.innerHTML = "";
      mNode.textContent = "Choisir une réponse.";
      q.options.forEach((opt, optIndex) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.textContent = opt;
        btn.style.cssText = "text-align:left;padding:9px 10px;border:1px solid #2a3b6b;border-radius:9px;background:#111a31;color:#e7ecff;cursor:pointer;";
        btn.onclick = () => {
          const ok = optIndex === answerIndex(q);
          if (ok) score += 1;
          mNode.textContent = ok ? "✅ Correct" : "❌ Incorrect";
          [...oNode.querySelectorAll("button")].forEach((b) => { b.disabled = true; b.style.opacity = "0.75"; });
          setTimeout(() => {
            index += 1;
            if (index < total) {
              show();
              return;
            }
            const pct = Math.round((score / total) * 100);
            qNode.textContent = `Score final : ${score}/${total} (${pct}%)`;
            oNode.innerHTML = "";
            mNode.textContent = "Résultat sauvegardé dans ta progression.";
            recordQuizResult(pct);
          }, 500);
        };
        oNode.appendChild(btn);
      });
    };
    show();
    scrollToBottom();
  }

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
      prenom: "Étudiant",
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
      `You are SmartLearn. Generate a progressive quiz on "${title}" (${matiere}).`,
      "Format:",
      "1) 5 easy MCQ questions",
      "2) 3 intermediate questions",
      "3) 2 synthesis questions",
      "For each question: give the correct answer with a short explanation.",
      resume ? `Chapter summary: ${resume}` : "",
      points ? `Key points:\n${points}` : "",
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
    pushSystem("Mode local : QWebChannel indisponible.");
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
    const qs = $("#quickSuggestions");
    if (qs) qs.classList.add("visible");
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
    if (S.quizRequestActive) return;
    if (!S.activeAiNode) addAiBubble();
    S.activeAiRaw += token;
    scheduleStreamingRender();
  }

  function onFinished(raw) {
    if (S.quizRequestActive) return;
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
    if (S.quizRequestActive) return;
    pushSystem(`Erreur : ${message}`);
    S.activeAiNode = null;
    S.activeAiRaw = "";
    S.parserFrameQueued = false;
    S.parserInFlight = false;
    S.parserLastRequestedRaw = "";
    unlockInput();
  }

  function onInterrupted() {
    if (S.quizRequestActive) return;
    pushSystem("Génération interrompue.");
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
              pushSystem(`Erreur : ${history.error}`);
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
              const role = (msg.role || '').toLowerCase();

              const rawContent = msg.content || (msg.metadata ? (typeof msg.metadata === 'string' ? msg.metadata : JSON.stringify(msg.metadata)) : '');

              if (role === 'user') {
                // Render user message with markdown parsing so LaTeX/formatting shows
                parseFinalWithBridge(rawContent, (html) => {
                  const wrap = document.createElement('div');
                  wrap.className = 'msg user';
                  wrap.innerHTML = `<div class='msg-av'>E</div><div class='msg-content'>${html}</div>`;
                  $('#messages')?.appendChild(wrap);
                  enhanceRenderedContent(wrap);
                  scrollToBottom();
                });
                return;
              }

              // Fallback: render anything not user as assistant/tool/system output.
              const raw = rawContent;

              if (!raw) {
                // show placeholder if nothing to render
                const wrap = document.createElement('div');
                wrap.className = 'msg ai';
                wrap.innerHTML = `<div class='msg-av'>∞</div><div class='msg-content'><em>(message vide)</em></div>`;
                $('#messages')?.appendChild(wrap);
                return;
              }

              // Use Python parser for rich rendering when available
              parseFinalWithBridge(raw, (html) => {
                const wrap = document.createElement('div');
                wrap.className = 'msg ai';
                wrap.innerHTML = `<div class='msg-av'>∞</div><div class='msg-content'>${html}</div>`;
                $('#messages')?.appendChild(wrap);
                enhanceRenderedContent(wrap);
                scrollToBottom();
              });
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

    setTimeout(() => onToken("SmartLearn en mode démo local."), 200);
    setTimeout(() => onFinished(JSON.stringify({ full: "SmartLearn en mode démo local." })), 500);
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
    // Hide quick suggestions, restore welcome
    const qs = $("#quickSuggestions");
    if (qs) qs.classList.remove("visible");
  }

  function repondreCompris(compris) {
    const bar = $("#comprehensionBar");
    bar?.classList.remove("show");
    // Persist comprehension signal for home.js dashboard
    try {
      const titre = sessionStorage.getItem("sl_titre_cours") || "Chapitre";
      // Sanitize key: only alphanumeric + underscore
      const safeKey = titre.toLowerCase().replace(/[^a-z0-9]+/g, "_").slice(0, 64);
      localStorage.setItem("sl_compris_" + safeKey, JSON.stringify({
        compris,
        titre,
        date: new Date().toISOString(),
      }));
    } catch (_) {}
    useSuggestion(
      compris
        ? "Parfait. Donne-moi maintenant 3 exercices d'entraînement progressifs."
        : "Réexplique-moi ce chapitre plus simplement, avec des analogies et des exemples concrets."
    );
  }

  async function proposerQuiz() {
    try {
      const prompt = [
        "Generate a 3-question MCQ quiz about our conversation.",
        "Strict JSON format only:",
        '{"questions":[{"q":"...","options":["...","...","...","..."],"answer":"..."}]}',
        "No markdown, no text outside the JSON."
      ].join("\n");
      const raw = await requestQuizFromAgent(prompt);
      const quiz = parseStrictQuizJson(raw);
      if (!quiz.questions.length) throw new Error("Quiz vide");
      renderQuizCard(quiz);
    } catch (e) {
      pushSystem(`Impossible de générer le quiz : ${e?.message || "erreur"}`);
    }
  }

  window.autoResize = autoResize;
  window.sendMessage = sendMessage;
  window.useSuggestion = useSuggestion;
  window.nouvelleConversation = nouvelleConversation;
  window.repondreCompris = repondreCompris;
  window.proposerQuiz = proposerQuiz;

  document.addEventListener("DOMContentLoaded", init);
})();
