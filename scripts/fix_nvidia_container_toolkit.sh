#!/usr/bin/env bash
# scripts/fix_nvidia_container_toolkit.sh
#
# ドライバロールバック後に Docker から GPU が見えなくなった状態を修復する。
#
# 症状:
#   $ docker compose -f compose.yml -f compose.gpu.yml up -d
#   Error response from daemon: could not select device driver "nvidia" with capabilities: [[gpu]]
#
# 原因:
#   apt purge '^nvidia-.*' 等の広いパターンで nvidia-container-toolkit まで
#   巻き添えで削除されたが、/etc/docker/daemon.json には nvidia ランタイム定義が残存しているため、
#   Docker は実体のないバイナリを呼びにいって失敗する。
#
# 復旧手順:
#   1. nvidia-container-toolkit を再インストール
#   2. Docker ランタイム設定を再生成
#   3. Docker daemon を再起動
#   4. 動作確認

set -euo pipefail

ok()    { printf "\033[32m[OK]\033[0m %s\n" "$*"; }
info()  { printf "\033[36m[..]\033[0m %s\n" "$*"; }
warn()  { printf "\033[33m[!!]\033[0m %s\n" "$*"; }
err()   { printf "\033[31m[ERR]\033[0m %s\n" "$*" >&2; }

if [ "$(id -u)" -ne 0 ]; then
  err "sudo で実行してください"; exit 1
fi

echo "===== nvidia-container-toolkit 修復 ====="

# ---- Phase 1: 再インストール ----
info "nvidia-container-toolkit を再インストール"
apt-get update
apt-get install -y nvidia-container-toolkit

# ---- Phase 2: Docker ランタイム再構成 ----
info "Docker ランタイム設定を再生成"
nvidia-ctk runtime configure --runtime=docker

# ---- Phase 3: Docker 再起動 ----
info "Docker daemon を再起動"
systemctl restart docker

# ---- Phase 4: 動作確認 ----
info "GPU 動作確認 (ホスト側)"
docker info 2>/dev/null | grep -iE "Runtimes|nvidia" || true

echo
info "テストコンテナで nvidia-smi"
if docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi; then
  ok "Docker から GPU 認識 OK"
else
  err "まだエラーが出ています。/etc/docker/daemon.json と nvidia-ctk のログを確認してください。"
  exit 1
fi

echo
ok "修復完了。コンテナを起動してください:"
echo "  CUDA_BASE_IMAGE=\"nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04\" \\"
echo "  PYTORCH_CUDA_VERSION=12.8 \\"
echo "  HOSTNAME=\$HOSTNAME \\"
echo "  sudo -E docker compose -f compose.yml -f compose.gpu.yml up -d"
