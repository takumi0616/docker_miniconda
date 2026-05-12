#!/usr/bin/env bash
# scripts/build_pro_gpu.sh
#
# pro-gpu (RTX PRO 4500 Blackwell, sm_120, driver 580.x) 用に
# Docker イメージを CUDA 12.8 + PyTorch cu128 (sm_120 native) でリビルドする。
#
# 背景:
#   compose.gpu.yml のデフォルトは CUDA 12.4 + pytorch-cuda=12.4 だが、
#   Blackwell sm_120 のネイティブバイナリは PyTorch cu128 ホイール (PyTorch 2.7+)
#   から提供される。cu124 だと PTX JIT 経由になり、Xid 13 (deaddead) を踏みやすい。
#
# 使い方:
#   ./scripts/build_pro_gpu.sh                # 既存キャッシュを使ってビルド
#   ./scripts/build_pro_gpu.sh --no-cache     # キャッシュ無効でフルビルド (推奨: 初回)
#   ./scripts/build_pro_gpu.sh --pip-override # ビルド後 pip cu128 で torch を強制上書き

set -euo pipefail

ok()    { printf "\033[32m[OK]\033[0m %s\n" "$*"; }
info()  { printf "\033[36m[..]\033[0m %s\n" "$*"; }
warn()  { printf "\033[33m[!!]\033[0m %s\n" "$*"; }
err()   { printf "\033[31m[ERR]\033[0m %s\n" "$*" >&2; }

CUDA_BASE_IMAGE="nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04"
PYTORCH_CUDA_VERSION="12.8"
NO_CACHE=""
PIP_OVERRIDE=0

for arg in "$@"; do
  case "$arg" in
    --no-cache) NO_CACHE="--no-cache" ;;
    --pip-override) PIP_OVERRIDE=1 ;;
    *) err "unknown arg: $arg"; exit 1 ;;
  esac
done

# プロジェクトルートへ
cd "$(dirname "$0")/.."

info "ビルド構成:"
echo "  BASE_IMAGE          = ${CUDA_BASE_IMAGE}"
echo "  PYTORCH_CUDA_VERSION = ${PYTORCH_CUDA_VERSION}"
echo "  --no-cache          = ${NO_CACHE:-(default: use cache)}"
echo "  --pip-override      = $([ ${PIP_OVERRIDE} -eq 1 ] && echo yes || echo no)"

# 既存コンテナの停止
if sudo docker ps --format '{{.Names}}' | grep -q "takumi0616-project"; then
  info "既存コンテナを停止"
  sudo docker compose -f compose.yml -f compose.gpu.yml down
fi

# ビルド
info "イメージをビルド (時間がかかります)"
CUDA_BASE_IMAGE="${CUDA_BASE_IMAGE}" \
PYTORCH_CUDA_VERSION="${PYTORCH_CUDA_VERSION}" \
sudo -E docker compose -f compose.yml -f compose.gpu.yml build ${NO_CACHE}

# コンテナ起動
info "コンテナを起動"
CUDA_BASE_IMAGE="${CUDA_BASE_IMAGE}" \
PYTORCH_CUDA_VERSION="${PYTORCH_CUDA_VERSION}" \
HOSTNAME="${HOSTNAME}" \
sudo -E docker compose -f compose.yml -f compose.gpu.yml up -d

# pip 上書き (任意)
if [ ${PIP_OVERRIDE} -eq 1 ]; then
  info "PyTorch を pip cu128 ホイールで強制上書き"
  sudo docker compose -f compose.yml -f compose.gpu.yml exec -T app bash -lc \
    "conda run -n swinunet_env pip install --upgrade --force-reinstall \
      --retries 5 --timeout 120 \
      torch torchvision torchaudio \
      --index-url https://download.pytorch.org/whl/cu128"
fi

# 検証
info "PyTorch / sm_120 検証"
sudo docker compose -f compose.yml -f compose.gpu.yml exec -T app bash -lc \
  "conda run -n swinunet_env python -c '
import torch
print(\"torch :\", torch.__version__)
print(\"cuda  :\", torch.version.cuda)
print(\"cudnn :\", torch.backends.cudnn.version())
print(\"arches:\", torch.cuda.get_arch_list())
print(\"device:\", torch.cuda.get_device_name(0))
print(\"capab :\", torch.cuda.get_device_capability(0))
assert torch.cuda.is_available(), \"CUDA not available!\"
arches = torch.cuda.get_arch_list()
if any(a.startswith(\"sm_12\") for a in arches):
    print(\"OK: sm_120 native binary present\")
else:
    print(\"WARN: sm_120 native binary NOT in arch list -> PTX JIT fallback (Xid 13 risk)\")
    print(\"     Consider rerunning with --pip-override\")
'"

ok "ビルドと検証完了"
echo
echo "学習を再開する場合:"
echo "  sudo docker compose -f compose.yml -f compose.gpu.yml exec app bash"
echo "  # コンテナ内:"
echo "  cd /app/src/FrontLine"
echo "  notify-run pro-gpu -- nohup python main_v7.py --region jp --input-option option2 \\"
echo "    --resolution 0p25 --epochs 250 --data-dir /data/datasets/255_255 \\"
echo "    > output_v7_jp_opt2.log 2>&1 &"
