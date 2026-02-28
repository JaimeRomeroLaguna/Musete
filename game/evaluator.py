from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from game.deck import RANK_NAMES
from game.hand import Hand

# Valor de puntos para el lance de Juego
JUEGO_POINT_VALUES: dict[int, int] = {
    1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7,
    10: 10, 11: 10, 12: 10,
}


class ParesType(Enum):
    PAREJA = 1   # Un par
    MEDIAS = 2   # Trío
    DUPLES = 3   # Dos pares (o póker)


# ---------------------------------------------------------------------------
# Grande
# ---------------------------------------------------------------------------

@dataclass
class GrandeResult:
    """Mano de Grande. Gana el que tiene las cartas más altas.
    ranks está ordenado de mayor a menor.
    """
    ranks: tuple[int, ...]

    def beats(self, other: GrandeResult) -> bool:
        return self.ranks > other.ranks

    def ties(self, other: GrandeResult) -> bool:
        return self.ranks == other.ranks

    def description(self) -> str:
        return ", ".join(RANK_NAMES[r] for r in self.ranks)


# ---------------------------------------------------------------------------
# Chica
# ---------------------------------------------------------------------------

@dataclass
class ChicaResult:
    """Mano de Chica. Gana el que tiene las cartas más bajas.
    ranks está ordenado de menor a mayor; la tupla menor (lexicográficamente)
    es la mano ganadora.
    """
    ranks: tuple[int, ...]

    def beats(self, other: ChicaResult) -> bool:
        return self.ranks < other.ranks

    def ties(self, other: ChicaResult) -> bool:
        return self.ranks == other.ranks

    def description(self) -> str:
        return ", ".join(RANK_NAMES[r] for r in self.ranks)


# ---------------------------------------------------------------------------
# Pares
# ---------------------------------------------------------------------------

@dataclass
class ParesResult:
    """Mano de Pares.

    Jerarquía: Duples > Medias > Pareja > Sin pares.
    Dentro de la misma categoría se compara por comparison_key (mayor gana).
    """
    has_pares: bool
    pares_type: Optional[ParesType]
    comparison_key: tuple[int, ...]

    def beats(self, other: ParesResult) -> bool:
        if not self.has_pares and not other.has_pares:
            return False
        if self.has_pares and not other.has_pares:
            return True
        if not self.has_pares and other.has_pares:
            return False
        # Ambos tienen pares
        if self.pares_type.value != other.pares_type.value:  # type: ignore[union-attr]
            return self.pares_type.value > other.pares_type.value  # type: ignore[union-attr]
        return self.comparison_key > other.comparison_key

    def ties(self, other: ParesResult) -> bool:
        if not self.has_pares and not other.has_pares:
            return True
        if self.has_pares != other.has_pares:
            return False
        return (
            self.pares_type == other.pares_type
            and self.comparison_key == other.comparison_key
        )

    def description(self) -> str:
        if not self.has_pares:
            return "Sin pares"
        if self.pares_type == ParesType.PAREJA:
            return f"Pareja de {RANK_NAMES[self.comparison_key[0]]}"
        if self.pares_type == ParesType.MEDIAS:
            return f"Medias de {RANK_NAMES[self.comparison_key[0]]}"
        if self.pares_type == ParesType.DUPLES:
            r0, r1 = self.comparison_key
            if r0 == r1:
                return f"Dobles de {RANK_NAMES[r0]}"
            return f"Duples: {RANK_NAMES[r0]} y {RANK_NAMES[r1]}"
        return "—"


# ---------------------------------------------------------------------------
# Juego
# ---------------------------------------------------------------------------

@dataclass
class JuegoResult:
    """Mano de Juego.

    Tiene juego si la suma de puntos >= 31.
    Jerarquía de juego: 31 > 32 > 40 > 39 > … > 33.
    Sin juego se juega a Punto: gana el más cercano a 31 por debajo.
    """
    has_juego: bool
    total: int

    def _juego_rank(self) -> int:
        """Menor número = mejor mano de juego."""
        if self.total == 31:
            return 0
        if self.total == 32:
            return 1
        # 40 → 2, 39 → 3, … 33 → 9
        return 42 - self.total

    def beats(self, other: JuegoResult) -> bool:
        if self.has_juego and not other.has_juego:
            return True
        if not self.has_juego and other.has_juego:
            return False
        if self.has_juego and other.has_juego:
            return self._juego_rank() < other._juego_rank()
        # Ambos a Punto: el más cercano a 31 (mayor total) gana
        return self.total > other.total

    def ties(self, other: JuegoResult) -> bool:
        if self.has_juego != other.has_juego:
            return False
        if self.has_juego:
            return self._juego_rank() == other._juego_rank()
        return self.total == other.total

    def description(self) -> str:
        if self.has_juego:
            return f"Juego ({self.total} pts)"
        return f"Punto ({self.total} pts)"


# ---------------------------------------------------------------------------
# Evaluador
# ---------------------------------------------------------------------------

class HandEvaluator:

    @staticmethod
    def evaluate_grande(hand: Hand) -> GrandeResult:
        ranks = tuple(sorted((c.rank for c in hand.cards), reverse=True))
        return GrandeResult(ranks=ranks)

    @staticmethod
    def evaluate_chica(hand: Hand) -> ChicaResult:
        ranks = tuple(sorted(c.rank for c in hand.cards))
        return ChicaResult(ranks=ranks)

    @staticmethod
    def evaluate_pares(hand: Hand) -> ParesResult:
        rank_counts: Counter[int] = Counter(c.rank for c in hand.cards)

        pairs_list: list[int] = []
        triple_rank: Optional[int] = None
        four_rank: Optional[int] = None

        for rank, count in rank_counts.items():
            if count == 4:
                four_rank = rank
            elif count == 3:
                triple_rank = rank
            elif count == 2:
                pairs_list.append(rank)

        if four_rank is not None:
            return ParesResult(
                has_pares=True,
                pares_type=ParesType.DUPLES,
                comparison_key=(four_rank, four_rank),
            )
        if len(pairs_list) == 2:
            sorted_pairs = tuple(sorted(pairs_list, reverse=True))
            return ParesResult(
                has_pares=True,
                pares_type=ParesType.DUPLES,
                comparison_key=sorted_pairs,
            )
        if triple_rank is not None:
            return ParesResult(
                has_pares=True,
                pares_type=ParesType.MEDIAS,
                comparison_key=(triple_rank,),
            )
        if len(pairs_list) == 1:
            return ParesResult(
                has_pares=True,
                pares_type=ParesType.PAREJA,
                comparison_key=(pairs_list[0],),
            )

        return ParesResult(has_pares=False, pares_type=None, comparison_key=())

    @staticmethod
    def evaluate_juego(hand: Hand) -> JuegoResult:
        total = sum(JUEGO_POINT_VALUES[c.rank] for c in hand.cards)
        return JuegoResult(has_juego=total >= 31, total=total)
