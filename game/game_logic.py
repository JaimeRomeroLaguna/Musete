from __future__ import annotations

from dataclasses import dataclass

from game.evaluator import (
    ChicaResult,
    GrandeResult,
    JuegoResult,
    ParesResult,
)


@dataclass
class LanceResult:
    player_wins: bool
    bot_wins: bool
    is_tie: bool

    @property
    def winner(self) -> str:
        if self.player_wins:
            return "Jugador"
        if self.bot_wins:
            return "Bot"
        return "Empate"


@dataclass
class RoundEvaluation:
    grande: tuple[GrandeResult, GrandeResult, LanceResult]
    chica: tuple[ChicaResult, ChicaResult, LanceResult]
    pares: tuple[ParesResult, ParesResult, LanceResult]
    juego: tuple[JuegoResult, JuegoResult, LanceResult]
