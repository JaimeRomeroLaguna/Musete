from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
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
from ui.character_widget import CharacterWidget
from ui.score_widget import ScoreWidget

# ── Paleta ─────────────────────────────────────────────────────────────
BG_FELT   = "#1B4332"
BG_ACTION = "#0F2922"
BG_PANEL  = "#142D1E"
TXT_WHITE = "#FFFFFF"
TXT_DIM   = "#A7F3D0"

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


def _dim_label(text: str, font_size: int = 13) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {TXT_DIM}; font-size: {font_size}px;")
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setWordWrap(True)
    return lbl


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._game = MusGame()
        self._player_card_widgets:  list[CardWidget] = []
        self._partner_card_widgets: list[CardWidget] = []
        self._bot1_card_widgets:    list[CardWidget] = []
        self._bot2_card_widgets:    list[CardWidget] = []
        self._setup_window()
        self._build_ui()
        self._refresh_ui()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_window(self) -> None:
        self.setWindowTitle("Musete — Partida de Mus")
        self.setMinimumSize(1200, 860)
        self.resize(1400, 960)

    def _build_ui(self) -> None:
        central = QWidget()
        central.setStyleSheet(f"background-color: {BG_FELT};")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(16, 10, 16, 10)
        root.setSpacing(10)

        # ── TOP BAR: marcadores ──────────────────────────────────────
        top_bar = QHBoxLayout()
        self._score_bot = ScoreWidget("Eq. Bot")
        self._score_bot.setMinimumWidth(260)
        title_lbl = QLabel("MUSETE")
        title_lbl.setFont(QFont("Georgia", 28, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {TXT_WHITE};")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._score_player = ScoreWidget("Eq. Jugador")
        self._score_player.setMinimumWidth(260)
        top_bar.addWidget(self._score_bot)
        top_bar.addWidget(title_lbl, 1)
        top_bar.addWidget(self._score_player)
        root.addLayout(top_bar)

        # ── TABLE ROW ────────────────────────────────────────────────
        table_row = QHBoxLayout()
        table_row.setSpacing(12)

        # LEFT PANEL — Bot 1 (Roca)
        left_panel = QWidget()
        left_panel.setFixedWidth(260)
        left_panel.setStyleSheet("background: transparent;")
        left_vbox = QVBoxLayout(left_panel)
        left_vbox.setContentsMargins(6, 6, 6, 6)
        left_vbox.setSpacing(6)
        left_vbox.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._bot1_character = CharacterWidget(character_id=1, mood="neutral")
        bot1_name = QLabel("Roca")
        bot1_name.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        bot1_name.setStyleSheet(f"color: {TXT_DIM};")
        bot1_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bot1_cards_widget = QWidget()
        bot1_cards_widget.setStyleSheet("background: transparent;")
        self._bot1_cards_grid = QGridLayout(bot1_cards_widget)
        self._bot1_cards_grid.setSpacing(4)
        self._bot1_cards_grid.setContentsMargins(0, 0, 0, 0)

        self._bot1_eval_label = _dim_label("—")

        left_vbox.addWidget(self._bot1_character)
        left_vbox.addWidget(bot1_name)
        left_vbox.addWidget(bot1_cards_widget)
        left_vbox.addWidget(self._bot1_eval_label)

        # CENTER PANEL
        center_panel = QVBoxLayout()
        center_panel.setSpacing(8)

        # Partner box (Compañero / Paco)
        partner_box = QFrame()
        partner_box.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_PANEL};
                border-radius: 10px;
            }}
        """)
        pb_vbox = QVBoxLayout(partner_box)
        pb_vbox.setContentsMargins(10, 8, 10, 8)
        pb_vbox.setSpacing(4)

        self._partner_character = CharacterWidget(character_id=0, mood="neutral")
        partner_name = QLabel("Paco  —  Compañero")
        partner_name.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        partner_name.setStyleSheet(f"color: {TXT_DIM};")
        partner_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._partner_cards_row = QHBoxLayout()
        self._partner_cards_row.setSpacing(6)
        self._partner_cards_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._partner_eval_label = _dim_label("—")

        pb_vbox.addWidget(self._partner_character)
        pb_vbox.addWidget(partner_name)
        pb_vbox.addLayout(self._partner_cards_row)
        pb_vbox.addWidget(self._partner_eval_label)

        # Action frame
        action_frame = QFrame()
        action_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_ACTION};
                border-radius: 10px;
            }}
        """)
        af_vbox = QVBoxLayout(action_frame)
        af_vbox.setContentsMargins(18, 12, 18, 12)
        af_vbox.setSpacing(6)

        self._lance_label = QLabel("—")
        self._lance_label.setFont(QFont("Arial", 26, QFont.Weight.Bold))
        self._lance_label.setStyleSheet(f"color: {TXT_WHITE};")
        self._lance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        af_vbox.addWidget(self._lance_label)

        self._bet_label = QLabel("")
        self._bet_label.setStyleSheet(f"color: {TXT_DIM}; font-size: 16px;")
        self._bet_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        af_vbox.addWidget(self._bet_label)

        self._status_label = QLabel("Pulsa «NUEVA PARTIDA» para empezar.")
        self._status_label.setStyleSheet(f"color: {TXT_DIM}; font-size: 15px;")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setWordWrap(True)
        af_vbox.addWidget(self._status_label)

        self._btn_row = QHBoxLayout()
        self._btn_row.setSpacing(12)
        self._btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        af_vbox.addLayout(self._btn_row)

        center_panel.addWidget(partner_box)
        center_panel.addWidget(action_frame, 1)

        # RIGHT PANEL — Bot 2 (Lola)
        right_panel = QWidget()
        right_panel.setFixedWidth(260)
        right_panel.setStyleSheet("background: transparent;")
        right_vbox = QVBoxLayout(right_panel)
        right_vbox.setContentsMargins(6, 6, 6, 6)
        right_vbox.setSpacing(6)
        right_vbox.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._bot2_character = CharacterWidget(character_id=2, mood="neutral")
        bot2_name = QLabel("Lola")
        bot2_name.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        bot2_name.setStyleSheet(f"color: {TXT_DIM};")
        bot2_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bot2_cards_widget = QWidget()
        bot2_cards_widget.setStyleSheet("background: transparent;")
        self._bot2_cards_grid = QGridLayout(bot2_cards_widget)
        self._bot2_cards_grid.setSpacing(4)
        self._bot2_cards_grid.setContentsMargins(0, 0, 0, 0)

        self._bot2_eval_label = _dim_label("—")

        right_vbox.addWidget(self._bot2_character)
        right_vbox.addWidget(bot2_name)
        right_vbox.addWidget(bot2_cards_widget)
        right_vbox.addWidget(self._bot2_eval_label)

        table_row.addWidget(left_panel)
        table_row.addLayout(center_panel, 1)
        table_row.addWidget(right_panel)
        root.addLayout(table_row, 1)

        # ── PLAYER SECTION (prominent, bottom) ───────────────────────
        player_frame = QFrame()
        player_frame.setStyleSheet("""
            QFrame {
                background-color: #0D2E1C;
                border: 2px solid #4ADE80;
                border-radius: 14px;
            }
        """)
        pf_vbox = QVBoxLayout(player_frame)
        pf_vbox.setContentsMargins(16, 10, 16, 10)
        pf_vbox.setSpacing(6)

        self._player_eval_label = _dim_label("—")

        self._player_cards_row = QHBoxLayout()
        self._player_cards_row.setSpacing(8)
        self._player_cards_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        player_name_lbl = QLabel("JUGADOR")
        player_name_lbl.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        player_name_lbl.setStyleSheet(f"color: {TXT_DIM};")
        player_name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pf_vbox.addWidget(self._player_eval_label)
        pf_vbox.addLayout(self._player_cards_row)
        pf_vbox.addWidget(player_name_lbl)

        root.addWidget(player_frame)

    # ------------------------------------------------------------------
    # Refresh UI según fase
    # ------------------------------------------------------------------

    def _refresh_ui(self) -> None:
        r = self._game.round
        phase = r.phase

        self._score_player.set_score(self._game.player_team_score)
        self._score_bot.set_score(self._game.bot_team_score)

        self._status_label.setText(r.status_message)

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

        self._rebuild_player_cards(phase)
        self._rebuild_partner_cards(phase)
        self._rebuild_bot1_cards(phase)
        self._rebuild_bot2_cards(phase)
        self._rebuild_buttons(phase)
        self._update_eval_labels(phase)
        self._update_character_moods(phase)

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

    def _rebuild_partner_cards(self, phase: GamePhase) -> None:
        self._clear_layout(self._partner_cards_row)
        self._partner_card_widgets.clear()

        r = self._game.round
        face_down = phase not in (GamePhase.HAND_OVER, GamePhase.GAME_OVER)
        for card in r.partner_hand.cards:
            w = CardWidget(card=card, face_down=face_down)
            self._partner_card_widgets.append(w)
            self._partner_cards_row.addWidget(w)

    def _rebuild_bot1_cards(self, phase: GamePhase) -> None:
        self._clear_grid(self._bot1_cards_grid)
        self._bot1_card_widgets.clear()

        r = self._game.round
        face_down = phase not in (GamePhase.HAND_OVER, GamePhase.GAME_OVER)
        for i, card in enumerate(r.bot1_hand.cards):
            w = CardWidget(card=card, face_down=face_down)
            self._bot1_card_widgets.append(w)
            self._bot1_cards_grid.addWidget(w, i // 2, i % 2)

    def _rebuild_bot2_cards(self, phase: GamePhase) -> None:
        self._clear_grid(self._bot2_cards_grid)
        self._bot2_card_widgets.clear()

        r = self._game.round
        face_down = phase not in (GamePhase.HAND_OVER, GamePhase.GAME_OVER)
        for i, card in enumerate(r.bot2_hand.cards):
            w = CardWidget(card=card, face_down=face_down)
            self._bot2_card_widgets.append(w)
            self._bot2_cards_grid.addWidget(w, i // 2, i % 2)

    @staticmethod
    def _clear_layout(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    @staticmethod
    def _clear_grid(grid: QGridLayout) -> None:
        while grid.count():
            item = grid.takeAt(0)
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
                b1 = _make_btn("QUIERO",    bg="#1A5E2A", hov="#27AE60", prs="#0F3A1A")
                b1.clicked.connect(lambda: self._on_player_action("quiero"))
                b2 = _make_btn("NO QUIERO", bg="#8B2200", hov="#B03000", prs="#600F00")
                b2.clicked.connect(lambda: self._on_player_action("no_quiero"))
                b3 = _make_btn("ENVIDO",    bg="#14456B", hov="#1A6EA8", prs="#0A2A45")
                b3.clicked.connect(lambda: self._on_player_action("envido"))
                b4 = _make_btn("ÓRDAGO",    bg="#5C2D00", hov="#8B4500", prs="#3A1A00")
                b4.clicked.connect(lambda: self._on_player_action("ordago"))
                add(b1); add(b2); add(b3); add(b4)
            else:
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
        show_evals = phase in (GamePhase.HAND_OVER, GamePhase.GAME_OVER)
        if show_evals:
            def _fmt(hand) -> str:
                g  = HandEvaluator.evaluate_grande(hand).description()
                c  = HandEvaluator.evaluate_chica(hand).description()
                pa = HandEvaluator.evaluate_pares(hand).description()
                j  = HandEvaluator.evaluate_juego(hand).description()
                return f"Grande: {g} | Chica: {c} | Pares: {pa} | Juego: {j}"

            self._player_eval_label.setText(_fmt(r.player_hand))
            self._partner_eval_label.setText(_fmt(r.partner_hand))
            self._bot1_eval_label.setText(_fmt(r.bot1_hand))
            self._bot2_eval_label.setText(_fmt(r.bot2_hand))
        else:
            self._player_eval_label.setText("—")
            self._partner_eval_label.setText("—")
            self._bot1_eval_label.setText("—")
            self._bot2_eval_label.setText("—")

    # ------------------------------------------------------------------
    # Character moods
    # ------------------------------------------------------------------

    def _update_character_moods(self, phase: GamePhase) -> None:
        r = self._game.round

        if phase == GamePhase.IDLE:
            mood_ally = mood_enemy = "neutral"

        elif phase in (GamePhase.MUS_DECISION, GamePhase.DISCARDING, GamePhase.BETTING):
            mood_ally = mood_enemy = "thinking"

        elif phase == GamePhase.LANCE_RESULT and r.betting:
            lr = r._lance_results.get(r.betting.lance)
            if lr and lr.player_wins:
                mood_ally, mood_enemy = "happy", "sad"
            elif lr and lr.bot_wins:
                mood_ally, mood_enemy = "sad", "happy"
            else:
                mood_ally = mood_enemy = "neutral"

        elif phase in (GamePhase.HAND_OVER, GamePhase.GAME_OVER) and r.hand_result:
            pa = r.hand_result.player_team_stones_earned
            ba = r.hand_result.bot_team_stones_earned
            mood_ally  = "happy" if pa > ba else ("sad" if ba > pa else "neutral")
            mood_enemy = "happy" if ba > pa else ("sad" if pa > ba else "neutral")

        else:
            mood_ally = mood_enemy = "neutral"

        self._partner_character.set_mood(mood_ally)
        self._bot1_character.set_mood(mood_enemy)
        self._bot2_character.set_mood(mood_enemy)

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

        discards = r.player_discard_indices
        was_from = from_idx in discards
        was_to   = to_idx in discards
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
