"""Backend de mando multiplataforma basado en SDL GameController (Windows / macOS / Linux).

Cualquier mando con mapeo SDL (Xbox, PlayStation, Switch Pro 1...) llega aquí con los mismos
nombres de botón. Más adelante se pueden añadir otros backends (p. ej. Switch 2 Pro Controller
por USB) que devuelvan el mismo PadState.
"""
import math
import time
from dataclasses import dataclass

import pygame
from pygame._sdl2 import controller as sdl

# Nombre lógico -> botón SDL
BUTTONS = {
    "A": pygame.CONTROLLER_BUTTON_A,
    "B": pygame.CONTROLLER_BUTTON_B,
    "X": pygame.CONTROLLER_BUTTON_X,
    "Y": pygame.CONTROLLER_BUTTON_Y,
    "VIEW": pygame.CONTROLLER_BUTTON_BACK,
    "MENU": pygame.CONTROLLER_BUTTON_START,
    "GUIDE": pygame.CONTROLLER_BUTTON_GUIDE,
    "LS": pygame.CONTROLLER_BUTTON_LEFTSTICK,
    "RS": pygame.CONTROLLER_BUTTON_RIGHTSTICK,
    "LB": pygame.CONTROLLER_BUTTON_LEFTSHOULDER,
    "RB": pygame.CONTROLLER_BUTTON_RIGHTSHOULDER,
    "UP": pygame.CONTROLLER_BUTTON_DPAD_UP,
    "DOWN": pygame.CONTROLLER_BUTTON_DPAD_DOWN,
    "LEFT": pygame.CONTROLLER_BUTTON_DPAD_LEFT,
    "RIGHT": pygame.CONTROLLER_BUTTON_DPAD_RIGHT,
    "SHARE": 15,      # SDL_CONTROLLER_BUTTON_MISC1 (Compartir del Xbox Series / Mute del DualSense)
    "TOUCHPAD": 20,   # SDL_CONTROLLER_BUTTON_TOUCHPAD (clic del touchpad del DualSense)
}
DEADZONE = 0.10


@dataclass(frozen=True)
class PadState:
    connected: bool = False
    name: str = ""
    buttons: frozenset = frozenset()
    lt: float = 0.0
    rt: float = 0.0
    ls: tuple = (0.0, 0.0)  # (x, y) con y positivo = arriba
    rs: tuple = (0.0, 0.0)
    kind: str = "xbox"      # distribución a usar: "xbox" | "playstation" | "switch2"


def kind_from_name(name: str) -> str:
    n = name.lower()
    if any(s in n for s in ("ps5", "ps4", "ps3", "dualsense", "dualshock", "playstation", "wireless controller")):
        return "playstation"
    return "xbox"


def _stick(x, y):
    x, y = x / 32767.0, -y / 32767.0
    mag = math.hypot(x, y)
    if mag < DEADZONE:
        return (0.0, 0.0)
    scale = min(1.0, (mag - DEADZONE) / (1 - DEADZONE)) / mag  # deadzone radial
    return (round(x * scale, 3), round(y * scale, 3))


class SDLGamepad:
    def __init__(self):
        sdl.init()
        self.pad = None
        self._last_scan = 0.0

    def _open(self):
        for i in range(sdl.get_count()):
            if sdl.is_controller(i):
                try:
                    self.pad = sdl.Controller(i)
                    return
                except Exception:
                    pass

    def poll(self) -> PadState:
        if self.pad is not None:
            try:
                if not self.pad.attached():
                    self.pad = None
            except Exception:
                self.pad = None
        if self.pad is None:
            now = time.time()
            if now - self._last_scan > 1.0:  # reintenta cada segundo (hotplug)
                self._last_scan = now
                self._open()
            if self.pad is None:
                return PadState()
        p = self.pad
        pressed = set()
        for name, code in BUTTONS.items():
            try:
                if p.get_button(code):
                    pressed.add(name)
            except Exception:
                pass
        ax = p.get_axis
        return PadState(
            connected=True,
            name=p.name,
            kind=kind_from_name(p.name),
            buttons=frozenset(pressed),
            lt=round(max(0, ax(pygame.CONTROLLER_AXIS_TRIGGERLEFT)) / 32767.0, 2),
            rt=round(max(0, ax(pygame.CONTROLLER_AXIS_TRIGGERRIGHT)) / 32767.0, 2),
            ls=_stick(ax(pygame.CONTROLLER_AXIS_LEFTX), ax(pygame.CONTROLLER_AXIS_LEFTY)),
            rs=_stick(ax(pygame.CONTROLLER_AXIS_RIGHTX), ax(pygame.CONTROLLER_AXIS_RIGHTY)),
        )
