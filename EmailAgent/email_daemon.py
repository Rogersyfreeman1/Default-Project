import subprocess
import time
import os
import sys
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_SCRIPT = os.path.join(BASE_DIR, "email_agent.py")
LOG_FILE = os.path.join(BASE_DIR, "daemon.log")


def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} - {msg}\n")


def next_run_time(hour=9, minute=0):
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target


def run_agent():
    log("Running email agent...")
    try:
        result = subprocess.run(
            [sys.executable, AGENT_SCRIPT],
            timeout=3600,
            capture_output=True,
            text=True,
        )
        log(f"Agent finished with exit code {result.returncode}")
        if result.stdout:
            log("STDOUT: " + result.stdout[-2000:])
        if result.stderr:
            log("STDERR: " + result.stderr[-2000:])
    except subprocess.TimeoutExpired:
        log("Agent timed out after 1 hour")
    except Exception as e:
        log(f"Agent failed: {e}")


def main():
    log("Email agent daemon started")
    run_agent()
    while True:
        target = next_run_time()
        wait_secs = (target - datetime.now()).total_seconds()
        log(f"Next run at {target.isoformat()} (waiting {int(wait_secs)}s)")
        time.sleep(max(wait_secs, 1))
        run_agent()


if __name__ == "__main__":
    main()
