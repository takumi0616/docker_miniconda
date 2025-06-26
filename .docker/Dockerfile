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
    netcdf-bin && \
    rm -rf /var/lib/apt/lists/*

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

# PATH環境変数の設定: Condaの実行可能ファイルがシステムPATHに追加され、どこからでもコマンドが実行できるようになります
ENV PATH=$CONDA_DIR/bin:$PATH

# Condaの初期設定:
# - `auto_activate_base`を無効にし、デフォルトでbase環境がアクティベートされないようにします。
# - `conda-forge`, `pytorch`, `nvidia`チャネルを追加し、必要なパッケージを探索できるようにします。
RUN conda config --set auto_activate_base false && \
    conda config --add channels conda-forge && \
    conda config --add channels pytorch && \
    conda config --add channels nvidia

# 4. Conda環境の段階的構築

# (ステップ1) CPU用の共通環境を構築 (environments/*.yml)
# `environments`ディレクトリ内の全てのYAMLファイルを読み込み、Conda環境を構築または更新します。
# `--prune`オプションにより、YAMLファイルにないパッケージは環境から削除されます。
COPY environments /app/environments
RUN find /app/environments -name "*.yml" -print0 | xargs -0 -I {} bash -c \
    'echo "Creating/updating env from {}" && conda env update --file {} --prune'

# (ステップ2) GPUが有効な場合のみ、GPU用の環境で上書き更新 (environments_gpu/*.yml)
# `GPU_ENABLED`引数が"true"の場合のみ実行されます。
# PYTORCH_CUDA_VERSIONを動的に環境ファイルに注入し、Conda環境を構築または更新します。
ARG GPU_ENABLED=false
ARG PYTORCH_CUDA_VERSION=12.4 # コマンドラインから渡されるCUDAバージョン
 
COPY environments_gpu /app/environments_gpu
RUN if [ "${GPU_ENABLED}" = "true" ]; then \
        echo "==> Templating Conda GPU environments with CUDA version: ${PYTORCH_CUDA_VERSION}" && \
        # environments_gpu内の全ymlファイルに対し、pytorch-cudaのバージョンを動的に置換する
        find /app/environments_gpu -name "*.yml" -exec \
            sed -i "s/pytorch-cuda=\S*/pytorch-cuda=${PYTORCH_CUDA_VERSION}/g" {} + && \
        \
        # 各環境ファイルをループで処理し、エラーがあればビルドを中断
        # これにより、どの環境構築で問題が発生したかを明確に把握できます。
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
        echo "==> Cleaning up Conda cache" && \
        conda clean -a -y; \
    fi

# Condaをbashで使えるように初期化
# これにより、コンテナ内でシェルにログインした際にcondaコマンドが利用可能になります。
RUN conda init bash

# デフォルトのConda環境を有効化
# コンテナ起動時に自動的に`pytorch_env`がアクティベートされるように設定します。
RUN echo "conda activate pytorch_env" >> ~/.bashrc

# コンテナをバックグラウンドで起動し続けるコマンド
# コンテナがすぐに終了しないようにし、後から`docker compose exec`でアクセスできるようにします。
CMD ["sleep", "infinity"]