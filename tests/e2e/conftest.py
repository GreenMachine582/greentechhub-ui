import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

pytest.importorskip("playwright")

_REPO_ROOT = Path(__file__).parent.parent.parent
_APP_PATH = _REPO_ROOT / "playground" / "app.py"
_TEST_PORT = 8501
_BASE_URL = f"http://127.0.0.1:{_TEST_PORT}"


def _wait_until_ready(url: str, timeout: float = 15.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.2)
    raise RuntimeError(f"playground server didn't become ready at {url} within {timeout}s")


@pytest.fixture(scope="session")
def playground_url():
    proc = subprocess.Popen(
        [sys.executable, str(_APP_PATH)],
        cwd=_REPO_ROOT,
        env={**os.environ, "PORT": str(_TEST_PORT)},
    )
    try:
        _wait_until_ready(_BASE_URL)
        yield _BASE_URL
    finally:
        proc.terminate()
        proc.wait(timeout=5)
