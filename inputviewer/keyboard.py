"""Datos del diseño por defecto: teclado compacto de 4 filas con el ratón integrado.

Cada fila mide 9 unidades. Las posiciones se convierten en un layout en layout.builtin().
"""

UNIT = 28          # ancho de una unidad de tecla (incluye separación)
KEY_H, ROW_H = 22, 25

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
