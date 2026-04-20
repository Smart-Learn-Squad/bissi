/**
 * app.js — BISSI WebEngine Frontend
 *
 * Wires QWebChannel signals → DOM, renders chat, manages file explorer,
 * handles input history and theme toggling.
 */

'use strict';

// ── Global state ───────────────────────────────────────────────
const S = {
  bissi:        null,   // QWebChannel bridge object
  busy:         false,
  bubble:       null,   // active streaming bubble element
  inputHist:    [],     // ring buffer of sent messages
  histIdx:      -1,     // -1 = not navigating
  currentConversationId: null,
  curPath:      null,
  rafPending:   false,  // requestAnimationFrame scheduled for stream render
  welcomeHTML:  '',
  pendingNewConversation: false,
  sessionMenuBound: false,
};
window.S = S;
const LAYOUT_KEYS = {
  sidebarCollapsed: 'bissi-master-sidebar-collapsed',
  panelCollapsed: 'bissi-master-panel-collapsed',
  panelWidth: 'bissi-master-panel-width',
};
const THEME_MODE_KEY = 'bissi-theme-mode';
const LEGACY_THEME_KEY = 'bissi-theme';
const WORKSPACE_DEFAULT_WIDTH = 420;
const WORKSPACE_MIN_WIDTH = 320;

// ── Bootstrap ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const messages = el('#messages');
  S.welcomeHTML = messages ? messages.innerHTML : '';
  bindInput();
  bindTheme();
  bindTabs();
  bindLayoutToggles();
  bindWorkspaceResize();
  waitForBridge(0);
});

// Qt injects `qt.webChannelTransport` asynchronously after page load.
// Poll up to 2 s (20 × 100 ms) before falling back to demo mode.
function waitForBridge(tries) {
  if (typeof qt !== 'undefined' && typeof QWebChannel !== 'undefined') {
    new QWebChannel(qt.webChannelTransport, channel => {
      S.bissi = channel.objects.bissi;
      wireSignals();
      loadInitial();
    });
  } else if (tries < 20) {
    setTimeout(() => waitForBridge(tries + 1), 100);
  } else {
    console.warn('[bissi] QWebChannel unavailable — demo mode');
    sysMsg('Mode démo — QWebChannel non disponible', 'warn');
    const dot = el('#status-dot');
    if (dot) dot.className = 'status-dot amber';
  }
}

// ── Signal wiring ──────────────────────────────────────────────
function wireSignals() {
  const b = S.bissi;
  b.tokenReceived.connect(onToken);
  b.toolStarted.connect(onToolStart);
  b.toolDone.connect(onToolDone);
  b.thinkingChanged.connect(onThinking);
  b.responseFinished.connect(onFinished);
  b.errorOccurred.connect(onError);
  b.interrupted.connect(onInterrupted);
  b.conversationUpdated.connect(onConvsUpdated);
  b.themeChanged.connect(onThemeChanged);
}

function loadInitial() {
  // QWebChannel methods with return values are async — use callback form
  S.bissi.getInitialData(raw => {
    try {
      const data = JSON.parse(raw);
      applyTheme(data.theme || 'light', data.tokens);
      setModel(data.model || '');
      updateProfile(data.profile);
      const convs = Array.isArray(data.conversations) ? data.conversations : [];
      renderSessions(convs, true); // auto-load existing conversations
      
      // If no conversations, create a new one
      if (convs.length === 0) {
        startNewConversation();
      }
      
      sysMsg(`Bissi prêt · ${data.model} · tape un message`, 'dim');
      loadDir(null);
    } catch (e) {
      console.error('[bissi] loadInitial error:', e);
    }
  });
}

// ── Signal handlers ────────────────────────────────────────────
function onToken(token) {
  if (!S.bubble) S.bubble = mkAssistantBubble();
  streamToken(S.bubble, token);
}

function onToolStart(name, args) {
  if (!S.bubble) S.bubble = mkAssistantBubble();
  addToolCard(S.bubble, name, args, 'running');
}

function onToolDone(name, result) {
  if (!S.bubble) return;
  const card = S.bubble.querySelector(
    `.tool-card[data-tool="${CSS.escape(name)}"].running`
  );
  if (!card) return;
  card.classList.replace('running', 'done');
  // Replace spinner with done checkmark
  const spinner = card.querySelector('.step-spinner');
  if (spinner) {
    spinner.outerHTML = `<svg class="step-done-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`;
  }
  const r = card.querySelector('.tool-result');
  if (r) r.textContent = result;
}

function onThinking(msg) {
  const hint = el('#routing-hint');
  if (!hint) return;
  hint.textContent = msg;
  if (!msg) return;
  if (msg.includes('gemma4:')) {
    try {
      const [modelPart, scorePart] = msg.split('·');
      const model = modelPart.replace('→', '').trim();
      const score = parseFloat((scorePart || '').replace('score', '').trim());
      hint.style.color = 'var(--teal)';
      const badge = el('#model-badge');
      if (badge) {
        badge.textContent = `● ${model} · en ligne`;
        badge.className = 'badge badge-teal';
      }
    } catch { /* malformed, ignore */ }
  }
}

function onFinished(json) {
  try {
    const data = JSON.parse(json);
    // Finalize streaming bubble: re-render with proper markdown using Python parser
    if (S.bubble) {
      const content = S.bubble.querySelector('.bubble-content');
      if (content && S.bubble._raw) {
        // Use Python parser for full markdown support
        S.bissi.parseMarkdown(S.bubble._raw, result => {
          try {
            const parseResult = JSON.parse(result);
            content.innerHTML = parseResult.html || renderMd(S.bubble._raw || '');
            hlCode(content);
            renderMath(content);
          } catch (e) {
            console.error('[bissi] parseMarkdown error:', e);
            content.innerHTML = renderMd(S.bubble._raw || '');
          }
        });
      }
      S.bubble = null;
    }
    updateProfile(data.profile);
    setModel(data.model || '');
    el('#routing-hint').textContent = '';
  } catch (e) {
    console.error('[bissi] onFinished error:', e);
  }
  unlock();
}

function onError(msg) {
  if (S.bubble) { S.bubble.remove(); S.bubble = null; }
  sysMsg(`✗ ${msg}`, 'error');
  unlock();
}

function onInterrupted() {
  S.bubble = null;
  sysMsg('⊘ interrompu', 'warn');
  unlock();
}

function onConvsUpdated(json) {
  try {
    const shouldAutoLoad = S.pendingNewConversation;
    renderSessions(JSON.parse(json), shouldAutoLoad);
    S.pendingNewConversation = false;
  } catch { /* noop */ }
}

function onThemeChanged(name) {
  setThemeMode(name);
  applyThemeLocal(name);
}

// ── Message rendering ──────────────────────────────────────────
function mkUserBubble(text) {
  const d = document.createElement('div');
  d.className = 'msg-user';
  d.textContent = text;
  el('#messages').appendChild(d);
  // Hide welcome screen on first message
  const w = el('#welcome-screen');
  if (w) w.style.display = 'none';
  scrollEnd();
}

function mkAssistantBubble() {
  const wrap = document.createElement('div');
  wrap.className = 'msg-assistant';
  wrap.innerHTML = `
    <div class="assistant-icon">
      <svg viewBox="0 0 44 28" fill="none">
        <path d="M22 14C22 14 17 4 10 4C3 4 3 24 10 24C17 24 22 14 22 14C22 14 27 4 34 4C41 4 41 24 34 24C27 24 22 14 22 14Z"
          stroke="currentColor" stroke-width="2.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>
    <div class="msg-body">
      <div class="msg-header">
        <span class="msg-name">bissi</span>
      </div>
      <div class="bubble-content"><span class="stream-cursor">▌</span></div>
      <div class="tool-cards"></div>
    </div>`;
  wrap._raw = '';
  el('#messages').appendChild(wrap);
  scrollEnd();
  return wrap;
}

function streamToken(wrap, token) {
  wrap._raw += token;
  // Batch renders with requestAnimationFrame — one markdown parse per frame
  // regardless of how many tokens arrive. No flickering, no cursor loss.
  if (!S.rafPending) {
    S.rafPending = true;
    requestAnimationFrame(() => {
      S.rafPending = false;
      if (S.bubble) renderStreamBubble(S.bubble);
    });
  }
}

function renderStreamBubble(wrap) {
  const content = wrap.querySelector('.bubble-content');
  if (!content) return;
  content.innerHTML = renderMdPartial(wrap._raw) +
                      '<span class="stream-cursor">▌</span>';
  renderMath(content);
  scrollEnd();
}

// Like renderMd but tolerates incomplete fences and bold/italic
function renderMdPartial(text) {
  // Close unclosed ``` fences so the parser doesn't eat the rest as code
  const fences = (text.match(/```/g) || []).length;
  if (fences % 2 !== 0) text += '\n```';
  return renderMd(text);
}

function addToolCard(wrap, name, args, status) {
  const cards = wrap.querySelector('.tool-cards');
  if (!cards) return;
  const card = document.createElement('div');
  card.className = `tool-card ${status}`;
  card.dataset.tool = name;
  // Manus-style: spinner while running, check icon when done
  const iconHtml = status === 'running'
    ? `<div class="step-spinner"></div>`
    : `<svg class="step-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">${toolIconSvg(name)}</svg>`;
  card.innerHTML = `
    ${iconHtml}
    <span class="tool-name">${esc(name)}</span>
    <span class="tool-args">${esc(args)}</span>
    <span class="tool-result"></span>`;
  cards.appendChild(card);
  scrollEnd();
}

function sysMsg(text, variant = 'dim') {
  const d = document.createElement('div');
  d.className = `system-msg system-${variant}`;
  d.textContent = text;
  el('#messages').appendChild(d);
  scrollEnd();
}

function resetMessages(showWelcome = false) {
  const messagesEl = el('#messages');
  if (!messagesEl) return;
  messagesEl.innerHTML = showWelcome ? (S.welcomeHTML || '') : '';
  const welcomeEl = el('#welcome-screen');
  if (welcomeEl) welcomeEl.style.display = showWelcome ? 'block' : 'none';
  S.bubble = null;
}

function renderAssistantHistory(markdownText) {
  const wrap = mkAssistantBubble();
  wrap._raw = markdownText || '';
  const content = wrap.querySelector('.bubble-content');
  if (!content) return;

  const fallbackRender = () => {
    content.innerHTML = renderMd(wrap._raw);
    hlCode(content);
    renderMath(content);
  };

  if (!S.bissi || !wrap._raw) {
    fallbackRender();
    return;
  }

  S.bissi.parseMarkdown(wrap._raw, result => {
    try {
      const parsed = JSON.parse(result);
      content.innerHTML = parsed.html || renderMd(wrap._raw);
    } catch {
      content.innerHTML = renderMd(wrap._raw);
    }
    hlCode(content);
    renderMath(content);
  });
}

function startNewConversation() {
  if (!S.bissi) return;
  // Immediately reset the visual state before waiting for the bridge
  resetMessages(true);
  S.pendingNewConversation = true;
  S.bissi.newConversation(() => {});
}

// ── Markdown renderer ──────────────────────────────────────────
function renderMd(text) {
  const parts = [];
  let last = 0;
  const codeRe = /```(\w*)\r?\n?([\s\S]*?)```/g;
  let m;
  while ((m = codeRe.exec(text)) !== null) {
    if (m.index > last) parts.push({ t: 'text', s: text.slice(last, m.index) });
    parts.push({ t: 'code', lang: m[1], s: m[2] });
    last = m.index + m[0].length;
  }
  if (last < text.length) parts.push({ t: 'text', s: text.slice(last) });

  return parts.map(p =>
    p.t === 'code'
      ? `<pre class="code-block" data-lang="${esc(p.lang)}"><code>${esc(p.s)}</code></pre>`
      : renderBlock(p.s)
  ).join('');
}

function isTableSeparator(line) {
  return /^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$/.test(line);
}

function splitTableRow(line) {
  let row = line.trim();
  if (row.startsWith('|')) row = row.slice(1);
  if (row.endsWith('|')) row = row.slice(0, -1);
  return row.split('|').map(cell => cell.trim());
}

function renderTable(headers, rows) {
  const width = Math.max(headers.length, ...rows.map(r => r.length), 1);
  const h = headers.slice();
  while (h.length < width) h.push('');
  const bodyRows = rows.map(r => {
    const cells = r.slice();
    while (cells.length < width) cells.push('');
    return cells;
  });

  const thStyle = 'padding:7px 9px;border-bottom:1px solid #e8e8e8;background:#f4f4f7;text-align:left;font-weight:600;color:#2C2C2A;vertical-align:top;';
  const tdStyle = 'padding:7px 9px;border-top:1px solid #e8e8e8;vertical-align:top;word-break:break-word;';
  const tableStyle = 'width:100%;border-collapse:collapse;border:1px solid #e8e8e8;border-radius:6px;overflow:hidden;margin:8px 0;font-family:Inter,Segoe UI,Helvetica Neue,Arial,sans-serif;font-size:12px;line-height:1.5;';

  const head = h.map(cell => `<th style="${thStyle}">${inl(cell)}</th>`).join('');
  const body = bodyRows.map(row =>
    `<tr>${row.map(cell => `<td style="${tdStyle}">${inl(cell)}</td>`).join('')}</tr>`
  ).join('');

  return `<table style="${tableStyle}"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function renderBlock(text) {
  const out = [];
  let inUl = false, inOl = false;

  const lines = text.split('\n');
  for (let i = 0; i < lines.length; ) {
    const line = lines[i];
    const isUl = /^[-*+] /.test(line);
    const isOl = /^\d+\. /.test(line);

    if (!isUl && inUl) { out.push('</ul>'); inUl = false; }
    if (!isOl && inOl) { out.push('</ol>'); inOl = false; }

    if (i + 1 < lines.length && line.includes('|') && isTableSeparator(lines[i + 1])) {
      const headers = splitTableRow(line);
      i += 2;
      const rows = [];
      while (i < lines.length) {
        const rowLine = lines[i];
        if (!rowLine.trim() || !rowLine.includes('|')) break;
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
    else if (/^---+$/.test(line.trim())) out.push('<hr>');
    else if (isUl) {
      if (!inUl) { out.push('<ul>'); inUl = true; }
      out.push(`<li>${inl(line.replace(/^[-*+] /, ''))}</li>`);
    } else if (isOl) {
      if (!inOl) { out.push('<ol>'); inOl = true; }
      out.push(`<li>${inl(line.replace(/^\d+\. /, ''))}</li>`);
    } else if (line.trim() === '') {
      out.push('<br>');
    } else {
      out.push(`<p>${inl(line)}</p>`);
    }
    i += 1;
  }
  if (inUl) out.push('</ul>');
  if (inOl) out.push('</ol>');
  return out.join('');
}

// Inline markdown (applied after html-escaping)
function inl(text) {
  let s = esc(text);
  s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/\*(.+?)\*/g,     '<em>$1</em>');
  s = s.replace(/`([^`]+)`/g,     '<code>$1</code>');
  s = s.replace(/~~(.+?)~~/g,     '<del>$1</del>');
  return s;
}

// Minimal syntax highlight hook (class only, Prism-friendly)
function hlCode(container) {
  container.querySelectorAll('pre.code-block code').forEach(b => {
    b.className = `language-${b.closest('pre').dataset.lang || 'plaintext'}`;
  });
  if (window.BissiFrontend?.highlightCodeBlocks) {
    window.BissiFrontend.highlightCodeBlocks(container);
  }
}

// Render LaTeX math with KaTeX (fires after markdown is in the DOM)
function renderMath(container) {
  if (!container) return;
  if (!window._katexReady || typeof renderMathInElement === 'undefined') {
    // KaTeX CDN can load after first render; retry a few times.
    const retries = Number(container.dataset.katexRetries || '0');
    if (retries < 20) {
      container.dataset.katexRetries = String(retries + 1);
      setTimeout(() => renderMath(container), 120);
    }
    return;
  }
  delete container.dataset.katexRetries;
  if (window.BissiFrontend?.renderMath) {
    window.BissiFrontend.renderMath(container);
    return;
  }
  try {
    renderMathInElement(container, {
      delimiters: [
        { left: '$$',  right: '$$',  display: true  },
        { left: '$',   right: '$',   display: false },
        { left: '\\[', right: '\\]', display: true  },
        { left: '\\(', right: '\\)', display: false },
      ],
      throwOnError: false,
      strict: 'ignore',
    });
  } catch { /* ignore parse errors */ }
}

// ── Input handling ─────────────────────────────────────────────
function setSendBtnState(sending) {
  const btn = el('#send-btn');
  if (!btn) return;
  if (sending) {
    btn.title = 'Stop';
    btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>';
    btn.onclick = interrupt;
    btn.disabled = false;
  } else {
    btn.title = 'Send';
    btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>';
    btn.onclick = submit;
    btn.disabled = false;
  }
}

function bindInput() {
  const inp = el('#chat-input');
  setSendBtnState(false);
  el('#send-btn').onclick = submit;

  inp.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); return; }
    if (e.key === 'ArrowUp'   && !e.shiftKey) { e.preventDefault(); navHist(+1); return; }
    if (e.key === 'ArrowDown' && !e.shiftKey) { e.preventDefault(); navHist(-1); return; }
    if (e.key === 'c' && e.ctrlKey && S.busy) { interrupt(); }
  });

  inp.addEventListener('input', () => {
    inp.style.height = 'auto';
    inp.style.height = Math.min(inp.scrollHeight, 160) + 'px';
  });
}

function submit() {
  if (S.busy) return;
  const inp = el('#chat-input');
  const txt = inp.value.trim();
  if (!txt) return;

  S.inputHist.unshift(txt);
  if (S.inputHist.length > 50) S.inputHist.pop();
  S.histIdx = -1;

  inp.value = '';
  inp.style.height = 'auto';

  mkUserBubble(txt);
  lock();

  if (S.bissi) {
    S.bissi.sendMessage(txt);
  } else {
    // Demo stub
    setTimeout(() => onToken('**Bissi** en mode démo.'), 300);
    setTimeout(() => onFinished(JSON.stringify({
      full: '**Bissi** en mode démo.',
      turns: 1,
      profile: { total: 1 },
      model: 'demo',
    })), 600);
  }
}

function navHist(dir) {
  const inp = el('#chat-input');
  const len = S.inputHist.length;
  if (!len) return;
  S.histIdx = Math.max(-1, Math.min(len - 1, S.histIdx + dir));
  inp.value = S.histIdx >= 0 ? S.inputHist[S.histIdx] : '';
}

function interrupt() {
  if (S.bissi) S.bissi.stopGeneration();
}

// ── UI lock / unlock ───────────────────────────────────────────
function lock() {
  S.busy = true;
  setSendBtnState(true);
  el('#chat-input').disabled = true;
  const dot = el('#status-dot');
  if (dot) dot.className = 'status-dot amber';
  const hint = el('#routing-hint');
  if (hint && !hint.textContent) hint.textContent = 'Génération…';
}

function unlock() {
  S.busy = false;
  setSendBtnState(false);
  const inp = el('#chat-input');
  inp.disabled = false;
  inp.focus();
  const dot = el('#status-dot');
  if (dot) dot.className = 'status-dot teal';
  const hint = el('#routing-hint');
  if (hint && hint.textContent === 'Génération…') hint.textContent = '';
}

// ── Theme ──────────────────────────────────────────────────────
function bindTheme() {
  // The theme button keeps its SVG icon — no textContent override needed

  el('#theme-toggle').addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme') || getSystemTheme();
    const next = current === 'dark' ? 'light' : 'dark';
    setThemeMode(next);
    applyThemeLocal(next);
    if (S.bissi) S.bissi.applyTheme(next);   // sync Python side (QSS)
  });

  // Follow system preference changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
    if (getThemeMode() === 'auto') {
      applyThemeLocal(e.matches ? 'dark' : 'light');
    }
  });
}

function applyThemeLocal(name) {
  // Clear stale inline token overrides to avoid mixed-theme states.
  const root = document.documentElement;
  const toRemove = [];
  for (let i = 0; i < root.style.length; i += 1) {
    const prop = root.style[i];
    if (prop && prop.startsWith('--')) toRemove.push(prop);
  }
  toRemove.forEach((prop) => root.style.removeProperty(prop));
  document.documentElement.setAttribute('data-theme', name);
}

function applyTheme(name, _tokens) {
  const mode = getThemeMode();
  if (mode === 'light' || mode === 'dark') {
    applyThemeLocal(mode);
    return;
  }
  applyThemeLocal(getSystemTheme());
}

function getSystemTheme() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function getThemeMode() {
  const mode = localStorage.getItem(THEME_MODE_KEY);
  if (mode === 'light' || mode === 'dark' || mode === 'auto') return mode;
  const legacy = localStorage.getItem(LEGACY_THEME_KEY);
  if (legacy === 'light' || legacy === 'dark') {
    localStorage.setItem(THEME_MODE_KEY, legacy);
    return legacy;
  }
  localStorage.setItem(THEME_MODE_KEY, 'auto');
  return 'auto';
}

function setThemeMode(mode) {
  if (mode === 'light' || mode === 'dark' || mode === 'auto') {
    localStorage.setItem(THEME_MODE_KEY, mode);
  }
}

// ── Model badge & profile ──────────────────────────────────────
function setModel(model) {
  if (!model || model === 'demo') return;
  const cmb = el('#chat-model-badge');
  if (cmb) cmb.textContent = model;
}

function updateProfile(profile) {
  if (!profile) return;
}

// ── Sessions sidebar ───────────────────────────────────────────
function renderSessions(convs, autoLoad = true) {
  const list = el('#sessions-list');
  list.innerHTML = '';
  if (!S.sessionMenuBound) {
    document.addEventListener('click', () => {
      list.querySelectorAll('.session-item.menu-open').forEach((node) => node.classList.remove('menu-open'));
    });
    S.sessionMenuBound = true;
  }
  if (!convs || !convs.length) {
    S.currentConversationId = null;
    return;
  }
  let firstItem = null;
  convs.forEach((c, i) => {
    const d = document.createElement('div');
    const convId = Number(c.id);
    const isActive = S.currentConversationId != null
      ? Number(S.currentConversationId) === convId
      : i === 0;
    d.className = 'session-item' + (isActive ? ' active' : '');
    d.dataset.convId = c.id;
    const title = c.title || (c.first_message || '').slice(0, 40) || `Session ${i + 1}`;
    const date  = c.updated_at ? new Date(c.updated_at).toLocaleDateString('fr') : '';
    d.innerHTML = `
      <div class="session-main">
        <div class="session-title">${esc(title)}</div>
        <div class="session-date">${esc(date)}</div>
      </div>
      <button class="session-menu-btn" type="button" title="Actions conversation" aria-label="Actions conversation">
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="12" cy="5" r="1.8" fill="currentColor"></circle>
          <circle cx="12" cy="12" r="1.8" fill="currentColor"></circle>
          <circle cx="12" cy="19" r="1.8" fill="currentColor"></circle>
        </svg>
      </button>
      <div class="session-menu" role="menu">
        <button class="session-menu-item rename" type="button" role="menuitem" title="Renommer">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M12 20h9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"></path>
            <path d="M16.5 3.5a2.1 2.1 0 1 1 3 3L7 19l-4 1 1-4 12.5-12.5z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"></path>
          </svg>
          <span>Renommer</span>
        </button>
        <button class="session-menu-item archive" type="button" role="menuitem" title="Archiver">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <rect x="3.5" y="4.5" width="17" height="4" rx="1" stroke="currentColor" stroke-width="1.8"></rect>
            <path d="M5 8.5v9a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-9" stroke="currentColor" stroke-width="1.8"></path>
            <path d="M10 12h4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"></path>
          </svg>
          <span>Archiver</span>
        </button>
        <button class="session-menu-item delete" type="button" role="menuitem" title="Supprimer">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M4 7h16" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"></path>
            <path d="M9 7V5h6v2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path>
            <path d="M7 7l1 12h8l1-12" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"></path>
          </svg>
          <span>Supprimer</span>
        </button>
      </div>`;
    d.addEventListener('click', () => {
      list.querySelectorAll('.session-item').forEach(s => s.classList.remove('active'));
      d.classList.add('active');
      S.currentConversationId = convId;
      // Load conversation content
      S.bissi.loadConversation(convId, json => {
        try {
          const history = JSON.parse(json);
          if (history.error) {
            sysMsg(`Erreur : ${history.error}`, 'error');
            return;
          }
          const hasMessages = Array.isArray(history) && history.length > 0;
          resetMessages(!hasMessages);

          if (!hasMessages) {
            sysMsg('Conversation prête', 'dim');
            return;
          }

          // Render each message from history with markdown parsing
          history.forEach(msg => {
            if (msg.role === 'user') {
              mkUserBubble(msg.content);
            } else if (msg.role === 'assistant') {
              renderAssistantHistory(msg.content);
            }
          });
          S.bubble = null;
          sysMsg(`Conversation chargée (${history.length} messages)`, 'dim');
        } catch (e) {
          console.error('[bissi] loadConversation error:', e);
        }
      });
    });

    const menuBtn = d.querySelector('.session-menu-btn');
    menuBtn?.addEventListener('click', (event) => {
      event.stopPropagation();
      const isOpen = d.classList.contains('menu-open');
      list.querySelectorAll('.session-item.menu-open').forEach((node) => node.classList.remove('menu-open'));
      if (!isOpen) d.classList.add('menu-open');
    });

    const renameBtn = d.querySelector('.session-menu-item.rename');
    renameBtn?.addEventListener('click', (event) => {
      event.stopPropagation();
      d.classList.remove('menu-open');
      if (!S.bissi?.renameConversation) return;
      const nextTitle = window.prompt('Nouveau titre de la conversation :', title);
      if (!nextTitle) return;
      const trimmed = nextTitle.trim();
      if (!trimmed || trimmed === title) return;
      S.bissi.renameConversation(convId, trimmed, (raw) => {
        let payload = {};
        try { payload = JSON.parse(raw); } catch (_) {}
        if (!payload.success) {
          sysMsg(`Erreur : ${payload.error || 'renommage impossible'}`, 'error');
        }
      });
    });

    const archiveBtn = d.querySelector('.session-menu-item.archive');
    archiveBtn?.addEventListener('click', (event) => {
      event.stopPropagation();
      d.classList.remove('menu-open');
      if (!S.bissi?.archiveConversation) return;
      if (!window.confirm('Archiver cette conversation ?')) return;
      S.bissi.archiveConversation(convId, (raw) => {
        let payload = {};
        try { payload = JSON.parse(raw); } catch (_) {}
        if (!payload.success) {
          sysMsg(`Erreur : ${payload.error || 'archivage impossible'}`, 'error');
          return;
        }
        if (S.currentConversationId === convId) {
          S.currentConversationId = null;
          resetMessages(true);
        }
      });
    });

    const deleteBtn = d.querySelector('.session-menu-item.delete');
    deleteBtn?.addEventListener('click', (event) => {
      event.stopPropagation();
      d.classList.remove('menu-open');
      if (!S.bissi?.deleteConversation) return;
      if (!window.confirm('Supprimer définitivement cette conversation ?')) return;
      S.bissi.deleteConversation(convId, (raw) => {
        let payload = {};
        try { payload = JSON.parse(raw); } catch (_) {}
        if (!payload.success) {
          sysMsg(`Erreur : ${payload.error || 'suppression impossible'}`, 'error');
          return;
        }
        if (S.currentConversationId === convId) {
          S.currentConversationId = null;
          resetMessages(true);
        }
      });
    });

    list.appendChild(d);
    if (isActive || (!firstItem && i === 0)) firstItem = d;
  });
  
  // Auto-load the first (newest) conversation only if autoLoad flag is true
  if (autoLoad && firstItem) {
    firstItem.click();
  }
}

// ── File explorer ──────────────────────────────────────────────
function bindTabs() {
  // Support both .tab-btn (old) and .ptab (new Manus style)
  document.querySelectorAll('.tab-btn, .ptab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn, .ptab').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      const tab = btn.dataset.tab;
      const content = el(`#tab-${tab}`);
      if (content) content.classList.add('active');
      // Update panel subheader visibility
      const epath = el('#explorer-path');
      const efname = el('#editor-filename');
      if (tab === 'explorer') {
        if (epath) epath.classList.remove('hidden');
        if (efname) efname.classList.add('hidden');
      } else {
        if (epath) epath.classList.add('hidden');
        if (efname) efname.classList.remove('hidden');
      }
    });
  });
}

function loadDir(path) {
  if (!S.bissi) return;
  const target = path || '/home';
  S.bissi.listDirectory(target, raw => {
    try {
      const data = JSON.parse(raw);
      if (!data.success) return;
      S.curPath = target;
      el('#explorer-path').textContent = maskPath(target);
      buildTree(data.items, target);
    } catch { /* ignore */ }
  });
}

function buildTree(items, parent) {
  const tree = el('#file-tree');
  tree.innerHTML = '';

  if (parent && parent !== '/') {
    const up = document.createElement('div');
    up.className = 'file-item dir';
    up.innerHTML = '<span class="file-icon">↑</span><span class="file-name">..</span>';
    up.addEventListener('click', () => {
      const p = parent.replace(/\/[^/]+\/?$/, '') || '/';
      loadDir(p);
    });
    tree.appendChild(up);
  }

  items.forEach(item => {
    const d = document.createElement('div');
    d.className = `file-item ${item.is_dir ? 'dir' : 'file'}`;
    d.innerHTML = `
      <span class="file-icon">${item.is_dir ? '📁' : fileIcon(item.name)}</span>
      <span class="file-name">${esc(item.name)}</span>`;
    d.addEventListener('click', () => {
      if (item.is_dir) loadDir(item.path);
      else openFile(item.path, false);
    });
    tree.appendChild(d);
  });
}

function openFile(path, byAgent) {
  if (!S.bissi) return;
  S.bissi.readFile(path, raw => {
    try {
      const data = JSON.parse(raw);
      if (!data.success) return;

      // Switch to editor tab
      document.querySelectorAll('.tab-btn, .ptab').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
      const editorBtn = document.querySelector('[data-tab="editor"]');
      if (editorBtn) editorBtn.classList.add('active');
      el('#tab-editor').classList.add('active');

      const fname = data.name || path.split('/').pop();
      el('#editor-filename').textContent = fname;
      el('#editor-filename').classList.remove('hidden');
      el('#explorer-path').classList.add('hidden');

      const badge = el('#editor-agent-badge');
      byAgent ? badge.classList.remove('hidden') : badge.classList.add('hidden');
      el('#code-content').textContent = data.content;
    } catch { /* silent */ }
  });
}

// ── Layout (collapsible sidebar + workspace panel) ─────────────
function bindLayoutToggles() {
  const app = el('.app');
  if (!app) return;

  const sidebarCollapsed = localStorage.getItem(LAYOUT_KEYS.sidebarCollapsed) === '1';
  const panelCollapsed = localStorage.getItem(LAYOUT_KEYS.panelCollapsed) === '1';
  const storedPanelWidth = Number(localStorage.getItem(LAYOUT_KEYS.panelWidth));

  if (Number.isFinite(storedPanelWidth) && storedPanelWidth > 0) {
    setWorkspacePanelWidth(storedPanelWidth, false);
  } else {
    setWorkspacePanelWidth(WORKSPACE_DEFAULT_WIDTH, false);
  }

  setSidebarCollapsed(sidebarCollapsed);
  setWorkspaceCollapsed(panelCollapsed);

  const sbBtn = el('#sidebar-toggle');
  if (sbBtn) {
    sbBtn.addEventListener('click', () => {
      setSidebarCollapsed(!app.classList.contains('sidebar-collapsed'));
    });
  }

  document.querySelectorAll('.workspace-toggle-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      setWorkspaceCollapsed(!app.classList.contains('panel-collapsed'));
    });
  });
}

function bindWorkspaceResize() {
  const resizer = el('#workspace-resizer');
  if (!resizer) return;

  let resizing = false;

  resizer.addEventListener('pointerdown', e => {
    const app = el('.app');
    if (!app || app.classList.contains('panel-collapsed') || window.innerWidth <= 860) return;
    resizing = true;
    resizer.classList.add('resizing');
    document.body.style.cursor = 'col-resize';
    e.preventDefault();
  });

  window.addEventListener('pointermove', e => {
    if (!resizing) return;
    const width = window.innerWidth - e.clientX;
    setWorkspacePanelWidth(width, false);
  });

  window.addEventListener('pointerup', () => {
    if (!resizing) return;
    resizing = false;
    resizer.classList.remove('resizing');
    document.body.style.cursor = '';
    const panel = el('#right-panel');
    if (panel) setWorkspacePanelWidth(panel.getBoundingClientRect().width, true);
  });

  window.addEventListener('resize', () => {
    const app = el('.app');
    if (!app || app.classList.contains('panel-collapsed') || window.innerWidth <= 860) return;
    const panel = el('#right-panel');
    if (panel) setWorkspacePanelWidth(panel.getBoundingClientRect().width, false);
  });
}

function workspaceMaxWidth() {
  const app = el('.app');
  const sidebarVisible = app && !app.classList.contains('sidebar-collapsed') && window.innerWidth > 600;
  const reservedForMain = sidebarVisible ? 560 : 420;
  return Math.max(WORKSPACE_MIN_WIDTH, window.innerWidth - reservedForMain);
}

function setWorkspacePanelWidth(width, persist) {
  const raw = Number(width);
  const base = Number.isFinite(raw) && raw > 0 ? raw : WORKSPACE_DEFAULT_WIDTH;
  const clamped = Math.max(WORKSPACE_MIN_WIDTH, Math.min(Math.round(base), workspaceMaxWidth()));
  document.documentElement.style.setProperty('--panel-width', `${clamped}px`);
  if (persist) {
    localStorage.setItem(LAYOUT_KEYS.panelWidth, String(clamped));
  }
}

function setSidebarCollapsed(collapsed) {
  const app = el('.app');
  if (!app) return;
  app.classList.toggle('sidebar-collapsed', collapsed);
  localStorage.setItem(LAYOUT_KEYS.sidebarCollapsed, collapsed ? '1' : '0');
  updateLayoutToggleLabels();
}

function setWorkspaceCollapsed(collapsed) {
  const app = el('.app');
  if (!app) return;
  app.classList.toggle('panel-collapsed', collapsed);
  localStorage.setItem(LAYOUT_KEYS.panelCollapsed, collapsed ? '1' : '0');
  if (!collapsed) {
    const storedPanelWidth = Number(localStorage.getItem(LAYOUT_KEYS.panelWidth));
    setWorkspacePanelWidth(storedPanelWidth, false);
  }
  updateLayoutToggleLabels();
}

function updateLayoutToggleLabels() {
  const app = el('.app');
  if (!app) return;
  const isSidebarCollapsed = app.classList.contains('sidebar-collapsed');
  const isPanelCollapsed = app.classList.contains('panel-collapsed');

  const sbBtn = el('#sidebar-toggle');
  if (sbBtn) {
    const title = isSidebarCollapsed ? 'Show sidebar' : 'Collapse sidebar';
    sbBtn.title = title;
    sbBtn.setAttribute('aria-label', title);
  }

  document.querySelectorAll('.workspace-toggle-btn').forEach(btn => {
    const title = isPanelCollapsed ? 'Show workspace' : 'Collapse workspace';
    btn.title = title;
    btn.setAttribute('aria-label', title);
  });
}

function toggleSidebar() {
  const app = el('.app');
  if (!app) return;
  setSidebarCollapsed(!app.classList.contains('sidebar-collapsed'));
}
function openSidebar() {
  setSidebarCollapsed(false);
}
function closeSidebar() {
  setSidebarCollapsed(true);
}

// ── Utilities ──────────────────────────────────────────────────
const el = s => document.querySelector(s);

function maskPath(path) {
  const p = String(path || '');
  if (!p) return '~';
  if (p === '/home' || p === '/Users') return '~';
  return p.replace(/^\/(home|Users)\/[^/]+/, '~');
}

function esc(str) {
  if (window.BissiFrontend?.esc) return window.BissiFrontend.esc(str);
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function scrollEnd() {
  const c = el('#messages-container') || el('.chat-area');
  if (c) c.scrollTop = c.scrollHeight;
}

function toolIcon(name) {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">${toolIconSvg(name)}</svg>`;
}

function toolIconSvg(name) {
  const paths = {
    read_file:      '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>',
    read_text_file: '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>',
    write_file:     '<path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/>',
    edit_file:      '<path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>',
    list_directory: '<path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>',
    search_files:   '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/>',
    python_runner:  '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>',
    safe_operator:  '<circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>',
    read_excel:     '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18"/>',
    read_word:      '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>',
    read_pdf:       '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M9 13h6M9 17h4"/>',
    web_search:     '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 010 20"/>',
  };
  return paths[name] || '<circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4"/>';
}

function fileIcon(name) {
  const ext = name.split('.').pop().toLowerCase();
  const map = {
    py: '🐍', js: '📜', ts: '📜', html: '🌐', css: '🎨',
    json: '📋', md: '📝', txt: '📄', sh: '⚙️',
    xlsx: '📊', xls: '📊', csv: '📊',
    docx: '📝', doc: '📝',
    pptx: '📑', ppt: '📑',
    pdf: '📕',
    png: '🖼️', jpg: '🖼️', jpeg: '🖼️', gif: '🖼️', svg: '🖼️',
    zip: '📦', tar: '📦', gz: '📦',
  };
  return map[ext] || '📄';
}
