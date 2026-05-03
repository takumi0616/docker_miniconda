import platform
import sys
import time
import math


def print_separator(title):
    """セクションごとの区切り線とタイトルを印刷する"""
    print("\n" + "=" * 60)
    print(f"===== {title.upper()}")
    print("=" * 60)


def fmt_gflops(flops, seconds):
    return f"{flops / seconds / 1e9:.2f} GFLOPS"


def _mp_worker(*_args):
    """multiprocessing.Pool用のワーカ。エラトステネスの篩でCPUを焼く。"""
    n = 2_000_000
    sieve = bytearray(b"\x01") * (n + 1)
    sieve[0] = sieve[1] = 0
    i = 2
    while i * i <= n:
        if sieve[i]:
            sieve[i * i :: i] = b"\x00" * (((n - i * i) // i) + 1)
        i += 1
    return sum(sieve)


def check_system_info():
    """システムとCPUの情報を表示する"""
    print_separator("System & CPU Information")
    print(f"Python Version: {sys.version}")
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Processor: {platform.processor()}")

    try:
        import psutil
        print(f"CPU Physical Cores: {psutil.cpu_count(logical=False)}")
        print(f"CPU Logical Cores: {psutil.cpu_count(logical=True)}")
        freq = psutil.cpu_freq()
        if freq:
            print(f"CPU Frequency: current={freq.current:.0f} MHz, max={freq.max:.0f} MHz")
        vm = psutil.virtual_memory()
        print(f"Total Memory: {vm.total / (1024**3):.2f} GB")
        print(f"Available Memory: {vm.available / (1024**3):.2f} GB")
    except ImportError:
        print("\n'psutil' is not installed. CPU core and memory details are not available.")
        print("To get more details, run: pip install psutil")
    except Exception as e:
        print(f"Could not retrieve CPU/Memory details: {e}")


def stress_numpy():
    """NumPyによる大規模行列演算 / FFT / 固有値分解の負荷ベンチマーク"""
    print_separator("NumPy Heavy Benchmark")
    try:
        import numpy as np
        print(f"NumPy Version: {np.__version__}")
        try:
            np.show_config()
        except Exception:
            pass

        rng = np.random.default_rng(0)

        # ----- 1. 大規模 GEMM (float64) -----
        n = 4096
        print(f"\n[1] Dense GEMM: {n}x{n} float64, 5 iterations")
        a = rng.standard_normal((n, n), dtype=np.float64)
        b = rng.standard_normal((n, n), dtype=np.float64)
        # warmup
        np.matmul(a, b)
        iters = 5
        t0 = time.perf_counter()
        for _ in range(iters):
            c = np.matmul(a, b)
        dt = (time.perf_counter() - t0) / iters
        flops = 2.0 * n * n * n  # 行列積のFLOPs
        print(f"    avg time : {dt * 1000:.1f} ms/iter")
        print(f"    perf     : {fmt_gflops(flops, dt)}")
        print(f"    checksum : {float(c.sum()):.4e}")

        # ----- 2. GEMM (float32) -----
        n = 4096
        print(f"\n[2] Dense GEMM: {n}x{n} float32, 5 iterations")
        af = a.astype(np.float32)
        bf = b.astype(np.float32)
        np.matmul(af, bf)
        t0 = time.perf_counter()
        for _ in range(iters):
            cf = np.matmul(af, bf)
        dt = (time.perf_counter() - t0) / iters
        print(f"    avg time : {dt * 1000:.1f} ms/iter")
        print(f"    perf     : {fmt_gflops(flops, dt)}")
        print(f"    checksum : {float(cf.sum()):.4e}")

        # ----- 3. FFT 大規模 -----
        size = 1 << 22  # 4M points
        print(f"\n[3] FFT: 1D complex128, n={size}, 5 iterations")
        x = rng.standard_normal(size) + 1j * rng.standard_normal(size)
        np.fft.fft(x)
        t0 = time.perf_counter()
        for _ in range(5):
            y = np.fft.fft(x)
        dt = (time.perf_counter() - t0) / 5
        # FFTのFLOPs近似 5 N log2 N
        flops = 5.0 * size * math.log2(size)
        print(f"    avg time : {dt * 1000:.1f} ms/iter")
        print(f"    perf     : {fmt_gflops(flops, dt)}")
        print(f"    checksum : {float(np.abs(y).sum()):.4e}")

        # ----- 4. 固有値分解 -----
        m = 1024
        print(f"\n[4] Symmetric eigendecomposition: {m}x{m}")
        s = rng.standard_normal((m, m))
        s = (s + s.T) / 2
        t0 = time.perf_counter()
        w, _ = np.linalg.eigh(s)
        dt = time.perf_counter() - t0
        print(f"    time     : {dt * 1000:.1f} ms")
        print(f"    min/max eigenvalue: {w.min():.3f} / {w.max():.3f}")

        # ----- 5. SVD -----
        m, k = 2048, 1024
        print(f"\n[5] SVD: {m}x{k}")
        s = rng.standard_normal((m, k))
        t0 = time.perf_counter()
        _, sv, _ = np.linalg.svd(s, full_matrices=False)
        dt = time.perf_counter() - t0
        print(f"    time     : {dt * 1000:.1f} ms")
        print(f"    top singular values: {sv[:5]}")

        print("\nNumPy heavy benchmark: PASSED")
    except ImportError:
        print("NumPy is not installed in this environment.")
    except Exception as e:
        print(f"NumPy benchmark FAILED: {e}")


def stress_pytorch_cpu():
    """PyTorchのCPU向け重ベンチマーク"""
    print_separator("PyTorch CPU Heavy Benchmark")
    try:
        import torch
        print(f"PyTorch Version: {torch.__version__}")
        print(f"Threads (intra-op): {torch.get_num_threads()}")
        print(f"Threads (inter-op): {torch.get_num_interop_threads()}")
        print(f"MKL available: {torch.backends.mkl.is_available()}")
        print(f"OpenMP available: {torch.backends.openmp.is_available()}")

        if torch.cuda.is_available():
            print("Note: CUDA is available, but this benchmark is intentionally CPU-only.")
        device = torch.device("cpu")

        # ----- 1. 大規模 matmul (float32) -----
        n = 4096
        iters = 5
        print(f"\n[1] torch.matmul: {n}x{n} float32, {iters} iterations")
        a = torch.randn(n, n, device=device, dtype=torch.float32)
        b = torch.randn(n, n, device=device, dtype=torch.float32)
        torch.matmul(a, b)  # warmup
        t0 = time.perf_counter()
        for _ in range(iters):
            c = torch.matmul(a, b)
        dt = (time.perf_counter() - t0) / iters
        flops = 2.0 * n * n * n
        print(f"    avg time : {dt * 1000:.1f} ms/iter")
        print(f"    perf     : {fmt_gflops(flops, dt)}")
        print(f"    checksum : {c.sum().item():.4e}")

        # ----- 2. 畳み込み (Conv2d) -----
        print("\n[2] Conv2d forward: batch=8, 3->64, kernel=3, 512x512, 5 iterations")
        conv = torch.nn.Conv2d(3, 64, kernel_size=3, padding=1).to(device)
        x = torch.randn(8, 3, 512, 512, device=device)
        with torch.no_grad():
            conv(x)  # warmup
            t0 = time.perf_counter()
            for _ in range(5):
                y = conv(x)
            dt = (time.perf_counter() - t0) / 5
        print(f"    avg time : {dt * 1000:.1f} ms/iter")
        print(f"    output shape: {tuple(y.shape)}")

        # ----- 3. ミニNN学習ループ -----
        print("\n[3] Tiny MLP training: 512 hidden, 100 steps, batch=256")
        torch.manual_seed(0)
        model = torch.nn.Sequential(
            torch.nn.Linear(1024, 512),
            torch.nn.ReLU(),
            torch.nn.Linear(512, 512),
            torch.nn.ReLU(),
            torch.nn.Linear(512, 10),
        ).to(device)
        opt = torch.optim.SGD(model.parameters(), lr=1e-2)
        loss_fn = torch.nn.CrossEntropyLoss()
        xb = torch.randn(256, 1024, device=device)
        yb = torch.randint(0, 10, (256,), device=device)
        # warmup
        opt.zero_grad()
        loss_fn(model(xb), yb).backward()
        opt.step()
        t0 = time.perf_counter()
        for _ in range(100):
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()
        dt = time.perf_counter() - t0
        print(f"    100 steps total: {dt * 1000:.1f} ms ({dt * 10:.2f} ms/step)")
        print(f"    final loss     : {loss.item():.4f}")

        print("\nPyTorch CPU heavy benchmark: PASSED")
    except ImportError:
        print("PyTorch is not installed in this environment.")
    except Exception as e:
        print(f"PyTorch CPU benchmark FAILED: {e}")


def stress_tensorflow_cpu():
    """TensorFlowのCPU向け重ベンチマーク"""
    print_separator("TensorFlow CPU Heavy Benchmark")
    try:
        import os
        os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
        import tensorflow as tf
        print(f"TensorFlow Version: {tf.__version__}")
        gpus = tf.config.list_physical_devices("GPU")
        if gpus:
            print(f"Note: {len(gpus)} GPU(s) detected, but this benchmark is CPU-only.")
            tf.config.set_visible_devices([], "GPU")

        with tf.device("/CPU:0"):
            # ----- 1. 大規模 matmul -----
            n = 4096
            iters = 5
            print(f"\n[1] tf.matmul: {n}x{n} float32, {iters} iterations")
            a = tf.random.normal((n, n))
            b = tf.random.normal((n, n))

            @tf.function
            def matmul(x, y):
                return tf.linalg.matmul(x, y)

            matmul(a, b)  # trace + warmup
            t0 = time.perf_counter()
            for _ in range(iters):
                c = matmul(a, b)
            _ = c.numpy()  # force materialization
            dt = (time.perf_counter() - t0) / iters
            flops = 2.0 * n * n * n
            print(f"    avg time : {dt * 1000:.1f} ms/iter")
            print(f"    perf     : {fmt_gflops(flops, dt)}")

            # ----- 2. CNN forward -----
            print("\n[2] Keras CNN forward: batch=8, 256x256x3, 3 conv blocks, 5 iters")
            model = tf.keras.Sequential([
                tf.keras.layers.Input(shape=(256, 256, 3)),
                tf.keras.layers.Conv2D(32, 3, padding="same", activation="relu"),
                tf.keras.layers.Conv2D(64, 3, padding="same", activation="relu"),
                tf.keras.layers.MaxPool2D(),
                tf.keras.layers.Conv2D(128, 3, padding="same", activation="relu"),
                tf.keras.layers.GlobalAveragePooling2D(),
                tf.keras.layers.Dense(10),
            ])
            x = tf.random.normal((8, 256, 256, 3))
            model(x, training=False)  # warmup
            t0 = time.perf_counter()
            for _ in range(5):
                y = model(x, training=False)
            _ = y.numpy()
            dt = (time.perf_counter() - t0) / 5
            print(f"    avg time : {dt * 1000:.1f} ms/iter")
            print(f"    output shape: {tuple(y.shape)}")

        print("\nTensorFlow CPU heavy benchmark: PASSED")
    except ImportError:
        print("TensorFlow is not installed in this environment.")
    except Exception as e:
        print(f"TensorFlow CPU benchmark FAILED: {e}")


def stress_sklearn():
    """Scikit-learnのモデル学習負荷"""
    print_separator("Scikit-learn Heavy Benchmark")
    try:
        import sklearn
        from sklearn.datasets import make_classification
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression

        print(f"Scikit-learn Version: {sklearn.__version__}")
        print("\n[1] Generating synthetic dataset (50000 samples x 50 features)...")
        X, y = make_classification(
            n_samples=50000, n_features=50, n_informative=20,
            n_classes=4, random_state=0,
        )

        print("[2] RandomForest fit (n_estimators=200, n_jobs=-1)")
        rf = RandomForestClassifier(n_estimators=200, n_jobs=-1, random_state=0)
        t0 = time.perf_counter()
        rf.fit(X, y)
        dt = time.perf_counter() - t0
        print(f"    fit time : {dt:.2f} s")
        print(f"    train acc: {rf.score(X, y):.4f}")

        print("\n[3] LogisticRegression fit (saga, max_iter=200)")
        lr = LogisticRegression(solver="saga", max_iter=200, n_jobs=-1)
        t0 = time.perf_counter()
        lr.fit(X, y)
        dt = time.perf_counter() - t0
        print(f"    fit time : {dt:.2f} s")
        print(f"    train acc: {lr.score(X, y):.4f}")

        print("\nScikit-learn heavy benchmark: PASSED")
    except ImportError:
        print("Scikit-learn is not installed in this environment.")
    except Exception as e:
        print(f"Scikit-learn benchmark FAILED: {e}")


def stress_multiprocess():
    """全コアを使った純Pythonの計算負荷テスト"""
    print_separator("Multiprocess CPU Stress")
    try:
        import os
        from multiprocessing import Pool

        try:
            import psutil
            cores = psutil.cpu_count(logical=True) or os.cpu_count() or 1
        except ImportError:
            cores = os.cpu_count() or 1

        print(f"Spawning {cores} workers for prime sieve up to N=2,000,000 each")

        t0 = time.perf_counter()
        with Pool(cores) as pool:
            results = pool.map(_mp_worker, range(cores))
        dt = time.perf_counter() - t0
        print(f"    elapsed  : {dt:.2f} s")
        print(f"    primes   : {results[0]} (per worker)")
        print(f"    workers  : {len(results)} -> consistent: {len(set(results)) == 1}")
        print("\nMultiprocess CPU stress: PASSED")
    except Exception as e:
        print(f"Multiprocess CPU stress FAILED: {e}")


if __name__ == "__main__":
    print("Starting heavy CPU environment check...")
    overall_t0 = time.perf_counter()
    check_system_info()
    stress_numpy()
    stress_pytorch_cpu()
    stress_tensorflow_cpu()
    stress_sklearn()
    stress_multiprocess()
    overall_dt = time.perf_counter() - overall_t0
    print("\n" + "=" * 60)
    print(f"===== CHECK COMPLETE (total: {overall_dt:.1f} s)")
    print("=" * 60)
