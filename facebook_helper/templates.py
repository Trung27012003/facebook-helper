"""A guided recruitment template; plain text keeps its structure on Facebook."""

from html import escape

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .widgets import hint

FIELDS = [
    ("position", "Vị trí tuyển dụng *", "Kỹ sư điện tự động hóa"),
    ("company", "Tên công ty *", "Tên công ty của bạn"),
    ("region", "Khu vực", "HÀ NỘI"),
    ("salary", "Thu nhập", "15–25 triệu/tháng + thưởng"),
    ("intro", "Lời giới thiệu", "Bạn yêu thích PLC, HMI, Robot? Cùng phát triển sự nghiệp với chúng tôi!"),
    (
        "duties",
        "Công việc · mỗi dòng một ý",
        "Lập trình PLC/HMI, Robot công nghiệp\nThiết kế bản vẽ điện\nTriển khai hệ thống tự động hóa",
    ),
    (
        "requirements",
        "Yêu cầu · mỗi dòng một ý",
        "Tốt nghiệp ngành phù hợp\nChào đón Fresher và thực tập sinh",
    ),
    ("benefits", "Quyền lợi · mỗi dòng một ý", "Đầy đủ bảo hiểm\nĐào tạo chuyên môn và cơ hội phát triển"),
    ("location", "Địa điểm làm việc", "Địa chỉ công ty"),
    ("schedule", "Thời gian làm việc", "Thứ 2 – Thứ 6"),
    ("email", "Email nhận CV", "tuyendung@congty.vn"),
    ("phone", "Điện thoại / Zalo", "Số điện thoại liên hệ"),
    ("closing", "Lời kết", "Gia nhập đội ngũ của chúng tôi ngay hôm nay!"),
    ("tags", "Hashtag cuối bài", "#TuyenDung #TuDongHoa #ViecLamHaNoi"),
]
MULTILINE = {"intro", "duties", "requirements", "benefits", "closing"}


def recruitment_article(values):
    v = {key: str(values.get(key, "")).strip() for key, _, _ in FIELDS}
    if not v["position"] or not v["company"]:
        raise ValueError("Điền vị trí tuyển dụng và tên công ty trước nhé.")
    title = f"{v['company']} TUYỂN DỤNG {v['position']}".upper()
    if v["region"]:
        title = f"[{v['region'].upper()}] {title}"
    parts = [f"<p><b>{escape(title)}</b></p>"]
    if v["intro"]:
        parts.append(f"<p>{escape(v['intro']).replace(chr(10), '<br>')}</p>")
    sections = [("CƠ HỘI DÀNH CHO BẠN", v["duties"]), ("YÊU CẦU", v["requirements"])]
    benefits = v["benefits"]
    if v["salary"]:
        benefits = f"Thu nhập: {v['salary']}\n{benefits}"
    sections.append(("QUYỀN LỢI", benefits))
    for heading, body in sections:
        lines = [line.strip().lstrip("•- ") for line in body.splitlines() if line.strip()]
        if lines:
            parts.append(
                f"<p><b>{heading}</b><br>" + "<br>".join(f"• {escape(line)}" for line in lines) + "</p>"
            )
    for key, label in [("location", "Địa điểm"), ("schedule", "Thời gian")]:
        if v[key]:
            parts.append(f"<p><b>{label}:</b> {escape(v[key])}</p>")
    contacts = []
    if v["email"]:
        contacts.append(f"• Email: {escape(v['email'])}")
    if v["phone"]:
        contacts.append(f"• Điện thoại/Zalo: {escape(v['phone'])}")
    if contacts:
        parts.append("<p><b>ỨNG TUYỂN NGAY</b><br>" + "<br>".join(contacts) + "</p>")
    if v["closing"]:
        parts.append(f"<p><b>{escape(v['closing'])}</b></p>")
    return {"title": title, "html": "".join(parts), "tags": v["tags"]}


class RecruitmentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tạo bài tuyển dụng theo mẫu")
        self.resize(700, 720)
        layout = QVBoxLayout(self)
        layout.addWidget(
            hint(
                "Điền thông tin bên dưới. Mục nào không cần có thể để trống. "
                "Bạn vẫn sửa toàn bộ nội dung và thêm ảnh sau khi tạo bài."
            )
        )
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        form = QFormLayout(content)
        self.fields = {}
        for key, label, placeholder in FIELDS:
            field = QTextEdit() if key in MULTILINE else QLineEdit()
            field.setPlaceholderText(placeholder)
            if key in MULTILINE:
                field.setAcceptRichText(False)
                field.setFixedHeight(80)
            self.fields[key] = field
            form.addRow(label, field)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        actions = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        actions.button(QDialogButtonBox.StandardButton.Ok).setText("Tạo nội dung bài")
        actions.button(QDialogButtonBox.StandardButton.Cancel).setText("Hủy")
        actions.accepted.connect(self.generate)
        actions.rejected.connect(self.reject)
        layout.addWidget(actions)
        self.article = None

    def generate(self):
        values = {
            key: field.toPlainText() if isinstance(field, QTextEdit) else field.text()
            for key, field in self.fields.items()
        }
        try:
            self.article = recruitment_article(values)
        except ValueError as exc:
            QMessageBox.warning(self, "Còn thiếu thông tin", str(exc))
            return
        self.accept()
