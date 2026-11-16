"""Primitivas de dibujo (estilo minimalista: contorno blanco, relleno al pulsar).

Todo se dibuja en coordenadas lógicas y se escala por `k` a la resolución real de la ventana.
"""
import pygame

WHITE = (240, 242, 247)
BLACK = (0, 0, 0)
FONT_NAMES = "arial,segoeui,helveticaneue,helvetica,dejavusans,liberationsans,freesans"


class Painter:
    def __init__(self):
        self.k = 1.0
        self.surf = None
        self._fonts = {}

    def begin(self, lw, lh, k, bg):
        size = (max(1, int(lw * k)), max(1, int(lh * k)))
        self.k = k
        if self.surf is None or self.surf.get_size() != size:
            self.surf = pygame.Surface(size)
        self.surf.fill(bg)

    def w(self, v):
        """Grosor de línea en píxeles (entero, mínimo 1)."""
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

    def line(self, a, b, color, lw=1.0):
        pygame.draw.line(self.surf, color, (a[0] * self.k, a[1] * self.k), (b[0] * self.k, b[1] * self.k),
                         self.w(lw))

    def dot(self, x, y, r, color):
        pygame.draw.circle(self.surf, color, (x * self.k, y * self.k), max(1, r * self.k))

    def rrect(self, x, y, w, h, r, on, label="", tsz=12, lw=2, color=WHITE):
        """Tecla/botón: contorno redondeado; relleno (y texto negro) cuando está pulsado."""
        k = self.k
        rect = pygame.Rect(x * k, y * k, w * k, h * k)
        if on:
            pygame.draw.rect(self.surf, color, rect, border_radius=int(r * k))
        pygame.draw.rect(self.surf, color, rect, width=self.w(lw), border_radius=int(r * k))
        if label:
            self.text(label, x + w / 2, y + h / 2, tsz, BLACK if on else color)
