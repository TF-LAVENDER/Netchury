import os
import sys

from PySide6.QtCore import QFile
from PySide6.QtGui import QFontDatabase, QFontMetrics
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QLineEdit, QPushButton, QWidget


IS_WINDOWS = sys.platform.startswith("win")
_FONT_SIZE_RESOLVE_MASK = 0x02


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)


def configure_application(app: QApplication):
    """Use macOS-like logical font sizing only on Windows."""
    if not IS_WINDOWS:
        return

    available_families = set(QFontDatabase.families())
    family = next(
        (name for name in ("Malgun Gothic", "Segoe UI", "Arial") if name in available_families),
        app.font().family(),
    )
    font = app.font()
    font.setFamily(family)
    font.setPixelSize(13)
    app.setFont(font)


def _apply_windows_font_compatibility(root: QWidget):
    if not IS_WINDOWS:
        return

    fitted_types = (QLabel, QPushButton, QLineEdit, QComboBox)
    for widget in [root, *root.findChildren(QWidget)]:
        font = widget.font()

        # Qt point sizes become physically larger on Windows (normally 96 DPI)
        # than on macOS (normally 72 DPI). Preserve the numeric designer size as
        # pixels so fixed-height controls keep the same visual proportions.
        if font.pointSizeF() > 0 and font.resolveMask() & _FONT_SIZE_RESOLVE_MASK:
            font.setPixelSize(max(1, round(font.pointSizeF())))

        if isinstance(widget, fitted_types) and font.pixelSize() > 0:
            available_height = max(1, widget.height() - 2)
            while font.pixelSize() > 6 and QFontMetrics(font).height() > available_height:
                font.setPixelSize(font.pixelSize() - 1)

        if isinstance(widget, (QLabel, QPushButton)) and font.pixelSize() > 0 and widget.text():
            available_width = max(1, widget.width() - 4)
            while (
                font.pixelSize() > 6
                and QFontMetrics(font).horizontalAdvance(widget.text()) > available_width
            ):
                font.setPixelSize(font.pixelSize() - 1)

        widget.setFont(font)


def load_ui_file(path) -> QWidget:
    loader = QUiLoader()
    file = QFile(path)
    if not file.open(QFile.ReadOnly):
        raise RuntimeError(f"UI 파일을 열 수 없습니다: {path}")
    try:
        ui = loader.load(file)
    finally:
        file.close()

    if ui is None:
        raise RuntimeError(f"UI 파일을 불러올 수 없습니다: {path}")
    _apply_windows_font_compatibility(ui)
    return ui
