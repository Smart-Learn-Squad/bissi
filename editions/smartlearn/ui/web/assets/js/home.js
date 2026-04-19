/* ══════════════════════════════════════════
     REAL DATA — localStorage only
  ══════════════════════════════════════════ */

  const MOIS = ['Jan','Fév','Mar','Avr','Mai','Jun','Jul','Aoû','Sep','Oct','Nov','Déc'];
  const PROGRESS_KEY = "bissi_smartlearn_progress";

  function normalizeProgress(parsed) {
    return {
      chapitres: Array.isArray(parsed?.chapitres) ? parsed.chapitres.map((c) => ({
        titre: String(c?.titre || c?.nom || "Chapitre"),
        score: Math.max(0, Math.min(100, Number(c?.score || 0))),
        date: c?.date || (c?.timestamp ? new Date(c.timestamp).toISOString() : new Date().toISOString()),
      })) : [],
      quizCompleted: Math.max(0, Number(parsed?.quizCompleted || 0)),
      totalTemps: Math.max(0, Number(parsed?.totalTemps || 0)),
    };
  }

  function chargerDonnees() {
    try {
      const s = localStorage.getItem(PROGRESS_KEY);
      if (s) return normalizeProgress(JSON.parse(s));
    } catch (_) {}

    // Legacy migration from old storage shape.
    try {
      const old = localStorage.getItem('sl_progression');
      if (old) {
        const parsed = JSON.parse(old);
        const migrated = normalizeProgress({
          chapitres: parsed?.chapitres || [],
          quizCompleted: Array.isArray(parsed?.chapitres)
            ? parsed.chapitres.reduce((a, c) => a + Number(c?.quiz || 0), 0)
            : 0,
          totalTemps: Number(localStorage.getItem("sl_temps_etude") || 0),
        });
        localStorage.setItem(PROGRESS_KEY, JSON.stringify(migrated));
        return migrated;
      }
    } catch (_) {}

    return { chapitres: [], quizCompleted: 0, totalTemps: 0 };
  }

  function sauvegarder(data) {
    localStorage.setItem(PROGRESS_KEY, JSON.stringify(normalizeProgress(data)));
  }

  function classeScore(s) {
    return s >= 80 ? 'high' : s >= 60 ? 'medium' : 'low';
  }

  /* Generates a dynamic schedule based on actual scores */
  function genererPlanning(chapitres) {
    if (chapitres.length === 0) return [];
    const sorted = [...chapitres].sort((a, b) => a.score - b.score);
    const planning = [];
    const today = new Date();

    sorted.slice(0, 5).forEach((ch, i) => {
      const d = new Date(today);
      d.setDate(today.getDate() + i + (ch.score >= 80 ? 3 : 1));
      let urgency, duration;
      if (ch.score < 50)      { urgency = 'urgent'; duration = '25 min · Focus intensif'; }
      else if (ch.score < 70) { urgency = 'normal'; duration = '25 min · Révision active'; }
      else                    { urgency = 'ok';     duration = '15 min · Maintien'; }
      planning.push({
        jour: String(d.getDate()).padStart(2, '0'),
        mois: MOIS[d.getMonth()],
        titre: ch.titre,
        duree: duration,
        urgence: urgency,
      });
    });
    return planning;
  }

  /* Formats relative date for a quiz */
  function dateRelative(ts) {
    if (!ts) return '';
    const base = new Date(ts).getTime();
    if (!Number.isFinite(base)) return "";
    const diff = Math.floor((Date.now() - base) / 86400000);
    if (diff === 0) return "Aujourd'hui";
    if (diff === 1) return 'Hier';
    if (diff < 7)  return `Il y a ${diff}j`;
    return new Date(ts).toLocaleDateString('fr-FR', { day:'numeric', month:'short' });
  }

  /* ── RENDER ── */
  function renderChapitres(data) {
    const liste = document.getElementById('chaptersList');
    liste.innerHTML = '';
    document.getElementById('chapterBadge').textContent = data.chapitres.length + ' chapitre' + (data.chapitres.length > 1 ? 's' : '');

    if (data.chapitres.length === 0) {
      liste.innerHTML = `
        <div style="text-align:center;padding:40px 16px;color:var(--text-dim)">
          <div style="font-size:36px;margin-bottom:12px">📚</div>
          <div style="font-size:14px;font-weight:500;color:var(--text);margin-bottom:6px">Aucune activité encore</div>
          <div style="font-size:12px">Complète ton premier quiz sur <a href="index.html" style="color:var(--blue)">SmartLearn Chat</a> pour voir ta progression ici.</div>
        </div>`;
      return;
    }

    data.chapitres.forEach((ch, i) => {
      const cls = classeScore(ch.score);
      const dateAff = dateRelative(ch.timestamp);
      const item = document.createElement('div');
      item.className = 'chapter-item';
      item.innerHTML = `
        <div class="chapter-top">
          <div class="chapter-name">${esc(ch.titre)}</div>
          <div class="chapter-score score-${cls}">${ch.score}%</div>
        </div>
        <div class="prog-bar-wrap">
          <div class="prog-bar ${cls}" id="bar${i}" style="width:0%"></div>
        </div>
        <div class="chapter-meta">
          <span class="chapter-tag">Chapitre</span>
          <span>${dateAff ? dateAff : 'Récent'}</span>
        </div>`;
      liste.appendChild(item);
      setTimeout(() => {
        const bar = document.getElementById('bar' + i);
        if (bar) bar.style.width = ch.score + '%';
      }, 100 + i * 70);
    });
  }

  function renderPointsFaibles(data) {
    const liste = document.getElementById('weakList');
    if (data.chapitres.length === 0) {
      liste.innerHTML = `<div style="text-align:center;padding:16px;color:var(--text-faint);font-size:12px">Lance un quiz pour identifier tes points faibles.</div>`;
      return;
    }
    const faibles = data.chapitres.filter(ch => ch.score < 70).sort((a, b) => a.score - b.score);
    if (faibles.length === 0) {
      liste.innerHTML = `<div style="text-align:center;padding:16px;color:var(--green);font-size:13px">✓ Aucun point faible — continue ainsi !</div>`;
      return;
    }
    liste.innerHTML = '';
    faibles.forEach(ch => {
      const item = document.createElement('div');
      item.className = 'weak-item';
      item.innerHTML = `<div class="weak-dot"></div><div class="weak-name">${esc(ch.titre)}</div><div class="weak-score">${ch.score}%</div>`;
      liste.appendChild(item);
    });
  }

  function renderPlanning(data) {
    const liste = document.getElementById('planList');
    const planning = genererPlanning(data.chapitres);
    if (planning.length === 0) {
      liste.innerHTML = `<div style="text-align:center;padding:16px;color:var(--text-faint);font-size:12px">Le planning se génère automatiquement après tes premiers quiz.</div>`;
      return;
    }
    liste.innerHTML = '';
    const labels = { urgent:'Prioritaire', normal:'Planifié', ok:'Maintien' };
    planning.forEach(p => {
      const item = document.createElement('div');
      item.className = 'plan-item';
      item.innerHTML = `
        <div>
          <div class="plan-date">${p.jour}</div>
          <div class="plan-date-lbl">${p.mois}</div>
        </div>
        <div class="plan-info">
          <div class="plan-name">${esc(p.titre)}</div>
          <div class="plan-duration">${p.duree}</div>
        </div>
        <span class="plan-chip ${p.urgence}">${labels[p.urgence]}</span>`;
      liste.appendChild(item);
    });
  }

  function renderAnneau(data) {
    let moyenne = 0, label = 'Aucune donnée', sub = 'Lance ton premier quiz !';
    if (data.chapitres.length > 0) {
      const scores = data.chapitres.map(c => c.score);
      moyenne = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
      if (moyenne >= 80)      { label = 'Niveau avancé';         sub = 'Excellent travail — continue ainsi !'; }
      else if (moyenne >= 65) { label = 'Niveau intermédiaire';  sub = 'Tu progresses très bien !'; }
      else if (moyenne >= 50) { label = 'En cours';              sub = 'Quelques chapitres encore à revoir.'; }
      else                    { label = 'Débutant';              sub = 'Priorise la révision des bases.'; }
    }
    document.getElementById('ringPct').textContent = moyenne ? moyenne + '%' : '—';
    document.getElementById('statMoyenne').innerHTML = moyenne ? moyenne + '<span style="font-size:18px">%</span>' : '—';
    document.querySelector('.ring-info-title').textContent = label;
    document.querySelector('.ring-info-sub').textContent = sub;
    const circ = 2 * Math.PI * 60;
    const offset = circ - (moyenne / 100) * circ;
    setTimeout(() => {
      const ring = document.getElementById('ringFill');
      if (ring) { ring.style.strokeDasharray = circ; ring.style.strokeDashoffset = offset; }
    }, 300);
  }

  function renderTemps(totalSecs = null) {
    const fallback = Math.max(
      Number(localStorage.getItem("sl_temps_etude") || 0),
      Number(chargerDonnees().totalTemps || 0),
    );
    const secs = Math.max(0, Number(totalSecs == null ? fallback : totalSecs));
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    let aff;
    if (secs === 0)       aff = '—';
    else if (h === 0)     aff = m + '<span style="font-size:18px">min</span>';
    else if (m === 0)     aff = h + '<span style="font-size:18px">h</span>';
    else                  aff = h + '<span style="font-size:18px">h</span>' + m + '<span style="font-size:14px">min</span>';
    document.getElementById('statTemps').innerHTML = aff;
  }

  function renderStats(data) {
    document.getElementById('statChapitres').textContent = data.chapitres.length;
    document.getElementById('statQuiz').textContent = Number(data.quizCompleted || 0);
    renderTemps(Number(data.totalTemps || 0));
  }

  function resetDonnees() {
    if (confirm('Réinitialiser toutes les données de progression ?')) {
      localStorage.removeItem(PROGRESS_KEY);
      localStorage.removeItem('sl_progression');
      localStorage.removeItem('sl_temps_etude');
      init();
    }
  }

  function esc(s) {
    return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function init() {
    const data = chargerDonnees();
    renderStats(data);
    renderChapitres(data);
    renderPointsFaibles(data);
    renderPlanning(data);
    renderAnneau(data);
  }

  window.addEventListener('DOMContentLoaded', init);

  /* ── Public API called from model.js ── */
  window.ajouterResultat = function(nomChapitre, matiere, score) {
    const data = chargerDonnees();
    const titre = String(nomChapitre || "Chapitre");
    const existant = data.chapitres.find(c => c.titre.toLowerCase() === titre.toLowerCase());
    if (existant) {
      existant.score = Math.round((Number(existant.score || 0) + Number(score || 0)) / 2);
      existant.date = new Date().toISOString();
    } else {
      data.chapitres.unshift({
        titre,
        score: Math.max(0, Math.min(100, Number(score || 0))),
        date: new Date().toISOString(),
      });
    }
    data.quizCompleted = Number(data.quizCompleted || 0) + 1;
    data.totalTemps = Math.max(
      Number(data.totalTemps || 0),
      Number(localStorage.getItem("sl_temps_etude") || 0),
    );
    sauvegarder(data);
  };

  /* ══════════════════════════════════════════
     POMODORO TIMER
  ══════════════════════════════════════════ */
  const CIRC = 2 * Math.PI * 65; // radius 65

  let timerState = {
    mode:        'focus',       // 'focus' | 'short' | 'long'
    totalSecs:   25 * 60,
    remaining:   25 * 60,
    running:     false,
    session:     0,             // 0–3 (4 pomodoros)
    maxSessions: 4,
    interval:    null,
    isBreak:     false,
  };

  function setTimerMode(mode, minutes, label) {
    timerStop();
    timerState.mode      = mode;
    timerState.totalSecs = minutes * 60;
    timerState.remaining = minutes * 60;
    timerState.isBreak   = mode !== 'focus';

    // Badge header
    document.getElementById('timerBadge').textContent = label;
    document.getElementById('timerLabelInner').textContent = label;

    // Active mode buttons
    ['focus','short','long'].forEach(m => {
      document.getElementById('modeBtn-' + m).classList.toggle('active', m === mode);
    });

    // Ring colour
    const prog = document.getElementById('timerProgress');
    prog.classList.toggle('break', timerState.isBreak);

    timerRenderDisplay();
    timerRenderRing();
  }

  function timerToggle() {
    timerState.running ? timerStop() : timerStart();
  }

  function timerStart() {
    if (timerState.remaining === 0) return;
    timerState.running = true;
    document.getElementById('timerPlayBtn').textContent = '⏸';
    timerState.interval = setInterval(() => {
      timerState.remaining--;
      timerRenderDisplay();
      timerRenderRing();
      if (timerState.remaining <= 0) {
        timerComplete();
      }
    }, 1000);
  }

  function timerStop() {
    // Save elapsed time if a focus session was running
      if (timerState.running && !timerState.isBreak) {
        const elapsed = timerState.totalSecs - timerState.remaining;
        if (elapsed > 5) { // ignore accidental stops < 5s
          const current = parseInt(localStorage.getItem('sl_temps_etude') || '0');
          const total = current + elapsed;
          localStorage.setItem('sl_temps_etude', total);
          const data = chargerDonnees();
          data.totalTemps = Math.max(Number(data.totalTemps || 0), total);
          sauvegarder(data);
          renderTemps(data.totalTemps); // update display immediately
        }
      }
    timerState.running = false;
    clearInterval(timerState.interval);
    timerState.interval = null;
    document.getElementById('timerPlayBtn').textContent = '▶';
  }

  function timerReset() {
    timerStop();
    timerState.remaining = timerState.totalSecs;
    timerRenderDisplay();
    timerRenderRing();
  }

  function timerSkip() {
    timerStop();
    timerComplete(true);
  }

  function timerComplete(skipped) {
    timerStop();
    const wasBreak = timerState.isBreak;

    if (!wasBreak) {
      // End of a focus session: advance session count
      timerState.session = Math.min(timerState.session + 1, timerState.maxSessions);
      timerRenderDots();
      if (!skipped) flash('🎉 Focus terminé ! Prends une pause.');
      // Automatically switch to short break
      const isLong = timerState.session >= timerState.maxSessions;
      if (isLong) {
        flash('🏆 4 sessions ! Longue pause méritée.');
        timerState.session = 0;
        timerRenderDots();
        setTimerMode('long', 15, 'Longue pause');
      } else {
        setTimerMode('short', 5, 'Pause courte');
      }
    } else {
      // End of a break: back to focus
      if (!skipped) flash('▶ Pause terminée. C\'est parti !');
      setTimerMode('focus', 25, 'Focus');
    }
  }

  function timerRenderDisplay() {
    const m = Math.floor(timerState.remaining / 60);
    const s = timerState.remaining % 60;
    document.getElementById('timerDisplay').textContent =
      String(m).padStart(2,'0') + ':' + String(s).padStart(2,'0');
  }

  function timerRenderRing() {
    const ratio = timerState.remaining / timerState.totalSecs;
    const offset = CIRC * (1 - ratio);
    document.getElementById('timerProgress').style.strokeDasharray = CIRC;
    document.getElementById('timerProgress').style.strokeDashoffset = offset;
  }

  function timerRenderDots() {
    for (let i = 0; i < timerState.maxSessions; i++) {
      const dot = document.getElementById('dot-' + i);
      if (!dot) continue;
      dot.className = 'session-dot';
      if (i < timerState.session) dot.classList.add('done');
      else if (i === timerState.session) dot.classList.add('current');
    }
    document.getElementById('sessionLbl').textContent =
      'Session ' + (timerState.session + 1) + '/' + timerState.maxSessions;
  }

  function flash(msg) {
    const el = document.getElementById('timerFlash');
    el.textContent = msg;
    el.classList.add('show');
    setTimeout(() => el.classList.remove('show'), 3200);
  }

  // Init timer
  timerRenderDisplay();
  timerRenderRing();
  timerRenderDots();

  // Local desktop mode: hydrate sidebar user without redirecting.
  if (window.SmartLearnShell) {
    const u = window.SmartLearnShell.readStoredUser() || {
      prenom: 'Étudiant',
      filiere: 'SmartLearn',
      email: 'local@bissi'
    };
    window.SmartLearnShell.setSidebarUser(u);
  }
