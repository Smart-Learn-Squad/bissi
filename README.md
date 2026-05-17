<div align="center">
  <img src="./bissi-master-ui/renderer/assets/gem.svg" width="80" alt="Bissi logo" />
  <h1>Bissi: Your Personal Task Handler ✨</h1>
  <p><em>Augmented intelligence, entirely offline.</em></p>
</div>

---

## The Problem

Across Africa and much of the developing world, millions of students, professionals, and everyday users face the same invisible wall: powerful AI tools exist, but they require a stable internet connection, a subscription, and often a high-end device. In Cotonou, Lomé, Dakar, or Kinshasa, that wall is real. **Bissi was built to tear it down.**

---

## What is Bissi?

*Bissi* means **augmented** in Yoruba — and that is exactly what it is: an augmented version of Gemma 4, fine-tuned and extended to become a capable local agent. The name is a deliberate nod to the West African roots of the team that built it, and a statement about who this technology is for.

Bissi is a **local-first AI agent** powered by a fine-tuned **Gemma 4 E2B** model, designed to run entirely on your machine — no internet, no cloud, no subscription. It is the ChatGPT of the Edge-AI era: always available, fully private, and capable of executing real tasks from simple to complex.

A student can upload a course file and ask Bissi to explain it, generate a summary document, or help with a homework assignment — all offline. A professional can ask Bissi to read, write, and organize Word, Excel, and PDF files without a single byte leaving their machine.

Bissi is officially supported on **Windows 11** and **Ubuntu/Debian 24.04**.

---

## How It Was Built

The development followed a deliberate, phased approach:

1. **Tool implementation** — Core functions built in Python: file reading/writing (Word, Excel, PDF, text), Python code execution, and document generation via python-docx and Jinja2 templates.
2. **Agentic loop** — A custom agent loop handling tool call parsing, multi-turn iteration, and model-tool permutation cycles.
3. **Model bridge** — llama.cpp serves the model locally on port 8001 via an OpenAI-compatible HTTP API. FastAPI on port 8765 handles the agentic pipeline and streams responses to the frontend via SSE.
4. **Fine-tuning** — After initial tests revealed model instability on function calling, Gemma 4 E2B was fine-tuned into `bissi-gemma4-e2b` using **Unsloth** for optimized training efficiency, then quantized at Q4_K_M for broad hardware compatibility.
5. **Frontend** — Built with Electron, integrating markdown-it, KaTeX, highlight.js, mammoth, xlsx, pdfjs-dist, and transformers.js for rich local rendering including LaTeX math equations.
6. **Integration & testing** — Backend and frontend connected via FastAPI, tested across multiple machines.

---

## What Bissi Can Do Today

- Explain any course or document uploaded by the user, with full KaTeX math rendering
- Generate structured Word documents from conversation context
- Execute Python code locally for analysis and calculation
- Read and write Excel and PDF files
- Think step-by-step with visible reasoning (Thinking mode)
- Run **100% offline** on modest hardware (tested on 16GB RAM, CPU+GPU)

---

## Why Gemma 4?

Gemma 4 E2B's native function calling capability was central to Bissi's architecture. Its small footprint after Q4_K_M quantization (3.2GB) makes it viable on any modern laptop. Fine-tuning with Unsloth on task-execution scenarios dramatically improved tool call reliability and reduced model hallucinations on function calling.

---

## Impact

Bissi directly addresses the **Digital Equity & Inclusivity** and **Future of Education** tracks. A student in a low-connectivity environment can now have a capable AI tutor and document assistant running entirely on a modest laptop. No API key. No subscription. No internet. Just Bissi.

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Model** | Gemma 4 E2B → fine-tuned with Unsloth → quantized Q4_K_M (3.2 GB) |
| **Inference** | llama.cpp (OpenAI-compatible API on `localhost:8001`) |
| **Backend** | Python, FastAPI, SSE streaming on `localhost:8765` |
| **Frontend** | Electron 28, vanilla HTML/CSS/JS |
| **Vendors** | markdown-it, KaTeX, highlight.js, mammoth, xlsx, pdfjs-dist, transformers.js |
| **Platforms** | Windows 11, Ubuntu/Debian 24.04 |

---

## Quick Start

### Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/Smart-Learn-Squad/bissi/main/install.sh | bash
./start.sh
```

### Windows

```powershell
irm https://raw.githubusercontent.com/Smart-Learn-Squad/bissi/main/install.ps1 | iex
start.bat
```

---

## Architecture

```
bissi/
├── core/
│   ├── agent.py               # Agent orchestrator + tools
│   ├── engine.py              # LLM streaming via llama.cpp
│   └── memory/
│       └── conversation_store.py  # SQLite persistent history
│
├── functions/                 # Agent tool implementations
│   ├── filesystem/            # File read/write
│   ├── code/                  # Python execution
│   ├── office/                # Word, Excel, PDF
│   └── data/                  # CSV/data analysis
│
├── api/
│   └── server.py              # FastAPI — SSE streaming + file upload
│
├── bissi-master-ui/           # Electron frontend
│   ├── main.js                # Window + permissions
│   ├── preload.js             # Secure IPC bridge
│   └── renderer/
│       ├── chat.html          # Main UI (chat + canvas + voice)
│       └── onboarding.html    # First-run onboarding
│
├── main.py                    # Backend entry point
├── bissi-master.sh            # llama.cpp launch script
├── start.sh / start.bat       # Dev startup scripts
└── requirements.txt
```

---

## Development

```bash
# Backend only
uvicorn api.server:app --port 8765 --reload

# Frontend only
cd bissi-master-ui && npm start

# Full stack
./start.sh
```

### API Reference

```bash
# Health check
curl http://localhost:8765/health

# Streaming chat (SSE)
curl -N -X POST http://localhost:8765/chat \
  -F "message=Hello Bissi" \
  -F "thinking=true"

# File upload
curl -N -X POST http://localhost:8765/chat \
  -F "message=Analyze this file" \
  -F "files=@report.docx"
```

---

## Acknowledgements

- **Google** for Gemma 4 and the Gemma 4 Good hackathon
- **Hugging Face** for model hosting
- **llama.cpp** for ultra-optimized local inference
- **Unsloth** for efficient fine-tuning
- **The Bissi Team** — building for the edge

---

<div align="center">
  <strong>Bissi</strong> — Powerful AI, private, on your machine. 🚀
</div>
