"""Menú contextual (clic derecho) con filas dinámicas, dibujado con pygame sobre la ventana.

Una fila es (clave, texto, marcada). Clave None = cabecera (texto) o separador (texto "-").
"""
import pygame

from .draw import FONT_NAMES

BG, BORDER, HOVER, TEXT, DIM = (28, 30, 36), (96, 102, 116), (62, 66, 80), (240, 242, 247), (150, 156, 168)
PAD_X, ROW_H, HEAD_H, SEP_H = 14, 28, 26, 9


class ContextMenu:
    def __init__(self):
        self.open = False
        self.pos = (0, 0)
        self.items = []
        self.hover = None
        self._font = None

    def font(self):
        if self._font is None:
            self._font = pygame.font.SysFont(FONT_NAMES, 15, bold=True)
        return self._font

    def show(self, pos, items):
        self.open, self.pos, self.items, self.hover = True, pos, items, None

    def hide(self):
        self.open, self.hover = False, None

    def _row_h(self, key, label):
        if key is None:
            return SEP_H if label == "-" else HEAD_H
        return ROW_H

    def _geometry(self, win_size):
        f = self.font()
        w = max([f.size(t)[0] for _, t, _ in self.items if t != "-"] + [120]) + PAD_X * 2 + 22
        h = sum(self._row_h(k, t) for k, t, _ in self.items) + 6
        x = max(0, min(self.pos[0], win_size[0] - w))
        y = max(0, min(self.pos[1], win_size[1] - h))
        rows, cy = [], y + 3
        for k, t, _ in self.items:
            rh = self._row_h(k, t)
            rows.append(pygame.Rect(x, cy, w, rh))
            cy += rh
        return pygame.Rect(x, y, w, h), rows

    def item_at(self, pos, win_size):
        _, rows = self._geometry(win_size)
        for (key, _, _), r in zip(self.items, rows):
            if key is not None and r.collidepoint(pos):
                return key
        return None

    def draw(self, surf):
        box, rows = self._geometry(surf.get_size())
        f = self.font()
        pygame.draw.rect(surf, BG, box, border_radius=8)
        pygame.draw.rect(surf, BORDER, box, 1, border_radius=8)
        for (key, label, checked), r in zip(self.items, rows):
            if key is None:
                if label == "-":
                    pygame.draw.line(surf, BORDER, (r.x + 8, r.centery), (r.right - 8, r.centery))
                else:
                    surf.blit(f.render(label, True, DIM), (r.x + PAD_X, r.centery - 8))
                continue
            if key == self.hover:
                pygame.draw.rect(surf, HOVER, r.inflate(-8, -2), border_radius=5)
            if checked:
                pygame.draw.circle(surf, TEXT, (r.x + PAD_X - 2, r.centery), 3)
            img = f.render(label, True, TEXT)
            surf.blit(img, (r.x + PAD_X + 10, r.centery - img.get_height() // 2))
