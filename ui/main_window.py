from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from game.evaluator import HandEvaluator
from game.mus_game import MusGame
from game.state import GamePhase
from ui.card_widget import CardWidget
from ui.score_widget import ScoreWidget

# ── Paleta ─────────────────────────────────────────────────────────────
BG_FELT = "#1B4332"
BG_ACTION = "#0F2922"
TXT_WHITE = "#FFFFFF"
TXT_DIM = "#A7F3D0"

BTN_BASE = """
QPushButton {{
    background-color: {bg};
    color: {fg};
    border: none;
    border-radius: 8px;
    padding: 10px 22px;
    font-weight: bold;
    font-size: 17px;
    min-width: 130px;
}}
QPushButton:hover   {{ background-color: {hov}; }}
QPushButton:pressed {{ background-color: {prs}; }}
QPushButton:disabled {{ background-color: #2D4A40; color: #607060; }}
"""


def _make_btn(text: str, bg: str = "#2D6A4F", fg: str = "#FFFFFF",
              hov: str = "#3D8C6A", prs: str = "#1A4A35") -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet(BTN_BASE.format(bg=bg, fg=fg, hov=hov, prs=prs))
    return btn


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._game = MusGame()
        self._player_card_widgets: list[CardWidget] = []
        self._bot_card_widgets: list[CardWidget] = []
        self._setup_window()
        self._build_ui()
        self._refresh_ui()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_window(self) -> None:
        self.setWindowTitle("Musete — Partida de Mus")
        self.setMinimumSize(1000, 860)
        self.resize(1120, 960)

    def _build_ui(self) -> None:
        central = QWidget()
        central.setStyleSheet(f"background-color: {BG_FELT};")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(20, 14, 20, 14)
        root.setSpacing(12)

        # ── TOP BAR: marcadores ──────────────────────────────────────
        top_bar = QHBoxLayout()
        self._score_bot = ScoreWidget("Bot")
        self._score_bot.setMinimumWidth(260)
        title_lbl = QLabel("MUSETE")
        title_lbl.setFont(QFont("Georgia", 30, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {TXT_WHITE};")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._score_player = ScoreWidget("Jugador")
        self._score_player.setMinimumWidth(260)

        top_bar.addWidget(self._score_bot)
        top_bar.addWidget(title_lbl, 1)
        top_bar.addWidget(self._score_player)
        root.addLayout(top_bar)

        # ── BOT AREA ─────────────────────────────────────────────────
        bot_area = QWidget()
        bot_area.setStyleSheet("background: transparent;")
        bot_vbox = QVBoxLayout(bot_area)
        bot_vbox.setContentsMargins(0, 0, 0, 0)
        bot_vbox.setSpacing(4)

        bot_label = QLabel("Bot")
        bot_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        bot_label.setStyleSheet(f"color: {TXT_DIM};")
        bot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bot_vbox.addWidget(bot_label)

        self._bot_cards_row = QHBoxLayout()
        self._bot_cards_row.setSpacing(8)
        self._bot_cards_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bot_vbox.addLayout(self._bot_cards_row)

        self._bot_eval_label = QLabel("—")
        self._bot_eval_label.setStyleSheet(f"color: {TXT_DIM}; font-size: 15px;")
        self._bot_eval_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bot_vbox.addWidget(self._bot_eval_label)

        root.addWidget(bot_area)

        # ── ACTION FRAME ─────────────────────────────────────────────
        action_frame = QFrame()
        action_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_ACTION};
                border-radius: 10px;
            }}
        """)
        af_vbox = QVBoxLayout(action_frame)
        af_vbox.setContentsMargins(18, 14, 18, 14)
        af_vbox.setSpacing(8)

        self._lance_label = QLabel("—")
        self._lance_label.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        self._lance_label.setStyleSheet(f"color: {TXT_WHITE};")
        self._lance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        af_vbox.addWidget(self._lance_label)

        self._bet_label = QLabel("")
        self._bet_label.setStyleSheet(f"color: {TXT_DIM}; font-size: 18px;")
        self._bet_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        af_vbox.addWidget(self._bet_label)

        self._status_label = QLabel("Pulsa «NUEVA PARTIDA» para empezar.")
        self._status_label.setStyleSheet(f"color: {TXT_DIM}; font-size: 16px;")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setWordWrap(True)
        af_vbox.addWidget(self._status_label)

        self._btn_row = QHBoxLayout()
        self._btn_row.setSpacing(12)
        self._btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        af_vbox.addLayout(self._btn_row)

        root.addWidget(action_frame)

        # ── PLAYER AREA ───────────────────────────────────────────────
        player_area = QWidget()
        player_area.setStyleSheet("background: transparent;")
        player_vbox = QVBoxLayout(player_area)
        player_vbox.setContentsMargins(0, 0, 0, 0)
        player_vbox.setSpacing(4)

        self._player_eval_label = QLabel("—")
        self._player_eval_label.setStyleSheet(f"color: {TXT_DIM}; font-size: 15px;")
        self._player_eval_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        player_vbox.addWidget(self._player_eval_label)

        self._player_cards_row = QHBoxLayout()
        self._player_cards_row.setSpacing(8)
        self._player_cards_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        player_vbox.addLayout(self._player_cards_row)

        player_label = QLabel("Jugador")
        player_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        player_label.setStyleSheet(f"color: {TXT_DIM};")
        player_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        player_vbox.addWidget(player_label)

        root.addWidget(player_area)

    # ------------------------------------------------------------------
    # Refresh UI según fase
    # ------------------------------------------------------------------

    def _refresh_ui(self) -> None:
        r = self._game.round
        phase = r.phase

        self._score_player.set_score(self._game.player_score)
        self._score_bot.set_score(self._game.bot_score)

        self._status_label.setText(r.status_message)

        # Actualizar etiquetas de apuesta
        if phase == GamePhase.BETTING and r.betting:
            b = r.betting
            self._lance_label.setText(b.lance.upper())
            self._bet_label.setText(f"Apuesta actual: {b.current_bet} piedra(s)")
        elif phase in (GamePhase.LANCE_RESULT, GamePhase.HAND_OVER, GamePhase.GAME_OVER):
            if r.betting:
                self._lance_label.setText(r.betting.lance.upper())
            self._bet_label.setText("")
        elif phase == GamePhase.MUS_DECISION:
            self._lance_label.setText("¿MUS?")
            self._bet_label.setText("")
        elif phase == GamePhase.DISCARDING:
            self._lance_label.setText("DESCARTE")
            self._bet_label.setText("Selecciona las cartas a descartar")
        else:
            self._lance_label.setText("MUSETE")
            self._bet_label.setText("")

        # Cartas del jugador
        self._rebuild_player_cards(phase)
        # Cartas del bot
        self._rebuild_bot_cards(phase)
        # Botones
        self._rebuild_buttons(phase)
        # Evaluaciones
        self._update_eval_labels(phase)

    # ------------------------------------------------------------------
    # Cartas
    # ------------------------------------------------------------------

    def _rebuild_player_cards(self, phase: GamePhase) -> None:
        self._clear_layout(self._player_cards_row)
        self._player_card_widgets.clear()

        r = self._game.round
        draggable = phase != GamePhase.IDLE

        for i, card in enumerate(r.player_hand.cards):
            w = CardWidget(card=card, face_down=False)

            if draggable:
                w.enable_drag(i)
                w.reorder_requested.connect(self._on_card_reorder)

            if phase == GamePhase.DISCARDING:
                w.set_selected(i in r.player_discard_indices)
                w.enable_click(i)
                w.clicked.connect(self._on_card_click)

            self._player_card_widgets.append(w)
            self._player_cards_row.addWidget(w)

    def _rebuild_bot_cards(self, phase: GamePhase) -> None:
        self._clear_layout(self._bot_cards_row)
        self._bot_card_widgets.clear()

        r = self._game.round
        face_down = phase not in (GamePhase.LANCE_RESULT, GamePhase.HAND_OVER, GamePhase.GAME_OVER)
        for card in r.bot_hand.cards:
            w = CardWidget(card=card, face_down=face_down)
            self._bot_card_widgets.append(w)
            self._bot_cards_row.addWidget(w)

    @staticmethod
    def _clear_layout(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ------------------------------------------------------------------
    # Botones contextuales
    # ------------------------------------------------------------------

    def _rebuild_buttons(self, phase: GamePhase) -> None:
        self._clear_layout(self._btn_row)

        def add(btn: QPushButton) -> None:
            self._btn_row.addWidget(btn)

        if phase == GamePhase.IDLE:
            b = _make_btn("NUEVA PARTIDA")
            b.clicked.connect(self._on_new_game)
            add(b)

        elif phase == GamePhase.MUS_DECISION:
            b1 = _make_btn("MUS")
            b1.clicked.connect(self._on_mus)
            b2 = _make_btn("NO HAY MUS", bg="#8B2200", hov="#B03000", prs="#600F00")
            b2.clicked.connect(self._on_no_mus)
            add(b1); add(b2)

        elif phase == GamePhase.DISCARDING:
            b = _make_btn("CONFIRMAR DESCARTE")
            b.clicked.connect(self._on_confirm_discard)
            add(b)

        elif phase == GamePhase.BETTING:
            r = self._game.round
            b_obj = r.betting
            has_open_bet = b_obj is not None and b_obj.fold_winner is not None

            if has_open_bet:
                # Responding
                b1 = _make_btn("QUIERO", bg="#1A5E2A", hov="#27AE60", prs="#0F3A1A")
                b1.clicked.connect(lambda: self._on_player_action("quiero"))
                b2 = _make_btn("NO QUIERO", bg="#8B2200", hov="#B03000", prs="#600F00")
                b2.clicked.connect(lambda: self._on_player_action("no_quiero"))
                b3 = _make_btn("ENVIDO", bg="#14456B", hov="#1A6EA8", prs="#0A2A45")
                b3.clicked.connect(lambda: self._on_player_action("envido"))
                b4 = _make_btn("ÓRDAGO", bg="#5C2D00", hov="#8B4500", prs="#3A1A00")
                b4.clicked.connect(lambda: self._on_player_action("ordago"))
                add(b1); add(b2); add(b3); add(b4)
            else:
                # Opening
                b1 = _make_btn("PASO")
                b1.clicked.connect(lambda: self._on_player_action("paso"))
                b2 = _make_btn("ENVIDO", bg="#14456B", hov="#1A6EA8", prs="#0A2A45")
                b2.clicked.connect(lambda: self._on_player_action("envido"))
                b3 = _make_btn("ÓRDAGO", bg="#5C2D00", hov="#8B4500", prs="#3A1A00")
                b3.clicked.connect(lambda: self._on_player_action("ordago"))
                add(b1); add(b2); add(b3)

        elif phase == GamePhase.LANCE_RESULT:
            b = _make_btn("SIGUIENTE LANCE")
            b.clicked.connect(self._on_advance_lance)
            add(b)

        elif phase == GamePhase.HAND_OVER:
            b = _make_btn("NUEVA MANO")
            b.clicked.connect(self._on_new_hand)
            add(b)

        elif phase == GamePhase.GAME_OVER:
            b = _make_btn("NUEVA PARTIDA")
            b.clicked.connect(self._on_new_game)
            add(b)

    # ------------------------------------------------------------------
    # Evaluaciones
    # ------------------------------------------------------------------

    def _update_eval_labels(self, phase: GamePhase) -> None:
        r = self._game.round
        show_evals = phase in (
            GamePhase.LANCE_RESULT, GamePhase.HAND_OVER, GamePhase.GAME_OVER
        )
        if show_evals:
            p = r.player_hand
            b = r.bot_hand
            p_g = HandEvaluator.evaluate_grande(p).description()
            p_c = HandEvaluator.evaluate_chica(p).description()
            p_pa = HandEvaluator.evaluate_pares(p).description()
            p_j = HandEvaluator.evaluate_juego(p).description()
            b_g = HandEvaluator.evaluate_grande(b).description()
            b_c = HandEvaluator.evaluate_chica(b).description()
            b_pa = HandEvaluator.evaluate_pares(b).description()
            b_j = HandEvaluator.evaluate_juego(b).description()
            self._player_eval_label.setText(
                f"Grande: {p_g} | Chica: {p_c} | Pares: {p_pa} | Juego: {p_j}"
            )
            self._bot_eval_label.setText(
                f"Grande: {b_g} | Chica: {b_c} | Pares: {b_pa} | Juego: {b_j}"
            )
        else:
            self._player_eval_label.setText("—")
            self._bot_eval_label.setText("—")

    # ------------------------------------------------------------------
    # Handlers de acciones
    # ------------------------------------------------------------------

    def _on_new_game(self) -> None:
        self._game.new_game()
        self._refresh_ui()

    def _on_mus(self) -> None:
        self._game.round.player_mus()
        self._refresh_ui()

    def _on_no_mus(self) -> None:
        self._game.round.player_no_mus()
        self._refresh_ui()

    def _on_card_click(self, index: int) -> None:
        r = self._game.round
        if r.phase != GamePhase.DISCARDING:
            return
        r.toggle_discard(index)
        for i, w in enumerate(self._player_card_widgets):
            w.set_selected(i in r.player_discard_indices)

    def _on_card_reorder(self, from_idx: int, to_idx: int) -> None:
        """Intercambia dos cartas en la mano del jugador (cosmético)."""
        r = self._game.round
        cards = r.player_hand.cards
        cards[from_idx], cards[to_idx] = cards[to_idx], cards[from_idx]

        # Si estamos en descarte, la selección sigue a la carta, no a la posición
        discards = r.player_discard_indices
        was_from = from_idx in discards
        was_to   = to_idx   in discards
        if was_from != was_to:
            if was_from:
                discards.remove(from_idx)
                discards.append(to_idx)
            else:
                discards.remove(to_idx)
                discards.append(from_idx)

        self._rebuild_player_cards(r.phase)

    def _on_confirm_discard(self) -> None:
        self._game.round.player_confirm_discard()
        self._refresh_ui()

    def _on_player_action(self, action: str) -> None:
        self._game.round.player_action(action)
        self._maybe_apply_result()
        self._refresh_ui()

    def _on_advance_lance(self) -> None:
        self._game.round.advance_lance()
        self._maybe_apply_result()
        self._refresh_ui()

    def _on_new_hand(self) -> None:
        self._game.start_hand()
        self._refresh_ui()

    def _maybe_apply_result(self) -> None:
        r = self._game.round
        if r.phase == GamePhase.HAND_OVER and r.hand_result is not None:
            if not self._game.is_game_over:
                self._game.apply_round_result(r.hand_result)
