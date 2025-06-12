# ベースイメージはNVIDIA公式のものを継続して使用
FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

# 非対話型のインストール設定
ENV DEBIAN_FRONTEND=noninteractive

# 作業ディレクトリを設定
WORKDIR /app

# システム依存関係のインストール（Condaに必要なものを中心に）
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
    libgl1 && \
    rm -rf /var/lib/apt/lists/*

# Minicondaのインストール
ENV CONDA_DIR /opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-py312_24.5.0-0-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p $CONDA_DIR && \
    rm ~/miniconda.sh

# PATH環境変数の設定
ENV PATH=$CONDA_DIR/bin:$PATH

# Condaの初期設定
RUN conda config --set auto_activate_base false && \
    conda config --add channels conda-forge && \
    conda config --add channels pytorch && \
    conda config --add channels nvidia

# 環境定義ファイルをコピー
COPY environments /app/environments

# Conda環境の作成・更新
RUN conda env update -n pytorch_env --file /app/environments/pytorch_env.yml --prune && \
    conda env update -n tensorflow_env --file /app/environments/tensorflow_env.yml --prune && \
    conda env update -n acs_env --file /app/environments/acs_env.yml --prune

# Condaをbashで使えるように初期化する（.bashrcに設定を書き込む）
RUN conda init bash

# bashの起動時にデフォルトのConda環境を有効にする設定を追記
RUN echo "conda activate pytorch_env" >> ~/.bashrc

# コンテナをバックグラウンドで起動し続けるための命令
CMD ["sleep", "infinity"]