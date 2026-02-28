from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum


class Suit(Enum):
    OROS = "Oros"
    COPAS = "Copas"
    ESPADAS = "Espadas"
    BASTOS = "Bastos"


# Baraja española de 40 cartas: sin 8 ni 9
VALID_RANKS: list[int] = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]

RANK_NAMES: dict[int, str] = {
    1: "As",
    2: "Dos",
    3: "Tres",
    4: "Cuatro",
    5: "Cinco",
    6: "Seis",
    7: "Siete",
    10: "Sota",
    11: "Caballo",
    12: "Rey",
}

RANK_SHORT: dict[int, str] = {
    1: "A",
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    10: "S",
    11: "C",
    12: "R",
}

SUIT_SYMBOLS: dict[Suit, str] = {
    Suit.OROS: "⊙",
    Suit.COPAS: "♥",
    Suit.ESPADAS: "♠",
    Suit.BASTOS: "♣",
}

SUIT_COLORS: dict[Suit, str] = {
    Suit.OROS: "#B8860B",
    Suit.COPAS: "#CC2200",
    Suit.ESPADAS: "#1A1A2E",
    Suit.BASTOS: "#2A6000",
}


@dataclass(frozen=True)
class Card:
    rank: int   # 1–7, 10, 11, 12
    suit: Suit

    def display_name(self) -> str:
        return f"{RANK_NAMES[self.rank]} de {self.suit.value}"

    def short_name(self) -> str:
        return f"{RANK_SHORT[self.rank]}{self.suit.value[0]}"

    def __str__(self) -> str:
        return self.display_name()

    def __repr__(self) -> str:
        return f"Card({self.rank}, {self.suit.name})"


class Deck:
    def __init__(self) -> None:
        self._cards: list[Card] = [
            Card(rank, suit)
            for suit in Suit
            for rank in VALID_RANKS
        ]

    def shuffle(self) -> None:
        random.shuffle(self._cards)

    def deal(self, n: int) -> list[Card]:
        if len(self._cards) < n:
            raise ValueError(
                f"No hay suficientes cartas. Quedan {len(self._cards)}, se piden {n}."
            )
        dealt = self._cards[:n]
        self._cards = self._cards[n:]
        return dealt

    def add_cards(self, cards: list[Card]) -> None:
        """Devuelve cartas al mazo (p.ej. descartes) y baraja."""
        self._cards.extend(cards)
        random.shuffle(self._cards)

    @classmethod
    def all_cards(cls) -> list[Card]:
        """Devuelve todas las cartas de la baraja (sin barajar)."""
        return [Card(rank, suit) for suit in Suit for rank in VALID_RANKS]

    @property
    def remaining(self) -> int:
        return len(self._cards)

    def __len__(self) -> int:
        return self.remaining
