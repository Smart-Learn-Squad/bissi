"""FastAPI server bridging Electron UI and BISSI agent."""

from __future__ import annotations

import asyncio
import json
import logging
import tempfile
import os
from typing import Any, AsyncGenerator, Dict, Optional, List

from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from core.agent import BissiAgent
from core.config import DEFAULT_CONFIG


logger = logging.getLogger(__name__)

# Lazy-loaded Whisper model (offline STT)
_whisper_model = None

def _get_whisper():
    """Load faster-whisper model on first use (lazy, offline)."""
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
            logger.info("Whisper tiny model loaded")
        except Exception as exc:
            logger.warning(f"faster-whisper unavailable: {exc}")
            return None
    return _whisper_model

app = FastAPI(title="BISSI Backend", version="2.0.0")
agent = BissiAgent()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1", "http://localhost:*", "http://127.0.0.1:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Incoming chat payload from Electron UI."""

    message: str
    conversation_id: Optional[int] = None


class ConversationTitleRequest(BaseModel):
    """Incoming conversation rename payload."""

    title: str


async def _chat_stream(
    message: str,
    conversation_id: Optional[int] = None,
    files: Optional[List] = None,
    thinking_enabled: bool = True,
) -> AsyncGenerator[str, None]:
    """Run agent in worker thread and stream SSE events."""
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

    if conversation_id is not None:
        agent.current_conversation_id = conversation_id

    def _send_event(payload: Dict[str, Any]) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, payload)

    def on_chunk(content: str) -> None:
        _send_event({"type": "chunk", "content": content})

    def on_tool_start(name: str, args: Any) -> None:
        _send_event({"type": "tool_start", "name": name, "args": args})

    def on_tool_done(name: str, result: str) -> None:
        _send_event({"type": "tool_done", "name": name, "result": result})

    def on_thinking(content: str) -> None:
        _send_event({"type": "thinking", "content": content})

    def _run_agent() -> str:
        enriched_message = message
        if files:
            logger.info(f"Processing {len(files)} attached file(s)")
            file_contexts = []
            for f in files:
                try:
                    content = f.file.read().decode("utf-8", errors="replace")
                    preview = content[:3000]
                    if len(content) > 3000:
                        preview += f"\n... [tronqué — {len(content)} caractères au total]"
                    file_contexts.append(f"[Fichier joint : {f.filename}]\n{preview}")
                except Exception as exc:
                    logger.warning(f"Could not read file {f.filename}: {exc}")
            if file_contexts:
                enriched_message = "\n\n".join(file_contexts) + "\n\n" + message
        return agent.process_request(
            user_input=enriched_message,
            max_iterations=DEFAULT_CONFIG.agent.max_iterations,
            on_chunk=on_chunk,
            on_tool_start=on_tool_start,
            on_tool_done=on_tool_done,
            on_thinking=on_thinking if thinking_enabled else None,
            thinking_enabled=thinking_enabled,
            should_stop=lambda: False,
        )

    task = loop.run_in_executor(None, _run_agent)

    async def _watch_task() -> None:
        try:
            timeout_seconds = DEFAULT_CONFIG.llama_cpp.timeout_seconds
            full_response = await asyncio.wait_for(task, timeout=timeout_seconds)
            _send_event(
                {
                    "type": "done",
                    "full_response": full_response,
                    "conversation_id": agent.current_conversation_id,
                }
            )
        except asyncio.TimeoutError:
            logger.exception("chat_timeout")
            timeout_seconds = DEFAULT_CONFIG.llama_cpp.timeout_seconds
            _send_event({"type": "error", "message": f"Chat timeout after {timeout_seconds} seconds"})
        except Exception as exc:
            logger.exception("chat_failed")
            _send_event({"type": "error", "message": str(exc)})
        finally:
            _send_event({"type": "_end"})

    watcher = asyncio.create_task(_watch_task())

    while True:
        event = await queue.get()
        if event.get("type") == "_end":
            break
        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    await watcher


@app.post("/chat")
async def chat(
    message: str = Form(...),
    conversation_id: Optional[int] = Form(None),
    files: List[UploadFile] = File(default=[]),
    thinking: bool = Form(True),
) -> StreamingResponse:
    """Stream chat events back to Electron as SSE. Accepts message + optional files."""
    try:
        generator = _chat_stream(message, conversation_id, files, thinking_enabled=thinking)
        return StreamingResponse(generator, media_type="text/event-stream")
    except Exception as exc:
        logger.exception("chat_endpoint_error")
        raise HTTPException(status_code=500, detail=f"Chat failed: {exc}") from exc


@app.get("/conversations")
async def conversations() -> JSONResponse:
    """Return recent conversations list."""
    try:
        return JSONResponse(agent.get_recent_conversations(limit=50))
    except Exception as exc:
        logger.exception("conversations_endpoint_error")
        raise HTTPException(status_code=500, detail=f"Unable to list conversations: {exc}") from exc


@app.get("/conversations/{conversation_id}/history")
async def history(conversation_id: int) -> JSONResponse:
    """Return full history for one conversation."""
    try:
        return JSONResponse(agent.get_conversation_history(conversation_id))
    except Exception as exc:
        logger.exception("history_endpoint_error")
        raise HTTPException(status_code=500, detail=f"Unable to load history: {exc}") from exc


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int) -> JSONResponse:
    """Delete one conversation and confirm operation status."""
    try:
        return JSONResponse({"success": agent.delete_conversation(conversation_id)})
    except Exception as exc:
        logger.exception("delete_conversation_endpoint_error")
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})


@app.patch("/conversations/{conversation_id}/title")
async def update_conversation_title(conversation_id: int, request: ConversationTitleRequest) -> JSONResponse:
    """Rename one conversation."""
    try:
        title = request.title.strip()
        if not title:
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        success = agent.update_conversation_title(conversation_id, title)
        return JSONResponse({"success": success, "title": title})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("update_conversation_title_endpoint_error")
        raise HTTPException(status_code=500, detail=f"Unable to rename conversation: {exc}") from exc


@app.patch("/conversations/{conversation_id}/archive")
async def archive_conversation(conversation_id: int) -> JSONResponse:
    """Archive one conversation."""
    try:
        return JSONResponse({"success": agent.archive_conversation(conversation_id)})
    except Exception as exc:
        logger.exception("archive_conversation_endpoint_error")
        raise HTTPException(status_code=500, detail=f"Unable to archive conversation: {exc}") from exc


@app.get("/health")
async def health() -> JSONResponse:
    """Return backend health and model availability."""
    try:
        llama_cpp_ok = agent.engine.health_check()
        model_ok = agent.engine.ensure_model_available()
        return JSONResponse(
            {
                "llama_cpp": bool(llama_cpp_ok and model_ok),
                "model": agent.model,
                "status": "ok" if llama_cpp_ok and model_ok else "error",
            }
        )
    except Exception as exc:
        logger.exception("health_endpoint_error")
        return JSONResponse({"llama_cpp": False, "model": agent.model, "status": "error", "message": str(exc)})


@app.get("/tools")
async def tools() -> JSONResponse:
    """Return available tool names used by function-calling."""
    try:
        return JSONResponse(agent.get_available_tools())
    except Exception as exc:
        logger.exception("tools_endpoint_error")
        raise HTTPException(status_code=500, detail=f"Unable to list tools: {exc}") from exc


@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)) -> JSONResponse:
    """Offline speech-to-text using faster-whisper (tiny model, CPU).

    Accepts any audio format supported by ffmpeg (webm, wav, ogg, mp4…).
    Returns {"text": "...", "language": "fr"} or {"error": "..."}.
    """
    model = _get_whisper()
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="faster-whisper not available — run: pip install faster-whisper",
        )
    tmp_path = None  # guard: defined before try so finally never raises NameError
    try:
        audio_bytes = await audio.read()
        # Write to a temp file (faster-whisper needs a file path)
        suffix = os.path.splitext(audio.filename or "audio.webm")[1] or ".webm"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        loop = asyncio.get_running_loop()

        def _do_transcribe():
            segments, info = model.transcribe(
                tmp_path,
                language="fr",
                beam_size=3,
                vad_filter=True,
            )
            text = " ".join(seg.text.strip() for seg in segments).strip()
            return text, info.language

        text, lang = await loop.run_in_executor(None, _do_transcribe)
        return JSONResponse({"text": text, "language": lang})

    except Exception as exc:
        logger.exception("transcribe_error")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}") from exc
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
