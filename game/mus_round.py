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


def _best_eval(evals: list):
    """Returns the evaluation result that beats all others."""
    best = evals[0]
    for e in evals[1:]:
        if e.beats(best):
            best = e
    return best


def _combine_bot_team_initiate(a1: str, a2: str) -> str:
    if "ordago" in (a1, a2):
        return "ordago"
    if "envido" in (a1, a2):
        return "envido"
    return "paso"


def _combine_bot_team_respond(a1: str, a2: str, current_bet: int) -> str:
    if "ordago" in (a1, a2):
        return "ordago"
    if "envido" in (a1, a2) and current_bet < 4:
        return "envido"
    if "quiero" in (a1, a2):
        return "quiero"
    return "no_quiero"


class MusRound:
    """Orquesta una mano completa de Mus (4 jugadores, sin Qt)."""

    def __init__(self) -> None:
        self._bot = Bot()
        self._deck = Deck()
        self._deck.shuffle()

        # Equipo A: jugador humano + compañero bot
        self.player_hand: Hand = Hand(cards=self._deck.deal(4))
        self.partner_hand: Hand = Hand(cards=self._deck.deal(4))
        # Equipo B: dos bots rivales
        self.bot1_hand: Hand = Hand(cards=self._deck.deal(4))
        self.bot2_hand: Hand = Hand(cards=self._deck.deal(4))

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
        self._lance_stones: dict[str, tuple[int, int]] = {}  # lance → (player_team, bot_team)

        # Resultado final
        self.hand_result: Optional[HandResult] = None

        # Mensaje de estado para la UI
        self.status_message: str = "¿Mus o no hay mus?"

    # ------------------------------------------------------------------
    # Helpers de evaluación por equipo
    # ------------------------------------------------------------------

    def _team_a_eval(self, lance: str):
        """Best evaluation for Team A (player + partner) in the given lance."""
        if lance == "grande":
            return _best_eval([
                HandEvaluator.evaluate_grande(self.player_hand),
                HandEvaluator.evaluate_grande(self.partner_hand),
            ])
        if lance == "chica":
            return _best_eval([
                HandEvaluator.evaluate_chica(self.player_hand),
                HandEvaluator.evaluate_chica(self.partner_hand),
            ])
        if lance == "pares":
            return _best_eval([
                HandEvaluator.evaluate_pares(self.player_hand),
                HandEvaluator.evaluate_pares(self.partner_hand),
            ])
        # juego or punto
        return _best_eval([
            HandEvaluator.evaluate_juego(self.player_hand),
            HandEvaluator.evaluate_juego(self.partner_hand),
        ])

    def _team_b_eval(self, lance: str):
        """Best evaluation for Team B (bot1 + bot2) in the given lance."""
        if lance == "grande":
            return _best_eval([
                HandEvaluator.evaluate_grande(self.bot1_hand),
                HandEvaluator.evaluate_grande(self.bot2_hand),
            ])
        if lance == "chica":
            return _best_eval([
                HandEvaluator.evaluate_chica(self.bot1_hand),
                HandEvaluator.evaluate_chica(self.bot2_hand),
            ])
        if lance == "pares":
            return _best_eval([
                HandEvaluator.evaluate_pares(self.bot1_hand),
                HandEvaluator.evaluate_pares(self.bot2_hand),
            ])
        # juego or punto
        return _best_eval([
            HandEvaluator.evaluate_juego(self.bot1_hand),
            HandEvaluator.evaluate_juego(self.bot2_hand),
        ])

    # ------------------------------------------------------------------
    # Fase MUS_DECISION
    # ------------------------------------------------------------------

    def player_mus(self) -> None:
        """El jugador pide mus. Los 3 bots deciden; todos deben querer mus."""
        assert self.phase == GamePhase.MUS_DECISION
        partner_wants = self._bot.decide_mus(self.partner_hand)
        bot1_wants = self._bot.decide_mus(self.bot1_hand)
        bot2_wants = self._bot.decide_mus(self.bot2_hand)
        if partner_wants and bot1_wants and bot2_wants:
            self.phase = GamePhase.DISCARDING
            self.player_discard_indices = []
            self.status_message = "Mus aceptado. Elige cartas a descartar."
        else:
            self.status_message = "Algún jugador no acepta mus."
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
        """Aplica descartes del jugador y de los 3 bots, rellenan manos."""
        assert self.phase == GamePhase.DISCARDING

        # Player discards
        player_discards = [
            self.player_hand.cards[i] for i in self.player_discard_indices
        ]
        kept_player = [
            c for i, c in enumerate(self.player_hand.cards)
            if i not in self.player_discard_indices
        ]

        # Partner discards
        partner_idx = self._bot.decide_discard(self.partner_hand)
        partner_discards = [self.partner_hand.cards[i] for i in partner_idx]
        kept_partner = [
            c for i, c in enumerate(self.partner_hand.cards)
            if i not in partner_idx
        ]

        # Bot1 discards
        bot1_idx = self._bot.decide_discard(self.bot1_hand)
        bot1_discards = [self.bot1_hand.cards[i] for i in bot1_idx]
        kept_bot1 = [
            c for i, c in enumerate(self.bot1_hand.cards)
            if i not in bot1_idx
        ]

        # Bot2 discards
        bot2_idx = self._bot.decide_discard(self.bot2_hand)
        bot2_discards = [self.bot2_hand.cards[i] for i in bot2_idx]
        kept_bot2 = [
            c for i, c in enumerate(self.bot2_hand.cards)
            if i not in bot2_idx
        ]

        # Return all discards to deck
        all_discards = player_discards + partner_discards + bot1_discards + bot2_discards
        if all_discards:
            self._deck.add_cards(all_discards)

        # Refill all hands
        need_player = 4 - len(kept_player)
        need_partner = 4 - len(kept_partner)
        need_bot1 = 4 - len(kept_bot1)
        need_bot2 = 4 - len(kept_bot2)
        total_needed = need_player + need_partner + need_bot1 + need_bot2

        available = self._deck.remaining
        if available < total_needed:
            from game.deck import Deck as _Deck
            extra = _Deck()
            extra.shuffle()
            self._deck.add_cards(extra.deal(min(extra.remaining, total_needed - available)))

        new_player = self._deck.deal(min(need_player, self._deck.remaining))
        new_partner = self._deck.deal(min(need_partner, self._deck.remaining))
        new_bot1 = self._deck.deal(min(need_bot1, self._deck.remaining))
        new_bot2 = self._deck.deal(min(need_bot2, self._deck.remaining))

        self.player_hand = Hand(cards=kept_player + new_player)
        self.partner_hand = Hand(cards=kept_partner + new_partner)
        self.bot1_hand = Hand(cards=kept_bot1 + new_bot1)
        self.bot2_hand = Hand(cards=kept_bot2 + new_bot2)
        self.player_discard_indices = []

        # Bots decide if they want mus again; if all do → ask player again
        partner_wants = self._bot.decide_mus(self.partner_hand)
        bot1_wants = self._bot.decide_mus(self.bot1_hand)
        bot2_wants = self._bot.decide_mus(self.bot2_hand)
        if partner_wants and bot1_wants and bot2_wants:
            self.phase = GamePhase.MUS_DECISION
            self.status_message = "Los bots piden mus otra vez. ¿Mus o no hay mus?"
        else:
            self._start_lances()

    # ------------------------------------------------------------------
    # Lances internos
    # ------------------------------------------------------------------

    def _start_lances(self) -> None:
        self._lance_index = 0
        self._begin_lance(LANCES[0])

    def _begin_lance(self, lance: str) -> None:
        # Best pares and juego for each team
        p_pares = _best_eval([
            HandEvaluator.evaluate_pares(self.player_hand),
            HandEvaluator.evaluate_pares(self.partner_hand),
        ])
        b_pares = _best_eval([
            HandEvaluator.evaluate_pares(self.bot1_hand),
            HandEvaluator.evaluate_pares(self.bot2_hand),
        ])
        p_juego = _best_eval([
            HandEvaluator.evaluate_juego(self.player_hand),
            HandEvaluator.evaluate_juego(self.partner_hand),
        ])
        b_juego = _best_eval([
            HandEvaluator.evaluate_juego(self.bot1_hand),
            HandEvaluator.evaluate_juego(self.bot2_hand),
        ])

        if lance == "pares" and not pares_is_playable(p_pares, b_pares):
            self._skipped_lances.add(lance)
            self._lance_results[lance] = LanceResult(False, False, True)
            self._lance_stones[lance] = (0, 0)
            self.status_message = "Pares: ningún equipo tiene pares, lance saltado."
            self._advance_to_next_lance()
            return

        display_lance = lance
        if lance == "juego" and not p_juego.has_juego and not b_juego.has_juego:
            display_lance = "punto"

        base = base_stones_for_lance(lance, p_pares, b_pares, p_juego, b_juego)

        self.betting = BettingState(
            lance=display_lance,
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
        self.status_message = f"Lance: {display_lance.upper()} — apuesta base {base} piedra(s). Tu turno."

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
        Después, el equipo bot responde.
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
            b.whose_turn = "bot"
            self._bot_team_take_turn()
        else:
            self._resolve_betting()

    def _bot_team_take_turn(self) -> None:
        assert self.betting is not None
        b = self.betting
        lance = b.lance

        if b.fold_winner == "player":
            # Player bet → bot team responds
            a1 = self._bot.decide_bet_respond(self.bot1_hand, lance, b.current_bet)
            a2 = self._bot.decide_bet_respond(self.bot2_hand, lance, b.current_bet)
            bot_action = _combine_bot_team_respond(a1, a2, b.current_bet)
        elif b.fold_winner is None:
            # No open bet → bot team initiates
            a1 = self._bot.decide_bet_initiate(self.bot1_hand, lance, b.current_bet)
            a2 = self._bot.decide_bet_initiate(self.bot2_hand, lance, b.current_bet)
            bot_action = _combine_bot_team_initiate(a1, a2)
        else:
            # fold_winner == "bot" (bot team bet, player passed/re-raised) → respond
            a1 = self._bot.decide_bet_respond(self.bot1_hand, lance, b.current_bet)
            a2 = self._bot.decide_bet_respond(self.bot2_hand, lance, b.current_bet)
            bot_action = _combine_bot_team_respond(a1, a2, b.current_bet)

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
        # If there is an open bet, paso = no_quiero
        if b.fold_winner is not None:
            self._handle_no_quiero(actor)
            return
        # No open bet: if bot also passes → base prize
        if actor == "bot":
            b.stones_awarded = b.base_stones
            b.resolved = True

    def _handle_envido(self, actor: str) -> None:
        b = self.betting
        b.current_bet = b.current_bet + 1
        b.bet_history.append(b.current_bet)
        b.fold_winner = actor

    def _handle_ordago(self, actor: str) -> None:
        b = self.betting
        b.current_bet = 40
        b.bet_history.append(40)
        b.fold_winner = actor

    def _handle_quiero(self, actor: str) -> None:
        b = self.betting
        b.stones_awarded = b.current_bet
        b.resolved = True

    def _handle_no_quiero(self, actor: str) -> None:
        b = self.betting
        if b.fold_winner is not None:
            winner = b.fold_winner
        else:
            winner = "bot" if actor == "player" else "player"
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
            winner_str = b.fold_winner
            if winner_str == "player":
                lr = LanceResult(player_wins=True, bot_wins=False, is_tie=False)
            else:
                lr = LanceResult(player_wins=False, bot_wins=True, is_tie=False)
            stones = b.stones_awarded
        else:
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
        return _compare(self._team_a_eval(lance), self._team_b_eval(lance))

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
            player_team_stones_earned=player_total,
            bot_team_stones_earned=bot_total,
        )
        self.phase = GamePhase.HAND_OVER
        self.status_message = (
            f"Mano terminada. Equipo Jugador: +{player_total} | Equipo Bot: +{bot_total}"
        )
