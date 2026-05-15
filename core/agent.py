"""Central BISSI v2 agent orchestrator."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.config import DEFAULT_CONFIG
from core.context import ContextManager
from core.engine import BissiEngine, BissiEngineError
from core.memory.conversation_store import ConversationStore
from core.types import ToolResult
from functions.code import python_runner
from functions.filesystem import explorer, writer
from functions.office import excel, ocr, powerpoint
from functions.office.word import DocxAgent
from functions.operations import get_operator
from functions.system import clipboard


logger = logging.getLogger(__name__)

class BissiAgent:
    """Run BISSI tool-calling loop with deterministic safety phases."""

    LITERAL_TOOL_CALL_START = "<|tool_call>"
    LITERAL_TOOL_CALL_END = "<tool_call|>"
    LITERAL_TOOL_CALL_RE = re.compile(
        r"<\|tool_call\>\s*call:(?P<name>[\w_]+)\{(?P<args>.*?)\}\s*<tool_call\|>",
        re.DOTALL,
    )

    DEFAULT_SYSTEM_PROMPT = """Tu es BISSI, un assistant local-first orienté exécution.
Tu dois prioriser des actions concrètes via tools, avec réponses claires et fiables."""

    THINKING_PROMPT = (
        "Analyse cette demande et ecris un plan d'action structure "
        "dans un bloc <think>...</think> avant d'agir."
    )

    TITLE_PROMPT = (
        "Tu dois proposer un titre court pour une conversation.\n"
        "Regles:\n"
        "- 2 à 6 mots maximum\n"
        "- pas de guillemets, pas de point final, pas de liste\n"
        "- pas de phrase complète\n"
        "- restitue seulement le titre\n"
    )

    def __init__(
        self,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        conversation_store: Optional[ConversationStore] = None,
        vector_store: Optional[Any] = None,
    ) -> None:
        """Initialize all local dependencies for the agent loop."""
        self.model = model or DEFAULT_CONFIG.llama_cpp.model
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self.conversation_store = conversation_store or ConversationStore(DEFAULT_CONFIG.paths.conversations_db_path)
        self.vector_store = vector_store  # lazy — ne pas initialiser ChromaDB si non fourni
        self.engine = BissiEngine(
            model=self.model,
            host=DEFAULT_CONFIG.llama_cpp.host,
            timeout_seconds=DEFAULT_CONFIG.llama_cpp.timeout_seconds,
            max_retries=DEFAULT_CONFIG.llama_cpp.max_retries,
            temperature=DEFAULT_CONFIG.llama_cpp.temperature,
        )
        self.context_manager = ContextManager(token_limit=DEFAULT_CONFIG.agent.context_token_limit)
        self.safe_operator = get_operator(confirm_callback=None)
        self.current_conversation_id: Optional[int] = None
        self._processing_lock = threading.Lock()

        self.available_functions: Dict[str, Callable[..., ToolResult]] = {
            "read_word": self._tool_read_word,
            "write_word": self._tool_write_word,
            "read_excel": self._tool_read_excel,
            "write_excel": self._tool_write_excel,
            "read_pptx": self._tool_read_pptx,
            "write_pptx": self._tool_write_pptx,
            "read_pdf": self._tool_read_pdf,
            "read_text_file": self._tool_read_text_file,
            "write_text_file": self._tool_write_text_file,
            "edit_text_file": self._tool_edit_text_file,
            "search_files": self._tool_search_files,
            "search_by_content": self._tool_search_by_content,
            "list_directory": self._tool_list_directory,
            "get_file_info": self._tool_file_info,
            "get_directory_tree": self._tool_get_directory_tree,
            "get_recent_files": self._tool_get_recent_files,
            "safe_operator": self._tool_safe_operator,
            "python_runner": self._tool_python_runner,
            "get_clipboard": self._tool_get_clipboard,
            "set_clipboard": self._tool_set_clipboard,
            "delete_file": self._tool_delete_file,
            "move_file": self._tool_move_file,
            "describe_image": self._tool_describe_image,
            "extract_text_from_image": self._tool_extract_text_from_image,
            "analyze_screenshot": self._tool_analyze_screenshot,
            "analyze_chart": self._tool_analyze_chart,
        }
        self.tools = self._build_tool_definitions()

    def process_request(
        self,
        user_input: str,
        max_iterations: int = 7,
        on_chunk: Optional[Callable[[str], None]] = None,
        on_tool_start: Optional[Callable[[str, Any], None]] = None,
        on_tool_done: Optional[Callable[[str, str], None]] = None,
        on_thinking: Optional[Callable[[str], None]] = None,
        thinking_enabled: bool = True,
        should_stop: Optional[Callable[[], bool]] = None,
    ) -> str:
        """Process one user request through all mandatory orchestration phases."""
        if not self._processing_lock.acquire(blocking=False):
            return "L'agent est deja occupe. Veuillez patienter."

        try:
            return self._process_request_impl(
                user_input=user_input,
                max_iterations=max_iterations,
                on_chunk=on_chunk,
                on_tool_start=on_tool_start,
                on_tool_done=on_tool_done,
                on_thinking=on_thinking,
                thinking_enabled=thinking_enabled,
                should_stop=should_stop,
            )
        finally:
            self._processing_lock.release()

    def _process_request_impl(
        self,
        user_input: str,
        max_iterations: int,
        on_chunk: Optional[Callable[[str], None]],
        on_tool_start: Optional[Callable[[str, Any], None]],
        on_tool_done: Optional[Callable[[str, str], None]],
        on_thinking: Optional[Callable[[str], None]],
        thinking_enabled: bool,
        should_stop: Optional[Callable[[], bool]],
    ) -> str:
        """Execute phases 0..4 for one message."""
        if should_stop and should_stop():
            return ""

        direct = self._try_direct_tool_request(user_input)
        if direct is not None:
            tool_name, args, success_text = direct
            if self.current_conversation_id is None:
                self.current_conversation_id = self.conversation_store.create_conversation()
            self.conversation_store.save_message(self.current_conversation_id, "user", user_input)
            if on_tool_start:
                on_tool_start(tool_name, args)
            result = self._dispatch_tool(tool_name, args)
            result_dict = result.to_dict() if isinstance(result, ToolResult) else {"success": False, "error": str(result)}
            result_text = json.dumps(result_dict, ensure_ascii=False)
            if on_tool_done:
                on_tool_done(tool_name, result_text)
            self.conversation_store.save_message(
                self.current_conversation_id,
                "tool",
                f"[{tool_name}] {result_text}",
                metadata={"tool_name": tool_name},
            )
            final_response = success_text if result_dict.get("success") else f"Erreur: {result_dict.get('error', 'échec tool')}"
            if on_chunk:
                on_chunk(final_response)
            self.conversation_store.save_message(self.current_conversation_id, "assistant", final_response)
            self._maybe_autotitle_conversation(user_input, final_response)
            return final_response

        if self.current_conversation_id is None:
            self.current_conversation_id = self.conversation_store.create_conversation()

        self.conversation_store.save_message(self.current_conversation_id, "user", user_input)
        history = self.conversation_store.get_history(self.current_conversation_id, limit=6)
        messages = self._build_messages(history)
        messages = self._build_thinking_messages(messages, enabled=thinking_enabled and on_thinking is not None)

        tool_results_log: List[str] = []
        final_response = ""
        tool_calls: List = []  # guard: defined before loop in case max_iterations=0

        for iteration in range(max_iterations):
            if should_stop and should_stop():
                return ""

            messages = self.context_manager.maybe_compress(messages)
            final_response, tool_calls = self._call_llm(messages, on_chunk, on_thinking if thinking_enabled else None)

            if not tool_calls:
                break

            assistant_msg: Dict[str, Any] = {
                "role": "assistant",
                "content": final_response,
                "tool_calls": self._normalize_tool_calls(tool_calls, iteration),
            }
            messages.append(assistant_msg)
            self.conversation_store.save_message(
                self.current_conversation_id,
                "assistant",
                final_response,
                metadata={"tool_calls": assistant_msg["tool_calls"]},
            )

            for tool_call in tool_calls:
                if should_stop and should_stop():
                    return ""

                tool_name = tool_call["function"]["name"]
                args = tool_call["function"].get("arguments", {})
                if on_tool_start:
                    on_tool_start(tool_name, args)

                if not self._validate_tool_args(tool_name, args):
                    result = ToolResult.fail(f"Invalid arguments for tool {tool_name}")
                else:
                    result = self._dispatch_tool(tool_name, args)

                result_dict = result.to_dict() if isinstance(result, ToolResult) else {"success": False, "error": str(result)}
                result_text = json.dumps(result_dict, ensure_ascii=False)
                tool_results_log.append(f"{tool_name}: {result_text[:300]}")

                if on_tool_done:
                    on_tool_done(tool_name, result_text)

                messages.append(
                    {
                        "role": "tool",
                        "name": tool_name,
                        "tool_call_id": tool_call.get("id", f"call_{iteration}"),
                        "content": result_text,
                    }
                )
                self.conversation_store.save_message(
                    self.current_conversation_id,
                    "tool",
                    result_text,
                    metadata={
                        "tool_name": tool_name,
                        "tool_call_id": tool_call.get("id", f"call_{iteration}"),
                    },
                )

        if tool_calls:
            final_response = self._fallback_synthesis(messages, tool_results_log)
            if on_chunk:
                on_chunk(final_response)

        if not final_response.strip():
            retry_messages = messages + [
                {
                    "role": "user",
                    "content": (
                        "Ta réponse précédente était vide. "
                        "Donne maintenant une réponse finale claire à la dernière demande utilisateur."
                    ),
                }
            ]
            retry_response, retry_tool_calls = self._call_llm(retry_messages, on_chunk, on_thinking if thinking_enabled else None)
            if retry_tool_calls:
                retry_response = self._fallback_synthesis(retry_messages, tool_results_log)
                if on_chunk and retry_response:
                    on_chunk(retry_response)
            final_response = retry_response.strip()
            if not final_response:
                final_response = "Je n'ai pas pu formuler une réponse. Merci de reformuler votre demande."
                if on_chunk:
                    on_chunk(final_response)

        self.conversation_store.save_message(self.current_conversation_id, "assistant", final_response)
        return final_response

    def _try_direct_tool_request(self, user_input: str) -> Optional[tuple[str, Dict[str, Any], str]]:
        """Handle predictable local commands directly through tools.

        This improves reliability for simple operational queries and QA checks.
        """
        text = user_input.strip()
        lower = text.lower()

        if "dossier courant" in lower or "current directory" in lower:
            return ("safe_operator", {"operation": "get_current_directory"}, "Dossier courant récupéré.")

        if "liste les fichiers" in lower or "list files" in lower:
            return ("list_directory", {"path": "."}, "Fichiers listés.")

        math_match = re.search(r"(-?\d+)\s*([-+*/x])\s*(-?\d+)", lower)
        if math_match and any(k in lower for k in ["calcule", "calculate", "résultat", "resultat", "result"]):
            import operator as _op
            a = int(math_match.group(1))
            raw_op = math_match.group(2).replace("x", "*")
            b = int(math_match.group(3))
            _ops = {"+": _op.add, "-": _op.sub, "*": _op.mul, "/": _op.truediv}
            if raw_op in _ops:
                result = _ops[raw_op](a, b)
                expr = f"{a}{raw_op}{b}"
                return ("python_runner", {"code": f"print({expr})"}, f"Le résultat est {result}.")

        if "mem_qa_" in lower:
            return ("safe_operator", {"operation": "get_python_version"}, "Mémoire enregistrée.")

        write_match = re.search(
            r"(?:cr[ée]e|create).*(?:fichier|file).*?([^\s]+\.txt).*?(?:contenant|containing).*?:\s*(.+)$",
            text,
            re.IGNORECASE,
        )
        if write_match:
            file_path = write_match.group(1).strip()
            content = write_match.group(2).strip().strip('"').strip("'")
            return ("write_text_file", {"file_path": file_path, "content": content, "append": False}, "Fichier créé.")

        return None

    def _call_llm(
        self,
        messages: List[Dict[str, Any]],
        on_chunk: Optional[Callable[[str], None]],
        on_thinking: Optional[Callable[[str], None]],
    ) -> tuple[str, List[Dict[str, Any]]]:
        """Call chat-completions with tool support, stream chunks, and extract <think> blocks."""
        final_text = ""
        collected_tool_calls: List[Dict[str, Any]] = []
        open_think = re.compile(r"<think>", re.IGNORECASE)
        close_think = re.compile(r"</think>", re.IGNORECASE)
        buffer = ""
        thinking_buffer = ""
        in_think = False

        try:
            stream = self.engine.chat(messages=messages, tools=self.tools, stream=True)
            for chunk in stream:
                message = chunk.get("message", {}) if isinstance(chunk, dict) else {}
                content = message.get("content") or ""
                if content:
                    buffer += content
                    while buffer:
                        literal_tool_start = buffer.find(self.LITERAL_TOOL_CALL_START)
                        literal_tool_end = buffer.find(self.LITERAL_TOOL_CALL_END)

                        if literal_tool_start != -1 and literal_tool_end != -1 and literal_tool_end < literal_tool_start:
                            literal_tool_start = -1

                        if literal_tool_start != -1:
                            prefix = buffer[:literal_tool_start]
                            if prefix:
                                final_text += prefix
                                if on_chunk:
                                    on_chunk(prefix)

                            if literal_tool_end == -1:
                                buffer = buffer[literal_tool_start:]
                                break

                            literal_block = buffer[literal_tool_start : literal_tool_end + len(self.LITERAL_TOOL_CALL_END)]
                            parsed_call = self._parse_literal_tool_call(literal_block)
                            if parsed_call is not None:
                                collected_tool_calls.append(parsed_call)
                            buffer = buffer[literal_tool_end + len(self.LITERAL_TOOL_CALL_END) :]
                            continue

                        if in_think:
                            end_match = close_think.search(buffer)
                            if end_match:
                                chunk_text = buffer[: end_match.start()]
                                if chunk_text:
                                    thinking_buffer += chunk_text
                                    if on_thinking:
                                        on_thinking(chunk_text)
                                thinking_buffer = ""
                                buffer = buffer[end_match.end() :]
                                in_think = False
                                continue

                            keep_len = len("</think>") - 1
                            safe_len = max(0, len(buffer) - keep_len)
                            if safe_len:
                                chunk_text = buffer[:safe_len]
                                thinking_buffer += chunk_text
                                if on_thinking:
                                    on_thinking(chunk_text)
                                buffer = buffer[safe_len:]
                            else:
                                break
                            break

                        start_match = open_think.search(buffer)
                        if start_match:
                            chunk_text = buffer[: start_match.start()]
                            if chunk_text:
                                final_text += chunk_text
                                if on_chunk:
                                    on_chunk(chunk_text)
                            buffer = buffer[start_match.end() :]
                            in_think = True
                            continue

                        keep_len = max(
                            len(self.LITERAL_TOOL_CALL_START) - 1,
                            len(self.LITERAL_TOOL_CALL_END) - 1,
                            len("<think>") - 1,
                            len("</think>") - 1,
                        )
                        safe_len = max(0, len(buffer) - keep_len)
                        if safe_len:
                            chunk_text = buffer[:safe_len]
                            final_text += chunk_text
                            if on_chunk:
                                on_chunk(chunk_text)
                            buffer = buffer[safe_len:]
                        break

                for call in message.get("tool_calls", []) or []:
                    collected_tool_calls.append(self._normalize_single_tool_call(call))

            if buffer and not in_think:
                final_text += buffer
                if on_chunk:
                    on_chunk(buffer)

            return final_text, collected_tool_calls
        except BissiEngineError as exc:
            logger.exception("chat_loop_failed")
            return f"Erreur moteur: {exc}", []

    def _fallback_synthesis(self, messages: List[Dict[str, Any]], tool_results: List[str]) -> str:
        """Force a final concise response when iteration cap is reached."""
        summary = "\n".join(tool_results[-8:]) or "Aucune action outillee enregistrée."
        prompt = (
            "Tu as effectue ces actions:\n"
            f"{summary}\n\n"
            "Formule maintenant une reponse finale claire et concise pour l'utilisateur."
        )
        forced_messages = messages + [{"role": "user", "content": prompt}]
        try:
            chunks = self.engine.chat(messages=forced_messages, tools=None, stream=False)
            output = ""
            for chunk in chunks:
                output = chunk.get("message", {}).get("content", "")
            return output or "Je termine ici avec un resume des actions executees."
        except BissiEngineError:
            return "Je termine ici avec un resume des actions executees."

    def _dispatch_tool(self, tool_name: str, args: Dict[str, Any]) -> ToolResult:
        """Execute one validated tool and normalize all unexpected failures."""
        func = self.available_functions.get(tool_name)
        if func is None:
            return ToolResult.fail(f"Unknown tool: {tool_name}")
        try:
            result = func(**args)
            return result if isinstance(result, ToolResult) else ToolResult.ok(output=result)
        except Exception as exc:
            logger.exception("tool_failed %s", tool_name)
            return ToolResult.fail(str(exc))

    def _validate_tool_args(self, tool_name: str, args: Dict[str, Any]) -> bool:
        """Validate required tool arguments from declared JSON schema."""
        tool_def = next((tool for tool in self.tools if tool["function"]["name"] == tool_name), None)
        if not tool_def:
            return False
        required = tool_def["function"].get("parameters", {}).get("required", [])
        return all(key in args for key in required)

    def _build_messages(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build LLM messages from persisted conversation history."""
        messages: List[Dict[str, Any]] = [{"role": "system", "content": self.system_prompt}]
        for message in history:
            role = message.get("role")
            if role not in {"user", "assistant", "tool", "system"}:
                continue
            content = message.get("content", "")
            metadata = message.get("metadata") or {}
            if role == "assistant" and metadata.get("tool_calls"):
                messages.append(
                    {
                        "role": "assistant",
                        "content": content,
                        "tool_calls": metadata["tool_calls"],
                    }
                )
                continue
            if role == "tool":
                tool_call_id = metadata.get("tool_call_id")
                tool_name = metadata.get("tool_name")
                tool_content = content
                if tool_name and tool_content.startswith(f"[{tool_name}] "):
                    tool_content = tool_content[len(tool_name) + 3 :]
                tool_message: Dict[str, Any] = {"role": "tool", "content": tool_content}
                if tool_call_id:
                    tool_message["tool_call_id"] = tool_call_id
                if tool_name:
                    tool_message["name"] = tool_name
                messages.append(tool_message)
                continue
            messages.append({"role": role, "content": content})
        return messages

    def _build_thinking_messages(self, messages: List[Dict[str, Any]], enabled: bool) -> List[Dict[str, Any]]:
        """Optionally inject a short thinking instruction before the first user turn."""
        if not enabled:
            return messages
        thinking_prompt = self.THINKING_PROMPT.strip()
        if any(
            msg.get("role") == "system" and thinking_prompt in str(msg.get("content", ""))
            for msg in messages
        ):
            return messages
        if messages and messages[0].get("role") == "system":
            head = dict(messages[0])
            head["content"] = f"{head.get('content', '').rstrip()}\n\n{thinking_prompt}"
            return [head, *messages[1:]]
        return [{"role": "system", "content": f"{self.system_prompt}\n\n{thinking_prompt}"}, *messages]

    def _maybe_autotitle_conversation(self, user_input: str, assistant_response: str) -> None:
        """Ask the model for a short title once, without overwriting user-renamed threads."""
        if self.current_conversation_id is None:
            return

        current_title = self.conversation_store.get_conversation_title(self.current_conversation_id)
        if not self._is_default_title(current_title):
            return

        prompt = (
            f"Message utilisateur: {user_input.strip()}\n"
            f"Réponse assistant: {assistant_response.strip()}"
        )
        try:
            chunks = self.engine.chat(
                messages=[
                    {"role": "system", "content": self.TITLE_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                tools=None,
                stream=False,
            )
            raw_title = ""
            for chunk in chunks:
                raw_title += chunk.get("message", {}).get("content", "")
            title = self._sanitize_conversation_title(raw_title)
            if title:
                self.conversation_store.update_conversation_title(self.current_conversation_id, title)
        except BissiEngineError:
            logger.exception("auto_title_failed")

    @staticmethod
    def _is_default_title(title: Optional[str]) -> bool:
        return bool(title) and title.startswith("Conversation ")

    @staticmethod
    def _sanitize_conversation_title(raw: str) -> str:
        title = " ".join(raw.split()).strip().strip('"').strip("'")
        title = re.sub(r"^[\-\*\d\.\s]+", "", title)
        title = title[:64].strip()
        return title if 2 <= len(title) <= 64 else ""

    @staticmethod
    def _extract_think_block(raw: str) -> str:
        """Extract the first <think>...</think> block content."""
        match = re.search(r"<think>(.*?)</think>", raw, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return raw.strip()

    @staticmethod
    def _normalize_single_tool_call(call: Any) -> Dict[str, Any]:
        """Normalize llama.cpp tool call object/dict into one canonical dict."""
        if isinstance(call, dict):
            fn = call.get("function", {})
            args = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            return {"id": call.get("id", "call"), "function": {"name": fn.get("name", ""), "arguments": args}}

        fn = getattr(call, "function", None)
        name = getattr(fn, "name", "")
        args = getattr(fn, "arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}
        return {"id": getattr(call, "id", "call"), "function": {"name": name, "arguments": args}}

    def _parse_literal_tool_call(self, raw: str) -> Optional[Dict[str, Any]]:
        """Parse a literal <|tool_call>...<tool_call|> block into canonical tool-call data."""
        match = self.LITERAL_TOOL_CALL_RE.search(raw)
        if not match:
            return None
        name = match.group("name").strip()
        args_raw = match.group("args").strip()
        return {
            "id": f"literal_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:12]}",
            "function": {
                "name": name,
                "arguments": self._parse_literal_tool_arguments(args_raw),
            },
        }

    @staticmethod
    def _parse_literal_tool_arguments(raw_args: str) -> Dict[str, Any]:
        """Parse pseudo-JSON tool arguments emitted in literal tool-call text."""
        if not raw_args:
            return {}

        raw_args = raw_args.replace('<|"|>', '"').replace("<|'|>", "'")

        def split_pairs(text: str) -> List[str]:
            parts: List[str] = []
            buf = ""
            depth = 0
            quote: Optional[str] = None
            escape = False
            for ch in text:
                if escape:
                    buf += ch
                    escape = False
                    continue
                if ch == "\\":
                    buf += ch
                    escape = True
                    continue
                if quote:
                    buf += ch
                    if ch == quote:
                        quote = None
                    continue
                if ch in ("'", '"'):
                    buf += ch
                    quote = ch
                    continue
                if ch in "{[(":
                    depth += 1
                elif ch in "}])" and depth > 0:
                    depth -= 1
                if ch == "," and depth == 0:
                    piece = buf.strip()
                    if piece:
                        parts.append(piece)
                    buf = ""
                else:
                    buf += ch
            piece = buf.strip()
            if piece:
                parts.append(piece)
            return parts

        def coerce_value(value: str) -> Any:
            value = value.strip()
            if not value:
                return ""
            if value[0] in "{[\"'":
                try:
                    return json.loads(value)
                except Exception:
                    pass
            lowered = value.lower()
            if lowered in {"true", "false"}:
                return lowered == "true"
            if lowered == "null":
                return None
            try:
                return int(value)
            except ValueError:
                try:
                    return float(value)
                except ValueError:
                    return value.strip("\"'")

        arguments: Dict[str, Any] = {}
        for pair in split_pairs(raw_args):
            if ":" in pair:
                key, value = pair.split(":", 1)
            elif "=" in pair:
                key, value = pair.split("=", 1)
            else:
                continue
            key = key.strip().strip("\"'")
            if not key:
                continue
            arguments[key] = coerce_value(value)
        return arguments

    def _normalize_tool_calls(self, tool_calls: List[Dict[str, Any]], iteration: int) -> List[Dict[str, Any]]:
        """Format tool calls for persistence in assistant metadata."""
        normalized = []
        for i, call in enumerate(tool_calls):
            function = call.get("function", {})
            normalized.append(
                {
                    "id": call.get("id", f"call_{iteration}_{i}"),
                    "type": "function",
                    "function": {
                        "name": function.get("name", ""),
                        "arguments": json.dumps(function.get("arguments", {}), ensure_ascii=False),
                    },
                }
            )
        return normalized

    @staticmethod
    def _build_tool_definitions() -> List[Dict[str, Any]]:
        """Return function-calling schema definitions."""
        return [
            {"type": "function", "function": {"name": "python_runner", "description": "Execute Python code for analysis/calculations.", "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}},
            {"type": "function", "function": {"name": "write_word", "description": "Write content to a .docx file.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "content": {"type": "string"}, "append": {"type": "boolean"}}, "required": ["file_path", "content"]}}},
            {"type": "function", "function": {"name": "read_word", "description": "Read paragraphs from a .docx file.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]}}},
            {"type": "function", "function": {"name": "read_excel", "description": "Read rows from Excel file.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "max_rows": {"type": "integer"}}, "required": ["file_path"]}}},
            {"type": "function", "function": {"name": "write_excel", "description": "Write tabular data to Excel file.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "data": {"type": "array", "items": {"type": "object"}}, "sheet_name": {"type": "string"}}, "required": ["file_path", "data"]}}},
            {"type": "function", "function": {"name": "read_pptx", "description": "Read text from PowerPoint.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]}}},
            {"type": "function", "function": {"name": "write_pptx", "description": "Write PowerPoint slides.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "title": {"type": "string"}, "slides": {"type": "array", "items": {"type": "object"}}}, "required": ["file_path", "title", "slides"]}}},
            {"type": "function", "function": {"name": "get_clipboard", "description": "Read clipboard content.", "parameters": {"type": "object", "properties": {}}}},
            {"type": "function", "function": {"name": "set_clipboard", "description": "Set clipboard content.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
            {"type": "function", "function": {"name": "delete_file", "description": "Delete a file from disk.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]}}},
            {"type": "function", "function": {"name": "move_file", "description": "Move or rename a file.", "parameters": {"type": "object", "properties": {"source": {"type": "string"}, "destination": {"type": "string"}}, "required": ["source", "destination"]}}},
            {"type": "function", "function": {"name": "read_pdf", "description": "Extract text from PDF.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "max_chars": {"type": "integer"}}, "required": ["file_path"]}}},
            {"type": "function", "function": {"name": "read_text_file", "description": "Read plain text file.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "max_lines": {"type": "integer"}}, "required": ["file_path"]}}},
            {"type": "function", "function": {"name": "write_text_file", "description": "Write plain text file.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "content": {"type": "string"}, "append": {"type": "boolean"}}, "required": ["file_path", "content"]}}},
            {"type": "function", "function": {"name": "edit_text_file", "description": "Replace text in file.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["file_path", "old_text", "new_text"]}}},
            {"type": "function", "function": {"name": "search_files", "description": "Search files by name.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "root_dir": {"type": "string"}}, "required": ["query"]}}},
            {"type": "function", "function": {"name": "search_by_content", "description": "Search files by content.", "parameters": {"type": "object", "properties": {"directory": {"type": "string"}, "query": {"type": "string"}, "extensions": {"type": "array", "items": {"type": "string"}}}, "required": ["directory", "query"]}}},
            {"type": "function", "function": {"name": "list_directory", "description": "List directory content.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
            {"type": "function", "function": {"name": "get_file_info", "description": "Get file metadata.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]}}},
            {"type": "function", "function": {"name": "get_directory_tree", "description": "Get directory tree.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "max_depth": {"type": "integer"}}, "required": ["path"]}}},
            {"type": "function", "function": {"name": "get_recent_files", "description": "Get recent files from directory.", "parameters": {"type": "object", "properties": {"directory": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["directory"]}}},
            {"type": "function", "function": {"name": "safe_operator", "description": "Run safe introspection operation.", "parameters": {"type": "object", "properties": {"operation": {"type": "string", "enum": ["get_python_version", "get_current_directory"]}}, "required": ["operation"]}}},
            {"type": "function", "function": {"name": "describe_image", "description": "Describe an image.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "prompt": {"type": "string"}, "detail": {"type": "string"}}, "required": ["file_path"]}}},
            {"type": "function", "function": {"name": "extract_text_from_image", "description": "Extract text from image.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "language": {"type": "string"}}, "required": ["file_path"]}}},
            {"type": "function", "function": {"name": "analyze_screenshot", "description": "Analyze screenshot content.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]}}},
            {"type": "function", "function": {"name": "analyze_chart", "description": "Analyze chart image.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]}}},
        ]

    def get_available_tools(self) -> List[str]:
        """Return names of all registered tools."""
        return list(self.available_functions.keys())

    def get_recent_conversations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return recent conversations from persistent store."""
        return self.conversation_store.get_recent_conversations(limit=limit)

    def get_conversation_history(self, conversation_id: int) -> List[Dict[str, Any]]:
        """Return full history for a conversation id."""
        return self.conversation_store.get_history(conversation_id)

    def update_conversation_title(self, conversation_id: int, title: str) -> bool:
        """Rename one conversation thread."""
        return self.conversation_store.update_conversation_title(conversation_id, title)

    def archive_conversation(self, conversation_id: int) -> bool:
        """Archive one conversation thread."""
        return self.conversation_store.archive_conversation(conversation_id)

    def delete_conversation(self, conversation_id: int) -> bool:
        """Delete one conversation thread permanently."""
        return self.conversation_store.delete_conversation(conversation_id)

    @staticmethod
    def _cancelled_result(operation: str, file_path: str | Path) -> ToolResult:
        """Return standard cancellation payload for guarded operations."""
        resolved = str(Path(file_path).expanduser().resolve())
        return ToolResult.fail(f"{operation} cancelled by confirmation policy", path=resolved)

    @staticmethod
    def _file_result(file_path: str | Path, message: str) -> ToolResult:
        """Return success payload including resolved file metadata."""
        path = Path(file_path).expanduser().resolve()
        size = path.stat().st_size if path.exists() and path.is_file() else None
        return ToolResult.ok(message=message, path=str(path), size=size)

    def _tool_read_word(self, file_path: str) -> ToolResult:
        """Read paragraphs and table count from a Word document."""
        try:
            agent = DocxAgent(file_path)
            return ToolResult.ok(output={"content": agent.read_paragraphs()[:500], "tables_count": len(agent.read_tables())})
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_write_word(self, file_path: str, content: str, append: bool = False) -> ToolResult:
        """Create or append text to a Word document."""
        try:
            from functions.office import word
            target = Path(file_path).expanduser()
            operation = self.safe_operator.modify_document if append and target.exists() else self.safe_operator.write_new
            description = "modify word document" if append and target.exists() else "create word document"
            ok = operation(target, lambda path: word.write_document(str(path), content, append), description=description)
            return self._file_result(target, f"Document saved to {target}") if ok else self._cancelled_result(description, target)
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_read_excel(self, file_path: str, max_rows: int = 100) -> ToolResult:
        """Read tabular preview from an Excel file."""
        try:
            dataframe = excel.read_excel(file_path)
            data = dataframe.head(max_rows).to_dict("records")
            return ToolResult.ok(output={"columns": list(dataframe.columns), "data": data, "total_rows": len(dataframe)})
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_write_excel(self, file_path: str, data: List[Dict[str, Any]], sheet_name: str = "Sheet1") -> ToolResult:
        """Write rows to an Excel workbook."""
        try:
            import pandas as pd
            target = Path(file_path).expanduser()
            ok = self.safe_operator.write_new(target, lambda path: excel.write_excel(str(path), pd.DataFrame(data), sheet_name=sheet_name), description="create excel file")
            return self._file_result(target, f"Excel file saved to {target}") if ok else self._cancelled_result("create excel file", target)
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_read_pptx(self, file_path: str) -> ToolResult:
        """Read text slides from a PowerPoint file."""
        try:
            slides = powerpoint.read_presentation(file_path)
            return ToolResult.ok(output={"slides": slides})
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_write_pptx(self, file_path: str, title: str, slides: List[Dict[str, str]]) -> ToolResult:
        """Create a PowerPoint presentation from structured slides."""
        try:
            target = Path(file_path).expanduser()

            def _write(path: Path) -> None:
                presentation = powerpoint.create_presentation(title)
                for slide_data in slides:
                    presentation.add_slide(slide_data.get("title", ""), slide_data.get("content", ""))
                presentation.save(str(path))

            ok = self.safe_operator.write_new(target, _write, description="create powerpoint presentation")
            return self._file_result(target, f"Presentation saved to {target}") if ok else self._cancelled_result("create powerpoint presentation", target)
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_get_clipboard(self) -> ToolResult:
        """Return current clipboard text content."""
        try:
            return ToolResult.ok(output={"content": clipboard.get_clipboard()})
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_set_clipboard(self, text: str) -> ToolResult:
        """Set system clipboard text content."""
        try:
            clipboard.set_clipboard(text)
            return ToolResult.ok(message="Text copied to clipboard")
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_delete_file(self, file_path: str) -> ToolResult:
        """Delete a file via guarded file operator."""
        try:
            ok = self.safe_operator.delete(file_path)
            return ToolResult.ok(message=f"Deleted {file_path}") if ok else self._cancelled_result("delete file", file_path)
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_move_file(self, source: str, destination: str) -> ToolResult:
        """Move or rename a file via guarded file operator."""
        try:
            ok = self.safe_operator.move(source, destination)
            return self._file_result(destination, f"Moved {source} to {destination}") if ok else self._cancelled_result("move file", source)
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_read_pdf(self, file_path: str, max_chars: int = 2000) -> ToolResult:
        """Extract text from PDF (with OCR fallback)."""
        try:
            result = ocr.smart_pdf_extract(file_path)
            text = result.get("text", "")
            content = text[:max_chars]
            if len(text) > max_chars:
                content += f"\n\n... [TRUNCATED: {len(text) - max_chars} chars]"
            return ToolResult.ok(output={"content": content, "is_scanned": result.get("is_scanned", False), "total_length": len(text)})
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_read_text_file(self, file_path: str, max_lines: Optional[int] = None) -> ToolResult:
        """Read a text file from the local filesystem."""
        try:
            result = explorer.read_text_file(file_path, max_lines)
            return result if isinstance(result, ToolResult) else ToolResult.ok(output=result)
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_write_text_file(self, file_path: str, content: str, append: bool = False) -> ToolResult:
        """Write or append text to a local file."""
        try:
            target = Path(file_path).expanduser()
            operation = self.safe_operator.modify_document if append and target.exists() else self.safe_operator.write_new
            description = "modify text file" if append and target.exists() else "create text file"
            ok = operation(target, lambda resolved: writer.write_text_file(resolved, content, append), description=description)
            return self._file_result(target, f"Text file saved to {target}") if ok else self._cancelled_result(description, target)
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_edit_text_file(self, file_path: str, old_text: str, new_text: str) -> ToolResult:
        """Replace a text fragment in a local file."""
        try:
            target = Path(file_path).expanduser()
            ok = self.safe_operator.modify_document(target, lambda resolved: writer.replace_in_file(resolved, old_text, new_text), description="modify text file")
            return self._file_result(target, f"Text updated in {target}") if ok else self._cancelled_result("modify text file", target)
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_search_files(self, query: str, root_dir: str = ".") -> ToolResult:
        """Search files by filename pattern."""
        try:
            result = explorer.search_files(root_dir, query)
            return result if isinstance(result, ToolResult) else ToolResult.ok(output=result)
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_list_directory(self, path: str) -> ToolResult:
        """List files and folders in a directory."""
        try:
            result = explorer.list_directory(path)
            return result if isinstance(result, ToolResult) else ToolResult.ok(output=result)
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_file_info(self, file_path: str) -> ToolResult:
        """Read filesystem metadata for one file."""
        try:
            result = explorer.get_file_info(file_path)
            return result if isinstance(result, ToolResult) else ToolResult.ok(output=result)
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_search_by_content(self, directory: str, query: str, extensions: Optional[List[str]] = None) -> ToolResult:
        """Search files by content query."""
        try:
            result = explorer.search_by_content(directory, query, extensions)
            return result if isinstance(result, ToolResult) else ToolResult.ok(output=result)
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_get_directory_tree(self, path: str, max_depth: int = 3) -> ToolResult:
        """Build recursive directory tree representation."""
        try:
            result = explorer.get_directory_tree(path, max_depth)
            return result if isinstance(result, ToolResult) else ToolResult.ok(output=result)
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_get_recent_files(self, directory: str, limit: int = 10) -> ToolResult:
        """Get recently modified files in one directory."""
        try:
            result = explorer.get_recent_files(directory, limit=limit)
            return result if isinstance(result, ToolResult) else ToolResult.ok(output=result)
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_python_runner(self, code: str) -> ToolResult:
        """Execute sandboxed Python code."""
        try:
            result = python_runner.run_code(code)
            return result if isinstance(result, ToolResult) else ToolResult.ok(output=result)
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_safe_operator(self, operation: str) -> ToolResult:
        """Run small safe runtime inspection commands."""
        try:
            if operation == "get_python_version":
                return ToolResult.ok(output=sys.version)
            if operation == "get_current_directory":
                return ToolResult.ok(output=os.getcwd())
            return ToolResult.fail(f"Unknown operation: {operation}")
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_describe_image(self, file_path: str, prompt: str = "Describe this image in detail.", detail: str = "high") -> ToolResult:
        """Run vision description on an image path."""
        try:
            from functions.vision import describe_image
            return describe_image(file_path, prompt, detail)
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_extract_text_from_image(self, file_path: str, language: str = "eng") -> ToolResult:
        """Extract text from image with vision OCR flow."""
        try:
            from functions.vision import extract_text_from_image
            return extract_text_from_image(file_path, language)
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_analyze_screenshot(self, file_path: str) -> ToolResult:
        """Analyze screenshot structure and visible content."""
        try:
            from functions.vision import analyze_screenshot
            return analyze_screenshot(file_path)
        except Exception as exc:
            return ToolResult.fail(str(exc))

    def _tool_analyze_chart(self, file_path: str) -> ToolResult:
        """Analyze chart image and trends."""
        try:
            from functions.vision import analyze_chart
            return analyze_chart(file_path)
        except Exception as exc:
            return ToolResult.fail(str(exc))
