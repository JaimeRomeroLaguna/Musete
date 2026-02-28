from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
)
from PySide6.QtWidgets import QWidget

from game.deck import Card, RANK_SHORT, Suit

CARD_W = 120
CARD_H = 170


class CardWidget(QWidget):
    """Carta dibujada con QPainter. Admite modo 'face_down' y 'selected'."""

    def __init__(
        self,
        card: Optional[Card] = None,
        face_down: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.card = card
        self.face_down = face_down
        self.selected = False
        self.setFixedSize(CARD_W, CARD_H)

    def set_selected(self, selected: bool) -> None:
        self.selected = selected
        self.update()

    # ------------------------------------------------------------------
    # Paint
    # ------------------------------------------------------------------

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.face_down or self.card is None:
            self._draw_back(painter)
        else:
            self._draw_front(painter)

    def _draw_back(self, painter: QPainter) -> None:
        path = QPainterPath()
        path.addRoundedRect(QRectF(1, 1, CARD_W - 2, CARD_H - 2), 8, 8)

        grad = QLinearGradient(0, 0, CARD_W, CARD_H)
        grad.setColorAt(0.0, QColor("#312E81"))
        grad.setColorAt(1.0, QColor("#1E1B4B"))

        painter.fillPath(path, QBrush(grad))
        painter.setPen(QPen(QColor("#6366F1"), 1.5))
        painter.drawPath(path)

        # Patrón central decorativo
        painter.setPen(QPen(QColor("#4338CA"), 1))
        cx, cy = CARD_W // 2, CARD_H // 2
        for r in range(8, 30, 8):
            painter.drawEllipse(QPointF(cx, cy), r, r)

    def _draw_front(self, painter: QPainter) -> None:
        assert self.card is not None
        path = QPainterPath()
        path.addRoundedRect(QRectF(1, 1, CARD_W - 2, CARD_H - 2), 8, 8)

        painter.fillPath(path, QBrush(QColor("#FFFEF5")))
        border_color = QColor("#4ADE80") if self.selected else QColor("#BBBBBB")
        border_width = 2.5 if self.selected else 1.5
        painter.setPen(QPen(border_color, border_width))
        painter.drawPath(path)

        rank_str = RANK_SHORT[self.card.rank]
        suit_color = self._suit_color()

        font = QFont("Arial", 16, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(suit_color))

        # Rango top-left
        painter.drawText(QRectF(7, 5, 32, 26), Qt.AlignmentFlag.AlignLeft, rank_str)

        # Rango bottom-right (rotado 180°)
        painter.save()
        painter.translate(CARD_W, CARD_H)
        painter.rotate(180)
        painter.drawText(QRectF(7, 5, 32, 26), Qt.AlignmentFlag.AlignLeft, rank_str)
        painter.restore()

        # Símbolo central
        cx, cy = CARD_W / 2, CARD_H / 2
        self._draw_suit_symbol(painter, cx, cy, suit_color)

    def _suit_color(self) -> QColor:
        colors = {
            Suit.OROS: QColor("#B8860B"),
            Suit.COPAS: QColor("#CC2200"),
            Suit.ESPADAS: QColor("#1A1A2E"),
            Suit.BASTOS: QColor("#2A6000"),
        }
        return colors[self.card.suit]  # type: ignore[index]

    def _draw_suit_symbol(self, painter: QPainter, cx: float, cy: float, color: QColor) -> None:
        suit = self.card.suit  # type: ignore[union-attr]
        r = 27

        if suit == Suit.OROS:
            self._draw_oros(painter, cx, cy, r, color)
        elif suit == Suit.COPAS:
            self._draw_copas(painter, cx, cy, r, color)
        elif suit == Suit.ESPADAS:
            self._draw_espadas(painter, cx, cy, r, color)
        elif suit == Suit.BASTOS:
            self._draw_bastos(painter, cx, cy, r, color)

    # ---- Oros ----
    def _draw_oros(self, p: QPainter, cx: float, cy: float, r: float, color: QColor) -> None:
        gold = QColor("#FFD700")
        dark_gold = QColor("#B8860B")
        p.setBrush(QBrush(gold))
        p.setPen(QPen(dark_gold, 1.5))
        p.drawEllipse(QPointF(cx, cy), r, r)
        # Anillo interior
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(dark_gold, 2))
        p.drawEllipse(QPointF(cx, cy), r * 0.6, r * 0.6)
        # Punto central
        p.setBrush(QBrush(dark_gold))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), r * 0.15, r * 0.15)

    # ---- Copas ----
    def _draw_copas(self, p: QPainter, cx: float, cy: float, r: float, color: QColor) -> None:
        p.setBrush(QBrush(color))
        p.setPen(QPen(color.darker(150), 1))
        # Boca (elipse arriba)
        p.drawEllipse(QPointF(cx, cy - r * 0.6), r * 0.85, r * 0.5)
        # Cuerpo trapezoidal
        body = QPolygonF([
            QPointF(cx - r * 0.85, cy - r * 0.1),
            QPointF(cx + r * 0.85, cy - r * 0.1),
            QPointF(cx + r * 0.5,  cy + r * 0.6),
            QPointF(cx - r * 0.5,  cy + r * 0.6),
        ])
        p.drawPolygon(body)
        # Tallo
        tallo_rect = QRectF(cx - r * 0.12, cy + r * 0.6, r * 0.24, r * 0.45)
        p.drawRect(tallo_rect)
        # Base
        p.drawEllipse(QPointF(cx, cy + r * 1.1), r * 0.45, r * 0.18)

    # ---- Espadas ----
    def _draw_espadas(self, p: QPainter, cx: float, cy: float, r: float, color: QColor) -> None:
        p.setBrush(QBrush(color))
        p.setPen(QPen(color.darker(120), 1))
        # Hoja (triángulo apuntando arriba)
        blade = QPolygonF([
            QPointF(cx,          cy - r),
            QPointF(cx + r * 0.6, cy + r * 0.2),
            QPointF(cx - r * 0.6, cy + r * 0.2),
        ])
        p.drawPolygon(blade)
        # Guarda horizontal
        guard_rect = QRectF(cx - r * 0.7, cy + r * 0.15, r * 1.4, r * 0.22)
        p.drawRect(guard_rect)
        # Empuñadura
        grip_rect = QRectF(cx - r * 0.12, cy + r * 0.37, r * 0.24, r * 0.55)
        p.drawRect(grip_rect)
        # Pomo
        p.drawEllipse(QPointF(cx, cy + r * 0.95), r * 0.22, r * 0.22)

    # ---- Bastos ----
    def _draw_bastos(self, p: QPainter, cx: float, cy: float, r: float, color: QColor) -> None:
        p.setBrush(QBrush(color))
        p.setPen(QPen(color.darker(120), 1))
        cr = r * 0.42  # radio de cada bola
        # Tres círculos solapados en trébol
        p.drawEllipse(QPointF(cx,          cy - r * 0.55), cr, cr)
        p.drawEllipse(QPointF(cx - r * 0.5, cy + r * 0.1),  cr, cr)
        p.drawEllipse(QPointF(cx + r * 0.5, cy + r * 0.1),  cr, cr)
        # Mango
        handle_rect = QRectF(cx - r * 0.12, cy + r * 0.35, r * 0.24, r * 0.6)
        p.drawRect(handle_rect)
        # Remate del mango
        p.drawEllipse(QPointF(cx, cy + r * 0.95), r * 0.2, r * 0.2)
