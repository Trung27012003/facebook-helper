"""Include dot directories as well as browser binaries in the portable ZIP."""

import hashlib
import shutil
import zipfile
from pathlib import Path

root = Path("dist/FacebookHelper")
release = Path("release")
release.mkdir(exist_ok=True)
shutil.copy2("packaging/HUONG-DAN.txt", root / "HUONG-DAN.txt")
shutil.copy2("README.md", root / "README.md")
target = release / "FacebookHelper-Windows-x64.zip"
with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for path in sorted(root.rglob("*")):
        if path.is_file():
            archive.write(path, path.relative_to(root.parent))
with target.open("rb") as stream:
    digest = hashlib.file_digest(stream, "sha256").hexdigest()
(release / "SHA256SUMS.txt").write_text(f"{digest}  {target.name}\n", encoding="utf-8")
print(f"Packaged {target.name}: {target.stat().st_size:,} bytes")
