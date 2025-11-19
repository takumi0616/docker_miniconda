# 環境構築

## リポジトリをクローン

- docker_miniconda リポジトリをクローン

```bash
git clone https://github.com/takumi0616/docker_miniconda.git
```

- その他の研究用リポジトリをクローン

```bash
git clone git@github.com:takumi0616/PressurePattern.git

git clone git@github.com:takumi0616/FrontLine.git

git clone git@github.com:takumi0616/WeatherLLM.git

git clone git@github.com:takumi0616/AWCGS.git

git clone git@github.com:takumi0616/CompresionRain.git

git clone git@github.com:takumi0616/TyphoonForecast.git

git clone git@github.com:takumi0616/3D_avatars.git
```

- リポジトリまとめて fetch

```bash
chmod +x fetch.sh
./fetch.sh
```

- リポジトリオープン

```bash
chmod +x open.sh
./open.sh
```

# docker ビルド

## CPU 用

```bash
sudo docker compose build

sudo docker compose up -d
```

## GPU 用

- wsl-ubuntu, via-tml2 (CUDA 12.4 - デフォルト), gpu02 (CUDA 12.8)

```bash
PYTORCH_CUDA_VERSION=12.4 sudo docker compose -f compose.yml -f compose.gpu.yml build
```

- gpu01 (CUDA 12.1)

```bash
export CUDA_BASE_IMAGE="nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04" && export PYTORCH_CUDA_VERSION=12.1 && sudo -E docker compose -f compose.yml -f compose.gpu.yml build --no-cache && sudo -E docker compose -f compose.yml -f compose.gpu.yml up -d
```

- gpu02 の GPU 解放

```bash
pip uninstall torch torchvision torchaudio

pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu130
```

<!-- - tml-01-h100 (CUDA 13.0)

```bash
CUDA_BASE_IMAGE="nvidia/cuda:13.0.0-cudnn-devel-ubuntu22.04" PYTORCH_CUDA_VERSION=13.0 sudo docker compose -f compose.yml -f compose.gpu.yml build
``` -->

## GPU 起動

- GPU 用コンテナをバックグラウンド起動

```bash
sudo docker compose -f compose.yml -f compose.gpu.yml up -d
```

- 起動中コンテナへシェルで入る

```bash
sudo docker compose exec app bash
```

## 停止・削除

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

- すべての Docker リソースを強制削除（キャッシュ・イメージ・コンテナ・ボリューム）

```bash
sudo docker system prune -a --volumes -f
```

- Docker のディスク使用量を表示

```bash
sudo docker system df
```

- Docker ビルダーキャッシュを削除

```bash
sudo docker builder prune
```

# 権限変更

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

- ディレクトリ所有者を devel に再帰変更

```bash
sudo chown -R devel:devel /home/devel/work_takasuka/docker_miniconda/src
```

- ディレクトリ所有者を takumi に再帰変更

```bash
sudo chown -R takumi0616:takumi0616 /home/takumi0616/docker_miniconda/src
```

# Git 設定

- Git ローカルユーザー名を設定

```bash
git config --local user.name "takumi0616"
```

- Git ローカルメールアドレスを設定

```bash
git config --local user.email "takumi0616.mrt@gmail.com"
```

# データ移行(サーバー内におけるデータ移動)

- データ同期（SSD→HDD）rsync

```bash
sudo rsync -avP /home/devel/work_takasuka_git/docker_miniconda/src/anemoi/ /mnt/gpu01C/devel/work_takasuka_git/docker_miniconda/src/anemoi/
```
