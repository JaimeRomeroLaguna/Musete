from __future__ import annotations

from game.mus_round import MusRound
from game.state import GamePhase, HandResult

TARGET_SCORE = 40


class MusGame:
    """Sesión de juego multi-mano con marcador acumulado."""

    def __init__(self) -> None:
        self.player_team_score: int = 0
        self.bot_team_score: int = 0
        self.round: MusRound = self._make_idle_round()
        self.is_game_over: bool = False
        self.winner: str = ""

    @staticmethod
    def _make_idle_round() -> MusRound:
        r = MusRound()
        r.phase = GamePhase.IDLE
        r.status_message = "Pulsa «NUEVA PARTIDA» para empezar."
        return r

    def new_game(self) -> None:
        """Reset completo: marcador + nueva mano."""
        self.player_team_score = 0
        self.bot_team_score = 0
        self.is_game_over = False
        self.winner = ""
        self.round = MusRound()

    def start_hand(self) -> None:
        """Nueva mano sin resetear los marcadores."""
        self.round = MusRound()

    def apply_round_result(self, result: HandResult) -> None:
        """Acumula piedras al marcador y detecta si hay ganador."""
        self.player_team_score += result.player_team_stones_earned
        self.bot_team_score += result.bot_team_stones_earned

        if self.player_team_score >= TARGET_SCORE:
            self.is_game_over = True
            self.winner = "Equipo Jugador"
            self.round.phase = GamePhase.GAME_OVER
        elif self.bot_team_score >= TARGET_SCORE:
            self.is_game_over = True
            self.winner = "Equipo Bot"
            self.round.phase = GamePhase.GAME_OVER
