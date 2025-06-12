# Docker + Conda GPU開発環境

NVIDIA GPUに対応した、ポータブルな機械学習・データ分析用の開発環境です。DockerとCondaを利用することで、OS（Windows, Mac, Linux）を問わず、誰でも同じ環境を数分で構築できます。

## ✨ 特徴

- **OS非依存**: Dockerコンテナなので、あらゆるOSで動作します。
- **Condaによる環境管理**: 複数のPython仮想環境を`environments`ディレクトリ以下のYAMLファイルで簡単に管理できます。
- **GPU対応**: NVIDIA GPUが搭載されたマシンでは、自動でCUDA/cuDNNが有効化されたPyTorch/TensorFlow環境を利用できます。
- **CPUでも動作**: GPUがない環境でも、設定を一行変更するだけでCPUモードで動作します。
- **カスタマイズ性**: 新しい仮想環境の追加や、既存環境へのパッケージ追加が簡単に行えます。
- **再現性**: DockerとCondaの組み合わせにより、いつでもどこでも同じ環境を再現できます。

---

## 🔧 事前準備

この環境を利用するには、以下のソフトウェアがインストールされている必要があります。

1.  **Git**
2.  **Docker**
3.  **NVIDIA GPUをお使いの場合**:
    - [NVIDIA Driver](https://www.nvidia.co.jp/Download/index.aspx?lang=jp)
    - [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

---

## 🚀 使い方 (クイックスタート)

以下の手順で、開発環境を起動してコンテナ内に入ることができます。

#### 1. リポジトリをクローン

```bash
git clone [https://github.com/takumi0616/docker_miniconda.git](https://github.com/takumi0616/docker_miniconda.git)
cd docker_miniconda
```

#### 2. Dockerイメージをビルド

`Dockerfile`と環境定義ファイル（`.yml`）に基づいて、Dockerイメージを構築します。初回は時間がかかります。

```bash
sudo docker compose build
```

#### 3. コンテナを起動

ビルドしたイメージからコンテナをバックグラウンドで起動します。

```bash
sudo docker compose up -d
```

#### 4. コンテナにアクセス

起動したコンテナの中に入ります。

```bash
sudo docker compose exec app bash
```

成功すると、シェルのプロンプトが以下のように変わり、デフォルトの`pytorch_env`環境が自動で有効化された状態になります。

```bash
(pytorch_env) root@コンテナID:/app#
```

---

## 🎮 コンテナ内での操作

#### PyTorch (GPU) の動作確認

コンテナ内でサンプルスクリプトを実行し、PyTorchがGPUを正しく認識しているか確認します。

```bash
(pytorch_env) root@...:/app# python src/check_gpu_torch.py
```
**実行結果の例 (GPUがある場合):**
```
PyTorch version: 2.4.1
CUDA version: 12.4
cuDNN version: 8907
Number of GPUs available: 1
Device name: NVIDIA GeForce RTX 4090
```

#### 仮想環境の切り替え

`tensorflow_env`など、他のConda環境に切り替えることができます。

```bash
(pytorch_env) root@...:/app# conda activate tensorflow_env
(tensorflow_env) root@...:/app#
```

#### 利用可能な仮想環境の一覧表示

```bash
(tensorflow_env) root@...:/app# conda env list
```

---

## ⚙️ カスタマイズ

このプロジェクトは、あなたのニーズに合わせて柔軟にカスタマイズできます。

### GPUがない環境での利用方法

GPUがないPCでこの環境を利用する場合は、`compose.yml`ファイル内のGPU関連の記述をコメントアウト（または削除）してください。

**`compose.yml`**
```diff
 services:
   app:
     build:
       context: .
       dockerfile: .docker/Dockerfile
     stdin_open: true # コンテナの標準入力を開く
     tty: true # 仮想端末を割り当てる
     volumes:
       - ./src:/app/src # ホストのsrcディレクトリをコンテナの/app/srcにマウント
-    deploy: # GPUがない場合は、deployセクション全体をコメントアウト、または削除する
-      resources:
-        reservations:
-          devices:
-            - driver: nvidia
-              count: all
-              capabilities: [gpu]
+    # deploy: # GPUがない場合は、deployセクション全体をコメントアウト、または削除する
+    #   resources:
+    #     reservations:
+    #       devices:
+    #         - driver: nvidia
+    #           count: all
+    #           capabilities: [gpu]
```
ファイルを修正したら、`sudo docker compose build`から再度実行してください。コンテナはCPUモードで動作します。

### 新しい仮想環境の追加方法

例として、`scikit-learn`用の`sklearn_env`という新しい環境を追加します。

1.  **環境定義ファイルを作成**
    `environments`ディレクトリ内に、`sklearn_env.yml`という新しいファイルを作成します。

    **`environments/sklearn_env.yml`**:
    ```yaml
    name: sklearn_env
    channels:
      - conda-forge
    dependencies:
      - python=3.12
      - scikit-learn
      - pandas
      - matplotlib
    ```

2.  **Dockerfileを編集**
    `.docker/Dockerfile`を開き、Conda環境を作成している箇所に、新しい環境を追加するコマンドを追記します。

    **`.docker/Dockerfile`**:
    ```diff
     # Conda環境の作成・更新
     RUN conda env update -n pytorch_env --file /app/environments/pytorch_env.yml --prune && \
    -        conda env update -n tensorflow_env --file /app/environments/tensorflow_env.yml --prune
    +        conda env update -n tensorflow_env --file /app/environments/tensorflow_env.yml --prune && \
    +        conda env update -n sklearn_env --file /app/environments/sklearn_env.yml --prune
    ```

3.  **イメージを再ビルド**
    変更を反映させるために、イメージを再ビルドします。
    ```bash
    sudo docker compose build
    ```
    ビルド完了後、コンテナに入れば`conda activate sklearn_env`で新しい環境が使えるようになっています。

### 既存の環境へのパッケージ追加

1.  **YAMLファイルを編集**
    `environments`ディレクトリ内の、パッケージを追加したい環境のYAMLファイル（例: `pytorch_env.yml`）に、ライブラリ名を追加します。
2.  **イメージを再ビルド**
    ```bash
    sudo docker compose build
    ```
    `conda env update`コマンドが差分だけを賢く更新してくれるため、効率的にパッケージが追加されます。

---

## 📁 ファイル構成

```
.
├── .docker
│   └── Dockerfile            # Dockerイメージの設計図
├── .gitignore                # Gitの追跡対象外ファイルを指定
├── README.md                 # このファイル
├── compose.yml               # Dockerコンテナの起動設定
├── environments              # Conda環境定義ファイルを格納するディレクトリ
│   ├── pytorch_env.yml       # PyTorch環境の定義
│   └── tensorflow_env.yml    # TensorFlow環境の定義
└── src                       # ソースコードやスクリプトを配置
    └── check_gpu_torch.py    # GPU動作確認用スクリプト
```

---

## 🧹 クリーンアップ

コンテナを停止し、関連するネットワーク等を削除するには以下のコマンドを実行します。

```bash
sudo docker compose down
```
コンテナが使用していたボリューム（データを永続化する領域）も完全に削除したい場合は、`-v`オプションを追加してください。

```bash
sudo docker compose down -v
```