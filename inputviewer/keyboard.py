"""Teclado compacto + ratón (cuadrícula de 4 filas). Coordenadas lógicas.

Cada tecla se ilumina al pulsarla. Todo lo que se pulse y NO esté en la cuadrícula (números,
F1-F12, flechas, botones de mando...) aparece en una franja de cajitas debajo, solo mientras
se pulsa.
"""

UNIT = 28          # ancho de una unidad de tecla (incluye separación)
KEY_H, ROW_H = 22, 25
COLS = 9           # cada fila mide 9 unidades
LW = COLS * UNIT + 4
GRID_H = 4 * ROW_H
CHIPS_Y = GRID_H + 4
LH = CHIPS_Y + 24

# (nombre que llega de keys.py, texto en la tecla, ancho en unidades)
ROWS = [
    [("TAB", "Tab", 1.5), ("Q", "Q", 1), ("W", "W", 1), ("E", "E", 1), ("R", "R", 1), ("T", "T", 1),
     ("BACK", "←", 1), ("DEL", "Delete", 1.5)],
    [("CAPS", "Caps", 1.5), ("A", "A", 1), ("S", "S", 1), ("D", "D", 1), ("F", "F", 1), ("G", "G", 1),
     ("ENTER", "Enter", 2.5)],
    [("LShift", "LShift", 1.6), ("Z", "Z", 1), ("X", "X", 1), ("C", "C", 1), ("V", "V", 1),
     ("RShift", "RShift", 1.4), ("ScrollU", "ScrollU", 1), ("ScrollD", "ScrollD", 1)],
    [("LCtrl", "LCtrl", 1.2), ("LAlt", "LAlt", 1), ("SPACE", "Space", 3.8), ("M4", "M4", 1),
     ("LMB", "LMB", 1), ("RMB", "RMB", 1)],
]
GRID_NAMES = {name for row in ROWS for name, _, _ in row}


def draw(p, pressed):
    """Dibuja la cuadrícula con las teclas de `pressed` iluminadas."""
    for r, row in enumerate(ROWS):
        x = 2
        for name, label, units in row:
            w = units * UNIT - 4  # 4 unidades de separación entre teclas
            size = 11
            while size > 5 and p.text_width(label, size) > w - 6:  # que el texto quepa en la tecla
                size -= 0.5
            p.rrect(x, r * ROW_H + 1, w, KEY_H, 5, name in pressed, label, size, lw=1.6)
            x += units * UNIT
