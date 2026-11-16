"""Primitivas de dibujo (estilo minimalista: contorno blanco, relleno al pulsar).

Todo se dibuja en coordenadas lógicas y se escala por `k` a la resolución real de la ventana.
"""
import io

import pygame

WHITE = (240, 242, 247)
BLACK = (0, 0, 0)
GLOW = (255, 255, 255)
FONT_NAMES = "arial,segoeui,helveticaneue,helvetica,dejavusans,liberationsans,freesans"


def rounded_poly(pts, radii, steps=8):
    """Polígono con esquinas redondeadas (curva de Bézier cuadrática en cada vértice).
    `radii` es un número o una lista con un radio por vértice."""
    n = len(pts)
    if not isinstance(radii, (list, tuple)):
        radii = [radii] * n
    out = []
    for i in range(n):
        (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[(i + 1) % n]
        d1 = max(1e-6, ((x0 - x1) ** 2 + (y0 - y1) ** 2) ** 0.5)
        d2 = max(1e-6, ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5)
        r = min(radii[i], d1 / 2, d2 / 2)
        ax, ay = x1 + (x0 - x1) / d1 * r, y1 + (y0 - y1) / d1 * r
        bx, by = x1 + (x2 - x1) / d2 * r, y1 + (y2 - y1) / d2 * r
        for s in range(steps + 1):
            t = s / steps
            out.append(((1 - t) ** 2 * ax + 2 * (1 - t) * t * x1 + t ** 2 * bx,
                        (1 - t) ** 2 * ay + 2 * (1 - t) * t * y1 + t ** 2 * by))
    return out


class Painter:
    def __init__(self):
        self.k = 1.0
        self.surf = None
        self._fonts = {}
        self._icons = {}

    def begin(self, lw, lh, k, bg):
        size = (max(1, int(lw * k)), max(1, int(lh * k)))
        self.k = k
        if self.surf is None or self.surf.get_size() != size:
            self.surf = pygame.Surface(size)
        self.surf.fill(bg)

    # ----------------------------------------------------------- utilidades
    def w(self, v):
        return max(1, int(round(v * self.k)))

    def font(self, sz):
        key = (sz, round(self.k, 2))
        if key not in self._fonts:
            self._fonts[key] = pygame.font.SysFont(FONT_NAMES, max(6, int(sz * self.k)), bold=True)
        return self._fonts[key]

    def text_width(self, s, sz):
        return self.font(sz).size(s)[0] / self.k

    def text(self, s, cx, cy, sz, color=WHITE):
        img = self.font(sz).render(s, True, color)
        self.surf.blit(img, img.get_rect(center=(cx * self.k, cy * self.k)))

    # --------------------------------------------------------------- formas
    def rrect(self, x, y, w, h, r, on, label="", tsz=12, lw=2, color=WHITE):
        k = self.k
        rect = pygame.Rect(x * k, y * k, w * k, h * k)
        if on:
            pygame.draw.rect(self.surf, color, rect, border_radius=int(r * k))
        pygame.draw.rect(self.surf, color, rect, width=self.w(lw), border_radius=int(r * k))
        if label:
            self.text(label, x + w / 2, y + h / 2, tsz, BLACK if on else color)

    def circle(self, cx, cy, r, on, label="", tsz=12, lw=2, color=WHITE):
        k = self.k
        if on:
            pygame.draw.circle(self.surf, color, (cx * k, cy * k), r * k)
        pygame.draw.circle(self.surf, color, (cx * k, cy * k), r * k, self.w(lw))
        if label:
            self.text(label, cx, cy, tsz, BLACK if on else color)

    def poly(self, pts, color):
        pygame.draw.polygon(self.surf, color, [(x * self.k, y * self.k) for x, y in pts])

    def line(self, a, b, color, lw=1.4):
        pygame.draw.line(self.surf, color, (a[0] * self.k, a[1] * self.k), (b[0] * self.k, b[1] * self.k), self.w(lw))

    def _px(self, pts):
        return [(x * self.k, y * self.k) for x, y in pts]

    def shape(self, pts, radii, on, label="", tsz=10, lw=2, color=WHITE):
        """Forma libre (polígono con esquinas redondeadas); se rellena al pulsar."""
        poly = self._px(rounded_poly(pts, radii))
        if on:
            pygame.draw.polygon(self.surf, color, poly)
        pygame.draw.polygon(self.surf, color, poly, self.w(lw))
        if label:
            xs, ys = [q[0] for q in pts], [q[1] for q in pts]
            self.text(label, (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, tsz, BLACK if on else color)

    def svg_icon(self, svg, cx, cy, size, color):
        """Dibuja un icono SVG (bytes) centrado en (cx, cy), `size` en unidades lógicas."""
        px = max(4, int(size * self.k))
        key = (id(svg), px, color)
        img = self._icons.get(key)
        if img is None:
            img = pygame.image.load_sized_svg(io.BytesIO(svg), (px, px)).convert_alpha()
            img.fill((*color, 0), special_flags=pygame.BLEND_RGB_ADD)  # negro -> color, conserva alfa
            self._icons[key] = img
        self.surf.blit(img, img.get_rect(center=(cx * self.k, cy * self.k)))

    def dpad_dish(self, cx, cy, pressed):
        """Cruceta del Xbox Series: plato circular con una cruz de cuatro brazos."""
        k = self.k
        pygame.draw.circle(self.surf, WHITE, (cx * k, cy * k), 21 * k, self.w(1.6))
        arm = [(-6, -17.5), (6, -17.5), (6, -6), (-6, -6)]  # brazo "arriba"
        rot = {"UP": lambda x, y: (x, y), "DOWN": lambda x, y: (-x, -y),
               "LEFT": lambda x, y: (y, -x), "RIGHT": lambda x, y: (-y, x)}
        for name, f in rot.items():  # el brazo pulsado se rellena
            if name in pressed:
                poly = rounded_poly([(cx + f(x, y)[0], cy + f(x, y)[1]) for x, y in arm], [3, 3, 1.5, 1.5])
                pygame.draw.polygon(self.surf, WHITE, self._px(poly))
        # contorno de la cruz completa (una sola pieza)
        h, n = 6, 17.5
        plus = [(-h, -n), (h, -n), (h, -h), (n, -h), (n, h), (h, h),
                (h, n), (-h, n), (-h, h), (-n, h), (-n, -h), (-h, -h)]
        radii = [3, 3, 1.5, 3, 3, 1.5, 3, 3, 1.5, 3, 3, 1.5]
        self.shape([(cx + x, cy + y) for x, y in plus], radii, False, lw=1.8)

    def polyline(self, pts, color, lw=1.4):
        pygame.draw.lines(self.surf, color, False, self._px(pts), self.w(lw))

    def analog_shape(self, pts, radii, value, label, tsz=12):
        """Gatillo analógico con forma libre: se rellena de abajo hacia arriba (0..1)."""
        poly = self._px(rounded_poly(pts, radii))
        xs, ys = [q[0] for q in pts], [q[1] for q in pts]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        pygame.draw.polygon(self.surf, WHITE, poly, self.w(2))
        self.text(label, cx, cy, tsz, WHITE)
        if value > 0.02:
            top, bot = min(q[1] for q in poly), max(q[1] for q in poly)
            fh = (bot - top) * min(1.0, value)
            old = self.surf.get_clip()
            self.surf.set_clip(pygame.Rect(0, bot - fh, self.surf.get_width(), fh + 1))
            pygame.draw.polygon(self.surf, WHITE, poly)
            self.text(label, cx, cy, tsz, BLACK)
            self.surf.set_clip(old)

    def analog_rect(self, x, y, w, h, r, value, label, tsz=12):
        """Gatillo analógico: se rellena de abajo hacia arriba según lo pulsado (0..1)."""
        k = self.k
        rect = pygame.Rect(x * k, y * k, w * k, h * k)
        pygame.draw.rect(self.surf, WHITE, rect, width=self.w(2), border_radius=int(r * k))
        self.text(label, x + w / 2, y + h / 2, tsz, WHITE)
        if value > 0.02:
            fh = rect.height * min(1.0, value)
            old = self.surf.get_clip()
            self.surf.set_clip(pygame.Rect(rect.x, rect.bottom - fh, rect.width, fh + 1))
            pygame.draw.rect(self.surf, WHITE, rect, border_radius=int(r * k))
            self.text(label, x + w / 2, y + h / 2, tsz, BLACK)  # texto oscuro sobre la parte rellena
            self.surf.set_clip(old)

    # ------------------------------------------------------ sticks y cruceta
    def glow(self, cx, cy, mag, inner_r=13, outer_r=30):
        """Anillo de brillo blanco alrededor del stick; más intenso cuanto más se mueve."""
        k = self.k
        R, inner = int(outer_r * k), int(inner_r * k)
        g = pygame.Surface((R * 2, R * 2), pygame.SRCALPHA)
        steps = 16
        for i in range(steps):
            r = inner + (R - inner) * (1 - i / steps)
            pygame.draw.circle(g, (*GLOW, min(255, int(mag * 55))), (R, R), int(r))
        pygame.draw.circle(g, (0, 0, 0, 0), (R, R), inner)
        self.surf.blit(g, (int(cx * k) - R, int(cy * k) - R))

    def stick(self, name, cx, cy, pos, on):
        k = self.k
        pygame.draw.circle(self.surf, WHITE, (cx * k, cy * k), 24 * k, self.w(1))
        px, py = cx + pos[0] * 10, cy - pos[1] * 10
        mag = min(1.0, (pos[0] ** 2 + pos[1] ** 2) ** 0.5)
        if mag > 0.05:
            self.glow(px, py, mag)
        self.circle(px, py, 13, on, name, 10)

    def dpad_ps(self, cx, cy, pressed):
        """Cruceta estilo DualSense: cuatro teclas separadas (anchas fuera, estrechas hacia
        el centro, esquinas exteriores redondeadas) con una flecha cerca del borde."""
        arm = [(-7.5, -22.5), (7.5, -22.5), (3.2, -7), (-3.2, -7)]  # tecla "arriba"
        radii = [4.5, 4.5, 1.2, 1.2]
        rot = {"UP": lambda x, y: (x, y), "DOWN": lambda x, y: (-x, -y),
               "LEFT": lambda x, y: (y, -x), "RIGHT": lambda x, y: (-y, x)}
        d = 2.8
        tri = [(0, -d), (-d, d), (d, d)]  # flecha hacia arriba
        for name, f in rot.items():
            on = name in pressed
            self.shape([(cx + f(x, y)[0], cy + f(x, y)[1]) for x, y in arm], radii, on, lw=1.8)
            ax, ay = f(0, -15)
            self.poly([(cx + ax + f(x, y)[0], cy + ay + f(x, y)[1]) for x, y in tri], BLACK if on else WHITE)

    def dpad(self, cx, cy, pressed):
        s = 13
        arms = {"UP": (cx - s / 2, cy - s * 1.5), "DOWN": (cx - s / 2, cy + s * .5),
                "LEFT": (cx - s * 1.5, cy - s / 2), "RIGHT": (cx + s * .5, cy - s / 2)}
        d = 2.8
        shapes = {"UP": [(0, -d), (-d, d), (d, d)], "DOWN": [(0, d), (-d, -d), (d, -d)],
                  "LEFT": [(-d, 0), (d, -d), (d, d)], "RIGHT": [(d, 0), (-d, -d), (-d, d)]}
        for name, (x, y) in arms.items():
            on = name in pressed
            self.rrect(x, y, s, s, 3, on)
            self.poly([(x + s / 2 + dx, y + s / 2 + dy) for dx, dy in shapes[name]], BLACK if on else WHITE)
