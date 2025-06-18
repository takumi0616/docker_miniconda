# 1. ビルド引数でベースイメージを動的に受け取る
ARG BASE_IMAGE=ubuntu:22.04
FROM ${BASE_IMAGE}

# 非対話型のインストール設定
ENV DEBIAN_FRONTEND=noninteractive

# 作業ディレクトリを設定
WORKDIR /app

# 2. 共通のシステム依存関係をインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    bzip2 \
    build-essential \
    git \
    git-lfs \
    curl \
    htop \
    vim \
    tmux \
    tree \
    ncdu \
    ca-certificates \
    libsndfile1-dev \
    libgl1 \
    netcdf-bin && \
    rm -rf /var/lib/apt/lists/*

# 3. CPUアーキテクチャを自動判別し、適切なMinicondaをインストール
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
# (ステップ1) CPU用の共通環境を構築 (environments/*.yml)
COPY environments /app/environments
RUN find /app/environments -name "*.yml" -print0 | xargs -0 -I {} bash -c \
    'echo "Creating/updating env from {}" && conda env update --file {} --prune'

# (ステップ2) GPUが有効な場合のみ、GPU用の環境で上書き更新 (environments_gpu/*.yml)
ARG GPU_ENABLED=false
COPY environments_gpu /app/environments_gpu
RUN if [ "${GPU_ENABLED}" = "true" ]; then \
        if [ -d "/app/environments_gpu" ] && [ "$(ls -A /app/environments_gpu)" ]; then \
            find /app/environments_gpu -name "*.yml" -print0 | xargs -0 -I {} bash -c \
            'echo "Updating env with GPU packages from {}" && conda env update --file {} --prune'; \
        fi; \
    fi

# Condaをbashで使えるように初期化
RUN conda init bash

# デフォルトのConda環境を有効化
RUN echo "conda activate pytorch_env" >> ~/.bashrc

# コンテナをバックグラウンドで起動し続ける
CMD ["sleep", "infinity"]