import platform
import sys
import time

import torch


def print_separator(title):
    print("\n" + "=" * 60)
    print(f"===== {title.upper()}")
    print("=" * 60)


def fmt_tflops(flops, seconds):
    return f"{flops / seconds / 1e12:.2f} TFLOPS"


def fmt_gbs(bytes_, seconds):
    return f"{bytes_ / seconds / 1e9:.1f} GB/s"


def system_info():
    print_separator("System Information")
    print(f"Platform     : {platform.system()} {platform.release()}")
    print(f"Architecture : {platform.machine()}")
    print(f"Python       : {sys.version.split()[0]}")
    print(f"PyTorch      : {torch.__version__}")
    if torch.cuda.is_available():
        print(f"CUDA build   : {torch.version.cuda}")
        try:
            print(f"cuDNN        : {torch.backends.cudnn.version()}")
        except Exception:
            pass
        print(f"GPU count    : {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            p = torch.cuda.get_device_properties(i)
            print(
                f"  [{i}] {p.name} | "
                f"{p.total_memory / 1024**3:.1f} GB | "
                f"SMs={p.multi_processor_count} | "
                f"CC={p.major}.{p.minor}"
            )
    else:
        print("CUDA         : NOT AVAILABLE - falling back to CPU")
        print(f"CPU threads  : {torch.get_num_threads()}")


def sync(device):
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def benchmark_matmul(device):
    """大規模 GEMM ベンチマーク (FP32 / TF32 / FP16 / BF16)"""
    print_separator("GEMM Throughput")
    sizes = [4096, 8192]
    iters = 10
    warmup = 3

    dtype_specs = []
    if device.type == "cuda":
        dtype_specs = [
            ("FP32", torch.float32, False),
            ("TF32", torch.float32, True),
            ("FP16", torch.float16, False),
            ("BF16", torch.bfloat16, False),
        ]
    else:
        dtype_specs = [("FP32", torch.float32, False)]

    for n in sizes:
        print(f"\n--- Square matmul: {n}x{n} ---")
        for label, dtype, use_tf32 in dtype_specs:
            if device.type == "cuda":
                torch.backends.cuda.matmul.allow_tf32 = use_tf32
                torch.backends.cudnn.allow_tf32 = use_tf32

            try:
                a = torch.randn(n, n, device=device, dtype=dtype)
                b = torch.randn(n, n, device=device, dtype=dtype)
            except RuntimeError as e:
                print(f"    {label:5s}: skipped ({e})")
                continue

            for _ in range(warmup):
                c = a @ b
            sync(device)
            t0 = time.perf_counter()
            for _ in range(iters):
                c = a @ b
            sync(device)
            dt = (time.perf_counter() - t0) / iters
            flops = 2.0 * n * n * n
            print(
                f"    {label:5s}: {dt * 1000:7.2f} ms/iter   "
                f"{fmt_tflops(flops, dt):>12s}   "
                f"checksum={c.float().sum().item():.3e}"
            )
            del a, b, c
            if device.type == "cuda":
                torch.cuda.empty_cache()


def benchmark_memory_bandwidth(device):
    """メモリ帯域 (copy / add) を計測"""
    print_separator("Memory Bandwidth")
    n = 1 << 26  # 64M elements -> 256 MB at fp32
    iters = 20
    warmup = 3

    a = torch.randn(n, device=device, dtype=torch.float32)
    b = torch.randn(n, device=device, dtype=torch.float32)

    # copy
    for _ in range(warmup):
        b.copy_(a)
    sync(device)
    t0 = time.perf_counter()
    for _ in range(iters):
        b.copy_(a)
    sync(device)
    dt = (time.perf_counter() - t0) / iters
    print(f"    copy : {dt * 1000:.2f} ms   {fmt_gbs(2 * n * 4, dt)}")

    # element-wise add
    for _ in range(warmup):
        c = a + b
    sync(device)
    t0 = time.perf_counter()
    for _ in range(iters):
        c = a + b
    sync(device)
    dt = (time.perf_counter() - t0) / iters
    # 3バッファ (read a, read b, write c)
    print(f"    add  : {dt * 1000:.2f} ms   {fmt_gbs(3 * n * 4, dt)}")
    del a, b, c
    if device.type == "cuda":
        torch.cuda.empty_cache()


def benchmark_conv(device):
    """大規模 Conv2d (cuDNN) のベンチマーク"""
    print_separator("Conv2d Throughput")
    if device.type == "cuda":
        torch.backends.cudnn.benchmark = True

    cases = [
        # (batch, in_c, out_c, k, h, w)
        (16, 3, 64, 7, 224, 224),
        (16, 64, 128, 3, 112, 112),
        (16, 128, 256, 3, 56, 56),
        (16, 256, 512, 3, 28, 28),
    ]
    iters = 20
    warmup = 5

    for n, ic, oc, k, h, w in cases:
        x = torch.randn(n, ic, h, w, device=device, dtype=torch.float32)
        conv = torch.nn.Conv2d(ic, oc, kernel_size=k, padding=k // 2).to(device)
        with torch.no_grad():
            for _ in range(warmup):
                y = conv(x)
            sync(device)
            t0 = time.perf_counter()
            for _ in range(iters):
                y = conv(x)
            sync(device)
            dt = (time.perf_counter() - t0) / iters
        flops = 2.0 * n * oc * h * w * ic * k * k
        print(
            f"    bs={n:2d} {ic:3d}->{oc:3d} k={k} {h}x{w}: "
            f"{dt * 1000:6.2f} ms   {fmt_tflops(flops, dt):>10s}   "
            f"out={tuple(y.shape)}"
        )
        del x, y, conv
        if device.type == "cuda":
            torch.cuda.empty_cache()


def benchmark_train_step(device):
    """ResNet風モデルの学習ステップ反復"""
    print_separator("Training Step Throughput")
    try:
        import torchvision.models as models
        net = models.resnet50(weights=None).to(device)
        model_name = "torchvision.resnet50"
    except Exception:
        # torchvision が無くても自前で似た深さのCNNを組む
        layers = []
        in_c = 3
        for out_c in (64, 128, 256, 512):
            layers += [
                torch.nn.Conv2d(in_c, out_c, 3, padding=1),
                torch.nn.BatchNorm2d(out_c),
                torch.nn.ReLU(inplace=True),
                torch.nn.MaxPool2d(2),
            ]
            in_c = out_c
        layers += [torch.nn.AdaptiveAvgPool2d(1), torch.nn.Flatten(), torch.nn.Linear(512, 1000)]
        net = torch.nn.Sequential(*layers).to(device)
        model_name = "fallback CNN"

    print(f"    model    : {model_name}")
    n_params = sum(p.numel() for p in net.parameters())
    print(f"    params   : {n_params / 1e6:.2f} M")

    batch = 32 if device.type == "cuda" else 4
    x = torch.randn(batch, 3, 224, 224, device=device)
    target = torch.randint(0, 1000, (batch,), device=device)
    opt = torch.optim.SGD(net.parameters(), lr=1e-2, momentum=0.9)
    loss_fn = torch.nn.CrossEntropyLoss()

    # AMP if available
    use_amp = device.type == "cuda"
    scaler = torch.amp.GradScaler("cuda") if use_amp else None
    print(f"    batch    : {batch}, AMP: {use_amp}")

    # warmup
    for _ in range(3):
        opt.zero_grad(set_to_none=True)
        if use_amp:
            with torch.amp.autocast("cuda", dtype=torch.float16):
                out = net(x)
                loss = loss_fn(out, target)
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
        else:
            out = net(x)
            loss = loss_fn(out, target)
            loss.backward()
            opt.step()
    sync(device)

    iters = 30 if device.type == "cuda" else 5
    t0 = time.perf_counter()
    for _ in range(iters):
        opt.zero_grad(set_to_none=True)
        if use_amp:
            with torch.amp.autocast("cuda", dtype=torch.float16):
                out = net(x)
                loss = loss_fn(out, target)
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
        else:
            out = net(x)
            loss = loss_fn(out, target)
            loss.backward()
            opt.step()
    sync(device)
    dt = (time.perf_counter() - t0) / iters
    imgs_per_sec = batch / dt
    print(f"    {iters} iters avg: {dt * 1000:.2f} ms/iter   {imgs_per_sec:.1f} img/s")
    print(f"    final loss      : {loss.item():.4f}")
    del net, x, target, opt, loss_fn
    if device.type == "cuda":
        torch.cuda.empty_cache()


def vram_stress(device):
    """VRAM割り当て上限と利用状況の確認"""
    if device.type != "cuda":
        return
    print_separator("VRAM Stress")
    free0, total = torch.cuda.mem_get_info(device.index or 0)
    print(f"    total VRAM    : {total / 1024**3:.2f} GB")
    print(f"    free  before  : {free0 / 1024**3:.2f} GB")

    # 全空き容量の70%まで2GiB単位でブロック確保
    target_bytes = int(free0 * 0.70)
    block = 2 * 1024**3
    elements_per_block = block // 4  # float32
    blocks = []
    allocated = 0
    try:
        while allocated + block <= target_bytes:
            blocks.append(torch.empty(elements_per_block, dtype=torch.float32, device=device))
            allocated += block
        print(f"    allocated     : {allocated / 1024**3:.2f} GB across {len(blocks)} blocks")
        free1, _ = torch.cuda.mem_get_info(device.index or 0)
        print(f"    free  after   : {free1 / 1024**3:.2f} GB")
        print(f"    torch reserved: {torch.cuda.memory_reserved() / 1024**3:.2f} GB")
        print(f"    torch alloc.  : {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
    except RuntimeError as e:
        print(f"    OOM at {allocated / 1024**3:.2f} GB: {e}")
    finally:
        del blocks
        torch.cuda.empty_cache()


def main():
    overall_t0 = time.perf_counter()
    system_info()

    if torch.cuda.is_available():
        device = torch.device("cuda:0")
    else:
        device = torch.device("cpu")
    print(f"\nUsing device: {device}")

    benchmark_matmul(device)
    benchmark_memory_bandwidth(device)
    benchmark_conv(device)
    benchmark_train_step(device)
    vram_stress(device)

    overall_dt = time.perf_counter() - overall_t0
    print("\n" + "=" * 60)
    print(f"===== BENCHMARK COMPLETE (total: {overall_dt:.1f} s)")
    print("=" * 60)


if __name__ == "__main__":
    main()
