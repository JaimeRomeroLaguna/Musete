from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

# ── Character definitions ────────────────────────────────────────────────────
_CHARS = [
    # 0: Paco (compañero) — warm skin, curly dark hair, moustache
    {"name": "Paco", "skin": "#E0A87A", "hair": "#3D2010", "style": "curly",    "shirt": "#8B5A2B"},
    # 1: Roca (bot1) — grey skin, flat angular hair, thick brows
    {"name": "Roca", "skin": "#B8C8D8", "hair": "#404050", "style": "straight", "shirt": "#4A5568"},
    # 2: Lola (bot2) — olive skin, bun hair, rosy cheeks
    {"name": "Lola", "skin": "#C8956A", "hair": "#5C3010", "style": "bun",      "shirt": "#7B4A7A"},
]


class CharacterWidget(QWidget):
    """
    Draws a cartoon character face using QPainter.

    character_id: 0=Paco, 1=Roca, 2=Lola
    mood: 'neutral' | 'happy' | 'sad' | 'thinking'
    """

    def __init__(
        self,
        character_id: int = 0,
        mood: str = "neutral",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._character_id = character_id
        self._mood = mood
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setMinimumSize(80, 90)

    def set_mood(self, mood: str) -> None:
        if mood != self._mood:
            self._mood = mood
            self.update()

    def sizeHint(self) -> QSize:
        return QSize(150, 165)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._paint(p)

    # ------------------------------------------------------------------
    # Main drawing entry point
    # ------------------------------------------------------------------

    def _paint(self, p: QPainter) -> None:
        w, h = float(self.width()), float(self.height())
        cx = w / 2.0
        ch = _CHARS[self._character_id]

        r = min(w, h) * 0.30          # head radius
        cy = h * 0.40                 # head centre Y

        skin  = QColor(ch["skin"])
        hair  = QColor(ch["hair"])
        shirt = QColor(ch["shirt"])

        # Drawing order per plan
        self._shirt(p, cx, cy, r, skin, shirt)
        self._neck(p, cx, cy, r, skin)
        self._head(p, cx, cy, r, skin)
        {"curly": self._hair_curly,
         "straight": self._hair_straight,
         "bun": self._hair_bun}[ch["style"]](p, cx, cy, r, hair)
        self._ears(p, cx, cy, r, skin)
        self._eyebrows(p, cx, cy, r, hair)
        self._eyes(p, cx, cy, r, skin)
        self._nose(p, cx, cy, r, skin)
        # Special features
        if self._character_id == 0:
            self._mustache(p, cx, cy, r, hair)
        elif self._character_id == 2:
            self._cheeks(p, cx, cy, r)
        self._mouth(p, cx, cy, r)

    # ------------------------------------------------------------------
    # Body parts
    # ------------------------------------------------------------------

    def _shirt(self, p: QPainter, cx: float, cy: float, r: float,
               skin: QColor, shirt: QColor) -> None:
        h = float(self.height())
        top = cy + r * 1.05
        sw  = r * 2.2
        p.setBrush(QBrush(shirt))
        p.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.addRoundedRect(QRectF(cx - sw / 2, top, sw, h - top + 4), r * 0.2, r * 0.2)
        p.drawPath(path)
        # V-collar
        p.setBrush(QBrush(skin))
        collar = QPainterPath()
        collar.moveTo(cx, top + r * 0.32)
        collar.lineTo(cx - r * 0.22, top)
        collar.lineTo(cx + r * 0.22, top)
        collar.closeSubpath()
        p.drawPath(collar)

    def _neck(self, p: QPainter, cx: float, cy: float, r: float, skin: QColor) -> None:
        nw, nh = r * 0.38, r * 0.45
        nt = cy + r * 0.72
        p.setBrush(QBrush(skin))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(QRectF(cx - nw / 2, nt, nw, nh))

    def _head(self, p: QPainter, cx: float, cy: float, r: float, skin: QColor) -> None:
        p.setBrush(QBrush(skin))
        p.setPen(QPen(skin.darker(115), 1.0))
        p.drawEllipse(QRectF(cx - r, cy - r, 2 * r, 2 * r))

    def _ears(self, p: QPainter, cx: float, cy: float, r: float, skin: QColor) -> None:
        er = r * 0.15
        p.setBrush(QBrush(skin))
        p.setPen(QPen(skin.darker(115), 0.8))
        p.drawEllipse(QRectF(cx - r - er * 0.8,  cy - er, er * 2, er * 2))
        p.drawEllipse(QRectF(cx + r - er * 1.2,  cy - er, er * 2, er * 2))

    def _nose(self, p: QPainter, cx: float, cy: float, r: float, skin: QColor) -> None:
        p.setBrush(QBrush(skin.darker(140)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx - r * 0.06, cy + r * 0.10, r * 0.12, r * 0.12))

    # ------------------------------------------------------------------
    # Hair styles
    # ------------------------------------------------------------------

    def _hair_curly(self, p: QPainter, cx: float, cy: float, r: float, hair: QColor) -> None:
        """Puffs of curly dark hair around the top of the head."""
        p.setBrush(QBrush(hair))
        p.setPen(Qt.PenStyle.NoPen)
        pr = r * 0.28
        for px, py in [
            (cx - r * 0.60, cy - r * 0.85),
            (cx - r * 0.10, cy - r * 1.10),
            (cx + r * 0.40, cy - r * 0.90),
            (cx + r * 0.75, cy - r * 0.50),
            (cx - r * 0.85, cy - r * 0.38),
        ]:
            p.drawEllipse(QRectF(px - pr, py - pr, pr * 2, pr * 2))

    def _hair_straight(self, p: QPainter, cx: float, cy: float, r: float, hair: QColor) -> None:
        """Flat, angular hair block (Roca's signature look)."""
        p.setBrush(QBrush(hair))
        p.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.moveTo(cx - r * 0.95, cy)
        path.lineTo(cx - r * 1.00, cy - r * 0.50)
        path.lineTo(cx - r * 0.70, cy - r * 1.05)
        path.lineTo(cx,            cy - r * 1.15)
        path.lineTo(cx + r * 0.70, cy - r * 1.05)
        path.lineTo(cx + r * 1.00, cy - r * 0.50)
        path.lineTo(cx + r * 0.95, cy)
        path.closeSubpath()
        p.drawPath(path)

    def _hair_bun(self, p: QPainter, cx: float, cy: float, r: float, hair: QColor) -> None:
        """Top half-ellipse base hair + small bun circle on top."""
        p.setBrush(QBrush(hair))
        p.setPen(Qt.PenStyle.NoPen)
        base = QPainterPath()
        base.moveTo(cx - r * 0.95, cy - r * 0.1)
        base.arcTo(QRectF(cx - r, cy - r, 2 * r, 2 * r), 180, 180)
        base.closeSubpath()
        p.drawPath(base)
        br = r * 0.28
        p.drawEllipse(QRectF(cx - br, cy - r - br * 1.6, br * 2, br * 2))

    # ------------------------------------------------------------------
    # Facial features — mood-dependent
    # ------------------------------------------------------------------

    def _eyebrows(self, p: QPainter, cx: float, cy: float, r: float, hair: QColor) -> None:
        mood = self._mood
        by  = cy - r * 0.38          # base Y for neutral brows
        lx  = cx - r * 0.38         # left brow centre X
        rx  = cx + r * 0.38         # right brow centre X
        hw  = r * 0.22               # half-width of each brow
        drop = r * 0.09

        thick  = 3.5 if self._character_id == 1 else 2.0
        bcolor = QColor("#303040") if self._character_id == 1 else hair
        pen = QPen(bcolor, thick)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        if mood == "neutral":
            for bx in (lx, rx):
                p.drawLine(QPointF(bx - hw, by), QPointF(bx + hw, by))

        elif mood == "happy":
            offset = drop
            for bx in (lx, rx):
                p.drawLine(QPointF(bx - hw, by - offset),
                           QPointF(bx + hw, by - offset))

        elif mood == "sad":
            # Inner corners raised → worried look
            p.drawLine(QPointF(lx - hw, by),          QPointF(lx + hw, by - drop))
            p.drawLine(QPointF(rx - hw, by - drop),   QPointF(rx + hw, by))

        else:  # thinking — asymmetric raise
            p.drawLine(QPointF(lx - hw, by - drop * 0.4),
                       QPointF(lx + hw, by - drop * 1.2))
            p.drawLine(QPointF(rx - hw, by - drop * 0.2),
                       QPointF(rx + hw, by + drop * 0.2))

    def _eyes(self, p: QPainter, cx: float, cy: float, r: float, skin: QColor) -> None:
        mood = self._mood
        ey  = cy - r * 0.18
        erx = r * 0.17
        ery = r * 0.16

        for ex in (cx - r * 0.35, cx + r * 0.35):
            # Sclera
            p.setBrush(QBrush(QColor("#FFFFFF")))
            p.setPen(QPen(QColor("#AAAAAA"), 0.8))
            p.drawEllipse(QRectF(ex - erx, ey - ery, erx * 2, ery * 2))
            # Iris
            ir = erx * 0.65
            p.setBrush(QBrush(QColor("#2A5080")))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(ex - ir, ey - ir, ir * 2, ir * 2))
            # Pupil
            pr = ir * 0.55
            p.setBrush(QBrush(QColor("#101010")))
            p.drawEllipse(QRectF(ex - pr, ey - pr, pr * 2, pr * 2))
            # Highlight
            hr = pr * 0.35
            p.setBrush(QBrush(QColor("#FFFFFF")))
            p.drawEllipse(QRectF(ex + pr * 0.2, ey - pr * 0.6, hr * 2, hr * 2))
            # Thinking: eyelid overlay (upper half of eye)
            if mood == "thinking":
                p.setBrush(QBrush(skin))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRect(QRectF(ex - erx - 1, ey - ery - 1, erx * 2 + 2, ery + 2))

    # ------------------------------------------------------------------
    # Special features
    # ------------------------------------------------------------------

    def _mustache(self, p: QPainter, cx: float, cy: float, r: float, hair: QColor) -> None:
        my = cy + r * 0.28
        p.setBrush(QBrush(hair))
        p.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.moveTo(cx, my)
        path.cubicTo(cx - r * 0.10, my - r * 0.12,
                     cx - r * 0.28, my - r * 0.10,
                     cx - r * 0.32, my + r * 0.04)
        path.cubicTo(cx - r * 0.28, my + r * 0.12,
                     cx - r * 0.10, my + r * 0.08,
                     cx,            my + r * 0.05)
        path.cubicTo(cx + r * 0.10, my + r * 0.08,
                     cx + r * 0.28, my + r * 0.12,
                     cx + r * 0.32, my + r * 0.04)
        path.cubicTo(cx + r * 0.28, my - r * 0.10,
                     cx + r * 0.10, my - r * 0.12,
                     cx,            my)
        path.closeSubpath()
        p.drawPath(path)

    def _cheeks(self, p: QPainter, cx: float, cy: float, r: float) -> None:
        cc = QColor(255, 160, 170, 110)
        p.setBrush(QBrush(cc))
        p.setPen(Qt.PenStyle.NoPen)
        cr  = r * 0.22
        chy = cy + r * 0.05
        p.drawEllipse(QRectF(cx - r * 0.70 - cr, chy - cr, cr * 2, cr * 2))
        p.drawEllipse(QRectF(cx + r * 0.70 - cr, chy - cr, cr * 2, cr * 2))

    # ------------------------------------------------------------------
    # Mouth — mood-dependent
    # ------------------------------------------------------------------

    def _mouth(self, p: QPainter, cx: float, cy: float, r: float) -> None:
        mood = self._mood
        my = cy + r * 0.48
        hw = r * 0.28

        pen = QPen(QColor("#8B3A2A"), 2.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        if mood == "neutral":
            p.drawLine(QPointF(cx - hw, my), QPointF(cx + hw, my))

        elif mood == "happy":
            # Sag-down arc = smile (control point below endpoints)
            path = QPainterPath()
            path.moveTo(cx - hw, my)
            path.quadTo(cx, my + r * 0.22, cx + hw, my)
            p.drawPath(path)
            # White teeth hint
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor("#FFFFFF")))
            p.drawRect(QRectF(cx - hw * 0.65, my, hw * 1.3, r * 0.09))

        elif mood == "sad":
            # Arch-up arc = frown (control point above endpoints)
            path = QPainterPath()
            path.moveTo(cx - hw, my)
            path.quadTo(cx, my - r * 0.22, cx + hw, my)
            p.drawPath(path)

        else:  # thinking — sinuous/wavy mouth
            path = QPainterPath()
            path.moveTo(cx - hw, my)
            path.cubicTo(cx - hw * 0.3, my - r * 0.08,
                         cx + hw * 0.3, my + r * 0.08,
                         cx + hw * 0.6, my - r * 0.04)
            path.cubicTo(cx + hw * 0.8, my - r * 0.08,
                         cx + hw * 0.9, my,
                         cx + hw,       my + r * 0.02)
            p.drawPath(path)
