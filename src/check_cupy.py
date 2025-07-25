import cupy
try:
    print(cupy.show_config())
except Exception as e:
    print(f"CuPyの読み込みでエラーが発生しました: {e}")