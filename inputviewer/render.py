"""Dibujo de un layout (teclas) y de la fila de cajitas (entradas sin tecla en el diseño)."""
from .draw import BLACK, WHITE
from .layout import CHIPS_H, MARGIN


def fit_size(p, label, w, start=11.0):
    """Tamaño de letra más grande (hasta `start`) con el que `label` cabe en una tecla de ancho w."""
    size = start
    while size > 5 and p.text_width(label, size) > w - 6:
        size -= 0.5
    return size


def draw_key(p, k, on, color=WHITE, label=None):
    label = k["label"] if label is None else label
    p.rrect(k["x"], k["y"], k["w"], k["h"], 5, on, label, fit_size(p, label, k["w"]), lw=1.6, color=color)


def draw_layout(p, layout, pressed):
    """`pressed` = conjunto de nombres de entrada activos (se compara con el bind de cada tecla)."""
    for k in layout["keys"]:
        draw_key(p, k, bool(k["bind"]) and k["bind"] in pressed)


def draw_chips(p, names, canvas_w, canvas_h):
    """Cajitas centradas en la franja inferior; solo existen mientras se pulsa algo."""
    gap, pad, kh = 4, 7, 20
    y = canvas_h - CHIPS_H + 4
    shown, total = [], 0
    for n in names:
        w = max(kh, p.text_width(n, 11) + pad * 2)
        if total + w > canvas_w - 2 * MARGIN - 2:
            break
        shown.append((n, w))
        total += w + gap
    x = (canvas_w - (total - gap)) / 2
    for n, w in shown:
        p.rrect(x, y, w, kh, 6, True, n, 11)
        x += w + gap
