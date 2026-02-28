from __future__ import annotations

import sys
from pathlib import Path

# Garantiza que el directorio del proyecto esté en sys.path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Musete")
    app.setFont(QFont("Arial", 15))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
