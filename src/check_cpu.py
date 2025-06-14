import platform
import sys

def print_separator(title):
    """セクションごとの区切り線とタイトルを印刷する"""
    print("\n" + "="*60)
    print(f"===== {title.upper()} CHECKER")
    print("="*60)

def check_system_info():
    """システムとCPUの情報を表示する"""
    print_separator("System & CPU Information")
    print(f"Python Version: {sys.version}")
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")

    try:
        import psutil
        print(f"CPU Physical Cores: {psutil.cpu_count(logical=False)}")
        print(f"CPU Logical Cores: {psutil.cpu_count(logical=True)}")
        total_mem = psutil.virtual_memory().total / (1024**3)
        print(f"Total Memory: {total_mem:.2f} GB")
    except ImportError:
        print("\n'psutil' is not installed. CPU core and memory details are not available.")
        print("To get more details, run: pip install psutil")
    except Exception as e:
        print(f"Could not retrieve CPU/Memory details: {e}")


def check_pytorch():
    """PyTorchのCPU動作を確認する"""
    print_separator("PyTorch")
    try:
        import torch
        print(f"PyTorch Version: {torch.__version__}")
        
        # GPUが利用できないことを確認
        if torch.cuda.is_available():
            print("Warning: GPU is available, but this script is for CPU check.")
            device = torch.device("cuda")
        else:
            print("CUDA (GPU support): Not available. Running on CPU.")
            device = torch.device("cpu")
        
        print(f"Using device: {device}")

        # 簡単なテンソル演算をCPUで実行
        x = torch.tensor([[1, 2], [3, 4]], dtype=torch.float32, device=device)
        y = torch.tensor([[5, 6], [7, 8]], dtype=torch.float32, device=device)
        z = torch.matmul(x, y)
        
        print("\nPerforming a sample tensor multiplication (2x2 matrix)...")
        print("Result:")
        print(z)
        print("\nPyTorch CPU check: PASSED")

    except ImportError:
        print("PyTorch is not installed in this environment.")
    except Exception as e:
        print(f"An error occurred during PyTorch check: {e}")
        print("PyTorch CPU check: FAILED")


def check_tensorflow():
    """TensorFlowのCPU動作を確認する"""
    print_separator("TensorFlow")
    try:
        import tensorflow as tf
        print(f"TensorFlow Version: {tf.__version__}")

        # 利用可能な物理デバイスリストを取得
        physical_devices = tf.config.list_physical_devices()
        print(f"Available physical devices: {[device.name for device in physical_devices]}")
        
        gpu_devices = tf.config.list_physical_devices('GPU')
        if not gpu_devices:
            print("GPU: Not available. Running on CPU.")
        else:
            print("Warning: GPU is available, but this script is for CPU check.")

        # 簡単なテンソル演算をCPUで実行
        with tf.device('/CPU:0'):
            x = tf.constant([[1, 2], [3, 4]], dtype=tf.float32)
            y = tf.constant([[5, 6], [7, 8]], dtype=tf.float32)
            z = tf.matmul(x, y)

            print("\nPerforming a sample tensor multiplication (2x2 matrix)...")
            print("Result:")
            print(z)
        print("\nTensorFlow CPU check: PASSED")

    except ImportError:
        print("TensorFlow is not installed in this environment.")
    except Exception as e:
        print(f"An error occurred during TensorFlow check: {e}")
        print("TensorFlow CPU check: FAILED")


def check_common_libs():
    """NumpyとScikit-learnの動作を確認する"""
    print_separator("Numpy & Scikit-learn")
    try:
        import numpy as np
        print(f"Numpy Version: {np.__version__}")
        
        # 簡単なNumpy演算
        arr = np.array([1, 2, 3, 4, 5])
        print(f"Numpy array created: {arr}")
        print(f"Mean of the array: {np.mean(arr)}")
        print("Numpy check: PASSED")
    except ImportError:
        print("Numpy is not installed in this environment.")
    except Exception as e:
        print(f"An error occurred during Numpy check: {e}")

    print("-" * 30)

    try:
        import sklearn
        print(f"Scikit-learn Version: {sklearn.__version__}")
        print("Scikit-learn check: PASSED")
    except ImportError:
        print("Scikit-learn is not installed in this environment.")
    except Exception as e:
        print(f"An error occurred during Scikit-learn check: {e}")


if __name__ == "__main__":
    print("Starting CPU environment check...")
    check_system_info()
    check_pytorch()
    check_tensorflow()
    check_common_libs()
    print("\n" + "="*60)
    print("===== CHECK COMPLETE")
    print("="*60)