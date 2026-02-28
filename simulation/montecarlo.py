from __future__ import annotations

import random
from dataclasses import dataclass, field

from game.deck import Deck
from game.evaluator import HandEvaluator
from game.hand import Hand


@dataclass
class SimulationResult:
    n_simulations: int
    player_wins: dict[str, int] = field(default_factory=dict)
    bot_wins: dict[str, int] = field(default_factory=dict)
    ties: dict[str, int] = field(default_factory=dict)

    def win_rate(self, lance: str, side: str = "player") -> float:
        if self.n_simulations == 0:
            return 0.0
        wins = (
            self.player_wins.get(lance, 0)
            if side == "player"
            else self.bot_wins.get(lance, 0)
        )
        return wins / self.n_simulations


class MonteCarloSimulator:
    """Simulador Monte Carlo.

    Dado la mano conocida del jugador, muestrea manos aleatorias del bot
    del mazo restante para estimar probabilidades de victoria por lance.
    Listo para integrar en la UI cuando se requiera.
    """

    LANCES = ("grande", "chica", "pares", "juego")

    def __init__(self, n_simulations: int = 1000) -> None:
        self.n_simulations = n_simulations

    def simulate(self, player_hand: Hand) -> SimulationResult:
        result = SimulationResult(
            n_simulations=self.n_simulations,
            player_wins={l: 0 for l in self.LANCES},
            bot_wins={l: 0 for l in self.LANCES},
            ties={l: 0 for l in self.LANCES},
        )

        all_cards = Deck.all_cards()
        player_card_set = set(player_hand.cards)
        remaining_pool = [c for c in all_cards if c not in player_card_set]

        evaluators = {
            "grande": (HandEvaluator.evaluate_grande, HandEvaluator.evaluate_grande),
            "chica": (HandEvaluator.evaluate_chica, HandEvaluator.evaluate_chica),
            "pares": (HandEvaluator.evaluate_pares, HandEvaluator.evaluate_pares),
            "juego": (HandEvaluator.evaluate_juego, HandEvaluator.evaluate_juego),
        }

        p_evals = {
            lance: fn(player_hand)
            for lance, (fn, _) in evaluators.items()
        }

        for _ in range(self.n_simulations):
            bot_cards = random.sample(remaining_pool, 4)
            bot_hand = Hand(cards=bot_cards)

            for lance, (_, bot_fn) in evaluators.items():
                p_eval = p_evals[lance]
                b_eval = bot_fn(bot_hand)

                if p_eval.beats(b_eval):
                    result.player_wins[lance] += 1
                elif b_eval.beats(p_eval):
                    result.bot_wins[lance] += 1
                else:
                    result.ties[lance] += 1

        return result
