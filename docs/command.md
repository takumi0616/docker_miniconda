- リポジトリをクローン

```bash
git clone https://github.com/takumi0616/docker_miniconda.git
```

- 作業ディレクトリへ移動

```bash
cd docker_miniconda
```

- CPU 用イメージをビルド

```bash
sudo docker compose build
```

- CPU 用コンテナをバックグラウンド起動

```bash
sudo docker compose up -d
```

- GPU 用イメージをビルド（CUDA 12.1）

```bash
PYTORCH_CUDA_VERSION=12.1 sudo docker compose -f compose.yml -f compose.gpu.yml build
```

- GPU 用コンテナをバックグラウンド起動

```bash
sudo docker compose -f compose.yml -f compose.gpu.yml up -d
```

- 起動中コンテナへシェルで入る

```bash
sudo docker compose exec app bash
```

- CPU チェックスクリプト実行

```bash
python src/check_cpu.py
```

- GPU チェックスクリプト実行

```bash
python src/check_gpu_torch.py
```

- Conda 環境を acs_env に切り替え

```bash
conda activate acs_env
```

- Conda 環境を 1 つ戻す（deactivate）

```bash
conda deactivate
```

- Conda 環境一覧を表示

```bash
conda env list
```

- 新しい Conda 環境を有効化（例: my_new_env）

```bash
conda activate my_new_env
```

- CPU 環境で再ビルド＆起動

```bash
sudo docker compose up -d --build
```

- GPU 環境で再ビルド＆起動（CUDA 12.4）

```bash
PYTORCH_CUDA_VERSION=12.4 sudo docker compose -f compose.yml -f compose.gpu.yml up -d --build
```

- CPU 環境のコンテナ停止・削除

```bash
sudo docker compose down
```

- CPU 環境のコンテナ停止・削除＋ボリューム削除

```bash
sudo docker compose down -v
```

- GPU 環境のコンテナ停止・削除

```bash
sudo docker compose -f compose.yml -f compose.gpu.yml down
```

- GPU 環境のコンテナ停止・削除＋ボリューム削除

```bash
sudo docker compose -f compose.yml -f compose.gpu.yml down -v
```

- 指定ディレクトリ（例）の強制削除

```bash
sudo rm -rf src/ACS/prmsl/result_prmsl_acs_random_search_v4
```

- 実行中タスクをプロセス名で終了

```bash
pkill -f "multi_prmsl_acs_random_v4.py"
```

- すべての Docker リソースを強制削除（キャッシュ・イメージ・コンテナ・ボリューム）

```bash
sudo docker system prune -a --volumes -f
```

- Docker のディスク使用量を表示

```bash
sudo docker system df
```

- すべてのコンテナ一覧を表示

```bash
sudo docker ps -a
```

- 指定コンテナを削除

```bash
sudo docker rm [コンテナID]
```

- すべてのイメージ一覧を表示

```bash
sudo docker images
```

- 指定イメージを削除

```bash
sudo docker rmi [イメージID]
```

- Docker ビルダーキャッシュを削除

```bash
sudo docker builder prune
```

- ディレクトリ所有者を現在のユーザーに再帰変更（FrontLine 例）

```bash
sudo chown -R $USER:$USER /home/takumi/docker_miniconda/src/FrontLine/
```

- ディレクトリ所有者を s233319 に再帰変更

```bash
sudo chown -R s233319:s233319 /home/s233319/docker_miniconda/src
```

- ディレクトリ所有者を devel に再帰変更

```bash
sudo chown -R devel:devel /home/devel/work_takasuka_git/docker_miniconda/src
```

- ディレクトリ所有者を takumi に再帰変更

```bash
sudo chown -R takumi:takumi /home/takumi/docker_miniconda/src
```

- GPU 使用状況を 1 秒間隔で監視

```bash
watch -n 1 nvidia-smi
```

- PyTorch と関連をアンインストール

```bash
pip uninstall torch torchvision torchaudio
```

- Nightly CUDA 12.8 ビルドをインストール（指定 index）

```bash
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
```

- Git ローカルユーザー名を設定

```bash
git config --local user.name "takumi0616"
```

- Git ローカルメールアドレスを設定

```bash
git config --local user.email "takumi0616.mrt@gmail.com"
```

- データ同期（SSD→HDD）rsync

```bash
sudo rsync -avP /home/devel/work_takasuka_git/docker_miniconda/src/anemoi/ /mnt/gpu01C/devel/work_takasuka_git/docker_miniconda/src/anemoi/
```

- 旧ディレクトリを削除

```bash
sudo rm -rf /home/devel/work_takasuka_git/docker_miniconda/src/anemoi
```

- シンボリックリンクを作成

```bash
ln -s /mnt/gpu01C/devel/work_takasuka_git/docker_miniconda/src/anemoi /home/devel/work_takasuka_git/docker_miniconda/src/anemoi
```

- ジョブ監視付きでスクリプト実行（notify-run）

```bash
notify-run -- python src/train.py
```

- ログ付き・conda 環境指定でジョブ実行（notify-run）

```bash
notify-run -l logs/job*$(date +%F*%H%M).log -- conda run -n swinunet_env python src/train.py --cfg cfg.yaml
```

- 自前 ntfy サーバーを Docker で起動

```bash
docker run -d --name ntfy --restart=always -p 8080:80 \
  -v /opt/ntfy:/etc/ntfy \
  -e NTFY_BASE_URL=https://your.domain \
  -e NTFY_CACHE_FILE=/etc/ntfy/cache.db \
  binwiederhier/ntfy serve
```

- ntfy 公開サーバー疎通確認

```bash
curl https://ntfy.sh
```

- ntfy 通知のテスト実行

```bash
notify-run -- python ntfy_notify.py
```
