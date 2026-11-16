from PySide6.QtWidgets import QDialog

from facebook_helper.templates import RecruitmentDialog


def test_guided_template_generates_editable_draft_with_reference_sections(window, store, monkeypatch):
    def fill_dialog(dialog):
        dialog.fields["position"].setText("Kỹ sư tự động hóa")
        dialog.fields["company"].setText("Công ty mẫu")
        dialog.fields["region"].setText("Hà Nội")
        dialog.fields["duties"].setPlainText("Lập trình PLC\nTriển khai Robot")
        dialog.fields["requirements"].setPlainText("Chào đón Fresher")
        dialog.fields["salary"].setText("15–25 triệu/tháng")
        dialog.fields["email"].setText("hr@example.com")
        dialog.fields["tags"].setText("#TuyenDung #PLC")
        dialog.generate()
        return dialog.result()

    monkeypatch.setattr(RecruitmentDialog, "exec", fill_dialog)
    window.create_from_template()
    assert window.dirty and window.post_id is None
    text = window.content.toPlainText()
    for section in ["CƠ HỘI DÀNH CHO BẠN", "YÊU CẦU", "QUYỀN LỢI", "ỨNG TUYỂN NGAY", "• Lập trình PLC"]:
        assert section in text
    assert window.tags.text() == "#TuyenDung #PLC"
    post = store.post(window.save_post())
    assert "font-weight:700" in post["html"]
    assert "15–25 triệu/tháng" in post["plain"]


def test_cancelling_template_keeps_draft_unchanged(window, monkeypatch):
    monkeypatch.setattr(RecruitmentDialog, "exec", lambda self: QDialog.DialogCode.Rejected)
    window.create_from_template()
    assert window.content.toPlainText() == "" and not window.dirty
