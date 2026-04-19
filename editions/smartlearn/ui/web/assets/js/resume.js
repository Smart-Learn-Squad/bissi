(() => {
  "use strict";

  let fichierImporte = null; // { type, base64, mediaType, nom }
  let bridge = null;
  const PROGRESS_KEY = "bissi_smartlearn_progress";

  const $ = (sel) => document.querySelector(sel);
  const esc = (s) => String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  function updateProgressAfterAnalysis(titre) {
    const chapterTitle = String(titre || "Chapitre").trim();
    if (!chapterTitle) return;
    let progress = { chapitres: [], quizCompleted: 0, totalTemps: 0 };
    try {
      const raw = localStorage.getItem(PROGRESS_KEY);
      if (raw) progress = JSON.parse(raw);
    } catch (_) {}
    if (!Array.isArray(progress.chapitres)) progress.chapitres = [];
    const exists = progress.chapitres.some((c) =>
      String(c?.titre || "").trim().toLowerCase() === chapterTitle.toLowerCase()
    );
    if (!exists) {
      progress.chapitres.unshift({
        titre: chapterTitle,
        score: Number(0),
        date: new Date().toISOString(),
      });
    }
    progress.quizCompleted = Number(progress.quizCompleted || 0);
    progress.totalTemps = Math.max(
      Number(progress.totalTemps || 0),
      Number(localStorage.getItem("sl_temps_etude") || 0),
    );
    localStorage.setItem(PROGRESS_KEY, JSON.stringify(progress));
  }

  function setEtat(etat) {
    $("#loadingState")?.classList.toggle("show", etat === "loading");
    $("#results")?.classList.toggle("show", etat === "results");
    $("#errorState")?.classList.toggle("show", etat === "error");
    const btn = $("#btnAnalyser");
    if (btn) {
      btn.disabled = etat === "loading";
      btn.classList.toggle("loading", etat === "loading");
    }
  }

  function afficherErreur(msg) {
    const el = $("#errorState");
    if (!el) return;
    el.textContent = `⚠ ${msg}`;
    el.classList.add("show");
    setEtat("idle");
  }

  function updateCount() {
    const text = $("#courseText")?.value || "";
    const node = $("#charCount");
    if (node) node.textContent = `${text.length.toLocaleString("fr")} caractère${text.length !== 1 ? "s" : ""}`;
  }

  function importerFichier(input, type) {
    const file = input?.files?.[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
      alert("Fichier trop grand (max 10 Mo).");
      input.value = "";
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      const base64 = String(e.target?.result || "").split(",")[1] || "";
      fichierImporte = { type, base64, mediaType: file.type, nom: file.name };
      let badge = $("#uploadBadge");
      if (!badge) {
        badge = document.createElement("div");
        badge.id = "uploadBadge";
        badge.className = "upload-badge";
        $(".textarea-wrap")?.insertAdjacentElement("beforebegin", badge);
      }
      const icon = type === "pdf" ? "📄" : "🖼️";
      badge.innerHTML = `${icon} <span>${esc(file.name)}</span> <button class="upload-badge-sup" onclick="supprimerImport()">×</button>`;
      const ta = $("#courseText");
      if (ta) {
        ta.value = "";
        ta.placeholder = `Fichier importé : ${file.name}\nAjoute des instructions ici (facultatif).`;
      }
      updateCount();
    };
    reader.readAsDataURL(file);
    input.value = "";
  }

  function supprimerImport() {
    fichierImporte = null;
    $("#uploadBadge")?.remove();
    const ta = $("#courseText");
    if (ta) {
      ta.placeholder = "Colle ici le texte de ton cours (minimum 80 caractères)…";
      ta.value = "";
    }
    updateCount();
  }

  function normalizeJsonChunk(raw) {
    const cleaned = String(raw || "").replace(/```json|```/g, "").trim();
    const start = cleaned.indexOf("{");
    const end = cleaned.lastIndexOf("}");
    return (start >= 0 && end > start) ? cleaned.slice(start, end + 1) : cleaned;
  }

  async function askBridge(prompt) {
    if (!bridge?.sendMessage) throw new Error("Bridge unavailable");
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
        reject(new Error(String(msg || "AI error")));
      };
      const cleanup = () => {
        try { bridge.responseFinished.disconnect(onDone); } catch (_) {}
        try { bridge.errorOccurred.disconnect(onErr); } catch (_) {}
      };
      bridge.responseFinished.connect(onDone);
      bridge.errorOccurred.connect(onErr);
      bridge.sendMessage(prompt);
    });
  }

  async function analyser() {
    const texte = ($("#courseText")?.value || "").trim();
    if (!texte && !fichierImporte) {
      afficherErreur("Colle du texte ou importe un fichier.");
      return;
    }
    if (!fichierImporte && texte.length < 80) {
      const manque = 80 - texte.length;
      afficherErreur(`Texte trop court (${texte.length}/80 caractères). Ajoute ${manque} caractère${manque > 1 ? 's' : ''} ou importe un fichier.`);
      return;
    }
    setEtat("loading");
    $("#errorState")?.classList.remove("show");

    const systemPrompt = [
      "You are SmartLearn, an educational assistant.",
      "Respond ONLY with valid JSON in this format:",
      '{',
      '  "titre":"Short title",',
      '  "matiere":"Subject name",',
      '  "resume":"Clear summary in 3-4 sentences",',
      '  "concepts":["c1","c2","c3","c4","c5","c6"],',
      '  "points_cles":["p1","p2","p3","p4"],',
      '  "definitions":[{"terme":"T1","definition":"D1"},{"terme":"T2","definition":"D2"}]',
      "}",
      "No markdown.",
    ].join("\n");

    const sourceHint = fichierImporte
      ? `Imported file: ${fichierImporte.nom} (${fichierImporte.mediaType}).\nInstructions: ${texte || "Automatic analysis."}`
      : texte.slice(0, 7000);

    const prompt = `${systemPrompt}\n\nChapter to analyse:\n${sourceHint}`;

    try {
      const raw = await askBridge(prompt);
      const parsed = JSON.parse(normalizeJsonChunk(raw));
      afficherResultats(parsed);
    } catch (e) {
      afficherErreur("Analyse impossible via le moteur local.");
    }
  }

  function afficherResultats(d) {
    fichierImporte = null;
    $("#uploadBadge")?.remove();

    $("#resultTitle").textContent = d.titre || "Chapitre analysé";
    $("#resultResume").textContent = d.resume || "—";

    const concepts = $("#resultConcepts");
    if (concepts) {
      concepts.innerHTML = "";
      (d.concepts || []).forEach((c) => {
        const chip = document.createElement("span");
        chip.className = "concept-chip";
        chip.textContent = c;
        concepts.appendChild(chip);
      });
    }

    const points = $("#resultPoints");
    if (points) {
      points.innerHTML = "";
      (d.points_cles || []).forEach((p) => {
        const row = document.createElement("div");
        row.className = "point-item";
        row.textContent = p;
        points.appendChild(row);
      });
    }

    const defs = $("#resultDefs");
    if (defs) {
      defs.innerHTML = "";
      (d.definitions || []).forEach((def) => {
        const row = document.createElement("div");
        row.className = "def-item";
        row.innerHTML = `<div class="def-terme">${esc(def.terme)}</div><div class="def-desc">${esc(def.definition)}</div>`;
        defs.appendChild(row);
      });
    }

    sessionStorage.setItem("sl_texte_cours", $("#courseText")?.value || "");
    sessionStorage.setItem("sl_titre_cours", d.titre || "Chapitre");
    sessionStorage.setItem("sl_resume_cours", d.resume || "");
    sessionStorage.setItem("sl_concepts_cours", (d.concepts || []).join(", "));
    sessionStorage.setItem("sl_points_cours", (d.points_cles || []).join("\n"));
    sessionStorage.setItem("sl_matiere_cours", d.matiere || "Général");
    updateProgressAfterAnalysis(d.titre || "Chapitre");

    setEtat("results");
  }

  function nouvelleAnalyse() {
    setEtat("idle");
    const ta = $("#courseText");
    if (ta) {
      ta.value = "";
      ta.focus();
    }
    const c = $("#charCount");
    if (c) c.textContent = "0 caractère";
  }

  function copierTout() {
    const titre = $("#resultTitle")?.textContent || "";
    const resume = $("#resultResume")?.textContent || "";
    const concepts = [...document.querySelectorAll(".concept-chip")].map((c) => `• ${c.textContent}`).join("\n");
    const points = [...document.querySelectorAll(".point-item")].map((p) => `✓ ${p.textContent}`).join("\n");
    const defs = [...document.querySelectorAll(".def-item")].map((d) => {
      const t = d.querySelector(".def-terme")?.textContent || "";
      const v = d.querySelector(".def-desc")?.textContent || "";
      return `${t} : ${v}`;
    }).join("\n");
    navigator.clipboard.writeText(
      `SMARTLEARN — ${titre}\n\nRÉSUMÉ\n${resume}\n\nCONCEPTS CLÉS\n${concepts}\n\nPOINTS ESSENTIELS\n${points}\n\nDÉFINITIONS\n${defs}`
    );
  }

  function versQuiz() {
    window.location.href = "index.html?flow=resume";
  }

  function connectBridge(tries) {
    if (typeof qt !== "undefined" && typeof QWebChannel !== "undefined") {
      new QWebChannel(qt.webChannelTransport, (channel) => {
        bridge = channel.objects.bissi;
      });
      return;
    }
    if (tries < 20) setTimeout(() => connectBridge(tries + 1), 100);
  }

  function initSidebarUser() {
    if (!window.SmartLearnShell) return;
    const user = window.SmartLearnShell.readStoredUser?.() || {
      prenom: "Étudiant",
      filiere: "SmartLearn",
      email: "local@bissi",
    };
    window.SmartLearnShell.setSidebarUser?.(user);
  }

  window.importerFichier = importerFichier;
  window.supprimerImport = supprimerImport;
  window.updateCount = updateCount;
  window.analyser = analyser;
  window.nouvelleAnalyse = nouvelleAnalyse;
  window.copierTout = copierTout;
  window.versQuiz = versQuiz;

  document.addEventListener("DOMContentLoaded", () => {
    initSidebarUser();
    connectBridge(0);
    updateCount();
  });
})();
