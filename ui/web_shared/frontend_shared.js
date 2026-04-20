(() => {
  "use strict";

  function esc(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function normalizeEvent(payload) {
    if (!payload || typeof payload !== "object") {
      return { type: "unknown", payload: payload ?? null };
    }
    if (payload.type) return payload;
    if ("role" in payload && "content" in payload) {
      return { type: "message", payload };
    }
    if ("name" in payload && "result" in payload) {
      return { type: "tool_call", payload };
    }
    if ("message" in payload && !("role" in payload)) {
      return { type: "error", payload };
    }
    return { type: "legacy", payload };
  }

  function highlightCodeBlocks(root) {
    if (!root || typeof hljs === "undefined") return;
    root.querySelectorAll("pre code").forEach((block) => {
      try {
        const raw = block.textContent || "";
        block.textContent = raw;
        hljs.highlightElement(block);
      } catch (_) {}
    });
  }

  function renderMath(root) {
    if (!root || !window._katexReady || typeof renderMathInElement === "undefined") return;
    try {
      renderMathInElement(root, {
        delimiters: [
          { left: "$$", right: "$$", display: true },
          { left: "$", right: "$", display: false },
          { left: "\\[", right: "\\]", display: true },
          { left: "\\(", right: "\\)", display: false },
        ],
        throwOnError: false,
        strict: "ignore",
      });
    } catch (_) {}
  }

  window.BissiFrontend = {
    contractVersion: 1,
    esc,
    normalizeEvent,
    highlightCodeBlocks,
    renderMath,
  };
})();
