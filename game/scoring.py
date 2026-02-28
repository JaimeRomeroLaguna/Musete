from __future__ import annotations

from game.evaluator import JuegoResult, ParesResult, ParesType


def pares_is_playable(p_pares: ParesResult, b_pares: ParesResult) -> bool:
    """El lance de Pares sólo se juega si al menos uno tiene pares."""
    return p_pares.has_pares or b_pares.has_pares


def pares_base_value(winner: ParesResult) -> int:
    """Pareja=1, Medias=2, Duples=3."""
    if winner.pares_type == ParesType.PAREJA:
        return 1
    if winner.pares_type == ParesType.MEDIAS:
        return 2
    return 3  # DUPLES


def juego_base_value(p_juego: JuegoResult, b_juego: JuegoResult) -> int:
    """31→3, otro juego→2, Punto→1."""
    winner = p_juego if p_juego.beats(b_juego) else b_juego
    if not winner.has_juego:
        return 1   # Punto
    if winner.total == 31:
        return 3
    return 2


def base_stones_for_lance(
    lance: str,
    p_pares: ParesResult,
    b_pares: ParesResult,
    p_juego: JuegoResult,
    b_juego: JuegoResult,
) -> int:
    """Devuelve las piedras base apostadas en un lance sin betting extra."""
    if lance in ("grande", "chica"):
        return 1
    if lance == "pares":
        # Busca al ganador de pares para calcular valor base
        if p_pares.beats(b_pares):
            return pares_base_value(p_pares)
        if b_pares.beats(p_pares):
            return pares_base_value(b_pares)
        # Empate: usar el valor de cualquiera (mismo tipo)
        if p_pares.has_pares:
            return pares_base_value(p_pares)
        return 1
    if lance == "juego":
        return juego_base_value(p_juego, b_juego)
    return 1
