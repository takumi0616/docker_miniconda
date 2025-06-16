################################################################################
# Part 1: Gitリポジトリの準備 (オプション)
# (作業ディレクトリの準備として記載)
################################################################################

# 作業ディレクトリに移動
# cd ~/work_takasuka_git

# Gitリポジトリを初期化
$ git init
hint: Using 'master' as the name for the initial branch. This default branch name
hint: is subject to change. To configure the initial branch name to use in all
hint: of your new repositories, which will suppress this warning, call:
hint:
hint:   git config --global init.defaultBranch <name>
hint:
hint: Names commonly chosen instead of 'master' are 'main', 'trunk' and
hint: 'development'. The just-created branch can be renamed via this command:
hint:
hint:   git branch -m <name>
Initialized empty Git repository in /home/devel/work_takasuka_git/.git/

# このリポジトリ用のGitユーザーを設定
$ git config --local user.name "your-username"
$ git config --local user.email "your-email@example.com"

# GitHub連携のためのSSHキーを作成 (存在しない場合)
$ ssh-keygen -t ed25519 -C "your-email@example.com"
Generating public/private ed25519 key pair.
Enter file in which to save the key (/home/devel/.ssh/id_ed25519):
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in /home/devel/.ssh/id_ed25519
Your public key has been saved in /home/devel/.ssh/id_ed25519.pub
The key fingerprint is:
SHA256:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX your-email@example.com
The key's randomart image is:
+--[ED25519 256]--+
|        .        |
|       . .       |
|      .   .      |
|     .     .     |
|    S      .     |
|   . .      .    |
|  .   .      .   |
| .     .      .  |
|E . . . .      . |
+----[SHA256]-----+

# 作成した公開鍵を表示 (この内容をGitHubのSSH Keysに登録)
$ cat ~/.ssh/id_ed25519.pub
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb your-email@example.com

# GitHubとのSSH接続を確認
$ ssh -T git@github.com
Hi your-username! You've successfully authenticated, but GitHub does not provide shell access.

# リポジトリをクローン
$ git clone git@github.com:your-username/your-repository.git
Cloning into 'your-repository'...
remote: Enumerating objects: 83, done.
remote: Counting objects: 100% (83/83), done.
remote: Compressing objects: 100% (56/56), done.
remote: Total 83 (delta 28), reused 68 (delta 16), pack-reused 0
Receiving objects: 100% (83/83), 23.50 KiB | 23.50 MiB/s, done.
Resolving deltas: 100% (28/28), done.


################################################################################
# Part 2: Docker Engine & Docker Compose のインストール
################################################################################

# --- ステップ 2-1: 事前準備 ---

# システムのパッケージリストを更新
$ sudo apt-get update
Hit:1 http://security.ubuntu.com/ubuntu noble-security InRelease
...
Reading package lists... Done

# 古いバージョンのDockerがあればアンインストール（クリーンな環境ではエラーになるが正常）
$ sudo apt-get remove docker docker-engine docker.io containerd runc
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
Package 'docker' is not installed, so not removed
E: Unable to locate package docker-engine

# HTTPSリポジトリのために必要なパッケージをインストール
$ sudo apt-get install -y ca-certificates curl
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
ca-certificates is already the newest version (20240203).
curl is already the newest version (8.5.0-2ubuntu10.6).
0 upgraded, 0 newly installed, 0 to remove and 95 not upgraded.


# --- ステップ 2-2: Docker公式リポジトリのセットアップ ---

# GPGキー用のディレクトリを作成
$ sudo install -m 0755 -d /etc/apt/keyrings

# Dockerの公式GPGキーをダウンロード
$ sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc

# GPGキーの権限を設定
$ sudo chmod a+r /etc/apt/keyrings/docker.asc

# DockerのリポジトリをAptソースリストに追加
$ echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null


# --- ステップ 2-3: Docker Engine本体のインストール ---

# 追加したリポジトリの情報を含めてパッケージリストを再度更新
$ sudo apt-get update
Get:1 https://download.docker.com/linux/ubuntu noble InRelease [48.8 kB]
...
Fetched 74.7 kB in 1s (51.1 kB/s)
Reading package lists... Done

# Docker関連パッケージ一式をインストール
# 注意: この過程で "Could not execute systemctl" というエラーが出ることがありますが、次のステップで解決しますので問題ありません。
$ sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
Reading package lists... Done
...
The following packages will be REMOVED:
  containerd docker.io runc
The following NEW packages will be installed:
  containerd.io docker-buildx-plugin docker-ce docker-ce-cli docker-ce-rootless-extras docker-compose-plugin libslirp0 slirp4netns
...
Setting up docker-ce (5:28.2.2-1~ubuntu.24.04~noble) ...
Could not execute systemctl:  at /usr/bin/deb-systemd-invoke line 148.
...
Processing triggers for ...


################################################################################
# Part 3: サービス起動エラーの解決 (トラブルシューティング)
################################################################################

# --- ステップ 3-1: サービス起動試行と失敗の確認 ---

# Dockerサービスを手動で起動しようとすると、この段階では失敗する可能性が高い
$ sudo systemctl start docker
Job for docker.service failed because the control process exited with error code.
See "systemctl status docker.service" and "journalctl -xeu docker.service" for details.

# --- ステップ 3-2: systemd設定の修正とサービスの正常起動 ---

# 念のため、関連サービスを完全に停止
$ sudo systemctl stop docker.socket
$ sudo systemctl stop docker.service

# systemdに全サービスの設定ファイルを再読み込みさせる（これがエラー解決の鍵）
$ sudo systemctl daemon-reload

# 新しい正しい設定でDockerサービスを起動
$ sudo systemctl start docker

# サービスのステータスを確認
$ sudo systemctl status docker
● docker.service - Docker Application Container Engine
     Loaded: loaded (/usr/lib/systemd/system/docker.service; enabled; preset: enabled)
     Active: active (running) since Mon 2025-06-16 18:53:11 JST; 4s ago
TriggeredBy: ● docker.socket
       Docs: https://docs.docker.com
   Main PID: 901755 (dockerd)
      Tasks: 20
     Memory: 25.4M (peak: 30.2M)
        CPU: 258ms
     CGroup: /system.slice/docker.service
             └─901755 /usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock

...
Jun 16 18:53:11 gpu02 systemd[1]: Started docker.service - Docker Application Container Engine.

# これでデーモンが正常に起動していることが確認できたので、sudo付きで動作確認
$ sudo docker ps
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES


################################################################################
# Part 4: 最終設定 (sudoなしでの利用)
################################################################################

# --- ステップ 4-1: ユーザーをdockerグループに追加 ---

# 現在のログインユーザーをdockerグループに追加
$ sudo usermod -aG docker $USER

# --- ステップ 4-2: 設定の反映と最終確認 ---

# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# ★【最重要】上記コマンドの実行後、設定を有効にするには、      ★
# ★   必ずサーバーから一度ログアウトし、再度ログインしてください！  ★
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★

# (再ログイン後、以下のコマンドを実行)

# 自分がdockerグループに所属しているか確認
$ groups
devel adm cdrom sudo dip plugdev lxd docker

# sudoなしでdockerコマンドが実行できることを確認
$ docker ps
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES

# docker-composeコマンドもsudoなしで実行できることを確認
$ docker compose version
Docker Compose version v2.36.2

# これで全てのセットアップが完了です。