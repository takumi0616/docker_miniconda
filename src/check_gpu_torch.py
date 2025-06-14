import torch
import platform
import sys

# システム情報
print("=== System Information ===")
print(f"Platform: {platform.system()}")
print(f"Architecture: {platform.machine()}")
print(f"Python version: {sys.version}")

# PyTorchのバージョン確認
print("\n=== PyTorch Information ===")
print(f"PyTorch version: {torch.__version__}")

# CUDAが利用可能か確認
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"cuDNN version: {torch.backends.cudnn.version()}")
    print(f"Number of GPUs available: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
        print(f"  Memory: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.1f} GB")
else:
    print("CUDA is not available - Running on CPU")
    print(f"Number of CPU cores: {torch.get_num_threads()}")

# 簡単なテンソル演算
print("\n=== Performance Test ===")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# テストテンソルの作成と演算
size = 1000
a = torch.randn(size, size).to(device)
b = torch.randn(size, size).to(device)

import time
start = time.time()
c = torch.matmul(a, b)
torch.cuda.synchronize() if torch.cuda.is_available() else None
end = time.time()

print(f"Matrix multiplication ({size}x{size}) took: {(end-start)*1000:.2f} ms")