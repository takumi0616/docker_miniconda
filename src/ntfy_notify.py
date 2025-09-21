# src/ntfy_notify.py
import os
import sys
import time
import traceback
import platform
import urllib.request
import urllib.error
from contextlib import contextmanager
from typing import Optional, Iterable

def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.environ.get(name, default)
    return v if v not in ("", None) else default

def publish(
    message: str,
    title: Optional[str] = None,
    tags: Optional[Iterable[str]] = None,
    priority: int = 3,
    server: Optional[str] = None,
    topic: Optional[str] = None,
    token: Optional[str] = None,
) -> None:
    server = (server or _env("NTFY_SERVER", "https://ntfy.sh")).rstrip("/")
    topic = topic or _env("NTFY_TOPIC")
    token = token or _env("NTFY_TOKEN")

    if not topic:
        # 安全のため、トピック未設定なら送信しない
        print("[ntfy] NTFY_TOPIC is not set; skipping publish", file=sys.stderr)
        return

    url = f"{server}/{topic}"

    headers = {
        "X-Priority": str(priority),
    }
    if title:
        headers["X-Title"] = title
    if tags:
        headers["X-Tags"] = ",".join(tags)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = message.encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as _res:
            pass
    except Exception as e:
        # 通知失敗は本体処理には影響させない
        print(f"[ntfy] publish failed: {e}", file=sys.stderr)

@contextmanager
def notify_job(title: str, tags: Optional[Iterable[str]] = None, priority: int = 3):
    host = os.environ.get("HOST_HOSTNAME") or platform.node()
    container = os.environ.get("HOSTNAME", "unknown-container")
    user = os.environ.get("USER", "root")
    conda_env = os.environ.get("CONDA_DEFAULT_ENV", "none")
    cwd = os.getcwd()

    cmdline = " ".join(sys.argv) if sys.argv else "<python>"
    start_ts = time.time()
    start_msg = (
        f"host: {host}\n"
        f"container: {container}\n"
        f"user: {user}\n"
        f"conda: {conda_env}\n"
        f"cwd: {cwd}\n"
        f"cmd: {cmdline}\n"
    )
    publish(start_msg, title=f"{title} ▶️ START", tags=list(tags or []) + ["rocket", "hourglass"], priority=priority)
    try:
        yield
    except Exception as e:
        elapsed = int(time.time() - start_ts)
        h, m = divmod(elapsed, 3600)
        m, s = divmod(m, 60)
        tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        fail_msg = (
            f"host: {host}\n"
            f"container: {container}\n"
            f"user: {user}\n"
            f"conda: {conda_env}\n"
            f"cwd: {cwd}\n"
            f"elapsed: {h}:{m:02d}:{s:02d}\n"
            f"error: {e}\n"
            f"traceback:\n{tb}\n"
        )
        publish(fail_msg, title=f"{title} ❌ FAILED", tags=list(tags or []) + ["x", "cross_mark"], priority=5)
        raise
    else:
        elapsed = int(time.time() - start_ts)
        h, m = divmod(elapsed, 3600)
        m, s = divmod(m, 60)
        ok_msg = (
            f"host: {host}\n"
            f"container: {container}\n"
            f"user: {user}\n"
            f"conda: {conda_env}\n"
            f"cwd: {cwd}\n"
            f"elapsed: {h}:{m:02d}:{s:02d}\n"
        )
        publish(ok_msg, title=f"{title} ✅ DONE", tags=list(tags or []) + ["white_check_mark"], priority=priority)
