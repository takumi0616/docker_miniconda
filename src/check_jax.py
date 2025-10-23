#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JAX GPU 簡易チェック

- JAX / jaxlib のバージョン表示
- 利用可能デバイス一覧（CPU/GPU）
- GPU があれば簡単な JIT 計算を GPU 上で実行して確認
- GPU がなければ CPU での JIT 計算にフォールバック

使い方（コンテナ内例）:
  conda activate aimodel_env
  python src/check_jax.py
"""

from __future__ import annotations

import sys
import time
import platform

def main() -> int:
    print("=== JAX Environment Check ===")
    print(f"Python: {platform.python_version()} ({sys.executable})")

    try:
        import jax
        import jax.numpy as jnp
        print(f"jax: {getattr(jax, '__version__', 'unknown')}")
    except Exception as e:
        print("ERROR: Failed to import jax:", repr(e))
        return 1

    # jaxlib は独立パッケージの場合があるため別途 try
    try:
        import jaxlib  # type: ignore
        jaxlib_ver = getattr(jaxlib, "__version__", "unknown")
    except Exception:
        jaxlib_ver = "unknown"
    print(f"jaxlib: {jaxlib_ver}")

    # 利用可能デバイスを列挙
    try:
        all_devs = jax.devices()
        gpu_devs = jax.devices("gpu")
        cpu_devs = jax.devices("cpu")
    except Exception as e:
        print("ERROR: Failed to query devices:", repr(e))
        return 1

    print("\nDevices:")
    if not all_devs:
        print("  (no devices found)")
    for i, d in enumerate(all_devs):
        # jax 0.6 系では d.device_kind / d.platform が使える
        dev_kind = getattr(d, "device_kind", "unknown")
        platform_name = getattr(d, "platform", "unknown")
        # メモリ情報（存在しない環境もある）
        try:
            memory = getattr(d, "memory_size", None)
            mem_str = f"{int(memory/1024**3)} GiB" if memory else "unknown"
        except Exception:
            mem_str = "unknown"
        print(f"  [{i}] platform={platform_name}, kind={dev_kind}, id={getattr(d, 'id', 'n/a')}, memory={mem_str}")

    print(f"\nBackend default: {jax.default_backend()}")
    print(f"GPU count: {len(gpu_devs)} | CPU count: {len(cpu_devs)}")

    # テスト計算（GPU 優先）
    target_dev = gpu_devs[0] if gpu_devs else (cpu_devs[0] if cpu_devs else None)
    if target_dev is None:
        print("\nERROR: No JAX devices available.")
        return 1

    print(f"\nRunning a small JIT test on: platform={target_dev.platform}, kind={getattr(target_dev, 'device_kind', 'unknown')}")
    # シンプルな JIT 行列積
    @jax.jit
    def matmul(a, b):
        return a @ b + 1.0

    try:
        import numpy as np
    except Exception:
        np = None

    # 小さめの行列
    n = 1024
    if np is not None:
        a_h = np.random.RandomState(0).randn(n, n).astype("float32")
        b_h = np.random.RandomState(1).randn(n, n).astype("float32")
    else:
        # numpy がなければ jax.numpy で構築
        a_h = jnp.arange(n * n, dtype=jnp.float32).reshape(n, n) / 100.0
        b_h = jnp.flipud(a_h)

    # 指定デバイスへ転送
    a_d = jax.device_put(a_h, device=target_dev)
    b_d = jax.device_put(b_h, device=target_dev)

    # ウォームアップ（コンパイル）
    _ = matmul(a_d, b_d).block_until_ready()

    # 実行時間計測
    t0 = time.time()
    c = matmul(a_d, b_d).block_until_ready()
    t1 = time.time()

    # 結果の簡易要約
    try:
        # 単一デバイスなら .device() がある（sharded の場合は異なる）
        c_dev = getattr(c, "device", None)
        c_dev_str = str(c_dev()) if callable(c_dev) else str(c_dev)
    except Exception:
        c_dev_str = "unknown"

    # 値検証（平均値など）
    try:
        mean_val = float(jnp.mean(c).item())
        print(f"Result mean: {mean_val:.6f}")
    except Exception:
        print("Result mean: unknown")

    print(f"Execution time: {(t1 - t0)*1000:.1f} ms")
    print(f"Result device: {c_dev_str}")

    if gpu_devs:
        print("\nGPU is AVAILABLE and successfully executed the JIT test.")
    else:
        print("\nGPU is NOT available. The test ran on CPU.")

    print("\nOK: JAX environment check finished.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
