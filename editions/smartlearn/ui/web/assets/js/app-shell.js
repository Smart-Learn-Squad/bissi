(function () {
  function overlayEl() {
    return document.getElementById('overlay');
  }

  function sidebarEl() {
    return document.getElementById('sidebar');
  }

  function getInitials(user) {
    if (!user) return 'E';
    if (user.initiales && user.initiales.trim()) return user.initiales.trim();
    const first = (user.prenom || 'E').charAt(0);
    const last = (user.nom || '').charAt(0);
    return (first + last).toUpperCase() || 'E';
  }

  function setSidebarUser(user) {
    const avatar = document.getElementById('sidebarAvatar');
    const name = document.getElementById('sidebarName');
    const role = document.getElementById('sidebarRole');
    if (avatar) avatar.textContent = getInitials(user);
    if (name) name.textContent = (user && user.prenom) || 'Étudiant';
    if (role) role.textContent = (user && (user.filiere || user.niveau)) || 'SmartLearn';
  }

  function readStoredUser() {
    try {
      const raw = localStorage.getItem('sl_user');
      if (!raw) return null;
      return JSON.parse(raw);
    } catch (e) {
      return null;
    }
  }

  function loadSidebarUserFromStorage() {
    setSidebarUser(readStoredUser() || {});
  }

  const TIMER_STATE_KEY = 'sl_timer_state_v1';
  const TIMER_MODE_LABELS = {
    focus: 'Focus',
    short: 'Courte pause',
    long: 'Longue pause'
  };

  function clampInt(value, min, max, fallback) {
    const n = Number.parseInt(String(value), 10);
    if (!Number.isFinite(n)) return fallback;
    return Math.min(max, Math.max(min, n));
  }

  function normalizeTimerMode(mode) {
    return Object.prototype.hasOwnProperty.call(TIMER_MODE_LABELS, mode) ? mode : 'focus';
  }

  function timerDefaultsForMode(mode) {
    const m = normalizeTimerMode(mode);
    if (m === 'short') return 5;
    if (m === 'long') return 15;
    return 25;
  }

  function sanitizeTimerState(raw) {
    if (!raw || typeof raw !== 'object') return null;
    const mode = normalizeTimerMode(String(raw.mode || 'focus'));
    const totalSecs = clampInt(raw.totalSecs, 1, 10800, timerDefaultsForMode(mode) * 60);
    const remaining = clampInt(raw.remaining, 0, totalSecs, totalSecs);
    const session = clampInt(raw.session, 0, 3, 0);
    const maxSessions = clampInt(raw.maxSessions, 1, 8, 4);
    const running = Boolean(raw.running);
    const startedAtMs = Number.isFinite(Number(raw.startedAtMs)) ? Number(raw.startedAtMs) : null;
    const endAtMs = Number.isFinite(Number(raw.endAtMs)) ? Number(raw.endAtMs) : null;
    const runInitialRemaining = clampInt(raw.runInitialRemaining, 0, totalSecs, remaining);
    const updatedAtMs = Number.isFinite(Number(raw.updatedAtMs)) ? Number(raw.updatedAtMs) : Date.now();
    const source = typeof raw.source === 'string' ? raw.source : 'manual';

    return {
      mode,
      totalSecs,
      remaining,
      running,
      session,
      maxSessions,
      isBreak: mode !== 'focus',
      startedAtMs: running ? startedAtMs : null,
      endAtMs: running ? endAtMs : null,
      runInitialRemaining: running ? runInitialRemaining : null,
      updatedAtMs,
      source
    };
  }

  function dispatchTimerState(state) {
    try {
      window.dispatchEvent(new CustomEvent('sl:timer-state-changed', { detail: state }));
    } catch (e) {
      // noop
    }
  }

  function readTimerState() {
    try {
      const raw = localStorage.getItem(TIMER_STATE_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      return sanitizeTimerState(parsed);
    } catch (e) {
      return null;
    }
  }

  function writeTimerState(nextState) {
    const sanitized = sanitizeTimerState(nextState);
    if (!sanitized) return null;
    localStorage.setItem(TIMER_STATE_KEY, JSON.stringify(sanitized));
    dispatchTimerState(sanitized);
    return sanitized;
  }

  function startStudySession(options = {}) {
    const mode = normalizeTimerMode(String(options.mode || 'focus'));
    const defaultMinutes = timerDefaultsForMode(mode);
    const minutes = clampInt(options.minutes, 1, 180, defaultMinutes);
    const totalSecs = minutes * 60;
    const now = Date.now();
    const previous = readTimerState();

    const nextState = {
      mode,
      totalSecs,
      remaining: totalSecs,
      running: true,
      session: clampInt(previous?.session, 0, 3, 0),
      maxSessions: clampInt(previous?.maxSessions, 1, 8, 4),
      isBreak: mode !== 'focus',
      startedAtMs: now,
      endAtMs: now + totalSecs * 1000,
      runInitialRemaining: totalSecs,
      updatedAtMs: now,
      source: typeof options.source === 'string' ? options.source : 'manual'
    };

    return writeTimerState(nextState);
  }

  function toggleSidebar() {
    const sb = sidebarEl();
    if (sb) sb.classList.toggle('collapsed');
  }

  function openSidebar() {
    const sb = sidebarEl();
    const ov = overlayEl();
    if (sb) sb.classList.add('mobile-open');
    if (ov) ov.classList.add('show');
    document.documentElement.classList.add('sl-lock-scroll');
  }

  function closeSidebar() {
    const sb = sidebarEl();
    const ov = overlayEl();
    if (sb) sb.classList.remove('mobile-open');
    if (ov) ov.classList.remove('show');
    document.documentElement.classList.remove('sl-lock-scroll');
  }

  function isMobileViewport() {
    return window.matchMedia('(max-width: 900px)').matches;
  }

  function initShellBindings() {
    // Safety: ensure overlay never blocks clicks after refresh/state glitches.
    closeSidebar();
    const ov = overlayEl();
    if (ov) {
      ov.classList.remove('show');
      ov.addEventListener('click', closeSidebar);
    }

    const sb = sidebarEl();
    if (sb) {
      sb.querySelectorAll('.sb-nav-link').forEach((link) => {
        link.addEventListener('click', () => {
          if (isMobileViewport()) closeSidebar();
        });
      });
    }

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeSidebar();
    });

    window.addEventListener('resize', () => {
      if (!isMobileViewport()) closeSidebar();
    });
  }

  window.toggleSidebar = toggleSidebar;
  window.openSidebar = openSidebar;
  window.closeSidebar = closeSidebar;
  window.SmartLearnShell = {
    closeSidebar,
    loadSidebarUserFromStorage,
    openSidebar,
    readStoredUser,
    readTimerState,
    setSidebarUser,
    startStudySession,
    toggleSidebar
    ,
    writeTimerState
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initShellBindings);
  } else {
    initShellBindings();
  }

  // ── FLOATING TIMER WIDGET (toutes pages sauf home) ──
  function recordCompletedSession(state) {
    if (!state || state.mode !== 'focus') return;
    try {
      const sessions = JSON.parse(localStorage.getItem('sl_completed_sessions') || '[]');
      sessions.push({ completedAt: new Date().toISOString(), durationMin: Math.floor((state.totalSecs || 1500) / 60) });
      if (sessions.length > 100) sessions.splice(0, sessions.length - 100);
      localStorage.setItem('sl_completed_sessions', JSON.stringify(sessions));
    } catch (e) {}
  }

  function initFloatingTimer() {
    const path = window.location.pathname;
    if (path.endsWith('home.html') || path.endsWith('home.php') || path === '/home') return;

    const style = document.createElement('style');
    style.textContent = `
      #sl-timer-pill {
        position: fixed; bottom: 24px; right: 24px; z-index: 999;
        display: none; align-items: center; gap: 8px;
        background: var(--nav-bg, rgba(10,10,10,0.9));
        backdrop-filter: blur(14px);
        border: 1px solid rgba(96,165,250,0.2);
        border-radius: 40px; padding: 9px 18px;
        cursor: pointer; font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 13px; font-weight: 500; color: var(--text, #e8f0fe);
        box-shadow: 0 4px 24px rgba(0,0,0,0.35);
        transition: transform 0.2s, box-shadow 0.2s;
        user-select: none; text-decoration: none;
      }
      #sl-timer-pill:hover { transform: translateY(-2px); box-shadow: 0 6px 28px rgba(59,130,246,0.3); }
      #sl-timer-pill.sl-running { border-color: rgba(59,130,246,0.5); }
      #sl-timer-pill.sl-break   { border-color: rgba(16,185,129,0.5); }
      #sl-pill-time { font-family: 'Fira Code', monospace; font-size: 15px; color: #60a5fa; letter-spacing: 0.04em; }
      #sl-pill-label { font-size: 11px; opacity: 0.55; letter-spacing: 0.06em; }
    `;
    document.head.appendChild(style);

    const pill = document.createElement('a');
    pill.id = 'sl-timer-pill';
    pill.href = 'home.html';
    pill.title = 'Timer Focus actif — cliquer pour ouvrir';
    pill.innerHTML = `<span id="sl-pill-icon">⏱</span><span id="sl-pill-time">--:--</span><span id="sl-pill-label">Focus</span>`;
    document.body.appendChild(pill);

    function pad(n) { return String(Math.floor(n)).padStart(2, '0'); }

    function updatePill() {
      const state = readTimerState();
      if (!state || !state.running) { pill.style.display = 'none'; return; }

      const remaining = state.endAtMs
        ? Math.max(0, Math.floor((state.endAtMs - Date.now()) / 1000))
        : (state.remaining || 0);

      if (remaining <= 0) {
        pill.style.display = 'none';
        recordCompletedSession(state);
        return;
      }

      const mins = Math.floor(remaining / 60);
      const secs = remaining % 60;
      const isFocus = state.mode === 'focus';
      document.getElementById('sl-pill-icon').textContent  = isFocus ? '⏱' : '☕';
      document.getElementById('sl-pill-time').textContent  = `${pad(mins)}:${pad(secs)}`;
      document.getElementById('sl-pill-label').textContent = isFocus ? 'Focus' : state.mode === 'short' ? 'Pause' : 'Longue pause';
      pill.className = isFocus ? 'sl-running' : 'sl-break';
      pill.style.display = 'flex';
    }

    updatePill();
    setInterval(updatePill, 1000);
    window.addEventListener('sl:timer-state-changed', updatePill);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFloatingTimer);
  } else {
    initFloatingTimer();
  }

  window.SmartLearnShell.recordCompletedSession = recordCompletedSession;

  // register service worker for PWA support
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
      navigator.serviceWorker.register('/service-worker.js').then(function(registration) {
        console.log('Service worker enregistré avec succès:', registration.scope);
      }).catch(function(err) {
        console.log('Échec de l\'enregistrement du service worker:', err);
      });
    });
  }
})();
