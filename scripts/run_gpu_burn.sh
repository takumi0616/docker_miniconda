#!/usr/bin/env bash
# scripts/run_gpu_burn.sh
#
# gpu-burn を使って GPU 単体のストレステストを実施する。
# 学習スタックに依存せず、純粋に GPU + ドライバ + 電源・PCIe 系の安定性を見る。
#
# 結果の解釈:
#   - 完走 (FAULTY: 0)        → ハード/ドライバ層は健全。training 側の問題（PyTorch カーネル等）
#   - 途中で Xid / FAULTY > 0 → ハード/firmware/電源/PCIe 層に問題あり (RMA / 別ドライバ検討)
#
# 使い方:
#   ./scripts/run_gpu_burn.sh [秒数]
#   既定: 1800 秒 (30 分)

set -euo pipefail

DURATION="${1:-1800}"
BURN_DIR="/tmp/gpu-burn"

ok()   { printf "\033[32m[OK]\033[0m %s\n" "$*"; }
info() { printf "\033[36m[..]\033[0m %s\n" "$*"; }
warn() { printf "\033[33m[!!]\033[0m %s\n" "$*"; }
err()  { printf "\033[31m[ERR]\033[0m %s\n" "$*" >&2; }

# 1. ビルド確認 / インストール
if [ ! -x "${BURN_DIR}/gpu_burn" ]; then
  info "gpu-burn をクローン＋ビルド"
  rm -rf "${BURN_DIR}"
  git clone --depth 1 https://github.com/wilicc/gpu-burn.git "${BURN_DIR}"
  cd "${BURN_DIR}"
  if ! make; then
    err "make に失敗しました。CUDA toolkit が見えているか確認してください。"
    err "解決例: export PATH=/usr/local/cuda/bin:\$PATH"
    exit 1
  fi
fi

cd "${BURN_DIR}"

# 2. GPU 状態を記録するバックグラウンドジョブ
LOG_DIR="${HOME}/gpu_burn_logs"
mkdir -p "${LOG_DIR}"
TS=$(date +%Y%m%d_%H%M%S)
METRICS_LOG="${LOG_DIR}/metrics_${TS}.csv"
DMESG_LOG="${LOG_DIR}/dmesg_${TS}.log"

info "メトリクスを ${METRICS_LOG} に記録"
nvidia-smi dmon -s pucvmet -d 5 -o DT > "${METRICS_LOG}" &
DMON_PID=$!

info "カーネル GPU ログを ${DMESG_LOG} にストリーム"
( sudo journalctl -kf 2>/dev/null | grep --line-buffered -iE "xid|nvrm|nvidia" > "${DMESG_LOG}" ) &
JLOG_PID=$!

trap "kill ${DMON_PID} ${JLOG_PID} 2>/dev/null || true" EXIT

# 3. gpu_burn 実行
info "gpu_burn を ${DURATION} 秒実行 (バックグラウンドで進行表示)"
echo "=== gpu_burn 開始: $(date) ==="
./gpu_burn "${DURATION}" || RC=$?
RC=${RC:-0}
echo "=== gpu_burn 終了: $(date), 終了コード=${RC} ==="

# 4. 結果サマリ
echo
echo "===== 結果サマリ ====="
echo "metrics : ${METRICS_LOG}"
echo "dmesg   : ${DMESG_LOG}"

# Xid が出たかチェック
xid_count=$(wc -l < "${DMESG_LOG}" 2>/dev/null || echo 0)
if [ "${xid_count}" -gt 0 ]; then
  err "${xid_count} 件の GPU カーネルログ:"
  cat "${DMESG_LOG}"
  err "→ ハード/ドライバ層で異常検知。RMA / ドライバ降格 を検討してください。"
  exit 1
else
  ok "Xid / NVRM のカーネルログなし。ハード層は健全と推定。"
fi

if [ "${RC}" -ne 0 ]; then
  err "gpu_burn の終了コードが ${RC} (異常終了)"
  exit 1
fi

ok "gpu_burn ${DURATION} 秒完走、ハード健全性 OK"
echo
echo "→ Training 側の Xid 問題は PyTorch 等の上位層に原因あり。"
echo "  CUDA_LAUNCH_BLOCKING=1 で本番ワークロードを再起動して真の発火カーネルを特定してください。"
