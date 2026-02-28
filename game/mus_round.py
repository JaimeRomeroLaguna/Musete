from __future__ import annotations

from typing import Optional

from game.bot import Bot
from game.deck import Deck
from game.evaluator import HandEvaluator
from game.game_logic import LanceResult
from game.hand import Hand
from game.scoring import base_stones_for_lance, pares_is_playable
from game.state import BettingState, GamePhase, HandResult

LANCES = ["grande", "chica", "pares", "juego"]


def _compare(p_eval, b_eval) -> LanceResult:
    if p_eval.beats(b_eval):
        return LanceResult(player_wins=True, bot_wins=False, is_tie=False)
    if b_eval.beats(p_eval):
        return LanceResult(player_wins=False, bot_wins=True, is_tie=False)
    return LanceResult(player_wins=False, bot_wins=False, is_tie=True)


class MusRound:
    """Orquesta una mano completa de Mus (sin Qt)."""

    def __init__(self) -> None:
        self._bot = Bot()
        self._deck = Deck()
        self._deck.shuffle()

        self.player_hand: Hand = Hand(cards=self._deck.deal(4))
        self.bot_hand: Hand = Hand(cards=self._deck.deal(4))

        self.phase: GamePhase = GamePhase.MUS_DECISION

        # Descartes pendientes del jugador (índices)
        self.player_discard_indices: list[int] = []

        # Lances
        self._lance_index: int = 0
        self._skipped_lances: set[str] = set()

        # Estado de apuesta del lance actual
        self.betting: Optional[BettingState] = None

        # Resultado de cada lance
        self._lance_results: dict[str, LanceResult] = {}
        self._lance_stones: dict[str, tuple[int, int]] = {}  # lance → (player, bot)

        # Resultado final
        self.hand_result: Optional[HandResult] = None

        # Mensaje de estado para la UI
        self.status_message: str = "¿Mus o no hay mus?"

    # ------------------------------------------------------------------
    # Fase MUS_DECISION
    # ------------------------------------------------------------------

    def player_mus(self) -> None:
        """El jugador pide mus."""
        assert self.phase == GamePhase.MUS_DECISION
        bot_wants_mus = self._bot.decide_mus(self.bot_hand)
        if bot_wants_mus:
            self.phase = GamePhase.DISCARDING
            self.player_discard_indices = []
            self.status_message = "Mus aceptado. Elige cartas a descartar."
        else:
            # Bot dice no hay mus → empezamos lances
            self.status_message = "El bot no acepta mus. Comenzamos lances."
            self._start_lances()

    def player_no_mus(self) -> None:
        """El jugador dice no hay mus."""
        assert self.phase == GamePhase.MUS_DECISION
        self.status_message = "No hay mus. Comenzamos lances."
        self._start_lances()

    # ------------------------------------------------------------------
    # Fase DISCARDING
    # ------------------------------------------------------------------

    def toggle_discard(self, index: int) -> None:
        """Alterna selección de la carta en posición `index`."""
        assert self.phase == GamePhase.DISCARDING
        if index in self.player_discard_indices:
            self.player_discard_indices.remove(index)
        else:
            self.player_discard_indices.append(index)

    def player_confirm_discard(self) -> None:
        """Aplica descartes del jugador, el bot descarta, rellenan manos."""
        assert self.phase == GamePhase.DISCARDING

        # Cartas descartadas por el jugador
        player_discards = [
            self.player_hand.cards[i] for i in self.player_discard_indices
        ]
        # Nuevas cartas del jugador (conserva las no descartadas)
        kept_player = [
            c for i, c in enumerate(self.player_hand.cards)
            if i not in self.player_discard_indices
        ]

        # Bot descarta
        bot_discard_indices = self._bot.decide_discard(self.bot_hand)
        bot_discards = [self.bot_hand.cards[i] for i in bot_discard_indices]
        kept_bot = [
            c for i, c in enumerate(self.bot_hand.cards)
            if i not in bot_discard_indices
        ]

        # Devolver descartes al mazo
        all_discards = player_discards + bot_discards
        if all_discards:
            self._deck.add_cards(all_discards)

        # Rellenar manos
        need_player = 4 - len(kept_player)
        need_bot = 4 - len(kept_bot)
        total_needed = need_player + need_bot

        # Si el mazo no tiene suficientes cartas, rellenar lo que haya
        available = self._deck.remaining
        if available < total_needed:
            # Ampliar con cartas sobrantes del mazo completo
            from game.deck import Deck as _Deck
            extra = _Deck()
            extra.shuffle()
            self._deck.add_cards(extra.deal(min(extra.remaining, total_needed - available)))

        new_player = self._deck.deal(min(need_player, self._deck.remaining))
        new_bot = self._deck.deal(min(need_bot, self._deck.remaining))

        self.player_hand = Hand(cards=kept_player + new_player)
        self.bot_hand = Hand(cards=kept_bot + new_bot)
        self.player_discard_indices = []

        # Bot decide si vuelve a pedir mus
        bot_wants_mus = self._bot.decide_mus(self.bot_hand)
        if bot_wants_mus:
            self.phase = GamePhase.MUS_DECISION
            self.status_message = "El bot pide mus otra vez. ¿Mus o no hay mus?"
        else:
            self._start_lances()

    # ------------------------------------------------------------------
    # Lances internos
    # ------------------------------------------------------------------

    def _start_lances(self) -> None:
        self._lance_index = 0
        self._begin_lance(LANCES[0])

    def _begin_lance(self, lance: str) -> None:
        # Evalúa si el lance es jugable
        p_pares = HandEvaluator.evaluate_pares(self.player_hand)
        b_pares = HandEvaluator.evaluate_pares(self.bot_hand)
        p_juego = HandEvaluator.evaluate_juego(self.player_hand)
        b_juego = HandEvaluator.evaluate_juego(self.bot_hand)

        if lance == "pares" and not pares_is_playable(p_pares, b_pares):
            self._skipped_lances.add(lance)
            self._lance_results[lance] = LanceResult(False, False, True)
            self._lance_stones[lance] = (0, 0)
            self.status_message = "Pares: ninguno tiene pares, lance saltado."
            self._advance_to_next_lance()
            return

        base = base_stones_for_lance(lance, p_pares, b_pares, p_juego, b_juego)

        self.betting = BettingState(
            lance=lance,
            base_stones=base,
            current_bet=base,
            bet_history=[base],
            whose_turn="player",
            bot_last_action=None,
            resolved=False,
            fold_winner=None,
            stones_awarded=0,
        )
        self.phase = GamePhase.BETTING
        self.status_message = f"Lance: {lance.upper()} — apuesta base {base} piedra(s). Tu turno."

    def _advance_to_next_lance(self) -> None:
        self._lance_index += 1
        if self._lance_index < len(LANCES):
            self._begin_lance(LANCES[self._lance_index])
        else:
            self._finish_hand()

    # ------------------------------------------------------------------
    # Fase BETTING
    # ------------------------------------------------------------------

    def player_action(self, action: str) -> None:
        """
        El jugador actúa. action: 'paso' | 'envido' | 'quiero' | 'no_quiero' | 'ordago'
        Después, el bot responde.
        """
        assert self.phase == GamePhase.BETTING
        assert self.betting is not None
        b = self.betting

        if action == "paso":
            self._handle_paso(actor="player")
        elif action == "envido":
            self._handle_envido(actor="player")
        elif action == "ordago":
            self._handle_ordago(actor="player")
        elif action == "quiero":
            self._handle_quiero(actor="player")
        elif action == "no_quiero":
            self._handle_no_quiero(actor="player")

        if not b.resolved:
            # Turno del bot (sólo si el player apostó o pasó sin abrir)
            b.whose_turn = "bot"
            self._bot_take_turn()
        else:
            self._resolve_betting()

    def _bot_take_turn(self) -> None:
        assert self.betting is not None
        b = self.betting
        lance = b.lance

        # ¿El bot necesita responder a una subida o iniciar?
        # Si el jugador ha apostado (fold_winner == "player"), el bot responde
        # Si no hay apuesta abierta, el bot inicia
        if b.fold_winner == "player":
            # El jugador apostó → bot responde
            bot_action = self._bot.decide_bet_respond(self.bot_hand, lance, b.current_bet)
        elif b.fold_winner is None:
            # Nadie ha apostado → bot inicia
            bot_action = self._bot.decide_bet_initiate(self.bot_hand, lance, b.current_bet)
        else:
            # fold_winner == "bot" (bot apostó, jugador pasó/envido más) → responder
            bot_action = self._bot.decide_bet_respond(self.bot_hand, lance, b.current_bet)

        b.bot_last_action = bot_action

        if bot_action == "paso":
            self._handle_paso(actor="bot")
        elif bot_action == "envido":
            self._handle_envido(actor="bot")
        elif bot_action == "ordago":
            self._handle_ordago(actor="bot")
        elif bot_action == "quiero":
            self._handle_quiero(actor="bot")
        elif bot_action == "no_quiero":
            self._handle_no_quiero(actor="bot")

        if b.resolved:
            self._resolve_betting()
        else:
            b.whose_turn = "player"

    def _handle_paso(self, actor: str) -> None:
        b = self.betting
        # Si hay una apuesta abierta (fold_winner != None), paso = no_quiero
        if b.fold_winner is not None:
            self._handle_no_quiero(actor)
            return
        # Sin apuesta abierta: ambos pasan → premio base
        if actor == "bot":
            # El bot pasa después del jugador → ambos han pasado
            b.stones_awarded = b.base_stones
            b.resolved = True
        # Si actor == "player": esperar al bot

    def _handle_envido(self, actor: str) -> None:
        b = self.betting
        b.current_bet = b.current_bet + 1
        b.bet_history.append(b.current_bet)
        b.fold_winner = actor  # si el otro no quiere, este gana lo previo

    def _handle_ordago(self, actor: str) -> None:
        b = self.betting
        b.current_bet = 40
        b.bet_history.append(40)
        b.fold_winner = actor
        # El otro jugador deberá quiero/no_quiero en su siguiente turno

    def _handle_quiero(self, actor: str) -> None:
        b = self.betting
        b.stones_awarded = b.current_bet
        b.resolved = True
        # El ganador se determina por evaluación de mano

    def _handle_no_quiero(self, actor: str) -> None:
        b = self.betting
        # Gana quien apostó último (fold_winner); si no hay apuesta, gana el otro
        if b.fold_winner is not None:
            winner = b.fold_winner
        else:
            winner = "bot" if actor == "player" else "player"
        # Premio = apuesta anterior (antes de la última subida)
        if len(b.bet_history) >= 2:
            b.stones_awarded = b.bet_history[-2]
        else:
            b.stones_awarded = 0
        b.resolved = True
        b.fold_winner = winner
        b.was_fold = True

    def _resolve_betting(self) -> None:
        assert self.betting is not None
        b = self.betting
        lance = b.lance

        if b.was_fold:
            # Alguien se echó → fold_winner gana stones_awarded
            winner_str = b.fold_winner
            if winner_str == "player":
                lr = LanceResult(player_wins=True, bot_wins=False, is_tie=False)
            else:
                lr = LanceResult(player_wins=False, bot_wins=True, is_tie=False)
            stones = b.stones_awarded
        else:
            # Quiero o ambos pasaron → evaluar por la mano
            lr = self._evaluate_lance(lance)
            stones = b.stones_awarded

        self._lance_results[lance] = lr
        if lr.player_wins:
            self._lance_stones[lance] = (stones, 0)
        elif lr.bot_wins:
            self._lance_stones[lance] = (0, stones)
        else:
            self._lance_stones[lance] = (0, 0)

        self.phase = GamePhase.LANCE_RESULT
        winner_label = lr.winner
        self.status_message = (
            f"{lance.upper()}: gana {winner_label} → {stones} piedra(s)."
        )

    def _evaluate_lance(self, lance: str) -> LanceResult:
        if lance == "grande":
            return _compare(
                HandEvaluator.evaluate_grande(self.player_hand),
                HandEvaluator.evaluate_grande(self.bot_hand),
            )
        if lance == "chica":
            return _compare(
                HandEvaluator.evaluate_chica(self.player_hand),
                HandEvaluator.evaluate_chica(self.bot_hand),
            )
        if lance == "pares":
            return _compare(
                HandEvaluator.evaluate_pares(self.player_hand),
                HandEvaluator.evaluate_pares(self.bot_hand),
            )
        if lance == "juego":
            return _compare(
                HandEvaluator.evaluate_juego(self.player_hand),
                HandEvaluator.evaluate_juego(self.bot_hand),
            )
        return LanceResult(False, False, True)

    # ------------------------------------------------------------------
    # Avanzar lance (llamado desde UI tras LANCE_RESULT)
    # ------------------------------------------------------------------

    def advance_lance(self) -> None:
        assert self.phase == GamePhase.LANCE_RESULT
        self._advance_to_next_lance()

    # ------------------------------------------------------------------
    # Fin de mano
    # ------------------------------------------------------------------

    def _finish_hand(self) -> None:
        player_total = sum(s[0] for s in self._lance_stones.values())
        bot_total = sum(s[1] for s in self._lance_stones.values())

        self.hand_result = HandResult(
            lance_results=self._lance_results,
            player_stones_earned=player_total,
            bot_stones_earned=bot_total,
        )
        self.phase = GamePhase.HAND_OVER
        self.status_message = (
            f"Mano terminada. Jugador: +{player_total} | Bot: +{bot_total}"
        )
