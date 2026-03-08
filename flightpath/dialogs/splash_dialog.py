"""
Usage:
    from splash_dialog import SplashDialog

    dialog = SplashDialog(
        parent=None,
        image_path="tryone.png",          # 550×380 recommended
        license_url="https://yoursite.com/license",
        copyright_text="© 2024 Your Company Name. All rights reserved.",
    )
    dialog.exec()
"""

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class SplashDialog(QDialog):
    """
    First-launch splash dialog with:
      - Edge-to-edge banner image (550 × 380 px)
      - Clickable license link (small, muted)
      - Copyright statement
      - Close button
    """

    # ------------------------------------------------------------------ #
    #  Construction                                                        #
    # ------------------------------------------------------------------ #

    def __init__(
        self,
        parent=None,
        image_path: str = "",
        license_url: str = "https://www.gnu.org/licenses/lgpl-3.0.html",
        copyright_text: str = "© 2024 Atesta Analytics. All rights reserved.",
    ):
        super().__init__(parent)

        self._license_url = license_url
        self._copyright_text = copyright_text
        self._image_path = image_path

        self._build_ui()
        self._apply_styles()

        # Fixed width; height is determined by image + footer
        self.setFixedWidth(550)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)

        # Remove the title bar / window chrome
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

    # ------------------------------------------------------------------ #
    #  UI construction                                                     #
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Banner image ──────────────────────────────────────────────── #
        self._image_label = QLabel()
        self._image_label.setFixedSize(550, 380)
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_label.setObjectName("bannerImage")

        if self._image_path:
            pix = QPixmap(self._image_path)
            if not pix.isNull():
                pix = pix.scaled(
                    550, 380,
                    Qt.IgnoreAspectRatio,
                    Qt.SmoothTransformation,
                )
                self._image_label.setPixmap(pix)
            else:
                self._image_label.setText("[ splash image not found ]")
        else:
            # Placeholder when no path is supplied
            self._image_label.setText("[ no image configured ]")

        root.addWidget(self._image_label)

        # ── Footer panel ──────────────────────────────────────────────── #
        footer = QWidget()
        footer.setObjectName("footer")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(20, 14, 20, 16)
        footer_layout.setSpacing(6)

        # License link
        self._license_link = QLabel(
            f'<a href="{self._license_url}" style="color:#7a9cbf;">'
            f"View FlightPath Data and CsvPath Framework license (LGPL)</a>"
        )
        self._license_link.setObjectName("licenseLink")
        self._license_link.setOpenExternalLinks(False)
        self._license_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self._license_link.linkActivated.connect(self._open_license)
        footer_layout.addWidget(self._license_link, alignment=Qt.AlignLeft)

        # Copyright + Close button row
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(12)

        self._copyright_label = QLabel(self._copyright_text)
        self._copyright_label.setObjectName("copyrightLabel")
        bottom_row.addWidget(self._copyright_label, stretch=1)

        self._close_btn = QPushButton("Continue")
        self._close_btn.setObjectName("closeBtn")
        self._close_btn.setFixedWidth(88)
        self._close_btn.setCursor(Qt.PointingHandCursor)
        self._close_btn.clicked.connect(self.accept)
        bottom_row.addWidget(self._close_btn, alignment=Qt.AlignVCenter)

        footer_layout.addLayout(bottom_row)
        root.addWidget(footer)

    # ------------------------------------------------------------------ #
    #  Styling                                                             #
    # ------------------------------------------------------------------ #

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            /* ── Dialog shell ─────────────────────────────────────────── */
            SplashDialog {
                background: #1a1e24;
                border: 1px solid #2e3440;
                border-radius: 4px;
            }

            /* ── Banner placeholder text ──────────────────────────────── */
            QLabel#bannerImage {
                background: #11141a;
                color: #4a5568;
                font-size: 12px;
                font-family: "Courier New", monospace;
            }

            /* ── Footer ───────────────────────────────────────────────── */
            QWidget#footer {
                background: #1a1e24;
                border-top: 1px solid #2e3440;
            }

            /* ── License link ─────────────────────────────────────────── */
            QLabel#licenseLink {
                font-size: 10px;
                color: #4a5568;
            }

            /* ── Copyright ────────────────────────────────────────────── */
            QLabel#copyrightLabel {
                font-size: 10px;
                color: #4a5568;
            }

            /* ── Close button ─────────────────────────────────────────── */
            QPushButton#closeBtn {
                background: #252b36;
                color: #c8d0db;
                border: 1px solid #3a4250;
                border-radius: 3px;
                padding: 5px 14px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton#closeBtn:hover {
                background: #2e3646;
                border-color: #4e5f78;
                color: #e2e8f0;
            }
            QPushButton#closeBtn:pressed {
                background: #1e2530;
                border-color: #3a4250;
            }
            """
        )

    # ------------------------------------------------------------------ #
    #  Slots                                                               #
    # ------------------------------------------------------------------ #

    def _open_license(self, url: str) -> None:
        QDesktopServices.openUrl(QUrl(url))


# ────────────────────────────────────────────────────────────────────────── #
#  Quick smoke-test — run this file directly to preview the dialog           #
# ────────────────────────────────────────────────────────────────────────── #

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    imagepath = os.path.join("assets", "images", "splash.png")
    dlg = SplashDialog(
        image_path=imagepath,
        license_url="https://github.com/csvpath/csvpath?tab=LGPL-2.1-1-ov-file#readme",
        copyright_text="© 2025-2026 Atesta Analytics. All rights reserved.",
    )
    dlg.exec()
    sys.exit(0)
