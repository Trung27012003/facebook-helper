"""Remove optional development resources from a built application only."""

import json
import shutil
from pathlib import Path


def prune(root):
    root = Path(root)
    if not (root / "FacebookHelper.exe").is_file():
        raise ValueError("Expected a built FacebookHelper.exe directory")
    before = sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
    removed = []
    browsers = root / "_internal/playwright/driver/package/.local-browsers"
    for folder in browsers.glob("chromium_headless_shell-*"):
        removed.append(folder.relative_to(root).as_posix())
        shutil.rmtree(folder)
    for file in list(root.rglob("*")):
        if not file.is_file():
            continue
        optional = file.name.endswith(".js.map") or file.name.endswith(".d.ts")
        locale = (
            file.suffix == ".pak"
            and file.parent.name in {"locales", "qtwebengine_locales"}
            and file.stem not in {"en-US", "en-GB", "vi"}
        )
        if optional or locale:
            removed.append(file.relative_to(root).as_posix())
            file.unlink()
    after = sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
    return {
        "before_bytes": before,
        "after_bytes": after,
        "removed_bytes": before - after,
        "removed_files_or_folders": removed,
        "ok": True,
    }


if __name__ == "__main__":
    result = prune("dist/FacebookHelper")
    Path("release").mkdir(exist_ok=True)
    Path("release/prune-audit.json").write_text(json.dumps(result, indent=2))
    print("Bundle prune: " + json.dumps({k: v for k, v in result.items() if k != "removed_files_or_folders"}))
