#!/usr/bin/env python3
"""Extract FFN tensor layout from a GGUF model for MoE upcycling."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


LAYER_TENSOR_RE = re.compile(
    r"^blk\.(?P<layer>\d+)\.(?P<kind>ffn_gate|ffn_up|ffn_down)\.weight$"
)
EXPECTED_FFN_KINDS = ("ffn_gate", "ffn_up", "ffn_down")


@dataclass(frozen=True)
class TensorRecord:
    layer: int
    kind: str
    name: str
    shape: list[int]


def _decode(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _shape_from_tensor(tensor: Any) -> list[int]:
    for attr in ("shape", "dimensions", "dims", "ne"):
        raw = getattr(tensor, attr, None)
        if raw is None:
            continue
        try:
            return [int(x) for x in raw]
        except TypeError:
            continue
    return []


def _load_reader(gguf_path: Path) -> Any:
    try:
        from gguf import GGUFReader  # type: ignore
    except ImportError:
        try:
            from gguf.gguf_reader import GGUFReader  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "gguf-py is required. Install it from llama.cpp: "
                "`pip install gguf` or use the gguf-py package from llama.cpp."
            ) from exc

    return GGUFReader(str(gguf_path))


def _parse_layers_filter(raw: str | None) -> set[int] | None:
    if not raw:
        return None

    selected: set[int] = set()
    for part in (token.strip() for token in raw.split(",")):
        if not part:
            continue
        if "-" in part:
            start_str, end_str = part.split("-", maxsplit=1)
            start = int(start_str)
            end = int(end_str)
            if end < start:
                raise ValueError(f"Invalid range '{part}'")
            selected.update(range(start, end + 1))
            continue
        selected.add(int(part))

    return selected


def extract_ffn_tensors(gguf_path: Path, selected_layers: set[int] | None) -> list[TensorRecord]:
    reader = _load_reader(gguf_path)
    tensors = getattr(reader, "tensors", None)
    if tensors is None:
        raise RuntimeError("GGUFReader does not expose `tensors`; unsupported gguf-py version.")

    records: list[TensorRecord] = []
    for tensor in tensors:
        name = _decode(getattr(tensor, "name", ""))
        if not isinstance(name, str):
            continue

        match = LAYER_TENSOR_RE.match(name)
        if not match:
            continue

        layer = int(match.group("layer"))
        if selected_layers is not None and layer not in selected_layers:
            continue

        records.append(
            TensorRecord(
                layer=layer,
                kind=match.group("kind"),
                name=name,
                shape=_shape_from_tensor(tensor),
            )
        )

    records.sort(key=lambda item: (item.layer, item.kind))
    return records


def _missing_kinds(records: list[TensorRecord]) -> dict[int, list[str]]:
    by_layer: dict[int, set[str]] = {}
    for record in records:
        by_layer.setdefault(record.layer, set()).add(record.kind)

    missing: dict[int, list[str]] = {}
    for layer, kinds in by_layer.items():
        expected = set(EXPECTED_FFN_KINDS)
        absent = sorted(expected - kinds)
        if absent:
            missing[layer] = absent
    return missing


def _print_table(records: list[TensorRecord]) -> None:
    if not records:
        print("No FFN tensors found.", file=sys.stderr)
        return

    layer_w = max(5, max(len(str(item.layer)) for item in records))
    kind_w = max(8, max(len(item.kind) for item in records))
    shape_w = max(5, max(len(str(tuple(item.shape))) for item in records))

    print(f"{'layer':<{layer_w}} {'kind':<{kind_w}} {'shape':<{shape_w}} name")
    print("-" * (layer_w + kind_w + shape_w + 8 + 24))
    for item in records:
        print(
            f"{item.layer:<{layer_w}} "
            f"{item.kind:<{kind_w}} "
            f"{str(tuple(item.shape)):<{shape_w}} "
            f"{item.name}"
        )


def _build_json_payload(gguf_path: Path, records: list[TensorRecord]) -> dict[str, Any]:
    layers: dict[str, dict[str, list[int]]] = {}
    for item in records:
        key = str(item.layer)
        layers.setdefault(key, {})[item.kind] = item.shape

    return {
        "model_path": str(gguf_path),
        "ffn_tensor_count": len(records),
        "layers": layers,
        "records": [asdict(item) for item in records],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract blk.N.{ffn_gate,ffn_up,ffn_down}.weight tensors from GGUF."
    )
    parser.add_argument("gguf_path", type=Path, help="Path to the .gguf model file")
    parser.add_argument(
        "--layers",
        type=str,
        default=None,
        help="Optional layer filter (e.g. '0,1,4-7')",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional JSON output file",
    )
    args = parser.parse_args()

    if not args.gguf_path.exists():
        print(f"Model not found: {args.gguf_path}", file=sys.stderr)
        return 1

    try:
        selected_layers = _parse_layers_filter(args.layers)
    except ValueError as exc:
        print(f"Invalid --layers value: {exc}", file=sys.stderr)
        return 1

    try:
        records = extract_ffn_tensors(args.gguf_path, selected_layers=selected_layers)
    except Exception as exc:  # noqa: BLE001
        print(f"Extraction failed: {exc}", file=sys.stderr)
        return 1

    _print_table(records)

    missing = _missing_kinds(records)
    if missing:
        print("\nMissing FFN tensors in some layers:", file=sys.stderr)
        for layer in sorted(missing):
            missing_kinds = ", ".join(missing[layer])
            print(f"- layer {layer}: {missing_kinds}", file=sys.stderr)

    if args.json_out is not None:
        payload = _build_json_payload(args.gguf_path, records)
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nJSON written to {args.json_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
