from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from game.game_logic import LanceResult


class GamePhase(Enum):
    IDLE = auto()
    MUS_DECISION = auto()
    DISCARDING = auto()
    BETTING = auto()
    LANCE_RESULT = auto()
    HAND_OVER = auto()
    GAME_OVER = auto()


@dataclass
class BettingState:
    lance: str
    base_stones: int
    current_bet: int
    bet_history: list[int] = field(default_factory=list)
    whose_turn: str = "player"          # "player" | "bot"
    bot_last_action: Optional[str] = None
    resolved: bool = False
    fold_winner: Optional[str] = None   # quién apostó último (gana si el otro se echa)
    stones_awarded: int = 0
    was_fold: bool = False              # True si terminó con no_quiero (alguien se echó)


@dataclass
class HandResult:
    lance_results: dict[str, LanceResult]
    player_team_stones_earned: int
    bot_team_stones_earned: int
