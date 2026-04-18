import subprocess
from handlers.utils import log, send_json, HOME

def handle_system(h, p, body):
    if p == "/git_commit":
        try:
            cwd = body.get("path", HOME)
            msg = body.get("message", "Update")
            subprocess.run(["git", "add", "-A"], capture_output=True, text=True, cwd=cwd, timeout=10)
            commit = subprocess.run(["git", "commit", "-m", msg], capture_output=True, text=True, cwd=cwd, timeout=10)
            return send_json(h, {"out": commit.stdout + commit.stderr, "code": commit.returncode})
        except Exception as e:
            return send_json(h, {"error": str(e)}, 500)

    if p == "/git_push":
        try:
            cwd = body.get("path", HOME)
            push = subprocess.run(["git", "push"], capture_output=True, text=True, cwd=cwd, timeout=30)
            return send_json(h, {"out": push.stdout + push.stderr, "code": push.returncode})
        except Exception as e:
            return send_json(h, {"error": str(e)}, 500)

    return False
