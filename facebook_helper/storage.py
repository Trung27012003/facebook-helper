import json
import shutil
import sqlite3
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from platformdirs import user_data_path

from .domain import STATUSES, excel_text, normalize_group, post_url


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, root=None):
        self.root = Path(root) if root else user_data_path("FacebookHelper", appauthor=False)
        self.root.mkdir(parents=True, exist_ok=True)
        for folder in ("images", "evidence", "browser"):
            (self.root / folder).mkdir(exist_ok=True)
        self.db = sqlite3.connect(self.root / "helper.db")
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY, title TEXT NOT NULL, html TEXT NOT NULL,
                plain TEXT NOT NULL, tags TEXT NOT NULL DEFAULT '',
                images TEXT NOT NULL DEFAULT '[]', updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL, url TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY, post_id INTEGER REFERENCES posts(id) ON DELETE SET NULL,
                group_id INTEGER REFERENCES groups(id) ON DELETE SET NULL,
                title TEXT NOT NULL, group_name TEXT NOT NULL, group_url TEXT NOT NULL,
                body TEXT NOT NULL, images TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft', url TEXT NOT NULL DEFAULT '',
                evidence TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            PRAGMA user_version=1;
        """)

    def posts(self):
        return [dict(row) for row in self.db.execute("SELECT * FROM posts ORDER BY updated_at DESC, id DESC")]

    def post(self, post_id):
        row = self.db.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
        if row is None:
            raise ValueError("Bài viết không còn tồn tại.")
        result = dict(row)
        result["images"] = json.loads(result["images"])
        return result

    def import_image(self, source):
        from PySide6.QtGui import QImageReader

        path = Path(source)
        if not QImageReader(str(path)).canRead():
            raise ValueError(f"Không đọc được ảnh: {path.name}")
        if path.stat().st_size > 30 * 1024 * 1024:
            raise ValueError(f"Ảnh vượt quá 30 MB: {path.name}")
        target = Path("images") / f"{uuid.uuid4().hex}{path.suffix.lower()}"
        shutil.copy2(path, self.root / target)
        return target.as_posix()

    def save_post(self, post_id, title, html, plain, tags, images):
        if not title.strip() or not plain.strip():
            raise ValueError("Nhập tiêu đề quản lý và nội dung bài viết.")
        for image in images:
            self.asset(image)
        values = (title.strip(), html, plain.strip(), tags.strip(), json.dumps(images), now())
        with self.db:
            if post_id is None:
                return self.db.execute(
                    "INSERT INTO posts(title,html,plain,tags,images,updated_at) VALUES(?,?,?,?,?,?)", values
                ).lastrowid
            self.db.execute(
                "UPDATE posts SET title=?,html=?,plain=?,tags=?,images=?,updated_at=? WHERE id=?",
                (*values, post_id),
            )
        return post_id

    def delete_post(self, post_id):
        with self.db:
            self.db.execute("DELETE FROM posts WHERE id=?", (post_id,))

    def groups(self):
        return [dict(row) for row in self.db.execute("SELECT * FROM groups ORDER BY name")]

    def save_group(self, group_id, name, url, category, notes):
        if not name.strip():
            raise ValueError("Nhập tên nhóm.")
        values = (name.strip(), normalize_group(url), category.strip(), notes.strip())
        try:
            with self.db:
                if group_id is None:
                    return self.db.execute(
                        "INSERT INTO groups(name,url,category,notes) VALUES(?,?,?,?)", values
                    ).lastrowid
                self.db.execute(
                    "UPDATE groups SET name=?,url=?,category=?,notes=? WHERE id=?", (*values, group_id)
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError("Nhóm này đã có trong danh sách.") from exc
        return group_id

    def delete_group(self, group_id):
        with self.db:
            self.db.execute("DELETE FROM groups WHERE id=?", (group_id,))

    def create_job(self, post_id, group_id):
        post = self.post(post_id)
        group = self.db.execute("SELECT * FROM groups WHERE id=?", (group_id,)).fetchone()
        if group is None:
            raise ValueError("Nhóm không còn tồn tại.")
        body = post["plain"] + ("\n\n" + post["tags"] if post["tags"] else "")
        with self.db:
            return self.db.execute(
                """INSERT INTO jobs(post_id,group_id,title,group_name,group_url,body,images,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (
                    post_id,
                    group_id,
                    post["title"],
                    group["name"],
                    group["url"],
                    body,
                    json.dumps(post["images"]),
                    now(),
                    now(),
                ),
            ).lastrowid

    def jobs(self):
        return [dict(row) for row in self.db.execute("SELECT * FROM jobs ORDER BY id DESC")]

    def job(self, job_id):
        row = self.db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise ValueError("Không tìm thấy lượt đăng.")
        return dict(row)

    def update_job(self, job_id, **changes):
        if not changes or set(changes) - {"status", "url", "evidence", "note"}:
            raise ValueError("Trường cập nhật không hợp lệ.")
        if "status" in changes and changes["status"] not in STATUSES:
            raise ValueError("Trạng thái không hợp lệ.")
        old = self.job(job_id)
        if changes.get("url"):
            changes["url"] = post_url(changes["url"], old["group_url"])
        if changes.get("status", old["status"]) == "published" and not changes.get("url", old["url"]):
            raise ValueError("Cần lưu link bài cụ thể trước khi xác nhận đã hiển thị.")
        if changes.get("evidence"):
            self.asset(changes["evidence"])
        changes["updated_at"] = now()
        with self.db:
            self.db.execute(
                "UPDATE jobs SET " + ",".join(f"{field}=?" for field in changes) + " WHERE id=?",
                (*changes.values(), job_id),
            )

    def asset(self, relative):
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root.resolve()) or not path.is_file():
            raise ValueError(f"Không tìm thấy tệp trong thư mục dữ liệu: {relative}")
        return path

    def export_excel(self, target):
        from openpyxl import Workbook
        from openpyxl.styles import Font

        book = Workbook()
        sheet = book.active
        sheet.title = "Lịch sử đăng"
        sheet.append(
            [
                "Mã",
                "Bài tuyển dụng",
                "Nhóm",
                "Link nhóm",
                "Trạng thái",
                "Link bài",
                "Ảnh minh chứng",
                "Ghi chú",
                "Tạo lúc (UTC)",
                "Cập nhật (UTC)",
                "Nội dung",
            ]
        )
        for job in reversed(self.jobs()):
            sheet.append(
                [
                    excel_text(value)
                    for value in (
                        job["id"],
                        job["title"],
                        job["group_name"],
                        job["group_url"],
                        STATUSES[job["status"]],
                        job["url"],
                        job["evidence"],
                        job["note"],
                        job["created_at"],
                        job["updated_at"],
                        job["body"],
                    )
                ]
            )
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        for cell in sheet[1]:
            cell.font = Font(bold=True)
        for col in ("B", "C", "D", "E", "F", "G", "H", "K"):
            sheet.column_dimensions[col].width = 35
        book.save(target)

    def backup(self, target):
        """Consistent SQLite snapshot; deliberately exclude authenticated browser profile."""
        import tempfile

        destination = Path(target).resolve()
        if destination.is_relative_to(self.root.resolve()):
            raise ValueError("Lưu bản sao bên ngoài thư mục dữ liệu ứng dụng.")
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "helper.db"
            with sqlite3.connect(db_path) as snapshot:
                self.db.backup(snapshot)
            with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.write(db_path, "helper.db")
                for folder in ("images", "evidence"):
                    for path in (self.root / folder).rglob("*"):
                        if path.is_file() and not path.is_symlink():
                            archive.write(path, path.relative_to(self.root))

    def close(self):
        self.db.close()
