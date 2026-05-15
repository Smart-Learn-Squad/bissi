"""FastAPI server bridging Electron UI and BISSI agent."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict, Optional, List

from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from core.agent import BissiAgent
from core.config import DEFAULT_CONFIG


logger = logging.getLogger(__name__)

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
        # Log attached files if any
        if files:
            logger.info(f"Processing {len(files)} attached file(s)")
        return agent.process_request(
            user_input=message,
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
