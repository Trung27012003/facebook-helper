import hashlib
from pathlib import Path

release = Path("release")
files = sorted([*release.glob("*.zip"), *release.glob("*.exe")])
if not files:
    raise RuntimeError("No release files")
lines = []
for file in files:
    with file.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    lines.append(f"{digest}  {file.name}\n")
(release / "SHA256SUMS.txt").write_text("".join(lines), encoding="utf-8")
print("Release sizes: " + ", ".join(f"{p.name}={p.stat().st_size}" for p in files))
