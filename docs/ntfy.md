# ntfy 通知ガイド

## 1. これは何？

- Docker コンテナ内から HTTP でモバイル/PC にプッシュ通知を送る仕組みです
- 無料の公開サーバ（https://ntfy.sh）を使うので、サーバの外にポートを開ける必要はありません
- SSH が切れても通知は届きます

## 2. スマホ/PC の準備

- iOS/Android: アプリストアで「ntfy」をインストール
- Mac/PC: ブラウザで https://ntfy.sh を開く（通知許可）
- 「トピック」を作成
  - Mac/サーバ等:
    - openssl rand -hex 16
    - または: python -c "import secrets;print(secrets.token_urlsafe(24))"
  - 例: takumi-2fdfc8d6c1d9478a9d8d8fcd2a
- アプリ（またはブラウザ）でこのトピックを購読（Follow/Subscribe）

## 3. コンテナ側の設定

- プロジェクトの .env を作成
  - NTFY_SERVER=https://ntfy.sh
  - NTFY_TOPIC=<上で決めた値>
  - TZ=Asia/Tokyo
- コンテナをビルド
  - CPU: docker compose up -d --build
  - GPU: PYTORCH_CUDA_VERSION=12.4 docker compose -f compose.yml -f compose.gpu.yml up -d --build

## 4. 使い方

- notify-run を使う（推奨）
  - notify-run -- python src/train.py
  - notify-run -l logs/job*$(date +%F*%H%M).log -- conda run -n swinunet_env python src/train.py --cfg cfg.yaml
- Python コード内から
  - from notify.ntfy_notify import notify_job
  - with notify_job("My Experiment"):
    heavy_task()

## 5. トラブルシューティング

- 通知が来ない:
  - .env の NTFY_TOPIC が空でないか？
  - サーバから https に出られるか？（curl https://ntfy.sh で確認）
  - iOS 側の通知許可がオフになっていないか？
- 送信失敗してもジョブは継続:
  - notify-run / notify_job は通知失敗を握りつぶす（非停止設計）

## 6. セキュリティ

- 公開サーバ ntfy.sh を使う場合、トピック名は**長いランダム文字列**にして実質秘匿
- より厳格にしたい場合は**自前 ntfy サーバ**を立て、トークン認証を有効化：
  - 例（Docker）:
    - docker run -d --name ntfy --restart=always -p 8080:80 \
      -v /opt/ntfy:/etc/ntfy \
      -e NTFY_BASE_URL=https://your.domain \
      -e NTFY_CACHE_FILE=/etc/ntfy/cache.db \
      binwiederhier/ntfy serve
  - NGINX 等で HTTPS 終端、Basic 認証/TOKEN を利用
  - プロジェクトの .env で NTFY_SERVER と NTFY_TOKEN を設定

## 7. 補足（タグ・タイトル）

- notify-run/notify_job は自動で以下を付与：
  - START ▶️, DONE ✅, FAILED ❌
  - タグ: rocket/hourglass/white_check_mark/x など
- iOS の ntfy アプリではタグがアイコンに反映される

## チェック

```bush
notify-run -- python src/heavy_job.py
```
