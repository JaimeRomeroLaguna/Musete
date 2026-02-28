from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

TARGET = 40
CB = 30    # diámetro círculo grande (amayores, vale ×5 cada uno)
CS = 22    # diámetro círculo chica  (vale ×1 cada uno)
GAP = 8    # espacio entre círculos
PAD = 10   # padding interior del panel
ROW_GAP = 10  # espacio vertical entre filas


class ScoreWidget(QWidget):
    """
    Marcador de piedras de Mus con fondo oscuro redondeado.
      Fila grande : 8 círculos dorados  (×5 piedras c/u) → amayores
      Fila pequeña: 4 círculos blancos  (×1 piedra  c/u) → chicas
    """

    def __init__(self, label: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._score: int = 0
        self._label = label
        self.setMinimumSize(self._panel_w() + 4, self._panel_h() + 4)

    # ------------------------------------------------------------------

    def _panel_w(self) -> int:
        row_big_w   = 8 * CB + 7 * GAP
        row_small_w = 4 * CS + 3 * GAP
        return max(row_big_w, row_small_w) + 2 * PAD

    def _panel_h(self) -> int:
        label_h = 20  # nombre (Bot / Jugador)
        score_h = 24  # "X / 40"
        return PAD + label_h + 6 + CB + ROW_GAP + CS + 8 + score_h + PAD

    def set_score(self, score: int) -> None:
        self._score = max(0, min(score, TARGET))
        self.update()

    # ------------------------------------------------------------------

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pw = self._panel_w()
        ph = self._panel_h()
        ox = (self.width()  - pw) / 2
        oy = (self.height() - ph) / 2

        # ── Panel de fondo ────────────────────────────────────────────
        bg_path = QPainterPath()
        bg_path.addRoundedRect(QRectF(ox, oy, pw, ph), 12, 12)
        painter.fillPath(bg_path, QBrush(QColor("#0D2B1E")))
        painter.setPen(QPen(QColor("#2D6A4F"), 1.5))
        painter.drawPath(bg_path)

        amayores = self._score // 5
        chicas   = self._score % 5

        # ── Nombre (Bot / Jugador) ────────────────────────────────────
        y_cursor = oy + PAD
        painter.setPen(QPen(QColor("#6EE7B7")))
        painter.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        painter.drawText(
            QRectF(ox, y_cursor, pw, 20),
            Qt.AlignmentFlag.AlignCenter,
            self._label,
        )
        y_cursor += 20 + 6

        # ── Fila amayores (8 × CB) ────────────────────────────────────
        row_w = 8 * CB + 7 * GAP
        x0 = ox + (pw - row_w) / 2
        for i in range(8):
            x = x0 + i * (CB + GAP)
            rect = QRectF(x, y_cursor, CB, CB)
            if i < amayores:
                painter.setBrush(QBrush(QColor("#FFD700")))
                painter.setPen(QPen(QColor("#B8860B"), 2))
            else:
                painter.setBrush(QBrush(QColor("#122B1F")))
                painter.setPen(QPen(QColor("#2D5A40"), 1.5))
            painter.drawEllipse(rect)
        y_cursor += CB + ROW_GAP

        # ── Fila chicas (4 × CS) ──────────────────────────────────────
        row_w2 = 4 * CS + 3 * GAP
        x0s = ox + (pw - row_w2) / 2
        for i in range(4):
            x = x0s + i * (CS + GAP)
            rect = QRectF(x, y_cursor, CS, CS)
            if i < chicas:
                painter.setBrush(QBrush(QColor("#FFFFFF")))
                painter.setPen(QPen(QColor("#AAAAAA"), 1.5))
            else:
                painter.setBrush(QBrush(QColor("#122B1F")))
                painter.setPen(QPen(QColor("#2D5A40"), 1.5))
            painter.drawEllipse(rect)
        y_cursor += CS + 8

        # ── Score numérico ────────────────────────────────────────────
        painter.setPen(QPen(QColor("#A7F3D0")))
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        painter.drawText(
            QRectF(ox, y_cursor, pw, 24),
            Qt.AlignmentFlag.AlignCenter,
            f"{self._score} / {TARGET}",
        )
