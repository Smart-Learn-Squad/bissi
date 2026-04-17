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
  sessionStart: Date.now(),
  curPath:      null,
  rafPending:   false,  // requestAnimationFrame scheduled for stream render
};

// ── Bootstrap ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  bindInput();
  bindTheme();
  bindTabs();
  startTimer();
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
    el('#status-dot').className = 'status-dot amber';
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
      renderSessions(convs);
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
      hint.style.color = model.includes('e4b') ? 'var(--purple)' : 'var(--teal)';
      const statusModel = el('#status-model');
      if (statusModel) statusModel.textContent = `Ollama · ${model}`;
      
      const badge = el('#model-badge');
      if (badge) {
        badge.textContent = `● ${model} · en ligne`;
        badge.className = model.includes('e4b') ? 'badge badge-purple' : 'badge badge-teal';
      }
    } catch { /* malformed, ignore */ }
  }
}

function onFinished(json) {
  try {
    const data = JSON.parse(json);
    // Finalize streaming bubble: re-render with proper markdown
    if (S.bubble) {
      const content = S.bubble.querySelector('.bubble-content');
      if (content) {
        content.innerHTML = renderMd(S.bubble._raw || '');
        hlCode(content);
        renderMath(content);
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
  try { renderSessions(JSON.parse(json)); } catch { /* noop */ }
}

function onThemeChanged(name) {
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
  const model = (el('#chat-model-badge') || {}).textContent || 'bissi';
  const isHeavy = model.includes('e4b');
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
        <span class="msg-model-tag${isHeavy ? ' heavy' : ''}">${esc(model)}</span>
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

function renderBlock(text) {
  const out = [];
  let inUl = false, inOl = false;

  for (const line of text.split('\n')) {
    const isUl = /^[-*+] /.test(line);
    const isOl = /^\d+\. /.test(line);

    if (!isUl && inUl) { out.push('</ul>'); inUl = false; }
    if (!isOl && inOl) { out.push('</ol>'); inOl = false; }

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
}

// Render LaTeX math with KaTeX (fires after markdown is in the DOM)
function renderMath(container) {
  if (!window._katexReady || typeof renderMathInElement === 'undefined') return;
  try {
    renderMathInElement(container, {
      delimiters: [
        { left: '$$',  right: '$$',  display: true  },
        { left: '$',   right: '$',   display: false },
        { left: '\\[', right: '\\]', display: true  },
        { left: '\\(', right: '\\)', display: false },
      ],
      throwOnError: false,
    });
  } catch { /* ignore parse errors */ }
}

// ── Input handling ─────────────────────────────────────────────
function bindInput() {
  const inp = el('#chat-input');
  el('#send-btn').addEventListener('click', submit);

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
  el('#send-btn').disabled = true;
  el('#chat-input').disabled = true;
  el('#status-dot').className = 'status-dot amber';
}

function unlock() {
  S.busy = false;
  el('#send-btn').disabled = false;
  const inp = el('#chat-input');
  inp.disabled = false;
  inp.focus();
  el('#status-dot').className = 'status-dot teal';
}

// ── Theme ──────────────────────────────────────────────────────
function bindTheme() {
  // The theme button keeps its SVG icon — no textContent override needed

  el('#theme-toggle').addEventListener('click', () => {
    const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    applyThemeLocal(next);
    if (S.bissi) S.bissi.applyTheme(next);   // sync Python side (QSS)
  });

  // Follow system preference changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
    if (!localStorage.getItem('bissi-theme')) {
      applyThemeLocal(e.matches ? 'dark' : 'light');
    }
  });
}

function applyThemeLocal(name) {
  document.documentElement.setAttribute('data-theme', name);
  localStorage.setItem('bissi-theme', name);
}

function applyTheme(name, tokens) {
  document.documentElement.setAttribute('data-theme', name);
  el('#theme-toggle').textContent = name === 'dark' ? '☀' : '☾';
  if (tokens && typeof tokens === 'object') {
    const root = document.documentElement;
    for (const [k, v] of Object.entries(tokens)) {
      root.style.setProperty(`--${k.replace(/_/g, '-')}`, v);
    }
  }
}

// ── Model badge & profile ──────────────────────────────────────
function setModel(model) {
  if (!model || model === 'demo') return;
  const mb = el('#model-badge');
  if (mb) mb.textContent = `● ${model}`;
  const cmb = el('#chat-model-badge');
  if (cmb) cmb.textContent = model;
  const sm = el('#status-model');
  if (sm) sm.textContent = model;
}

function updateProfile(profile) {
  if (!profile) return;
  const total = profile.total || 0;
  const mc = el('#memory-count');
  if (mc) mc.textContent = total;
  const sm = el('#status-memory');
  if (sm) sm.textContent = `${total} souvenirs`;
}

// ── Sessions sidebar ───────────────────────────────────────────
function renderSessions(convs) {
  const list = el('#sessions-list');
  list.innerHTML = '';
  if (!convs || !convs.length) {
    list.innerHTML = '<div class="session-empty">Aucune session</div>';
    return;
  }
  let firstItem = null;
  convs.forEach((c, i) => {
    const d = document.createElement('div');
    d.className = 'session-item' + (i === 0 ? ' active' : '');
    d.dataset.convId = c.id;
    const title = c.title || (c.first_message || '').slice(0, 40) || `Session ${i + 1}`;
    const date  = c.updated_at ? new Date(c.updated_at).toLocaleDateString('fr') : '';
    d.innerHTML = `
      <div class="session-title">${esc(title)}</div>
      <div class="session-date">${esc(date)}</div>`;
    d.addEventListener('click', () => {
      list.querySelectorAll('.session-item').forEach(s => s.classList.remove('active'));
      d.classList.add('active');
      // Load conversation content
      const convId = parseInt(d.dataset.convId);
      S.bissi.loadConversation(convId, json => {
        try {
          const history = JSON.parse(json);
          if (history.error) {
            sysMsg(`Erreur: ${history.error}`, 'error');
            return;
          }
          // Clear messages and reload them
          const messagesEl = el('#messages');
          if (messagesEl) messagesEl.innerHTML = '';
          
          const welcomeEl = el('#welcome-screen');
          if (welcomeEl) welcomeEl.style.display = 'none';
          
          S.bubble = null;
          // Render each message from history
          history.forEach(msg => {
            if (msg.role === 'user') {
              const b = mkUserBubble(msg.content);
            } else if (msg.role === 'assistant') {
              S.bubble = mkAssistantBubble();
              S.bubble.textContent = msg.content;
            }
          });
          sysMsg(`Conversation chargée (${history.length} messages)`, 'dim');
        } catch (e) {
          console.error('[bissi] loadConversation error:', e);
        }
      });
    });
    list.appendChild(d);
    if (i === 0) firstItem = d;
  });
  
  // Auto-load the first (newest) conversation
  if (firstItem) {
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
      el('#explorer-path').textContent = target;
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

// ── Sidebar (collapsible, SmartLearn-style) ────────────────────
function toggleSidebar() {
  const sb = document.getElementById('sidebar');
  sb.classList.toggle('collapsed');
}
function openSidebar() {
  const sb = document.getElementById('sidebar');
  const ov = document.getElementById('overlay');
  sb.classList.add('mobile-open');
  if (ov) { ov.style.display = 'block'; }
}
function closeSidebar() {
  const sb = document.getElementById('sidebar');
  const ov = document.getElementById('overlay');
  sb.classList.remove('mobile-open');
  if (ov) { ov.style.display = 'none'; }
}

// ── Session timer ──────────────────────────────────────────────
function startTimer() {
  setInterval(() => {
    const ms = Date.now() - S.sessionStart;
    const hh = String(Math.floor(ms / 3600000)).padStart(2, '0');
    const mm = String(Math.floor((ms % 3600000) / 60000)).padStart(2, '0');
    const ss = String(Math.floor((ms % 60000) / 1000)).padStart(2, '0');
    el('#status-session').textContent = `Session · ${hh}:${mm}:${ss}`;
  }, 1000);
}

// ── Utilities ──────────────────────────────────────────────────
const el = s => document.querySelector(s);

function esc(str) {
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
