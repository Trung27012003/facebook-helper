import json
import os
import subprocess
import sys


def test_packaging_smoke_exits_cleanly_with_qt_and_chromium(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "facebook_helper", "--smoke-test", "--data-dir", str(tmp_path)],
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
        capture_output=True,
        text=True,
        timeout=60,
    )
    # A successful JSON file alone is insufficient: a crash during Qt teardown must fail this test.
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads((tmp_path / "smoke-result.json").read_text(encoding="utf-8"))
    assert data["ok"] and data["qt_started"] and data["worker_stopped"]
    assert data["tabs"] == 4 and data["chromium"]
    assert (tmp_path / "packaged-browser.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
