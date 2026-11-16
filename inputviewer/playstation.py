"""Distribución del DualSense / DualShock 4. Coordenadas lógicas (ancho 270).

Los nombres de botón llegan de SDL: A = Cruz, B = Círculo, X = Cuadrado, Y = Triángulo,
VIEW = Create/Share, MENU = Options, GUIDE = PS, LB/RB = L1/R1, LT/RT = L2/R2.
"""
import math

from .draw import BLACK, WHITE

LW, PAD_H = 270, 146

# Gatillos L2/R2: trapecio curvo, más ancho abajo (vistos de frente). R2 es el espejo de L2.
_L2 = [(15, 2), (49, 2), (56, 29), (6, 29)]
_R2 = [(LW - x, y) for x, y in _L2]
_TRIG_R = [6, 6, 5, 5]
# Touchpad: rectángulo ancho con las esquinas inferiores más redondeadas
_PAD = [(96, 30), (174, 30), (174, 66), (96, 66)]
_PAD_R = [3, 3, 11, 11]


def _symbol(p, kind, cx, cy, on):
    c = BLACK if on else WHITE
    r, lw = 4.2, 1.6
    if kind == "cross":
        p.line((cx - r, cy - r), (cx + r, cy + r), c, lw)
        p.line((cx - r, cy + r), (cx + r, cy - r), c, lw)
    elif kind == "circle":
        p.circle(cx, cy, r, False, lw=lw, color=c)
    elif kind == "square":
        p.rrect(cx - r, cy - r, r * 2, r * 2, 0.5, False, lw=lw, color=c)
    elif kind == "triangle":
        a, b, d = (cx, cy - r - 0.6), (cx - r - 0.6, cy + r - 0.6), (cx + r + 0.6, cy + r - 0.6)
        p.line(a, b, c, lw), p.line(b, d, c, lw), p.line(d, a, c, lw)


def _pill(cx, cy, length, thick, angle_deg):
    """Vértices de una pastilla (rectángulo alargado) girada; se redondea con radio = thick/2."""
    a = math.radians(angle_deg)
    ux, uy = math.sin(a), -math.cos(a)  # eje largo (casi vertical)
    vx, vy = math.cos(a), math.sin(a)
    hl, ht = length / 2, thick / 2
    return [(cx + ux * s * hl + vx * t * ht, cy + uy * s * hl + vy * t * ht)
            for s, t in ((1, -1), (1, 1), (-1, 1), (-1, -1))]


def draw(p, pad):
    b = pad.buttons
    # gatillos L2/R2 (analógicos, con forma) y bumpers L1/R1
    p.analog_shape(_L2, _TRIG_R, pad.lt, "L2", 12)
    p.rrect(6, 32, 50, 13, 6, "LB" in b, "L1", 10)
    p.analog_shape(_R2, _TRIG_R, pad.rt, "R2", 12)
    p.rrect(214, 32, 50, 13, 6, "RB" in b, "R1", 10)

    # cruceta (arriba-izquierda) y botones de cara (arriba-derecha)
    p.dpad_ps(50, 82, b)
    p.circle(222, 58, 10, "Y" in b); _symbol(p, "triangle", 222, 58, "Y" in b)
    p.circle(205, 75, 10, "X" in b); _symbol(p, "square", 205, 75, "X" in b)
    p.circle(239, 75, 10, "B" in b); _symbol(p, "circle", 239, 75, "B" in b)
    p.circle(222, 92, 10, "A" in b); _symbol(p, "cross", 222, 92, "A" in b)

    # centro: touchpad, Create y Options (pastillas inclinadas) y botón PS
    p.shape(_PAD, _PAD_R, "TOUCHPAD" in b)
    p.shape(_pill(84, 44, 20, 7, -14), 3.5, "VIEW" in b, lw=1.8)
    p.shape(_pill(186, 44, 20, 7, 14), 3.5, "MENU" in b, lw=1.8)
    p.circle(135, 86, 9, "GUIDE" in b, "PS", 9)

    # sticks (abajo, juntos como en el DualSense)
    p.stick("L3", 98, 116, pad.ls, "LS" in b)
    p.stick("R3", 172, 116, pad.rs, "RS" in b)
