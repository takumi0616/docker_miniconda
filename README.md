# Docker + Conda によるクロスプラットフォーム機械学習開発環境

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

NVIDIA GPU と CPU の両方に対応した、ポータブルな機械学習・データ分析用の開発環境です。Docker と Conda の力を最大限に活用し、OS（Windows, Mac, Linux）や CPU アーキテクチャ（Intel x86_64, Apple Silicon ARM64）を問わず、**誰でも・どこでも・いつでも** 同じ環境を数分で構築できます。

---

## ✨ 主な特徴

- **完全なクロスプラットフォーム対応**

  - Windows, Linux (Intel/AMD), Mac (Intel/Apple Silicon) のすべてで動作します。
  - ホストマシンの環境を自動で判別し、最適な設定でコンテナを構築します。

- **簡単な CPU/GPU 環境の切り替え**

  - NVIDIA GPU がなくても、CPU 環境で全ての機能が動作します。
  - GPU を使いたい時だけ、コマンドに短いオプションを追加するだけで、自動的に GPU 対応環境に切り替わります。もう設定ファイルを手で編集する必要はありません。

- **宣言的な Conda 環境管理**

  - `environments` ディレクトリに YAML ファイルを置くだけで、複数の Python 仮想環境を簡単に管理できます。
  - `Dockerfile`を直接編集することなく、ライブラリの追加や新しい環境の作成が可能です。

- **高い再現性とポータビリティ**

  - 「私の PC では動いたのに…」はもう過去の話。チームメンバー全員が全く同じ環境で作業でき、開発から本番環境への移行もスムーズです。

- **VSCode Remote に完全対応**
  - VSCode の Remote - Containers 拡張機能を使えば、ローカル環境と同じ感覚でコンテナ内のファイルを直接編集・デバッグできます。

---

## 🤔 こんな人におすすめ

- チームで開発環境を完全に統一したい方
- PC を買い替えても、数コマンドで以前の環境を再現したい方
- "pip/conda の依存関係地獄"から解放されたい方
- GPU を使った開発と、CPU のみでのテストをシームレスに切り替えたい方
- 機械学習の学習や研究に集中したいインフラ初心者の方

---

## 🔧 事前準備 (System Requirements)

この環境を利用するには、お使いの PC に以下のソフトウェアがインストールされている必要があります。

1.  **Git**: ソースコードのクローンに使用します。
2.  **Docker Desktop**: コンテナを動かすための必須ツールです。
    - [Windows/Mac 用ダウンロード](https://www.docker.com/products/docker-desktop/)
    - [Linux 用インストールガイド](https://docs.docker.com/engine/install/)
3.  **(NVIDIA GPU をお使いの場合のみ)**
    - 最新の **[NVIDIA Driver](https://www.nvidia.co.jp/Download/index.aspx?lang=jp)**
    - **[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)**

> **📝 Note:**
> Linux 環境で Docker コマンド実行時の`sudo`を省略したい場合は、[こちらの公式ガイド](https://docs.docker.com/engine/install/linux-postinstall/)に従って設定を行ってください。

---

## 🚀 クイックスタート (Quick Start)

### 1. リポジトリをクローン

まず、このプロジェクトをお手元にダウンロードします。

```bash
git clone [https://github.com/takumi0616/docker_miniconda.git](https://github.com/takumi0616/docker_miniconda.git)
cd docker_miniconda
```

### 2. 環境のビルドと起動

実行したい環境に応じて、以下のコマンドを選択してください。

#### A) CPU 環境の場合 (Mac, GPU なし PC)

Mac ユーザーや、NVIDIA GPU を搭載していない PC の場合は、こちらのコマンドを実行します。

```bash
# Dockerイメージをビルド
docker compose build

# コンテナをバックグラウンドで起動
docker compose up -d
```

#### B) GPU 環境の場合 (NVIDIA GPU 搭載 PC)

NVIDIA GPU を利用したい場合は、コマンドに`-f compose.gpu.yml`を追加して、GPU 用の設定を読み込ませます。

```bash
# GPU用の設定をマージしてDockerイメージをビルド
docker compose -f compose.yml -f compose.gpu.yml build

# GPUを有効にしてコンテナをバックグラウンドで起動
docker compose -f compose.yml -f compose.gpu.yml up -d
```

> **☕ Note:**
> 初回のビルドは、ベースイメージや多数のライブラリをダウンロードするため、ネットワーク環境によっては 10 分以上かかる場合があります。2 回目以降はキャッシュが利用されるため、高速に完了します。

### 3. コンテナにアクセス

起動したコンテナの中に入り、開発作業を開始します。

```bash
docker compose exec app bash
```

成功すると、シェルのプロンプトが以下のように変わり、デフォルトの`pytorch_env`環境が自動で有効化された状態になります。

```bash
(pytorch_env) root@<コンテナID>:/app#
```

---

## 🎮 コンテナ内での操作

### 動作確認

環境が正しく構築されているか、サンプルスクリプトを実行して確認してみましょう。

- **CPU 環境で実行する場合:**

  ```bash
  (pytorch_env) root@...:/app# python src/check_cpu.py
  ```

  **実行結果の例:**

  ```
  Starting CPU environment check...
  ============================================================
  ===== SYSTEM & CPU INFORMATION CHECKER
  ============================================================
  Python Version: 3.12.3 | packaged by conda-forge | (main, May 10 2024, 18:03:52) [GCC 12.3.0]
  OS: Linux 6.6.31-linuxkit
  Architecture: aarch64
  ...
  PyTorch CPU check: PASSED
  TensorFlow CPU check: PASSED
  ...
  ```

- **GPU 環境で実行する場合:**
  ```bash
  (pytorch_env) root@...:/app# python src/check_gpu_torch.py
  ```
  **実行結果の例:**
  ```
  PyTorch version: 2.4.1
  CUDA version: 12.4
  cuDNN version: 8907
  Number of GPUs available: 1
  Device name: NVIDIA GeForce RTX 4090
  ```

### Conda 環境の操作

- **他の環境への切り替え:**

  ```bash
  # tensorflow_envに切り替える
  (pytorch_env) root@...:/app# conda activate tensorflow_env
  (tensorflow_env) root@...:/app#

  # ベースの環境に戻る
  (tensorflow_env) root@...:/app# conda deactivate
  root@...:/app#
  ```

- **利用可能な環境の一覧表示:**
  ```bash
  (pytorch_env) root@...:/app# conda env list
  ```

---

## ⚙️ 環境のカスタマイズ

このプロジェクトの真価は、その高いカスタマイズ性にあります。

### 新しい Conda 環境を追加する

`Dockerfile`を編集する必要は一切ありません。

1.  **YAML ファイルを作成**: `environments`ディレクトリに、`<新しい環境名>.yml`というファイルを作成します。

    **例: `my_new_env.yml`**

    ```yaml
    name: my_new_env
    channels:
      - conda-forge
    dependencies:
      - python=3.12
      - pandas
      - jupyterlab
    ```

2.  **イメージを再ビルド**: CPU/GPU に応じた`build`コマンドを実行するだけです。

    ```bash
    # CPU環境の場合
    docker compose build

    # GPU環境の場合
    docker compose -f compose.yml -f compose.gpu.yml build
    ```

    ビルド完了後、コンテナに入れば`conda activate my_new_env`で新しい環境が使えます。

### 既存の環境にパッケージを追加する

1.  **YAML ファイルを編集**:

    - **CPU/共通パッケージ**: `environments`内の対応する YAML ファイルにライブラリ名を追加します。
    - **GPU 専用パッケージ**: `environments_gpu`内の対応する YAML ファイルに追加します。

2.  **イメージを再ビルド**: 上記と同様に`build`コマンドを実行します。`conda env update`が差分だけを賢く更新してくれるため、効率的にパッケージが追加されます。

> **⚠️ クロスプラットフォーム対応のヒント:** > `.yml`ファイルでライブラリのバージョンを厳密に固定（例: `pytorch=2.2.2`）すると、他の CPU アーキテクチャ（Intel vs Apple Silicon）でパッケージが見つからず、ビルドに失敗する原因となります。特別な理由がない限り、**バージョン番号は指定しない**ことを強く推奨します。これにより、Conda が各環境で利用可能な互換バージョンを自動で選択してくれます。

---

## 📁 プロジェクト構造

```
.
├── .docker
│   └── Dockerfile             # (全自動) 環境構築の設計図。通常は編集不要。
├── .gitignore                 # Gitの追跡対象外ファイルを指定
├── README.md                  # このファイル
├── compose.yml                # Dockerコンテナの基本設定 (CPU用)
├── compose.gpu.yml            # GPU利用時の上書き設定
├── environments               # (★主に編集する場所) CPU用のConda環境定義
│   ├── acs_env.yml
│   ├── pytorch_env.yml
│   └── tensorflow_env.yml
├── environments_gpu           # (★GPU利用時に編集) GPU用のConda環境定義
│   └── pytorch_env.yml
└── src                        # ソースコードやスクリプト、データを配置
    ├── check_cpu.py           # CPU環境の動作確認スクリプト
    └── check_gpu_torch.py     # GPU環境の動作確認スクリプト
```

---

## 🧹 クリーンアップ

開発が終わったら、以下のコマンドでコンテナと関連リソースを削除できます。

#### A) CPU 環境の場合

```bash
# コンテナを停止・削除
docker compose down

# データを永続化するボリュームも完全に削除する場合
docker compose down -v
```

#### B) GPU 環境の場合

```bash
# コンテナを停止・削除
docker compose -f compose.yml -f compose.gpu.yml down

# ボリュームも完全に削除する場合
docker compose -f compose.yml -f compose.gpu.yml down -v
```
