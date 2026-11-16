"""Convierte el estado de un mando en una lista de nombres de botón (cajitas, como las teclas).

Solo aparece lo que se está pulsando. Los sticks se muestran como flechas cuando se inclinan.
"""
from .gamepad import PadState

_DPAD = {"UP": "D↑", "DOWN": "D↓", "LEFT": "D←", "RIGHT": "D→", "LS": "L3", "RS": "R3"}

# nombre interno del botón -> texto de la cajita, por familia de mando
NAMES = {
    "xbox": {"A": "A", "B": "B", "X": "X", "Y": "Y", "LB": "LB", "RB": "RB", "VIEW": "View",
             "MENU": "Menu", "GUIDE": "Xbox", "SHARE": "Share", **_DPAD},
    "playstation": {"A": "Cross", "B": "Circle", "X": "Square", "Y": "Triangle", "LB": "L1",
                    "RB": "R1", "VIEW": "Create", "MENU": "Options", "GUIDE": "PS",
                    "TOUCHPAD": "Touchpad", **_DPAD},
    "switch2": {"A": "A", "B": "B", "X": "X", "Y": "Y", "L": "L", "R": "R", "ZL": "ZL", "ZR": "ZR",
                "PLUS": "+", "MINUS": "−", "HOME": "Home", "CAPTURE": "Capture", "C": "C",
                "GL": "GL", "GR": "GR", **_DPAD},
}
TRIGGERS = {"xbox": ("LT", "RT"), "playstation": ("L2", "R2")}  # gatillos analógicos
ORDER = ["A", "B", "X", "Y", "LB", "RB", "L", "R", "ZL", "ZR", "UP", "DOWN", "LEFT", "RIGHT",
         "VIEW", "MENU", "PLUS", "MINUS", "GUIDE", "HOME", "SHARE", "CAPTURE", "TOUCHPAD", "C",
         "GL", "GR", "LS", "RS"]
TRIGGER_AT = 0.3   # a partir de cuánto se considera pulsado un gatillo analógico
STICK_AT = 0.5     # a partir de cuánto se considera inclinado un stick


def _stick(prefix, pos):
    x, y = pos
    out = []
    if y > STICK_AT:
        out.append(prefix + "↑")
    if y < -STICK_AT:
        out.append(prefix + "↓")
    if x < -STICK_AT:
        out.append(prefix + "←")
    if x > STICK_AT:
        out.append(prefix + "→")
    return out


def pad_chips(pad: PadState) -> tuple:
    if not pad.connected:
        return ()
    names = NAMES.get(pad.kind, NAMES["xbox"])
    out = [names[b] for b in sorted(pad.buttons, key=lambda b: ORDER.index(b) if b in ORDER else 99)
           if b in names]
    if pad.kind in TRIGGERS:
        lt, rt = TRIGGERS[pad.kind]
        if pad.lt > TRIGGER_AT:
            out.append(lt)
        if pad.rt > TRIGGER_AT:
            out.append(rt)
    out += _stick("LS", pad.ls) + _stick("RS", pad.rs)
    return tuple(out)
