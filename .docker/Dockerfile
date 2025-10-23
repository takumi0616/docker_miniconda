# .docker/Dockerfile

# Dockerfile: ポータブルな機械学習開発環境の構築
# このDockerfileは、CPU/GPUの両方に対応したConda環境を動的に構築します。

# 1. ビルド引数でベースイメージを動的に受け取る
#    CPU環境の場合はubuntu:22.04、GPU環境の場合はnvidia/cudaイメージが使用されます。
ARG BASE_IMAGE=ubuntu:22.04
FROM ${BASE_IMAGE}

# 非対話型のインストール設定: apt-getなどのプロンプト表示を抑制します
ENV DEBIAN_FRONTEND=noninteractive

# 作業ディレクトリを設定: コンテナ内の作業の基準となるディレクトリです
WORKDIR /app

# 2. 共通のシステム依存関係をインストール
#    開発に必要な様々なツールやライブラリ（wget, git, vimなど）をインストールします。
#    インストールの最後にaptキャッシュをクリーンアップし、イメージサイズを最適化します。
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    bzip2 \
    build-essential \
    git \
    git-lfs \
    curl \
    htop \
    nvtop \
    vim \
    tmux \
    tree \
    ncdu \
    ca-certificates \
    libsndfile1-dev \
    libgl1 \
    netcdf-bin \
    chromium-chromedriver \
    chromium-browser \
    fonts-ipafont-gothic \
    libgbm-dev \
    libasound2 \
 && rm -rf /var/lib/apt/lists/*

# OS の CA バンドルを Requests が使えるよう既定パスを明示（コード側では優先は certifi）
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# 3. CPUアーキテクチャを自動判別し、適切なMinicondaをインストール
#    ビルド時のターゲットプラットフォーム（例: linux/amd64, linux/arm64）に基づいて、
#    適切なMinicondaインストーラーをダウンロードし、インストールします。
ARG TARGETPLATFORM
ENV CONDA_DIR /opt/conda
RUN case ${TARGETPLATFORM} in \
        "linux/amd64") ARCH="x86_64";; \
        "linux/arm64") ARCH="aarch64";; \
        *) echo "Unsupported architecture: ${TARGETPLATFORM}"; exit 1;; \
    esac && \
    wget --quiet "https://repo.anaconda.com/miniconda/Miniconda3-py312_24.5.0-0-Linux-${ARCH}.sh" -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p $CONDA_DIR && \
    rm ~/miniconda.sh

# PATH環境変数の設定
ENV PATH=$CONDA_DIR/bin:$PATH

# Condaの初期設定
RUN conda config --set auto_activate_base false && \
    conda config --add channels conda-forge && \
    conda config --add channels pytorch && \
    conda config --add channels nvidia

# 4. Conda環境の段階的構築

# (ステップ0) 既存のConda環境をすべて削除
RUN echo "==> Removing all existing conda environments..." && \
    rm -rf ${CONDA_DIR}/envs/* || true && \
    echo "All old environments removed successfully."

# (ステップ1) CPU用の共通環境を構築 (environments/*.yml)
COPY environments /app/environments
RUN find /app/environments -name "*.yml" -print0 | xargs -0 -I {} bash -c \
    'echo "Creating/updating env from {}" && conda env update --file {} --prune'

RUN conda run -n scraping_env python -m playwright install --with-deps chromium

# (ステップ2) GPUが有効な場合のみ、GPU用の環境で上書き更新 (environments_gpu/*.yml)
ARG GPU_ENABLED=false
ARG PYTORCH_CUDA_VERSION=12.4 # コマンドラインから渡されるCUDAバージョン
COPY environments_gpu /app/environments_gpu
RUN if [ "${GPU_ENABLED}" = "true" ]; then \
        echo "==> Templating Conda GPU environments with CUDA version: ${PYTORCH_CUDA_VERSION}" && \
        # sed の置換（GNU sed）。\S は使えないため [0-9.]+ に変更
        find /app/environments_gpu -name "*.yml" -exec \
            sed -E -i "s/pytorch-cuda=[0-9.]+/pytorch-cuda=${PYTORCH_CUDA_VERSION}/g; s/cuda-version=[0-9.]+/cuda-version=${PYTORCH_CUDA_VERSION}/g" {} + && \
        \
        for ENV_FILE in $(find /app/environments_gpu -name "*.yml"); do \
            echo "--> Attempting to create/update Conda environment from ${ENV_FILE}"; \
            conda env update --file "${ENV_FILE}" --prune || { \
                echo "ERROR: Failed to create/update Conda environment from ${ENV_FILE}"; \
                echo "Please check the contents of ${ENV_FILE} and ensure dependencies are resolvable."; \
                exit 1; \
            }; \
            echo "--> Successfully processed ${ENV_FILE}"; \
        done; \
        \
        # --- Install JAX CUDA plugin into aimodel_env (based on PYTORCH_CUDA_VERSION) ---
        # JAX の pip パッケージは v0.6 系で cuda12 プラグインが提供されており、
        # CUDA 12.x 系および 13.x でも 'cuda12' を使うのが現状の安定解です。
        # （NVIDIA ドライバが新しければ後方互換で動作）                          \
        JAX_CUDA_EXTRA="cuda12"; \
        MAJOR_VER="${PYTORCH_CUDA_VERSION%%.*}"; \
        if [ "${MAJOR_VER}" = "12" ] || [ "${MAJOR_VER}" = "13" ]; then \
          echo "==> Installing jax[${JAX_CUDA_EXTRA}] for CUDA ${PYTORCH_CUDA_VERSION} (aimodel_env)"; \
          conda run -n aimodel_env python -V && \
          conda run -n aimodel_env pip install -U "jax[${JAX_CUDA_EXTRA}]"; \
        else \
          echo "WARN: Unsupported CUDA version ${PYTORCH_CUDA_VERSION}; fallback to jax[cuda12]" && \
          conda run -n aimodel_env pip install -U "jax[cuda12]"; \
        fi; \
        \
        echo "==> Cleaning up Conda cache" && \
        conda clean -a -y; \
    fi

# Condaをbashで使えるように初期化
RUN conda init bash

# デフォルトのConda環境を有効化（必要に応じて変更）
RUN echo "conda activate swinunet_env" >> ~/.bashrc

# 通知ラッパーをイメージに同梱（PATHに入れる）
# リポジトリの scripts/notify-run をコピー（ビルドコンテキストはプロジェクトルート）
COPY scripts/notify-run /usr/local/bin/notify-run
RUN chmod +x /usr/local/bin/notify-run

# コンテナをバックグラウンドで起動し続ける
CMD ["sleep", "infinity"]
