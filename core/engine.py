"""Thread-safe llama.cpp engine wrapper for BISSI."""

from __future__ import annotations

import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterator, List, Optional

import httpx


logger = logging.getLogger(__name__)


class BissiEngineError(Exception):
    """Raised when a wrapped llama.cpp engine call fails."""


class BissiEngine:
    """Wrap llama.cpp OpenAI-compatible calls with retries and safe errors."""

    def __init__(
        self,
        model: str,
        host: str = "http://127.0.0.1:8001",
        timeout_seconds: float = 120.0,
        max_retries: int = 3,
        temperature: float = 0.5,
    ) -> None:
        """Initialize a local llama.cpp client wrapper."""
        self.model = model
        self.host = host.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.temperature = temperature
        self._client = httpx.Client(
            base_url=self.host,
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=True,
        )
        self._lock = threading.RLock()
        self._log_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="bissi-engine-log")

    def health_check(self) -> bool:
        """Return True when the llama.cpp health endpoint is reachable."""
        try:
            self._request_json("GET", "/health", call_name="health_check")
            return True
        except BissiEngineError as exc:
            self._async_log_call("health_check", time.perf_counter(), 0, 0, error=str(exc))
            return False

    def ensure_model_available(self) -> bool:
        """Return True when the llama.cpp model list is reachable and non-empty."""
        try:
            payload = self._request_json("GET", "/v1/models", call_name="list_models")
        except BissiEngineError as exc:
            self._async_log_call("list_models", time.perf_counter(), 0, 0, error=str(exc))
            return False

        models = payload.get("data", []) if isinstance(payload, dict) else []
        model_names = set()
        for model in models:
            if not isinstance(model, dict):
                continue
            for key in ("id", "name", "model"):
                value = model.get(key)
                if isinstance(value, str) and value:
                    model_names.add(value)

        return bool(model_names) and (self.model in model_names or bool(models))

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = True,
    ) -> Iterator[Dict[str, Any]]:
        """Call llama.cpp chat completions and yield normalized chunks."""
        start = time.perf_counter()
        input_tokens = self._estimate_tokens_from_messages(messages)
        payload = self._build_chat_payload(
            model=self.model,
            temperature=self.temperature,
            messages=messages,
            tools=tools,
            stream=stream,
        )

        try:
            if stream:

                def _iter() -> Iterator[Dict[str, Any]]:
                    output_tokens = 0
                    aggregated_tool_calls: List[Dict[str, Any]] = []
                    tool_call_index: Dict[int, int] = {}

                    try:
                        with self._lock:
                            with self._client.stream(
                                "POST",
                                "/v1/chat/completions",
                                json=payload,
                                headers={"Accept": "text/event-stream"},
                            ) as response:
                                response.raise_for_status()
                                for line in response.iter_lines():
                                    if not line:
                                        continue
                                    if isinstance(line, bytes):
                                        line = line.decode("utf-8", errors="replace")
                                    if not line.startswith("data:"):
                                        continue

                                    data = line[5:].strip()
                                    if not data or data == "[DONE]":
                                        continue

                                    event = json.loads(data)
                                    choice = self._first_choice(event)
                                    if not choice:
                                        continue

                                    delta = choice.get("delta", {}) if isinstance(choice, dict) else {}
                                    content = delta.get("content") or ""
                                    tool_deltas = delta.get("tool_calls") or []

                                    if content:
                                        output_tokens += max(1, len(content) // 4)
                                        yield {"message": {"content": content}}

                                    if tool_deltas:
                                        for tool_delta in tool_deltas:
                                            self._merge_tool_call_delta(tool_delta, aggregated_tool_calls, tool_call_index)

                                    finish_reason = choice.get("finish_reason") if isinstance(choice, dict) else None
                                    if finish_reason == "tool_calls" and aggregated_tool_calls:
                                        yield {"message": {"content": "", "tool_calls": self._finalize_tool_calls(aggregated_tool_calls)}}
                                        aggregated_tool_calls = []
                                        tool_call_index = {}
                    except Exception as exc:
                        self._async_log_call("chat", start, input_tokens, output_tokens, error=str(exc))
                        raise self._wrap_error("chat", exc) from exc

                    if aggregated_tool_calls:
                        yield {"message": {"content": "", "tool_calls": self._finalize_tool_calls(aggregated_tool_calls)}}

                    self._async_log_call("chat", start, input_tokens, output_tokens)

                return _iter()

            response = self._request_json("POST", "/v1/chat/completions", payload, call_name="chat")
            message = self._extract_chat_message(response)
            content = message.get("content", "")
            output_tokens = max(1, len(content) // 4) if content else 0
            self._async_log_call("chat", start, input_tokens, output_tokens)
            return iter([{"message": message}])
        except Exception as exc:
            self._async_log_call("chat", start, input_tokens, 0, error=str(exc))
            raise self._wrap_error("chat", exc) from exc

    def generate(self, prompt: str) -> str:
        """Call llama.cpp completions and return plain text."""
        start = time.perf_counter()
        input_tokens = max(1, len(prompt) // 4)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "temperature": self.temperature,
        }

        try:
            response = self._request_json("POST", "/v1/completions", payload, call_name="generate")
            text = self._extract_completion_text(response)
            output_tokens = max(1, len(text) // 4) if text else 0
            self._async_log_call("generate", start, input_tokens, output_tokens)
            return text
        except Exception as exc:
            self._async_log_call("generate", start, input_tokens, 0, error=str(exc))
            raise self._wrap_error("generate", exc) from exc

    def _request_json(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        call_name: str = "request",
    ) -> Dict[str, Any]:
        """Run one HTTP request with bounded retries and JSON parsing."""
        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with self._lock:
                    response = self._client.request(
                        method,
                        path,
                        json=payload,
                        headers={"Accept": "application/json"},
                    )
                response.raise_for_status()
                data = response.json()
                return data if isinstance(data, dict) else {"data": data}
            except Exception as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                backoff = min(2 ** (attempt - 1), 4)
                time.sleep(backoff)

        assert last_error is not None
        raise self._wrap_error(call_name, last_error)

    def _async_log_call(
        self,
        call_name: str,
        started_at: float,
        input_tokens: int,
        output_tokens: int,
        error: Optional[str] = None,
    ) -> None:
        """Send structured call logs asynchronously."""
        duration = time.perf_counter() - started_at

        def _log() -> None:
            payload = {
                "call": call_name,
                "model": self.model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "duration_sec": round(duration, 3),
            }
            if error:
                payload["error"] = error
                logger.error("engine_call_failed %s", payload)
            else:
                logger.info("engine_call_ok %s", payload)

        self._log_executor.submit(_log)

    @staticmethod
    def _estimate_tokens_from_messages(messages: List[Dict[str, Any]]) -> int:
        """Estimate message token usage with a cheap char-based heuristic."""
        total_chars = 0
        for message in messages:
            total_chars += len(str(message.get("content", "")))
        return max(1, total_chars // 4)

    @staticmethod
    def _build_chat_payload(
        model: str,
        temperature: float,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        stream: bool,
    ) -> Dict[str, Any]:
        """Build an OpenAI-compatible chat payload for llama.cpp."""
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = tools
        return payload

    def _extract_chat_message(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a non-stream chat completion response."""
        choice = self._first_choice(response)
        message = choice.get("message", {}) if isinstance(choice, dict) else {}
        content = message.get("content") or ""
        tool_calls = self._finalize_tool_calls(message.get("tool_calls") or [])
        normalized: Dict[str, Any] = {"content": content}
        if tool_calls:
            normalized["tool_calls"] = tool_calls
        return normalized

    @staticmethod
    def _extract_completion_text(response: Dict[str, Any]) -> str:
        """Normalize a completions response into plain text."""
        choice = BissiEngine._first_choice(response)
        if not choice:
            return ""
        text = choice.get("text")
        if isinstance(text, str):
            return text
        message = choice.get("message", {}) if isinstance(choice, dict) else {}
        if isinstance(message, dict):
            content = message.get("content", "")
            return content if isinstance(content, str) else ""
        return ""

    @staticmethod
    def _first_choice(response: Dict[str, Any]) -> Dict[str, Any]:
        """Return the first choice object from a response payload."""
        choices = response.get("choices", []) if isinstance(response, dict) else []
        if not choices:
            return {}
        first = choices[0]
        return first if isinstance(first, dict) else {}

    @staticmethod
    def _merge_tool_call_delta(
        tool_delta: Dict[str, Any],
        aggregated_tool_calls: List[Dict[str, Any]],
        tool_call_index: Dict[int, int],
    ) -> None:
        """Accumulate streamed tool-call deltas into complete OpenAI-style calls."""
        if not isinstance(tool_delta, dict):
            return

        position = int(tool_delta.get("index", 0) or 0)
        call_id = tool_delta.get("id") or f"call_{position}"
        merged_index = tool_call_index.get(position)
        if merged_index is None:
            merged_index = len(aggregated_tool_calls)
            tool_call_index[position] = merged_index
            aggregated_tool_calls.append(
                {
                    "id": call_id,
                    "type": tool_delta.get("type", "function"),
                    "function": {"name": "", "arguments": ""},
                }
            )

        target = aggregated_tool_calls[merged_index]
        function = tool_delta.get("function", {}) if isinstance(tool_delta.get("function", {}), dict) else {}
        if isinstance(tool_delta.get("id"), str) and tool_delta["id"]:
            target["id"] = tool_delta["id"]
        if isinstance(tool_delta.get("type"), str) and tool_delta["type"]:
            target["type"] = tool_delta["type"]

        name = function.get("name")
        if isinstance(name, str) and name:
            target_function = target.setdefault("function", {"name": "", "arguments": ""})
            target_function["name"] = name

        arguments = function.get("arguments")
        if isinstance(arguments, str) and arguments:
            target_function = target.setdefault("function", {"name": "", "arguments": ""})
            target_function["arguments"] = f"{target_function.get('arguments', '')}{arguments}"

    def _finalize_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize tool calls so downstream code always sees parsed arguments."""
        finalized: List[Dict[str, Any]] = []
        for call in tool_calls:
            if not isinstance(call, dict):
                continue
            function = call.get("function", {}) if isinstance(call.get("function", {}), dict) else {}
            arguments = function.get("arguments", {})
            if isinstance(arguments, str):
                try:
                    parsed_arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    parsed_arguments = {}
            elif isinstance(arguments, dict):
                parsed_arguments = arguments
            else:
                parsed_arguments = {}

            finalized.append(
                {
                    "id": call.get("id", "call"),
                    "type": call.get("type", "function"),
                    "function": {
                        "name": function.get("name", ""),
                        "arguments": parsed_arguments,
                    },
                }
            )
        return finalized

    @staticmethod
    def _wrap_error(operation: str, error: Exception) -> BissiEngineError:
        """Wrap arbitrary errors in a stable engine exception."""
        return BissiEngineError(f"llama.cpp {operation} failed: {error}")