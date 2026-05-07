"""Context compression utilities for BISSI."""

from __future__ import annotations

from typing import Any, Dict, List


class ContextManager:
    """Manage token estimation and lossy context compression."""

    def __init__(self, token_limit: int = 6000, max_tool_result_len: int = 500) -> None:
        """Initialize compression thresholds."""
        self.token_limit = token_limit
        self.max_tool_result_len = max_tool_result_len

    def estimate_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """Estimate token usage with len(chars)//4 heuristic."""
        total = 0
        for message in messages:
            total += len(str(message.get("content", "")))
        return max(1, total // 4)

    def maybe_compress(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compress context only when estimated tokens exceed configured limit."""
        if self.estimate_tokens(messages) <= self.token_limit:
            return messages
        return self._compress_context(messages)

    def _compress_context(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compress tool payloads while preserving critical conversation anchors."""
        if not messages:
            return messages

        system_indexes = [i for i, msg in enumerate(messages) if msg.get("role") == "system"]
        user_indexes = [i for i, msg in enumerate(messages) if msg.get("role") == "user"]
        assistant_indexes = [i for i, msg in enumerate(messages) if msg.get("role") == "assistant"]

        keep_indexes = set(system_indexes)
        if user_indexes:
            keep_indexes.add(user_indexes[-1])
        keep_indexes.update(assistant_indexes[-2:])

        tool_indexes = [i for i, msg in enumerate(messages) if msg.get("role") == "tool"]
        newest_tool_indexes = set(tool_indexes[-3:])

        compressed: List[Dict[str, Any]] = []
        for idx, message in enumerate(messages):
            role = message.get("role")
            content = str(message.get("content", ""))
            updated = dict(message)

            if role == "tool":
                if idx not in newest_tool_indexes:
                    # WHY: old tool details are high-cost and low-value for next steps.
                    updated["content"] = "[tool result archivé]"
                elif len(content) > self.max_tool_result_len:
                    original_len = len(content)
                    updated["content"] = (
                        f"{content[:self.max_tool_result_len]}\n[tronqué: {original_len - self.max_tool_result_len} chars]"
                    )

            if idx in keep_indexes or role == "tool":
                compressed.append(updated)
            else:
                if role in {"user", "assistant"}:
                    compressed.append(updated)

        return compressed
