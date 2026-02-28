from __future__ import annotations

from dataclasses import dataclass, field

from game.deck import Card


@dataclass
class Hand:
    cards: list[Card] = field(default_factory=list)

    def add_card(self, card: Card) -> None:
        self.cards.append(card)

    def clear(self) -> None:
        self.cards.clear()

    def is_full(self) -> bool:
        return len(self.cards) == 4

    def __len__(self) -> int:
        return len(self.cards)

    def __str__(self) -> str:
        return ", ".join(str(c) for c in self.cards)
