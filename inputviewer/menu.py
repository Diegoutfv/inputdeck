"""Menú contextual (clic derecho) para elegir la distribución. Dibujado con pygame sobre la ventana."""
import pygame

from .draw import FONT_NAMES

ITEMS = [
    ("auto", "Auto (connected controller)"),
    ("xbox", "Xbox Series"),
    ("playstation", "PlayStation / DualSense"),
    ("switch2", "Switch 2 Pro Controller"),
]
BG, BORDER, HOVER, TEXT, DIM = (28, 30, 36), (96, 102, 116), (62, 66, 80), (240, 242, 247), (150, 156, 168)
PAD_X, PAD_Y, ROW_H, HEAD_H = 14, 6, 28, 26


class ContextMenu:
    def __init__(self):
        self.open = False
        self.pos = (0, 0)
        self.hover = None
        self._font = None

    def font(self):
        if self._font is None:
            self._font = pygame.font.SysFont(FONT_NAMES, 15, bold=True)
        return self._font

    def show(self, pos):
        self.open, self.pos, self.hover = True, pos, None

    def hide(self):
        self.open, self.hover = False, None

    def _geometry(self, win_size):
        f = self.font()
        w = max(f.size(t)[0] for _, t in ITEMS) + PAD_X * 2 + 22
        h = HEAD_H + ROW_H * len(ITEMS) + PAD_Y
        x = max(0, min(self.pos[0], win_size[0] - w))
        y = max(0, min(self.pos[1], win_size[1] - h))
        rows = [pygame.Rect(x, y + HEAD_H + i * ROW_H, w, ROW_H) for i in range(len(ITEMS))]
        return pygame.Rect(x, y, w, h), rows

    def item_at(self, pos, win_size):
        _, rows = self._geometry(win_size)
        for (key, _), r in zip(ITEMS, rows):
            if r.collidepoint(pos):
                return key
        return None

    def contains(self, pos, win_size):
        return self._geometry(win_size)[0].collidepoint(pos)

    def draw(self, surf, current):
        box, rows = self._geometry(surf.get_size())
        f = self.font()
        pygame.draw.rect(surf, BG, box, border_radius=8)
        pygame.draw.rect(surf, BORDER, box, 1, border_radius=8)
        head = f.render("Layout", True, DIM)
        surf.blit(head, (box.x + PAD_X, box.y + 6))
        for (key, label), r in zip(ITEMS, rows):
            if key == self.hover:
                pygame.draw.rect(surf, HOVER, r.inflate(-8, -2), border_radius=5)
            if key == current:  # punto de selección
                pygame.draw.circle(surf, TEXT, (r.x + PAD_X - 2, r.centery), 3)
            img = f.render(label, True, TEXT)
            surf.blit(img, (r.x + PAD_X + 10, r.centery - img.get_height() // 2))
