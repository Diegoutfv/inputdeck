"""Distribución del Nintendo Switch 2 Pro Controller. Coordenadas lógicas (ancho 270)."""
from .draw import WHITE

LW, PAD_H = 270, 158


def draw(p, pad):
    b = pad.buttons
    p.rrect(6, 4, 50, 20, 7, "ZL" in b, "ZL", 12)
    p.rrect(6, 27, 50, 14, 5, "L" in b, "L", 10)
    p.rrect(214, 4, 50, 20, 7, "ZR" in b, "ZR", 12)
    p.rrect(214, 27, 50, 14, 5, "R" in b, "R", 10)

    p.stick("LS", 46, 68, pad.ls, "LS" in b)
    p.dpad(90, 116, b)
    p.stick("RS", 180, 114, pad.rs, "RS" in b)

    # botones de cara (Nintendo: X arriba, Y izquierda, A derecha, B abajo)
    p.circle(222, 53, 10, "X" in b, "X", 12)
    p.circle(222, 87, 10, "B" in b, "B", 12)
    p.circle(205, 70, 10, "Y" in b, "Y", 12)
    p.circle(239, 70, 10, "A" in b, "A", 12)

    p.circle(118, 52, 8, "MINUS" in b, "−", 12)
    p.circle(152, 52, 8, "PLUS" in b, "+", 12)
    p.rrect(110, 66, 16, 16, 4, "CAPTURE" in b, "", 9)
    p.text("CAP", 118, 90, 7, WHITE)
    p.circle(152, 74, 9, "HOME" in b, "H", 10)
    p.circle(135, 98, 8, "C" in b, "C", 10)

    p.rrect(100, 140, 32, 15, 5, "GL" in b, "GL", 10)
    p.rrect(138, 140, 32, 15, 5, "GR" in b, "GR", 10)
