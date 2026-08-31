# AGENTS.md — BISSI

Local-first AI agent (Gemma 4 E2B, offline). Electron frontend + Python/FastAPI backend serving a fine-tuned LLM via llama.cpp. Windows 11 & Ubuntu/Debian 24.04.

## Architecture (two servers — both required to run the app)

```
llama.cpp (port 8001)  ← OpenAI-compatible HTTP API serving bissi-gemma4-e2b-Q4_K_M.gguf
FastAPI   (port 8765)  → SSE streaming to Electron renderer
Electron  (bissi-master-ui/) → renderer/chat.html + onboarding.html
```

- Ports are fixed: llama.cpp `:8001`, backend `:8765`. Never change them — scripts hardcode them.
- All agent + tool logic lives in `core/` and `functions/`. `api/server.py` is a thin bridge.
- See `README.md` (architecture diagram) and `AGENT_TESTING.md` for background.

## Directory ownership — do not cross

| Team | Files |
| --- | --- |
| Backend | `core/` `api/` `functions/` `onboarding/` `configs/` `main.py` `utils/` |
| Design | `bissi-master-ui/renderer/chat.html` `bissi-master-ui/renderer/onboarding.html` only |

In `chat.html` you may change CSS variables, layout, animations, and font sizes. **Do not** touch the JavaScript (SSE reader, fetch), element `id`/`class` used by JS, or interactive element structure — breaking these silently kills the UI.

Design workflow: `git checkout -b design/<change>` → edit only allowed files → `npm start` to test visually → PR with review before merge. When in doubt, don't touch; open an issue.

## Setup / run

```bash
# One-time: .venv + pip deps + GGUF model + npm deps
./install.sh                 # or start from README Quick Start

# Full stack (llama.cpp → backend → Electron), cleans stale procs first
./start.sh

# Backend alone
source .venv/bin/activate && uvicorn api.server:app --port 8765 --reload

# Frontend alone (backend must already be on :8765)
cd bissi-master-ui && npm start
```

- The app **cannot run without the GGUF model file** (`bissi-gemma4-e2b-Q4_K_M.gguf`, ~3.2 GB) at repo root or `models/`. Start scripts exit if missing.
- `main.py` refuses to start (exits 1) if llama.cpp isn't on `:8001` — run `bissi-master.sh` first.

## Testing (three layers — pick the right one)

```bash
# Unit tests — NO LLM needed, ~3s, mocked engine. Safe to run anytime.
source .venv/bin/activate && python -m pytest tests/test_agentic_capabilities.py -v

# Integration tests — NO LLM needed, executes real tools against temp files.
python -m pytest tests/test_agentic_integration.py -v -s

# E2E / REPL — REQUIRE a live llama.cpp on :8001 (via ./start.sh or bissi-master.sh).
python test_e2e_quick.py      # speed + tool-use + clean-response check
python agent_repl.py          # interactive; commands: tools, info, history
```

- Unit/integration tests mock `BissiEngine`; E2E/REPL hit the real model and are slow (`n_ctx` 16384 → first response can be slow).
- E2E tool calls are historically flaky — the model sometimes emits a raw `<|tool_call|>` trace instead of executing. Inspect the tracked tool names via `on_tool_start`, don't assume success.
- The agent is tuned for French prompts.

## Conventions & gotchas

- Agent config lives in `core/config.py` (dataclasses, immutable `DEFAULT_CONFIG`); keep `n_ctx`/`context_token_limit` consistent with the llama.cpp `n_ctx` (16384 in start scripts).
- Renderer receives SSE events from `POST /chat`: `chunk`, `thinking`, `tool_start`, `tool_done`, `file_created`, `done`, `ping`, `error`. The `chat.html` SSE loop must handle them; `tool_start`/`tool_done` wiring has historically been missing in the renderer.
- Backend reads/decodes uploaded files (UTF-8) and injects a truncated preview into the message — files are already passed to `agent.process_request()`.
- `/transcribe` (Speech-to-text, faster-whisper tiny) exists and is lazy-loaded. `functions/media/` contains office/media tool code.
- Run from repo root; `tests/conftest.py` adds root to `sys.path` for pytest.

## Docs to consult (keep in sync, don't duplicate)

- `README.md` — architecture & full API reference
- `tests/README.md` + `AGENTIC_TESTS.md` + `AGENT_TESTING.md` — test suite, mocking pattern, REPL usage
