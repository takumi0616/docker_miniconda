# .docker/Dockerfile

# Dockerfile: ポータブルな機械学習開発環境の構築
# このDockerfileは、CPU/GPUの両方に対応したConda環境を動的に構築します。

# 1. ビルド引数でベースイメージを動的に受け取る
#    CPU環境の場合はubuntu:22.04、GPU環境の場合はnvidia/cudaイメージが使用されます。
ARG BASE_IMAGE=ubuntu:22.04
FROM ${BASE_IMAGE}

# 非対話型のインストール設定: apt-getなどのプロンプト表示を抑制します
ENV DEBIAN_FRONTEND=noninteractive
# APT network hardening: retries and timeouts
RUN printf 'Acquire::Retries "5";\nAcquire::http::Timeout "60";\nAcquire::https::Timeout "60";\n' > /etc/apt/apt.conf.d/99network-retries

# 作業ディレクトリを設定: コンテナ内の作業の基準となるディレクトリです
WORKDIR /app

# 2. 共通のシステム依存関係をインストール
#    開発に必要な様々なツールやライブラリ（wget, git, vimなど）をインストールします。
#    インストールの最後にaptキャッシュをクリーンアップし、イメージサイズを最適化します。
RUN set -eux; \
    SUCCESS=0; \
    for i in 1 2 3 4 5; do \
      if apt-get -o Acquire::Retries=5 -o Acquire::http::Timeout=60 -o Acquire::https::Timeout=60 update && \
         apt-get install -y --no-install-recommends \
           locales \
           language-pack-ja \
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
           libasound2; then \
         SUCCESS=1; break; \
      else \
         echo "APT failed (try $i/5)"; sleep $((i*10)); \
      fi; \
    done; \
    if [ "$SUCCESS" -ne 1 ]; then echo "[ERROR] APT update/install failed after retries"; exit 1; fi; \
    locale-gen ja_JP.UTF-8 && update-locale LANG=ja_JP.UTF-8 LC_ALL=ja_JP.UTF-8; \
    rm -rf /var/lib/apt/lists/*

# OS の CA バンドルを Requests が使えるよう既定パスを明示（コード側では優先は certifi）
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
# Locale and I/O encoding defaults (avoid mojibake in CLI/PIPEs)
ENV LANG=ja_JP.UTF-8 \
    LANGUAGE=ja_JP:ja \
    LC_ALL=ja_JP.UTF-8 \
    PYTHONIOENCODING=UTF-8
# pip network hardening: increase default timeout and disable version check
ENV PIP_DEFAULT_TIMEOUT=120 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 3. CPUアーキテクチャを自動判別し、適切なMinicondaをインストール
#    ビルド時のターゲットプラットフォーム（例: linux/amd64, linux/arm64）に基づいて、
#    適切なMinicondaインストーラーをダウンロードし、インストールします。
ARG TARGETPLATFORM
ENV CONDA_DIR /opt/conda
RUN set -eux; \
    case ${TARGETPLATFORM} in \
        "linux/amd64") ARCH="x86_64";; \
        "linux/arm64") ARCH="aarch64";; \
        *) echo "Unsupported architecture: ${TARGETPLATFORM}"; exit 1;; \
    esac; \
    URL="https://repo.anaconda.com/miniconda/Miniconda3-py312_24.5.0-0-Linux-${ARCH}.sh"; \
    for i in 1 2 3 4 5; do \
      wget -O ~/miniconda.sh --progress=dot:giga --tries=3 --timeout=60 "$URL" && break || { \
        echo "wget failed (try $i/5)"; sleep $((i*10)); \
      }; \
    done; \
    if [ ! -s ~/miniconda.sh ]; then \
      echo "Falling back to curl"; \
      curl -fL "$URL" --retry 5 --retry-all-errors --connect-timeout 30 --max-time 600 -o ~/miniconda.sh; \
    fi; \
    /bin/bash ~/miniconda.sh -b -p $CONDA_DIR; \
    rm ~/miniconda.sh

# PATH環境変数の設定
ENV PATH=$CONDA_DIR/bin:$PATH
# Prefer conda env libraries first; avoid relying on LD_PRELOAD
ENV CONDA_DEFAULT_ENV=swinunet_env
ENV CONDA_PREFIX=$CONDA_DIR/envs/swinunet_env
ENV LD_LIBRARY_PATH=$CONDA_PREFIX/lib:/usr/local/nvidia/lib:/usr/local/nvidia/lib64:$LD_LIBRARY_PATH
# Headless-safe matplotlib backend and avoid user-site contamination
ENV MPLBACKEND=Agg
ENV PYTHONNOUSERSITE=1

# Condaの初期設定
RUN conda config --set auto_activate_base false && \
    conda config --add channels conda-forge && \
    conda config --add channels pytorch && \
    conda config --add channels nvidia && \
    conda config --set remote_connect_timeout_secs 60 && \
    conda config --set remote_read_timeout_secs 120

# 4. Conda環境の段階的構築

# (ステップ0) 既存のConda環境をすべて削除
RUN echo "==> Removing all existing conda environments..." && \
    rm -rf ${CONDA_DIR}/envs/* || true && \
    echo "All old environments removed successfully."

# (ステップ1) CPU用の共通環境を構築 (environments/*.yml)
COPY environments /app/environments
RUN set -e; \
    find /app/environments -name "*.yml" -print0 | xargs -0 -I {} bash -c '\
      echo "Creating/updating env from {}"; \
      for i in 1 2 3 4 5; do \
        conda env update --file {} --prune && exit 0 || { \
          echo "[WARN] conda env update failed for {} (try $i/5). Backing off..."; \
          sleep $((i*20)); \
        }; \
      done; \
      echo "[ERROR] conda env update failed for {} after retries." >&2; \
      exit 1'

RUN set -e; \
    SUCCESS=0; \
    for i in 1 2 3 4 5; do \
      if conda run -n scraping_env python -m playwright install --with-deps chromium; then \
        SUCCESS=1; break; \
      else \
        echo "[WARN] Playwright install failed (try $i/5). Retrying..."; sleep $((i*15)); \
      fi; \
    done; \
    if [ "$SUCCESS" -ne 1 ]; then echo "[ERROR] Playwright install failed after retries"; exit 1; fi

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
            ATTEMPT=1; \
            until conda env update --file "${ENV_FILE}" --prune; do \
                if [ $ATTEMPT -ge 5 ]; then \
                    echo "ERROR: Failed to create/update Conda environment from ${ENV_FILE} after ${ATTEMPT} attempts"; \
                    exit 1; \
                fi; \
                echo "[WARN] conda env update failed for ${ENV_FILE} (attempt ${ATTEMPT}). Retrying after backoff..."; \
                sleep $((ATTEMPT*20)); \
                ATTEMPT=$((ATTEMPT+1)); \
            done; \
            echo "--> Successfully processed ${ENV_FILE}"; \
        done; \
        \
        # --- Install JAX CUDA plugin into aimodel_env (based on PYTORCH_CUDA_VERSION) ---
        # JAX の pip パッケージは v0.6 系で cuda12 プラグインが提供されており、
        # CUDA 12.x 系および 13.x でも 'cuda12' を使うのが現状の安定解です。
        # （NVIDIA ドライバが新しければ後方互換で動作）                          \
# --- Install JAX CUDA plugin into aimodel_env ---
        # JAX 0.6.x 以降は [cuda12] オプションを使用 (cuda12_pip は廃止)
        echo "==> Installing JAX with CUDA support into aimodel_env"; \
        SUCCESS=0; \
        for i in 1 2 3 4 5; do \
           # --force-reinstall で既存のCPU版などを確実に上書き
           if conda run -n aimodel_env pip install --upgrade --force-reinstall --retries 5 --timeout 120 "jax[cuda12]"; then \
             SUCCESS=1; break; \
           else \
             echo "[WARN] pip install jax[cuda12] failed (try $i/5). Retrying..."; \
             sleep $((i*15)); \
           fi; \
        done; \
        if [ "$SUCCESS" -ne 1 ]; then echo "[ERROR] pip install jax failed"; exit 1; fi; \
        \
        # =====================================================================
        # 【重要】JAX用 LD_LIBRARY_PATH 自動設定スクリプトの作成
        # Conda環境 activate 時に、pip で入れた nvidia-* ライブラリへのパスを自動で通す
        # シェルのエスケープ問題を避けるため、Pythonスクリプト経由で生成する
        # =====================================================================
        ACTIVATE_DIR="$CONDA_DIR/envs/aimodel_env/etc/conda/activate.d"; \
        DEACTIVATE_DIR="$CONDA_DIR/envs/aimodel_env/etc/conda/deactivate.d"; \
        mkdir -p "$ACTIVATE_DIR" "$DEACTIVATE_DIR"; \
        \
        # 生成用の一時Pythonスクリプトを作成
        printf "import os\n\
import site\n\
import glob\n\
\n\
try:\n\
    base = site.getsitepackages()[0]\n\
    nvidia_dir = os.path.join(base, 'nvidia')\n\
    lib_paths = []\n\
    # nvidiaディレクトリ以下のすべての lib ディレクトリを探索\n\
    if os.path.exists(nvidia_dir):\n\
        for root, dirs, files in os.walk(nvidia_dir):\n\
            if 'lib' in dirs:\n\
                lib_paths.append(os.path.join(root, 'lib'))\n\
    \n\
    # 重複を排除してコロンで結合\n\
    libs_str = ':'.join(sorted(list(set(lib_paths))))\n\
    \n\
    if libs_str:\n\
        print(f'export OLD_LD_LIBRARY_PATH=\${{LD_LIBRARY_PATH}}')\n\
        print(f'export LD_LIBRARY_PATH={libs_str}:\${{LD_LIBRARY_PATH}}')\n\
except Exception as e:\n\
    pass\n" > /tmp/gen_jax_env.py; \
        \
        # Pythonを実行して activate.d/env_vars.sh に書き込む
        echo "#!/bin/sh" > "$ACTIVATE_DIR/env_vars.sh"; \
        conda run -n aimodel_env python /tmp/gen_jax_env.py >> "$ACTIVATE_DIR/env_vars.sh"; \
        rm /tmp/gen_jax_env.py; \
        \
        # deactivate 用のスクリプト（元に戻す設定）
        echo "#!/bin/sh" > "$DEACTIVATE_DIR/env_vars.sh"; \
        echo 'export LD_LIBRARY_PATH=$OLD_LD_LIBRARY_PATH' >> "$DEACTIVATE_DIR/env_vars.sh"; \
        echo 'unset OLD_LD_LIBRARY_PATH' >> "$DEACTIVATE_DIR/env_vars.sh"; \
        \
        # --- 検証: 生成されたファイルの中身をログに出す --- \
        echo "==> Generated activate script content:"; \
        cat "$ACTIVATE_DIR/env_vars.sh"; \
        \
        echo "==> Cleaning up Conda cache" && \
        conda clean -a -y; \
    fi

# Ensure modern libstdc++ (CXXABI >= 1.3.15) inside swinunet_env to satisfy matplotlib and others (GPU builds only)
RUN if [ "${GPU_ENABLED}" = "true" ]; then \
      set -e; \
      SUCCESS=0; \
      for i in 1 2 3 4 5; do \
        if conda install -n swinunet_env -y -c conda-forge "libstdcxx-ng>=14" "libgcc-ng>=14"; then \
          SUCCESS=1; break; \
        else \
          echo "[WARN] conda install libstdcxx-ng/libgcc-ng failed (try $i/5). Retrying..."; \
          sleep $((i*20)); \
        fi; \
      done; \
      if [ "$SUCCESS" -ne 1 ]; then echo "[ERROR] Failed to install modern libstdc++ into swinunet_env"; exit 1; fi; \
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
