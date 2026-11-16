"""Distribución del mando Xbox Series (X|S). Coordenadas lógicas (ancho 270)."""
from .draw import BLACK, WHITE

LW, PAD_H = 270, 146  # ancho y alto de la zona del mando


def _icon_view(p, cx, cy, on):
    c = BLACK if on else WHITE
    p.rrect(cx - 4.5, cy - 3.5, 6.5, 5.5, 1, False, lw=1.2, color=c)
    p.rrect(cx - 2, cy - 1.5, 6.5, 5.5, 1, False, lw=1.2, color=c)


def _icon_menu(p, cx, cy, on):
    c = BLACK if on else WHITE
    for dy in (-3, 0, 3):
        p.line((cx - 4, cy + dy), (cx + 4, cy + dy), c, 1.5)


# Logo de Xbox (esfera con la X) como vector, para dibujarlo fiel a cualquier tamaño.
# Fuente: simple-icons (CC0).
XBOX_SVG = (
    b'<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M4.102 21.033C6.211 22.881 '
    b'8.977 24 12 24c3.026 0 5.789-1.119 7.902-2.967 1.877-1.912-4.316-8.709-7.902-11.417-3.582 2.708-9.779 '
    b'9.505-7.898 11.417zm11.16-14.406c2.5 2.961 7.484 10.313 6.076 12.912C23.002 17.48 24 14.861 24 '
    b'12.004c0-3.34-1.365-6.362-3.57-8.536 0 0-.027-.022-.082-.042-.063-.022-.152-.045-.281-.045-.592 '
    b'0-1.985.434-4.805 3.246zM3.654 3.426c-.057.02-.082.041-.086.042C1.365 5.642 0 8.664 0 12.004c0 '
    b'2.854.998 5.473 2.661 7.533-1.401-2.605 3.579-9.951 6.08-12.91-2.82-2.813-4.216-3.245-4.806-3.245-.131 '
    b'0-.223.021-.281.046v-.002zM12 3.551S9.055 1.828 6.755 1.746c-.903-.033-1.454.295-1.521.339C7.379.646 '
    b'9.659 0 11.984 0H12c2.334 0 4.605.646 6.766 2.085-.068-.046-.615-.372-1.52-.339C14.946 1.828 12 3.545 '
    b'12 3.545v.006z"/></svg>'
)


def _icon_xbox(p, cx, cy, on):
    p.svg_icon(XBOX_SVG, cx, cy, 15, BLACK if on else WHITE)


def draw(p, pad):
    b = pad.buttons
    # gatillos (analógicos) y bumpers
    p.analog_rect(6, 2, 50, 26, 8, pad.lt, "LT", 12)
    p.rrect(6, 31, 50, 14, 5, "LB" in b, "LB", 10)
    p.analog_rect(214, 2, 50, 26, 8, pad.rt, "RT", 12)
    p.rrect(214, 31, 50, 14, 5, "RB" in b, "RB", 10)

    # sticks y cruceta
    p.stick("LS", 46, 74, pad.ls, "LS" in b)
    p.dpad_dish(92, 116, b)
    p.stick("RS", 180, 114, pad.rs, "RS" in b)

    # botones de cara (Xbox: Y arriba, X izquierda, B derecha, A abajo)
    p.circle(222, 56, 10, "Y" in b, "Y", 12)
    p.circle(205, 73, 10, "X" in b, "X", 12)
    p.circle(239, 73, 10, "B" in b, "B", 12)
    p.circle(222, 90, 10, "A" in b, "A", 12)

    # centro: Guide (logo Xbox), View y Menu
    p.circle(135, 38, 12.5, "GUIDE" in b)
    _icon_xbox(p, 135, 38, "GUIDE" in b)
    p.circle(116, 62, 8, "VIEW" in b)
    _icon_view(p, 116, 62, "VIEW" in b)
    p.circle(154, 62, 8, "MENU" in b)
    _icon_menu(p, 154, 62, "MENU" in b)
