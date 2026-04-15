#!/usr/bin/env python3
"""Run virtual-group MoE initialization directly from a GGUF model."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import gguf

from extract_gguf_ffn import _decode, _load_reader, _parse_layers_filter
from virtual_group_init import DenseFFN, _build_router, _split_virtual_groups, _validate_shapes


@dataclass(frozen=True)
class LayerResult:
    layer: int
    status: str
    message: str
    dense_path: str | None = None
    moe_path: str | None = None
    meta_path: str | None = None
    dense_shape: dict[str, list[int]] | None = None
    expert_shape: dict[str, list[int]] | None = None


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


def _coerce_numpy(value: Any) -> np.ndarray | None:
    if isinstance(value, np.ndarray):
        return value
    if hasattr(value, "numpy"):
        arr = value.numpy()
        if isinstance(arr, np.ndarray):
            return arr
    if hasattr(value, "to_numpy"):
        arr = value.to_numpy()
        if isinstance(arr, np.ndarray):
            return arr
    return None


def _tensor_to_numpy(tensor: Any) -> np.ndarray:
    # gguf-py exposes quantized payloads in tensor.data; dequantize first when needed.
    tensor_type = getattr(tensor, "tensor_type", None)
    raw_data = getattr(tensor, "data", None)
    if tensor_type is not None and isinstance(raw_data, np.ndarray):
        try:
            arr = gguf.dequantize(raw_data, tensor_type)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Failed to dequantize GGUF tensor: {exc}") from exc
    else:
        arr = None

    if arr is None:
        for attr in ("data", "tensor", "weights", "values"):
            raw = getattr(tensor, attr, None)
            if raw is None:
                continue
            arr = _coerce_numpy(raw)
            if arr is not None:
                break
        else:
            arr = _coerce_numpy(tensor)

    if arr is None:
        raise RuntimeError(
            "Could not convert GGUF tensor to numpy array. "
            "Unsupported gguf-py tensor representation."
        )

    arr = np.array(arr, copy=False)
    expected_shape = tuple(_shape_from_tensor(tensor))
    if expected_shape and tuple(arr.shape) != expected_shape and arr.ndim == 2:
        if tuple(arr.T.shape) == expected_shape:
            arr = arr.T

    if arr.ndim == 1:
        shape = _shape_from_tensor(tensor)
        if len(shape) >= 2 and int(np.prod(shape)) == arr.size:
            arr = arr.reshape(tuple(shape))
    if arr.ndim != 2:
        raise RuntimeError(f"Expected rank-2 tensor, got shape={arr.shape}.")
    return arr.astype(np.float32, copy=False)


def _collect_ffn_tensors(gguf_path: Path) -> dict[int, dict[str, Any]]:
    reader = _load_reader(gguf_path)
    tensors = getattr(reader, "tensors", None)
    if tensors is None:
        raise RuntimeError("GGUFReader does not expose `tensors`; unsupported gguf-py version.")

    collected: dict[int, dict[str, Any]] = {}
    for tensor in tensors:
        name = _decode(getattr(tensor, "name", ""))
        if not isinstance(name, str):
            continue
        parts = name.split(".")
        if len(parts) != 4:
            continue
        if parts[0] != "blk" or parts[3] != "weight":
            continue

        try:
            layer = int(parts[1])
        except ValueError:
            continue
        kind = parts[2]
        if kind not in {"ffn_gate", "ffn_up", "ffn_down"}:
            continue

        collected.setdefault(layer, {})[kind] = tensor
    return collected


def _run_layer_upcycling(
    layer: int,
    tensors: dict[str, Any],
    output_dir: Path,
    experts: int,
    top_k: int,
    router_init: str,
    router_std: float,
    seed: int,
    expert_scale: float,
    write_dense: bool,
) -> LayerResult:
    required = {"ffn_gate", "ffn_up", "ffn_down"}
    missing = sorted(required - set(tensors))
    if missing:
        return LayerResult(
            layer=layer,
            status="skipped",
            message=f"missing tensors: {', '.join(missing)}",
        )

    gate = _tensor_to_numpy(tensors["ffn_gate"])
    up = _tensor_to_numpy(tensors["ffn_up"])
    down = _tensor_to_numpy(tensors["ffn_down"])
    dense_ffn = DenseFFN(gate=gate, up=up, down=down)
    _validate_shapes(dense_ffn, experts=experts)

    ffn_dim, hidden_dim = gate.shape
    gate_experts, up_experts, down_experts = _split_virtual_groups(
        dense_ffn,
        experts=experts,
        expert_scale=expert_scale,
    )
    router_weight = _build_router(
        hidden_dim=hidden_dim,
        experts=experts,
        mode=router_init,
        std=router_std,
        seed=seed + layer,
    )

    dense_path: Path | None = None
    dense_shape = {
        "ffn_gate": list(gate.shape),
        "ffn_up": list(up.shape),
        "ffn_down": list(down.shape),
    }

    if write_dense:
        dense_dir = output_dir / "dense"
        dense_dir.mkdir(parents=True, exist_ok=True)
        dense_path = dense_dir / f"blk_{layer:03d}_dense_ffn.npz"
        np.savez_compressed(
            dense_path,
            ffn_gate=gate,
            ffn_up=up,
            ffn_down=down,
        )

    moe_dir = output_dir / "moe_init"
    meta_dir = output_dir / "metadata"
    moe_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    moe_path = moe_dir / f"blk_{layer:03d}_moe_init.npz"
    np.savez_compressed(
        moe_path,
        gate_experts=gate_experts,
        up_experts=up_experts,
        down_experts=down_experts,
        router_weight=router_weight,
    )

    meta_path = meta_dir / f"blk_{layer:03d}_moe_init.json"
    meta = {
        "layer": layer,
        "experts": experts,
        "top_k": top_k,
        "router_init": router_init,
        "router_std": router_std,
        "seed": seed + layer,
        "expert_scale": expert_scale,
        "dense_shape": dense_shape,
        "expert_shape": {
            "gate_experts": list(gate_experts.shape),
            "up_experts": list(up_experts.shape),
            "down_experts": list(down_experts.shape),
            "router_weight": list(router_weight.shape),
        },
        "split_chunk": ffn_dim // experts,
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return LayerResult(
        layer=layer,
        status="ok",
        message="upcycled",
        dense_path=str(dense_path) if dense_path is not None else None,
        moe_path=str(moe_path),
        meta_path=str(meta_path),
        dense_shape=dense_shape,
        expert_shape=meta["expert_shape"],
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Start MoE upcycling from GGUF FFN tensors (virtual-group init)."
    )
    parser.add_argument("--gguf-path", type=Path, required=True, help="Input dense GGUF model")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output directory")
    parser.add_argument("--experts", type=int, required=True, help="Number of experts N")
    parser.add_argument("--top-k", type=int, default=2, help="Active experts K (top-k)")
    parser.add_argument("--layers", type=str, default=None, help="Layer filter, e.g. '0,1,4-7'")
    parser.add_argument("--max-blocks", type=int, default=None, help="Optional cap for quick POC")
    parser.add_argument("--seed", type=int, default=42, help="Random seed base")
    parser.add_argument(
        "--router-init",
        choices=("normal", "uniform", "zeros"),
        default="normal",
        help="Router init distribution",
    )
    parser.add_argument("--router-std", type=float, default=0.02, help="Router init scale")
    parser.add_argument("--expert-scale", type=float, default=1.0, help="Optional expert scaling")
    parser.add_argument(
        "--no-dense-export",
        action="store_true",
        help="Skip exporting intermediate dense FFN npz files",
    )
    args = parser.parse_args()

    if not args.gguf_path.exists():
        print(f"Model not found: {args.gguf_path}", file=sys.stderr)
        return 1
    if args.experts < 2:
        print("--experts must be >= 2", file=sys.stderr)
        return 1
    if args.top_k < 1 or args.top_k > args.experts:
        print("--top-k must satisfy 1 <= top-k <= experts", file=sys.stderr)
        return 1
    if args.max_blocks is not None and args.max_blocks < 1:
        print("--max-blocks must be >= 1", file=sys.stderr)
        return 1

    try:
        selected_layers = _parse_layers_filter(args.layers)
    except ValueError as exc:
        print(f"Invalid --layers value: {exc}", file=sys.stderr)
        return 1

    try:
        layer_map = _collect_ffn_tensors(args.gguf_path)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to load GGUF tensors: {exc}", file=sys.stderr)
        return 1

    layers = sorted(layer_map)
    if selected_layers is not None:
        layers = [layer for layer in layers if layer in selected_layers]
    if args.max_blocks is not None:
        layers = layers[: args.max_blocks]
    if not layers:
        print("No matching FFN layers found to upcycle.", file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)

    results: list[LayerResult] = []
    for layer in layers:
        try:
            result = _run_layer_upcycling(
                layer=layer,
                tensors=layer_map[layer],
                output_dir=args.output_dir,
                experts=args.experts,
                top_k=args.top_k,
                router_init=args.router_init,
                router_std=args.router_std,
                seed=args.seed,
                expert_scale=args.expert_scale,
                write_dense=not args.no_dense_export,
            )
        except Exception as exc:  # noqa: BLE001
            result = LayerResult(layer=layer, status="error", message=str(exc))
        results.append(result)
        print(f"[{result.status}] layer={layer} {result.message}")

    summary = {
        "gguf_path": str(args.gguf_path),
        "output_dir": str(args.output_dir),
        "experts": args.experts,
        "top_k": args.top_k,
        "router_init": args.router_init,
        "router_std": args.router_std,
        "seed": args.seed,
        "expert_scale": args.expert_scale,
        "layers_requested": args.layers,
        "max_blocks": args.max_blocks,
        "results": [asdict(item) for item in results],
    }
    summary_path = args.output_dir / "upcycle_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    ok_count = sum(1 for item in results if item.status == "ok")
    print(f"\n[done] upcycled {ok_count}/{len(results)} layers")
    print(f"[done] summary: {summary_path}")

    return 0 if ok_count > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
