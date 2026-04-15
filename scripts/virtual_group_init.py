#!/usr/bin/env python3
"""Create a Virtual Group MoE initialization from dense FFN tensors."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class DenseFFN:
    gate: np.ndarray
    up: np.ndarray
    down: np.ndarray


def _load_dense_ffn(npz_path: Path, gate_key: str, up_key: str, down_key: str) -> DenseFFN:
    with np.load(npz_path) as data:
        try:
            gate = np.array(data[gate_key], copy=False)
            up = np.array(data[up_key], copy=False)
            down = np.array(data[down_key], copy=False)
        except KeyError as exc:
            raise ValueError(
                f"Missing key in input npz: {exc}. "
                f"Expected keys: '{gate_key}', '{up_key}', '{down_key}'."
            ) from exc

    return DenseFFN(gate=gate, up=up, down=down)


def _validate_shapes(ffn: DenseFFN, experts: int) -> None:
    if experts < 2:
        raise ValueError("--experts must be >= 2")

    if ffn.gate.ndim != 2 or ffn.up.ndim != 2 or ffn.down.ndim != 2:
        raise ValueError("All FFN tensors must be rank-2 matrices.")

    ffn_dim, hidden_dim = ffn.gate.shape
    if ffn.up.shape != (ffn_dim, hidden_dim):
        raise ValueError(
            f"ffn_up shape mismatch. Expected {(ffn_dim, hidden_dim)}, got {ffn.up.shape}."
        )
    if ffn.down.shape != (hidden_dim, ffn_dim):
        raise ValueError(
            f"ffn_down shape mismatch. Expected {(hidden_dim, ffn_dim)}, got {ffn.down.shape}."
        )
    if ffn_dim % experts != 0:
        raise ValueError(
            f"ffn_dim={ffn_dim} is not divisible by experts={experts}. "
            "Virtual-group split requires an exact partition."
        )


def _build_router(hidden_dim: int, experts: int, mode: str, std: float, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    if mode == "normal":
        return rng.normal(0.0, std, size=(hidden_dim, experts)).astype(np.float32)
    if mode == "uniform":
        bound = std * np.sqrt(3.0)
        return rng.uniform(-bound, bound, size=(hidden_dim, experts)).astype(np.float32)
    if mode == "zeros":
        return np.zeros((hidden_dim, experts), dtype=np.float32)
    raise ValueError(f"Unsupported router mode: {mode}")


def _split_virtual_groups(ffn: DenseFFN, experts: int, expert_scale: float) -> tuple[np.ndarray, ...]:
    ffn_dim, hidden_dim = ffn.gate.shape
    chunk = ffn_dim // experts

    gate_experts = np.stack(
        [ffn.gate[i * chunk : (i + 1) * chunk, :] for i in range(experts)],
        axis=0,
    )
    up_experts = np.stack(
        [ffn.up[i * chunk : (i + 1) * chunk, :] for i in range(experts)],
        axis=0,
    )
    down_experts = np.stack(
        [ffn.down[:, i * chunk : (i + 1) * chunk] for i in range(experts)],
        axis=0,
    )

    if expert_scale != 1.0:
        gate_experts = gate_experts * expert_scale
        up_experts = up_experts * expert_scale
        down_experts = down_experts * expert_scale

    return (
        gate_experts.astype(np.float32),
        up_experts.astype(np.float32),
        down_experts.astype(np.float32),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Virtual-group MoE init for one dense FFN block. "
            "Input npz must contain dense tensors."
        )
    )
    parser.add_argument("--input-npz", type=Path, required=True, help="Input npz path")
    parser.add_argument("--output-npz", type=Path, required=True, help="Output npz path")
    parser.add_argument("--meta-out", type=Path, default=None, help="Optional metadata JSON path")
    parser.add_argument("--experts", type=int, required=True, help="Number of experts N")
    parser.add_argument("--top-k", type=int, default=2, help="Top-K experts used by router")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for router init")
    parser.add_argument(
        "--router-init",
        choices=("normal", "uniform", "zeros"),
        default="normal",
        help="Router init distribution",
    )
    parser.add_argument(
        "--router-std",
        type=float,
        default=0.02,
        help="Router std (normal) or derived bound (uniform)",
    )
    parser.add_argument(
        "--expert-scale",
        type=float,
        default=1.0,
        help="Optional scalar applied to all expert weights",
    )
    parser.add_argument("--gate-key", type=str, default="ffn_gate", help="Input key for gate")
    parser.add_argument("--up-key", type=str, default="ffn_up", help="Input key for up")
    parser.add_argument("--down-key", type=str, default="ffn_down", help="Input key for down")
    args = parser.parse_args()

    dense_ffn = _load_dense_ffn(
        npz_path=args.input_npz,
        gate_key=args.gate_key,
        up_key=args.up_key,
        down_key=args.down_key,
    )
    _validate_shapes(dense_ffn, experts=args.experts)

    ffn_dim, hidden_dim = dense_ffn.gate.shape
    chunk = ffn_dim // args.experts

    gate_experts, up_experts, down_experts = _split_virtual_groups(
        dense_ffn,
        experts=args.experts,
        expert_scale=args.expert_scale,
    )
    router_weight = _build_router(
        hidden_dim=hidden_dim,
        experts=args.experts,
        mode=args.router_init,
        std=args.router_std,
        seed=args.seed,
    )

    args.output_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.output_npz,
        gate_experts=gate_experts,
        up_experts=up_experts,
        down_experts=down_experts,
        router_weight=router_weight,
    )

    metadata = {
        "input_npz": str(args.input_npz),
        "output_npz": str(args.output_npz),
        "experts": args.experts,
        "top_k": args.top_k,
        "router_init": args.router_init,
        "router_std": args.router_std,
        "seed": args.seed,
        "expert_scale": args.expert_scale,
        "dense_shape": {
            "ffn_gate": list(dense_ffn.gate.shape),
            "ffn_up": list(dense_ffn.up.shape),
            "ffn_down": list(dense_ffn.down.shape),
        },
        "expert_shape": {
            "gate_experts": list(gate_experts.shape),
            "up_experts": list(up_experts.shape),
            "down_experts": list(down_experts.shape),
            "router_weight": list(router_weight.shape),
        },
        "split_chunk": chunk,
    }

    meta_path = args.meta_out or args.output_npz.with_suffix(".json")
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"[ok] MoE virtual-group init written: {args.output_npz}")
    print(f"[ok] Metadata written: {meta_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
