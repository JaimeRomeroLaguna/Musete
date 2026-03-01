from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QMimeData, QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QDrag,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
)
from PySide6.QtWidgets import QApplication, QWidget

from game.deck import Card, RANK_SHORT, Suit

CARD_W = 120
CARD_H = 170

_MIME_TYPE = "application/x-musete-card-index"


class CardWidget(QWidget):
    """
    Carta dibujada con QPainter.
    - face_down / selected para descarte
    - Drag & drop para reordenar la mano del jugador
    """

    # Emitido cuando el usuario hace click sin arrastrar (para descarte)
    clicked = Signal(int)
    # Emitido cuando se suelta una carta encima de otra (reordenar)
    reorder_requested = Signal(int, int)   # from_index, to_index

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

        self._card_index: int = 0
        self._drag_enabled: bool = False
        self._click_enabled: bool = False
        self._drag_start: Optional[QPoint] = None
        self._drag_hover: bool = False    # otra carta está sobre ésta

        self.setFixedSize(CARD_W, CARD_H)
        self.setAcceptDrops(True)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def set_selected(self, selected: bool) -> None:
        self.selected = selected
        self.update()

    def enable_drag(self, index: int) -> None:
        """Activa arrastrar esta carta. index = posición en la mano."""
        self._card_index = index
        self._drag_enabled = True
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def enable_click(self, index: int) -> None:
        """Activa la señal clicked (para selección de descarte)."""
        self._card_index = index
        self._click_enabled = True

    # ------------------------------------------------------------------
    # Eventos de ratón → drag
    # ------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()
            if self._drag_enabled:
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self._drag_enabled:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            # Emitir click solo si el ratón no se movió lo suficiente para drag
            if self._click_enabled and self._drag_start is not None:
                dist = (event.position().toPoint() - self._drag_start).manhattanLength()
                if dist < QApplication.startDragDistance():
                    self.clicked.emit(self._card_index)
        self._drag_start = None
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if not self._drag_enabled:
            return
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if self._drag_start is None:
            return
        dist = (event.position().toPoint() - self._drag_start).manhattanLength()
        if dist < QApplication.startDragDistance():
            return

        # Iniciar drag
        self._drag_start = None  # evitar que se dispare dos veces

        mime = QMimeData()
        mime.setData(_MIME_TYPE, str(self._card_index).encode())

        drag = QDrag(self)
        drag.setMimeData(mime)

        # Pixmap semitransparente como cursor de arrastre
        px = self.grab()
        drag.setPixmap(px)
        drag.setHotSpot(QPoint(px.width() // 2, px.height() // 3))

        drag.exec(Qt.DropAction.MoveAction)

    # ------------------------------------------------------------------
    # Eventos de drop (esta carta es el objetivo)
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasFormat(_MIME_TYPE):
            src = int(event.mimeData().data(_MIME_TYPE).toStdString())
            if src != self._card_index and self._drag_enabled:
                self._drag_hover = True
                self.update()
                event.acceptProposedAction()
                return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self._drag_hover = False
        self.update()

    def dropEvent(self, event) -> None:
        self._drag_hover = False
        self.update()
        if event.mimeData().hasFormat(_MIME_TYPE) and self._drag_enabled:
            from_idx = int(event.mimeData().data(_MIME_TYPE).toStdString())
            to_idx = self._card_index
            if from_idx != to_idx:
                self.reorder_requested.emit(from_idx, to_idx)
            event.acceptProposedAction()

    # ------------------------------------------------------------------
    # Pintura
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

        painter.setPen(QPen(QColor("#4338CA"), 1))
        cx, cy = CARD_W // 2, CARD_H // 2
        for r in range(8, 30, 8):
            painter.drawEllipse(QPointF(cx, cy), r, r)

    def _draw_front(self, painter: QPainter) -> None:
        assert self.card is not None
        path = QPainterPath()
        path.addRoundedRect(QRectF(1, 1, CARD_W - 2, CARD_H - 2), 8, 8)

        painter.fillPath(path, QBrush(QColor("#FFFEF5")))

        if self._drag_hover:
            border_color = QColor("#38BDF8")   # azul cielo: "suéltame aquí"
            border_width = 3.5
        elif self.selected:
            border_color = QColor("#4ADE80")   # verde: seleccionada para descarte
            border_width = 3.0
        else:
            border_color = QColor("#BBBBBB")
            border_width = 1.5

        painter.setPen(QPen(border_color, border_width))
        painter.drawPath(path)

        rank_str = RANK_SHORT[self.card.rank]
        suit_color = self._suit_color()

        painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        painter.setPen(QPen(suit_color))

        painter.drawText(QRectF(7, 5, 32, 26), Qt.AlignmentFlag.AlignLeft, rank_str)

        painter.save()
        painter.translate(CARD_W, CARD_H)
        painter.rotate(180)
        painter.drawText(QRectF(7, 5, 32, 26), Qt.AlignmentFlag.AlignLeft, rank_str)
        painter.restore()

        cx, cy = CARD_W / 2, CARD_H / 2
        self._draw_suit_symbol(painter, cx, cy, suit_color)

    def _suit_color(self) -> QColor:
        colors = {
            Suit.OROS:    QColor("#B8860B"),
            Suit.COPAS:   QColor("#CC2200"),
            Suit.ESPADAS: QColor("#1A1A2E"),
            Suit.BASTOS:  QColor("#2A6000"),
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
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(dark_gold, 2))
        p.drawEllipse(QPointF(cx, cy), r * 0.6, r * 0.6)
        p.setBrush(QBrush(dark_gold))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), r * 0.15, r * 0.15)

    # ---- Copas ----
    def _draw_copas(self, p: QPainter, cx: float, cy: float, r: float, color: QColor) -> None:
        p.setBrush(QBrush(color))
        p.setPen(QPen(color.darker(150), 1))
        p.drawEllipse(QPointF(cx, cy - r * 0.6), r * 0.85, r * 0.5)
        body = QPolygonF([
            QPointF(cx - r * 0.85, cy - r * 0.1),
            QPointF(cx + r * 0.85, cy - r * 0.1),
            QPointF(cx + r * 0.5,  cy + r * 0.6),
            QPointF(cx - r * 0.5,  cy + r * 0.6),
        ])
        p.drawPolygon(body)
        p.drawRect(QRectF(cx - r * 0.12, cy + r * 0.6, r * 0.24, r * 0.45))
        p.drawEllipse(QPointF(cx, cy + r * 1.1), r * 0.45, r * 0.18)

    # ---- Espadas ----
    def _draw_espadas(self, p: QPainter, cx: float, cy: float, r: float, color: QColor) -> None:
        p.setBrush(QBrush(color))
        p.setPen(QPen(color.darker(120), 1))
        blade = QPolygonF([
            QPointF(cx,           cy - r),
            QPointF(cx + r * 0.6, cy + r * 0.2),
            QPointF(cx - r * 0.6, cy + r * 0.2),
        ])
        p.drawPolygon(blade)
        p.drawRect(QRectF(cx - r * 0.7,  cy + r * 0.15, r * 1.4, r * 0.22))
        p.drawRect(QRectF(cx - r * 0.12, cy + r * 0.37, r * 0.24, r * 0.55))
        p.drawEllipse(QPointF(cx, cy + r * 0.95), r * 0.22, r * 0.22)

    # ---- Bastos ----
    def _draw_bastos(self, p: QPainter, cx: float, cy: float, r: float, color: QColor) -> None:
        p.setBrush(QBrush(color))
        p.setPen(QPen(color.darker(120), 1))
        cr = r * 0.42
        p.drawEllipse(QPointF(cx,           cy - r * 0.55), cr, cr)
        p.drawEllipse(QPointF(cx - r * 0.5, cy + r * 0.1),  cr, cr)
        p.drawEllipse(QPointF(cx + r * 0.5, cy + r * 0.1),  cr, cr)
        p.drawRect(QRectF(cx - r * 0.12, cy + r * 0.35, r * 0.24, r * 0.6))
        p.drawEllipse(QPointF(cx, cy + r * 0.95), r * 0.2, r * 0.2)
