import hashlib
import json
import shutil
import sqlite3
import unicodedata
import uuid
import zipfile
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path

from platformdirs import user_data_path

from .domain import STATUSES, excel_text, normalize_group, parse_tags, post_url
from .formatting import article_html


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
        self._image_hashes = {}
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
            CREATE TABLE IF NOT EXISTS batches (
                id INTEGER PRIMARY KEY, title TEXT NOT NULL, post_id INTEGER REFERENCES posts(id) ON DELETE SET NULL,
                audience TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL
            );
        """)
        columns = {row[1] for row in self.db.execute("PRAGMA table_info(jobs)")}
        with self.db:
            post_columns = {row[1] for row in self.db.execute("PRAGMA table_info(posts)")}
            if "uid" not in post_columns:
                self.db.execute("ALTER TABLE posts ADD COLUMN uid TEXT NOT NULL DEFAULT ''")
            for row in self.db.execute("SELECT id FROM posts WHERE uid='' ").fetchall():
                self.db.execute("UPDATE posts SET uid=? WHERE id=?", (uuid.uuid4().hex, row[0]))
            self.db.execute("CREATE UNIQUE INDEX IF NOT EXISTS posts_uid ON posts(uid) WHERE uid!=''")
            if "batch_id" not in columns:
                self.db.execute("ALTER TABLE jobs ADD COLUMN batch_id INTEGER REFERENCES batches(id)")
            if "position" not in columns:
                self.db.execute("ALTER TABLE jobs ADD COLUMN position INTEGER NOT NULL DEFAULT 0")
            if "body_html" not in columns:
                self.db.execute("ALTER TABLE jobs ADD COLUMN body_html TEXT NOT NULL DEFAULT ''")
            for field in ("sent_at", "checked_at", "first_visible_at", "check_outcome", "check_note"):
                if field not in columns:
                    self.db.execute(f"ALTER TABLE jobs ADD COLUMN {field} TEXT NOT NULL DEFAULT ''")
            if "hidden_at" not in columns:
                self.db.execute("ALTER TABLE jobs ADD COLUMN hidden_at TEXT NOT NULL DEFAULT ''")
            if "allow_duplicate" not in columns:
                self.db.execute("ALTER TABLE jobs ADD COLUMN allow_duplicate INTEGER NOT NULL DEFAULT 0")
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS job_events (
                    id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES jobs(id),
                    happened_at TEXT NOT NULL, source TEXT NOT NULL,
                    old_status TEXT NOT NULL, new_status TEXT NOT NULL, note TEXT NOT NULL, url TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS events_job ON job_events(job_id, id);
                CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            """)
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
                    name_key TEXT NOT NULL UNIQUE, notes TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS group_positions (
                    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
                    position_id INTEGER NOT NULL REFERENCES positions(id) ON DELETE RESTRICT,
                    PRIMARY KEY(group_id, position_id)
                );
                CREATE INDEX IF NOT EXISTS group_positions_position ON group_positions(position_id);
            """)
            self.db.execute("PRAGMA user_version=7")
        self.recovered = []

    def recover_interrupted(self):
        self.recovered = []
        for job in self.jobs():
            if job["status"] == "sending":
                self.update_job(
                    job["id"],
                    source="recovery",
                    status="uncertain",
                    note="Ứng dụng đóng khi đang gửi. Kiểm tra Facebook trước khi gửi lại.",
                )
                self.recovered.append(job["id"])

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
                    "INSERT INTO posts(title,html,plain,tags,images,updated_at,uid) VALUES(?,?,?,?,?,?,?)",
                    (*values, uuid.uuid4().hex),
                ).lastrowid
            self.db.execute(
                "UPDATE posts SET title=?,html=?,plain=?,tags=?,images=?,updated_at=? WHERE id=?",
                (*values, post_id),
            )
        return post_id

    def delete_post(self, post_id):
        with self.db:
            self.db.execute("DELETE FROM posts WHERE id=?", (post_id,))

    def positions(self):
        return [
            dict(r)
            for r in self.db.execute("""SELECT p.*,
            (SELECT COUNT(*) FROM group_positions gp WHERE gp.position_id=p.id) AS group_count
            FROM positions p ORDER BY p.name_key,p.id""")
        ]

    def save_position(self, position_id, name, notes=""):
        name = " ".join(unicodedata.normalize("NFC", name).split())
        if not name:
            raise ValueError("Nhập tên vị trí tuyển dụng.")
        try:
            with self.db:
                if position_id is None:
                    return self.db.execute(
                        "INSERT INTO positions(name,name_key,notes) VALUES(?,?,?)",
                        (name, name.casefold(), notes.strip()),
                    ).lastrowid
                updated = self.db.execute(
                    "UPDATE positions SET name=?,name_key=?,notes=? WHERE id=?",
                    (name, name.casefold(), notes.strip(), position_id),
                )
                if updated.rowcount != 1:
                    raise ValueError("Vị trí không còn tồn tại.")
        except sqlite3.IntegrityError as exc:
            raise ValueError("Tên vị trí này đã có trong danh sách.") from exc
        return position_id

    def delete_position(self, position_id):
        try:
            with self.db:
                self.db.execute("DELETE FROM positions WHERE id=?", (position_id,))
        except sqlite3.IntegrityError as exc:
            raise ValueError("Vị trí đang dùng cho nhóm. Gỡ vị trí khỏi các nhóm trước khi xóa.") from exc

    def groups(self):
        bindings = {}
        names = {p["id"]: p["name"] for p in self.positions()}
        for relation in self.db.execute(
            "SELECT group_id,position_id FROM group_positions ORDER BY position_id"
        ):
            bindings.setdefault(relation["group_id"], []).append(relation["position_id"])
        result = []
        for row in self.db.execute("SELECT * FROM groups ORDER BY name,id"):
            group = dict(row)
            group["position_ids"] = bindings.get(group["id"], [])
            group["position_names"] = [names[i] for i in group["position_ids"]]
            result.append(group)
        return result

    def save_group(self, group_id, name, url, category, notes, position_ids=None):
        if not name.strip():
            raise ValueError("Nhập tên nhóm.")
        ids = list(dict.fromkeys(position_ids or []))
        if not ids:
            raise ValueError("Chọn ít nhất một vị trí tuyển dụng cho nhóm.")
        if any(type(i) is not int for i in ids):
            raise ValueError("Vị trí tuyển dụng không hợp lệ.")
        values = (name.strip(), normalize_group(url), ", ".join(parse_tags(category)), notes.strip())
        try:
            with self.db:
                placeholders = ",".join("?" for _ in ids)
                found = self.db.execute(
                    f"SELECT count(*) FROM positions WHERE id IN ({placeholders})", ids
                ).fetchone()[0]
                if found != len(ids):
                    raise ValueError("Có vị trí không còn tồn tại. Hãy chọn lại.")
                if group_id is None:
                    group_id = self.db.execute(
                        "INSERT INTO groups(name,url,category,notes) VALUES(?,?,?,?)", values
                    ).lastrowid
                else:
                    updated = self.db.execute(
                        "UPDATE groups SET name=?,url=?,category=?,notes=? WHERE id=?", (*values, group_id)
                    )
                    if updated.rowcount != 1:
                        raise ValueError("Nhóm không còn tồn tại.")
                self.db.execute("DELETE FROM group_positions WHERE group_id=?", (group_id,))
                self.db.executemany(
                    "INSERT INTO group_positions(group_id,position_id) VALUES(?,?)",
                    [(group_id, i) for i in ids],
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError("Nhóm này đã có trong danh sách.") from exc
        return group_id

    def groups_for_selection(self, position_ids=(), tags=()):
        selected = set(position_ids)
        known = {p["id"] for p in self.positions()}
        if selected - known:
            raise ValueError("Có vị trí không còn tồn tại. Hãy chọn lại.")
        labels = {tag.casefold() for tag in parse_tags(",".join(tags))}
        if not selected and not labels:
            return []
        return [
            g
            for g in self.groups()
            if selected.intersection(g["position_ids"])
            or labels.intersection(t.casefold() for t in parse_tags(g["category"]))
        ]

    def delete_group(self, group_id):
        with self.db:
            self.db.execute("DELETE FROM groups WHERE id=?", (group_id,))

    def create_job(self, post_id, group_id, allow_duplicate=False):
        post = self.post(post_id)
        group = self.db.execute("SELECT * FROM groups WHERE id=?", (group_id,)).fetchone()
        if group is None:
            raise ValueError("Nhóm không còn tồn tại.")
        with self.db:
            return self._insert_job(post, group, allow_duplicate=allow_duplicate)

    def _insert_job(self, post, group, batch_id=None, position=0, allow_duplicate=False):
        body = post["plain"] + ("\n\n" + post["tags"] if post["tags"] else "")
        return self.db.execute(
            """INSERT INTO jobs(post_id,group_id,title,group_name,group_url,body,images,
            created_at,updated_at,batch_id,position,body_html,allow_duplicate) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                post["id"],
                group["id"],
                post["title"],
                group["name"],
                group["url"],
                body,
                json.dumps(post["images"]),
                now(),
                now(),
                batch_id,
                position,
                article_html(post["html"], post["tags"]),
                int(allow_duplicate),
            ),
        ).lastrowid

    def group_tags(self):
        labels = {}
        for group in self.groups():
            for tag in parse_tags(group["category"]):
                labels.setdefault(tag.casefold(), tag)
        return sorted(labels.values(), key=str.casefold)

    def groups_by_tag(self, tag):
        labels = parse_tags(tag)
        if len(labels) != 1:
            return []
        key = labels[0].casefold()
        return [
            group
            for group in self.groups()
            if key in {label.casefold() for label in parse_tags(group["category"])}
        ]

    def create_batch(self, post_id, group_ids, title="", audience="", allow_duplicate=False):
        post = self.post(post_id)
        ids = list(dict.fromkeys(group_ids))
        if not ids:
            raise ValueError("Chọn ít nhất một nhóm để đăng bài.")
        groups = []
        for group_id in ids:
            group = self.db.execute("SELECT * FROM groups WHERE id=?", (group_id,)).fetchone()
            if group is None:
                raise ValueError("Một nhóm đã bị xóa. Hãy chọn lại danh sách nhóm.")
            groups.append(group)
        with self.db:
            batch_id = self.db.execute(
                "INSERT INTO batches(title,post_id,audience,created_at) VALUES(?,?,?,?)",
                (title.strip() or post["title"], post_id, audience, now()),
            ).lastrowid
            for position, group in enumerate(groups):
                self._insert_job(post, group, batch_id, position, allow_duplicate)
        return batch_id

    def batches(self):
        return [
            dict(row)
            for row in self.db.execute(
                "SELECT b.*, (SELECT count(*) FROM jobs j WHERE j.batch_id=b.id) AS total FROM batches b ORDER BY b.id DESC"
            )
        ]

    def batch_jobs(self, batch_id):
        return [
            dict(row)
            for row in self.db.execute(
                "SELECT * FROM jobs WHERE batch_id=? ORDER BY position,id", (batch_id,)
            )
        ]

    def jobs(self):
        return [dict(row) for row in self.db.execute("SELECT * FROM jobs ORDER BY id DESC")]

    def posting_register(self):
        """Prefer actual send time, then attempted send, then creation for unsent rows."""
        return [
            dict(row)
            for row in self.db.execute("""
            SELECT j.*, COALESCE(b.title, '') AS batch_title,
                   COALESCE(NULLIF(j.sent_at, ''),
                            (SELECT e.happened_at FROM job_events e
                             WHERE e.job_id=j.id AND e.new_status='sending'
                             ORDER BY e.id DESC LIMIT 1), j.created_at) AS activity_at
            FROM jobs j LEFT JOIN batches b ON b.id=j.batch_id
            WHERE j.hidden_at=''
            ORDER BY activity_at DESC, j.id DESC
        """)
        ]

    def remove_posted_records(self, job_ids):
        """Remove sent entries from the register, retaining receipts against reposts."""
        ids = list(dict.fromkeys(job_ids))
        with self.db:
            jobs = [self.job(job_id) for job_id in ids]
            if any(
                j["status"] not in {"submitted", "pending", "published", "rejected", "removed"} for j in jobs
            ):
                raise ValueError("Chỉ xóa bản ghi của bài đã gửi. Lượt chưa gửi hoặc đang chạy được giữ lại.")
            self.db.executemany("UPDATE jobs SET hidden_at=? WHERE id=?", [(now(), j) for j in ids])
        return len(ids)

    def job(self, job_id):
        row = self.db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise ValueError("Không tìm thấy lượt đăng.")
        return dict(row)

    def update_job(self, job_id, source="manual", **changes):
        if not changes or set(changes) - {"status", "url", "evidence", "note"}:
            raise ValueError("Trường cập nhật không hợp lệ.")
        if "status" in changes and changes["status"] not in STATUSES:
            raise ValueError("Trạng thái không hợp lệ.")
        old = self.job(job_id)
        if changes.get("url"):
            changes["url"] = post_url(changes["url"], old["group_url"])
        if changes.get("status", old["status"]) == "published" and not changes.get("url", old["url"]):
            raise ValueError("Cần lưu link bài cụ thể trước khi xác nhận đã hiển thị.")
        if "url" in changes and changes["url"] != old["url"]:
            # Evidence and confirmation refer to one permalink, not any post in the group.
            changes.setdefault("evidence", "")
            if old["status"] == "published" and "status" not in changes:
                changes["status"] = "prepared"
        if changes.get("evidence"):
            self.asset(changes["evidence"])
        changes["updated_at"] = now()
        new_status = changes.get("status", old["status"])
        if (
            source in {"browser", "manual_sent"}
            and new_status in {"submitted", "pending", "published", "rejected", "removed"}
            and not old["sent_at"]
        ):
            changes["sent_at"] = now()
        if new_status == "published" and not old["first_visible_at"]:
            changes["first_visible_at"] = now()
        with self.db if not self.db.in_transaction else nullcontext():
            self.db.execute(
                "UPDATE jobs SET " + ",".join(f"{field}=?" for field in changes) + " WHERE id=?",
                (*changes.values(), job_id),
            )
            if (
                source == "check"
                or new_status != old["status"]
                or changes.get("url", old["url"]) != old["url"]
            ):
                self._event(
                    job_id,
                    source,
                    old["status"],
                    new_status,
                    changes.get("note", ""),
                    changes.get("url", old["url"]),
                )

    def _event(self, job_id, source, old_status, new_status, note, url):
        self.db.execute(
            "INSERT INTO job_events(job_id,happened_at,source,old_status,new_status,note,url) VALUES(?,?,?,?,?,?,?)",
            (job_id, now(), source, old_status, new_status, note, url),
        )

    def record_check(self, job_id, outcome, note, url=""):
        if outcome not in {"unknown", "pending", "published", "rejected", "removed"}:
            raise ValueError("Kết quả kiểm tra không hợp lệ.")
        old = self.job(job_id)
        with self.db:
            self.db.execute(
                "UPDATE jobs SET checked_at=?,check_outcome=?,check_note=? WHERE id=?",
                (now(), outcome, note, job_id),
            )
            if outcome != "unknown":
                changes = {"status": outcome, "note": note}
                if url:
                    changes["url"] = url
                self.update_job(job_id, source="check", **changes)
            if outcome == "unknown":
                self._event(job_id, "check", old["status"], old["status"], note, url or old["url"])

    def events(self, job_id):
        return [
            dict(row)
            for row in self.db.execute("SELECT * FROM job_events WHERE job_id=? ORDER BY id DESC", (job_id,))
        ]

    def preference(self, key, default=""):
        row = self.db.execute("SELECT value FROM preferences WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def set_preference(self, key, value):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO preferences(key,value) VALUES(?,?)", (key, str(value)))

    def content_key(self, body, images):
        normalized = " ".join(unicodedata.normalize("NFC", body).split())
        image_hashes = []
        for image in images:
            try:
                path = self.asset(image)
                stat = path.stat()
                key = (image, stat.st_mtime_ns, stat.st_size)
                if key not in self._image_hashes:
                    self._image_hashes[key] = hashlib.sha256(path.read_bytes()).hexdigest()
                image_hashes.append(self._image_hashes[key])
            except ValueError:
                image_hashes.append(image)
        return hashlib.sha256(json.dumps([normalized, image_hashes], ensure_ascii=False).encode()).hexdigest()

    def duplicates(self, body, images, group_urls, exclude_id=None, sent_only=False):
        key = self.content_key(body, images)
        groups = {normalize_group(url) for url in group_urls}
        return [
            job
            for job in self.jobs()
            if job["id"] != exclude_id
            and normalize_group(job["group_url"]) in groups
            and job["status"] != "skipped"
            and (
                not sent_only
                or job["status"]
                in {"sending", "uncertain", "submitted", "pending", "published", "rejected", "removed"}
            )
            and self.content_key(job["body"], json.loads(job["images"])) == key
        ]

    def post_duplicates(self, post_id, group_ids):
        post = self.post(post_id)
        body = post["plain"] + ("\n\n" + post["tags"] if post["tags"] else "")
        return self.duplicates(
            body, post["images"], [g["url"] for g in self.groups() if g["id"] in group_ids]
        )

    def asset(self, relative):
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root.resolve()) or not path.is_file():
            raise ValueError(f"Không tìm thấy tệp trong thư mục dữ liệu: {relative}")
        return path

    def export_excel(self, target, jobs=None):
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
                "Gửi lúc (UTC)",
                "Kiểm tra lúc (UTC)",
                "Phát hiện hiển thị (UTC)",
                "Kết quả kiểm tra",
                "Chi tiết kiểm tra",
            ]
        )
        for job in reversed(self.jobs() if jobs is None else jobs):
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
                        job["sent_at"],
                        job["checked_at"],
                        job["first_visible_at"],
                        job["check_outcome"],
                        job["check_note"],
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
