from __future__ import annotations

from game.evaluator import HandEvaluator, JuegoResult, ParesResult, ParesType
from game.hand import Hand


class Bot:
    """Bot con heurísticas simples. Base preparada para Monte Carlo."""

    # ------------------------------------------------------------------
    # Métodos originales (usados internamente y en el evaluador legacy)
    # ------------------------------------------------------------------

    def decide(self, hand: Hand, lance: str) -> str:
        """Devuelve 'envido' o 'paso' para el lance indicado."""
        handlers = {
            "grande": self._decide_grande,
            "chica": self._decide_chica,
            "pares": self._decide_pares,
            "juego": self._decide_juego,
        }
        handler = handlers.get(lance)
        return handler(hand) if handler else "paso"

    def _decide_grande(self, hand: Hand) -> str:
        result = HandEvaluator.evaluate_grande(hand)
        high_count = sum(1 for r in result.ranks if r >= 10)
        if high_count >= 2:
            return "envido"
        if result.ranks[0] >= 11:
            return "envido"
        return "paso"

    def _decide_chica(self, hand: Hand) -> str:
        result = HandEvaluator.evaluate_chica(hand)
        if result.ranks[0] == 1 and result.ranks[1] <= 3:
            return "envido"
        if result.ranks[0] <= 2 and result.ranks[1] <= 4:
            return "envido"
        return "paso"

    def _decide_pares(self, hand: Hand) -> str:
        result = HandEvaluator.evaluate_pares(hand)
        if not result.has_pares:
            return "paso"
        if result.pares_type in (ParesType.DUPLES, ParesType.MEDIAS):
            return "envido"
        if result.comparison_key[0] >= 10:
            return "envido"
        return "paso"

    def _decide_juego(self, hand: Hand) -> str:
        result = HandEvaluator.evaluate_juego(hand)
        if result.has_juego:
            return "envido"
        if result.total >= 28:
            return "envido"
        return "paso"

    # ------------------------------------------------------------------
    # Métodos nuevos para la partida completa
    # ------------------------------------------------------------------

    def decide_mus(self, hand: Hand) -> bool:
        """True si la mano es débil y conviene pedir Mus."""
        pares = HandEvaluator.evaluate_pares(hand)
        juego = HandEvaluator.evaluate_juego(hand)
        grande = HandEvaluator.evaluate_grande(hand)

        if pares.has_pares:
            return False
        if juego.has_juego:
            return False
        # Sin pares, sin juego: pide mus si la chica alta (primera carta >= 5)
        chica = HandEvaluator.evaluate_chica(hand)
        if chica.ranks[0] >= 5:
            return True
        if grande.ranks[0] <= 5:
            return True
        return False

    def decide_discard(self, hand: Hand) -> list[int]:
        """
        Devuelve los índices de cartas a descartar.
        Prioridad: conservar pares > conservar juego > conservar chica baja.
        """
        pares = HandEvaluator.evaluate_pares(hand)
        juego = HandEvaluator.evaluate_juego(hand)

        ranks = [c.rank for c in hand.cards]

        # Si tiene duples o medias, conserva todas las que forman el grupo
        if pares.has_pares and pares.pares_type in (ParesType.DUPLES, ParesType.MEDIAS):
            from collections import Counter
            cnt = Counter(ranks)
            keep_rank = max(
                (r for r, c in cnt.items() if c >= 2),
                key=lambda r: cnt[r],
            )
            discard = [
                i for i, c in enumerate(hand.cards)
                if c.rank != keep_rank
            ]
            # Descartar máximo 4 cartas (puede ser 0-2)
            return discard[:4]

        # Si tiene pareja, conservar la pareja
        if pares.has_pares and pares.pares_type == ParesType.PAREJA:
            pair_rank = pares.comparison_key[0]
            pair_indices = [i for i, c in enumerate(hand.cards) if c.rank == pair_rank]
            non_pair = [i for i in range(4) if i not in pair_indices]
            return non_pair  # descartar las que no son la pareja

        # Si tiene juego, conservar las cartas que aportan más puntos (10, 11, 12)
        if juego.has_juego:
            from game.evaluator import JUEGO_POINT_VALUES
            indexed = sorted(enumerate(hand.cards), key=lambda x: JUEGO_POINT_VALUES[x[1].rank])
            # Conservar las 4 con más puntos → descartar las de menor valor
            # En realidad ya tiene 4 cartas, si tiene juego no descarta nada útil
            return []

        # Sin nada especial: descartar las cartas altas (conservar chica)
        chica_ranks = sorted(range(4), key=lambda i: hand.cards[i].rank)
        # Conservar las 2 más bajas, descartar las 2 más altas
        return chica_ranks[2:]

    def decide_bet_initiate(self, hand: Hand, lance: str, current_bet: int) -> str:
        """
        El bot abre la apuesta. Devuelve 'paso' | 'envido' | 'ordago'.
        Sólo ordago si la mano es muy top y la apuesta es baja.
        """
        base_action = self.decide(hand, lance)
        if base_action == "paso":
            return "paso"

        # Evalúa si la mano merece órdago
        if self._is_top_hand(hand, lance) and current_bet <= 2:
            return "ordago"
        return "envido"

    def decide_bet_respond(self, hand: Hand, lance: str, current_bet: int) -> str:
        """
        El bot responde a la apuesta del jugador.
        Devuelve 'quiero' | 'no_quiero' | 'envido' | 'ordago'.
        Nunca re-sube si current_bet >= 4.
        """
        base_action = self.decide(hand, lance)

        if base_action == "paso":
            # Mano débil: no quiero
            return "no_quiero"

        # Mano fuerte
        if self._is_top_hand(hand, lance) and current_bet <= 2:
            return "ordago"

        if current_bet >= 4:
            return "quiero"

        return "envido"

    def _is_top_hand(self, hand: Hand, lance: str) -> bool:
        """True si la mano es de las mejores posibles para el lance."""
        if lance == "grande":
            result = HandEvaluator.evaluate_grande(hand)
            return sum(1 for r in result.ranks if r >= 10) >= 3
        if lance == "chica":
            result = HandEvaluator.evaluate_chica(hand)
            return result.ranks[1] <= 2
        if lance == "pares":
            result = HandEvaluator.evaluate_pares(hand)
            return result.has_pares and result.pares_type == ParesType.DUPLES
        if lance == "juego":
            result = HandEvaluator.evaluate_juego(hand)
            return result.has_juego and result.total == 31
        return False
