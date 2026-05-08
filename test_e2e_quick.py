#!/usr/bin/env python3
"""Quick E2E test: speed, tool use, clean communication."""

import sys
import time
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.agent import BissiAgent


def test(label: str, prompt: str, agent: BissiAgent, expect_tool: str = None):
    print(f"\n{'─'*60}")
    print(f"TEST: {label}")
    print(f"  → {prompt}")

    t0 = time.perf_counter()
    tool_called = []

    def on_tool_start(name, args):
        tool_called.append(name)
        print(f"  🔧 tool: {name}")

    try:
        response = agent.process_request(
            user_input=prompt,
            max_iterations=5,
            on_tool_start=on_tool_start,
        )
        elapsed = time.perf_counter() - t0

        speed = "✅ FAST" if elapsed < 30 else "⚠️  SLOW"
        tool_ok = "✅" if (expect_tool is None or expect_tool in tool_called) else "❌"
        comm_ok = "✅" if response and len(response.strip()) > 5 else "❌"

        print(f"  ⏱  {elapsed:.1f}s  {speed}")
        print(f"  🛠  tools={tool_called}  {tool_ok}")
        print(f"  💬 response preview: {response[:120].strip()!r}")
        print(f"  📣 communication  {comm_ok}")
        return elapsed, bool(tool_called), bool(response)

    except Exception as e:
        elapsed = time.perf_counter() - t0
        print(f"  ❌ ERROR after {elapsed:.1f}s: {e}")
        return elapsed, False, False


def main():
    print("="*60)
    print("BISSI AGENT — E2E QUICK TEST")
    print("3 criteria: speed | tool use | clean response")
    print("="*60)

    agent = BissiAgent()

    with tempfile.TemporaryDirectory() as tmp:
        results = []

        # 1. Speed + communication: simple factual question
        r = test("Réponse rapide sans outil", "Dis-moi juste 'Bonjour' en une phrase.", agent)
        results.append(r)

        # 2. Tool use: write a file
        r = test(
            "Écriture fichier (write_text_file)",
            f"Crée un fichier {tmp}/hello.txt avec le contenu 'Test BISSI OK'",
            agent,
            expect_tool="write_text_file",
        )
        results.append(r)

        # 3. Tool use: read back + communicate
        r = test(
            "Lecture fichier (read_text_file)",
            f"Lis le fichier {tmp}/hello.txt et dis-moi ce qu'il contient.",
            agent,
            expect_tool="read_text_file",
        )
        results.append(r)

    print("\n" + "="*60)
    print("SUMMARY")
    labels = ["Réponse rapide", "Écriture fichier", "Lecture fichier"]
    all_ok = True
    for label, (elapsed, used_tool, has_response) in zip(labels, results):
        speed_ok = elapsed < 30
        ok = speed_ok and has_response
        all_ok = all_ok and ok
        print(f"  {label}: {elapsed:.1f}s | tool={used_tool} | response={has_response} → {'✅' if ok else '❌'}")

    print()
    print("VERDICT:", "✅ PASS" if all_ok else "⚠️  ISSUES DETECTED")
    print("="*60)


if __name__ == "__main__":
    main()
