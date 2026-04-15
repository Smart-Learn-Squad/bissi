#!/usr/bin/env python3
"""Download and verify the offline research papers used by BISSI."""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class Paper:
    arxiv_id: str
    filename: str
    title: str


PAPERS: list[Paper] = [
    Paper("2210.17323", "01_gptq.pdf", "GPTQ"),
    Paper("2307.13304", "02_quip.pdf", "QuIP"),
    Paper("2302.01318", "03_speculative_sampling.pdf", "Speculative Sampling"),
    Paper("2005.11401", "04_rag.pdf", "RAG"),
    Paper("2307.03172", "05_lost_in_the_middle.pdf", "Lost in the Middle"),
    Paper("2106.09685", "06_lora.pdf", "LoRA"),
    Paper("2305.14314", "07_qlora.pdf", "QLoRA"),
]


def papers_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "papers"


def pdf_url(arxiv_id: str) -> str:
    return f"https://arxiv.org/pdf/{arxiv_id}.pdf"


def download_pdf(url: str, dest: Path) -> None:
    req = Request(url, headers={"User-Agent": "BissiResearchDownloader/1.0"})
    with urlopen(req, timeout=120) as resp, dest.open("wb") as out:
        shutil.copyfileobj(resp, out)


def verify(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def main() -> int:
    root = papers_dir()
    root.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    for paper in PAPERS:
        dest = root / paper.filename
        if not verify(dest):
            print(f"[download] {paper.title} -> {dest.name}")
            try:
                download_pdf(pdf_url(paper.arxiv_id), dest)
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{paper.filename}: {exc}")
                continue

        if verify(dest):
            size_mb = dest.stat().st_size / (1024 * 1024)
            print(f"[ok] {dest.name} ({size_mb:.2f} MB)")
        else:
            failures.append(f"{paper.filename}: missing or empty after download")

    if failures:
        print("\nFailures:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("\nAll papers downloaded and verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
