# docker_miniconda

使い方
Dockerイメージのビルド
ターミナルで以下のコマンドを実行し、Dockerfileと_env.ymlに基づいてDockerイメージをビルドします。

Bash

docker compose build
コンテナの起動
以下のコマンドでコンテナをバックグラウンドで起動します。

Bash

docker compose up -d
コンテナへのアクセス
コンテナ内に入り、開発作業を行います。DockerfileのSHELL命令により、デフォルトでpytorch_envが有効化された状態でbashが起動します。

Bash

docker compose exec app bash
コンテナ内でcheck_gpu_torch.pyを実行して、PyTorchがGPUを認識しているか確認できます。

Bash

(pytorch_env) root@container_id:/app# python src/check_gpu_torch.py
別のConda環境への切り替え
tensorflow_envなど、別の環境に切り替えることも簡単です。

Bash

(pytorch_env) root@container_id:/app# conda activate tensorflow_env
(tensorflow_env) root@container_id:/app#