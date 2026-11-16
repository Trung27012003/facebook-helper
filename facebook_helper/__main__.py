import argparse
import sys

from PySide6.QtCore import QCoreApplication, QEvent, QLockFile
from PySide6.QtWidgets import QApplication, QMessageBox

from .storage import Store
from .ui import MainWindow


def main():
    parser = argparse.ArgumentParser(description="Facebook Helper — HR")
    parser.add_argument("--data-dir", help="Thư mục dữ liệu riêng (mặc định theo hệ điều hành)")
    parser.add_argument("--smoke-test", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    app = QApplication(sys.argv[:1])
    app.setApplicationName("Facebook Helper")
    app.setOrganizationName("FacebookHelper")
    store = Store(args.data_dir)
    lock = QLockFile(str(store.root / "app.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        QMessageBox.warning(None, "Ứng dụng đang mở", "Chỉ mở một ứng dụng với cùng thư mục dữ liệu.")
        store.close()
        return 1
    window = None
    try:
        if args.smoke_test:
            from .smoke import run_smoke

            return run_smoke(app, store)
        window = MainWindow(store)
        window.show()
        return app.exec()
    finally:
        if window is not None:
            window.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        store.close()
        lock.unlock()


if __name__ == "__main__":
    sys.exit(main())
