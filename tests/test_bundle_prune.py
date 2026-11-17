import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "bundle_prune", Path(__file__).parents[1] / "packaging/prune_bundle.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_only_optional_bundle_resources_are_removed(tmp_path):
    root = tmp_path / "app"
    root.mkdir()
    (root / "FacebookHelper.exe").write_bytes(b"exe")
    base = root / "_internal/playwright/driver/package/.local-browsers"
    files = [
        "chromium_headless_shell-123/shell.exe",
        "chromium-123/chrome.exe",
        "chromium-123/locales/vi.pak",
        "chromium-123/locales/en-US.pak",
        "chromium-123/locales/fr.pak",
    ]
    for name in files:
        target = base / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"x" * 20)
    (root / "source.js.map").write_text("debug map")
    (root / "LICENSE.txt").write_text("license")
    report = module.prune(root)
    assert report["removed_bytes"] > 0
    assert not (base / files[0]).exists() and not (base / files[-1]).exists()
    assert (base / files[1]).exists() and (base / files[2]).exists() and (base / files[3]).exists()
    assert (root / "LICENSE.txt").exists()
    with pytest.raises(ValueError):
        module.prune(tmp_path / "not-built")
