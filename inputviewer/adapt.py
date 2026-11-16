"""Adapta el estado de un mando a la distribución elegida, aunque sean de familias distintas.

Xbox y PlayStation comparten nombres (SDL). El Switch 2 usa los suyos (ZL/ZR, PLUS/MINUS...).
Los botones de cara se convierten POR POSICIÓN física: el de abajo de un mando es el de abajo
del otro (A Xbox = B Nintendo = Cruz PlayStation), para que lo que se ilumine sea lo que pulsas.
"""
from dataclasses import replace

from .gamepad import PadState

SDL_FAMILY = ("xbox", "playstation")

# SDL (Xbox/PlayStation) -> Switch 2, por posición
_SDL_TO_SW2 = {"A": "B", "B": "A", "X": "Y", "Y": "X", "LB": "L", "RB": "R", "VIEW": "MINUS",
               "MENU": "PLUS", "GUIDE": "HOME", "SHARE": "CAPTURE", "LS": "LS", "RS": "RS",
               "UP": "UP", "DOWN": "DOWN", "LEFT": "LEFT", "RIGHT": "RIGHT"}
_SW2_TO_SDL = {"B": "A", "A": "B", "Y": "X", "X": "Y", "L": "LB", "R": "RB", "MINUS": "VIEW",
               "PLUS": "MENU", "HOME": "GUIDE", "CAPTURE": "SHARE", "LS": "LS", "RS": "RS",
               "UP": "UP", "DOWN": "DOWN", "LEFT": "LEFT", "RIGHT": "RIGHT"}


def adapt(pad: PadState, target: str) -> PadState:
    if not pad.connected or pad.kind == target:
        return pad
    if pad.kind in SDL_FAMILY and target in SDL_FAMILY:
        return replace(pad, kind=target)
    if pad.kind in SDL_FAMILY and target == "switch2":
        b = {_SDL_TO_SW2[n] for n in pad.buttons if n in _SDL_TO_SW2}
        if pad.lt > 0.5:
            b.add("ZL")
        if pad.rt > 0.5:
            b.add("ZR")
        return replace(pad, kind="switch2", buttons=frozenset(b))
    if pad.kind == "switch2" and target in SDL_FAMILY:
        b = {_SW2_TO_SDL[n] for n in pad.buttons if n in _SW2_TO_SDL}
        return replace(pad, kind=target, buttons=frozenset(b),
                       lt=1.0 if "ZL" in pad.buttons else 0.0, rt=1.0 if "ZR" in pad.buttons else 0.0)
    return pad
