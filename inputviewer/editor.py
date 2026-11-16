"""Editor de diseños: mover, redimensionar, renombrar y re-mapear teclas.

Ratón: arrastrar una tecla la mueve; el cuadradito de su esquina inferior derecha cambia su
tamaño; doble clic cambia el texto. Atajos: N nueva · B mapear · F2/Enter texto · Supr borrar ·
Ctrl+D duplicar · flechas mover (Mayús = más) · Ctrl+S guardar · Esc cancelar.

Mapear = pulsar la tecla, botón del ratón o botón de mando que quieras asignar.
"""
import copy
import time

import pygame

from . import layout as L
from .draw import BLACK, FONT_NAMES, WHITE
from .render import draw_key

ACCENT = (255, 200, 60)
GRID = (38, 42, 50)
BAR, BTN, BTN_ON, TXT, DIM = (24, 26, 32), (52, 56, 68), (96, 102, 120), (240, 242, 247), (150, 156, 168)
SNAP = 2
HANDLE = 6
BIND_TIMEOUT = 8.0
DOUBLE_CLICK = 0.35
BUTTONS = [("add", "+ Key"), ("label", "Label"), ("bind", "Bind"), ("dup", "Duplicate"),
           ("del", "Delete"), ("name", "Layout name"), ("cancel", "Cancel"), ("save", "Save")]


def _snap(v):
    return round(v / SNAP) * SNAP


class Editor:
    def __init__(self):
        self.active = False
        self._font = None
        self.bar_h = 0

    # ------------------------------------------------------------------ ciclo
    def begin(self, layout: dict, layout_id):
        self.layout = copy.deepcopy(layout)
        self.orig = copy.deepcopy(layout)
        self.id = layout_id  # None = se guardará como diseño nuevo
        x0, y0, x1, y1 = L.bounds(self.layout)
        self.canvas = (max(x1 + 70, 220.0), max(y1 + 50, 110.0))  # espacio libre para mover teclas
        self.sel = None
        self.mode = "idle"  # idle | drag | resize | text | bind
        self.rev = 0
        self.dirty = False
        self.armed = False   # primer Esc con cambios: pide confirmar
        self.msg = "Drag keys to move them · double-click to rename · B to bind a key"
        self.buf, self.target = "", None
        self.drag = None
        self.last_click = (0.0, None)
        self.bind_since = 0.0
        self.ignore = set()
        self.active = True
        pygame.key.start_text_input()

    def end(self):
        self.active = False
        pygame.key.stop_text_input()

    def _touch(self):
        self.rev += 1
        self.dirty = self.layout != self.orig
        self.armed = False

    @property
    def keys(self):
        return self.layout["keys"]

    # ----------------------------------------------------------------- barra
    def font(self):
        if self._font is None:
            self._font = pygame.font.SysFont(FONT_NAMES, 14, bold=True)
        return self._font

    def bar(self, ww):
        """Calcula los rectángulos de los botones (con salto de línea) y la altura de la barra."""
        f, x, y, rects = self.font(), 8, 8, []
        for key, label in BUTTONS:
            w = f.size(label)[0] + 18
            if x + w > ww - 8 and x > 8:
                x, y = 8, y + 32
            rects.append((pygame.Rect(x, y, w, 26), key, label))
            x += w + 6
        self.rects = rects
        self.bar_h = y + 26 + 8
        return self.bar_h

    def draw_ui(self, win):
        ww, wh = win.get_size()
        f = self.font()
        pygame.draw.rect(win, BAR, (0, 0, ww, self.bar_h))
        for r, key, label in self.rects:
            hot = (key == "bind" and self.mode == "bind") or (key == "label" and self.mode == "text")
            pygame.draw.rect(win, BTN_ON if hot else BTN, r, border_radius=6)
            win.blit(f.render(label, True, TXT), (r.x + 9, r.centery - 8))
        text = self._status()
        pygame.draw.rect(win, BAR, (0, wh - 24, ww, 24))
        win.blit(f.render(text, True, ACCENT if self.armed or self.mode in ("bind", "text") else DIM), (10, wh - 20))

    def _status(self):
        if self.mode == "bind":
            return "Press the key, mouse button or gamepad button to assign…"
        if self.mode == "text":
            return "Type the text · Enter to confirm · Esc to cancel"
        if self.armed:
            return "Unsaved changes: press Esc again to discard them"
        if self.sel is not None:
            k = self.keys[self.sel]
            return f'Selected: "{k["label"]}"  →  {k["bind"] or "(not assigned: press B)"}'
        return self.msg

    # ---------------------------------------------------------------- dibujo
    def draw(self, p):
        cw, ch = self.canvas
        for gx in range(0, int(cw) + 1, 8):
            for gy in range(0, int(ch) + 1, 8):
                p.dot(gx, gy, 0.35, GRID)
        for i, k in enumerate(self.keys):
            label = None
            if i == self.sel and self.mode == "bind":
                label = "…"
            elif i == self.sel and self.mode == "text" and self.target == "label":
                label = self.buf + "|"
            sel = i == self.sel
            draw_key(p, k, False, ACCENT if sel else WHITE, label)
            if not k["bind"] and not sel:  # sin asignar: se marca con una raya de aviso
                p.line((k["x"] + 3, k["y"] + k["h"] - 3), (k["x"] + k["w"] - 3, k["y"] + k["h"] - 3), ACCENT, 0.8)
        if self.sel is not None:
            k = self.keys[self.sel]
            p.rrect(k["x"] + k["w"] - HANDLE / 2, k["y"] + k["h"] - HANDLE / 2, HANDLE, HANDLE, 1, True, color=ACCENT)

    # ---------------------------------------------------------------- eventos
    def handle(self, e, to_logical):
        """Devuelve "save", "cancel" o None. `to_logical(pos)` convierte píxeles a coordenadas lógicas."""
        if e.type == pygame.TEXTINPUT and self.mode == "text":
            if e.text.isprintable():
                self.buf = (self.buf + e.text)[: 24 if self.target == "name" else 10]
                self.rev += 1
        elif e.type == pygame.KEYDOWN:
            return self._key(e)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            return self._down(e.pos, to_logical)
        elif e.type == pygame.MOUSEMOTION and self.mode in ("drag", "resize") and e.buttons[0]:
            self._move(to_logical(e.pos))
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1 and self.mode in ("drag", "resize"):
            self.mode, self.drag = "idle", None
            self.rev += 1
        return None

    def update(self, inputs):
        """Llamar cada fotograma con los nombres de entrada activos (para el modo mapear)."""
        if self.mode != "bind":
            return
        self.ignore &= set(inputs)  # lo que ya estaba pulsado al empezar no cuenta hasta soltarlo
        new = [n for n in inputs if n not in self.ignore]
        if new and self.sel is not None:
            k = self.keys[self.sel]
            k["bind"] = new[0]
            if k["label"] in ("", "Key"):
                k["label"] = new[0].replace("PAD:", "")[:10]
            self.mode = "idle"
            self.msg = f"Assigned: {new[0]}"
            self._touch()
        elif time.time() - self.bind_since > BIND_TIMEOUT:
            self.mode = "idle"
            self.rev += 1

    def _hit(self, pt):
        for i in range(len(self.keys) - 1, -1, -1):
            k = self.keys[i]
            if k["x"] <= pt[0] <= k["x"] + k["w"] and k["y"] <= pt[1] <= k["y"] + k["h"]:
                return i
        return None

    def _down(self, pos, to_logical):
        if pos[1] < self.bar_h:
            for r, key, _ in self.rects:
                if r.collidepoint(pos):
                    return self._do(key)
            return None
        if self.mode == "text":
            self._commit()
        if self.mode == "bind":
            return None  # un clic puede ser justo la entrada que se quiere asignar
        pt = to_logical(pos)
        if self.sel is not None:  # ¿agarra el cuadradito de tamaño?
            k = self.keys[self.sel]
            if abs(pt[0] - (k["x"] + k["w"])) <= HANDLE and abs(pt[1] - (k["y"] + k["h"])) <= HANDLE:
                self.mode, self.drag = "resize", None
                return None
        i = self._hit(pt)
        now = time.time()
        if i is None:
            self.sel = None
        else:
            if i == self.last_click[1] and now - self.last_click[0] < DOUBLE_CLICK:
                self.sel = i
                self.last_click = (0.0, None)
                return self._do("label")
            self.sel = i
            k = self.keys[i]
            self.mode, self.drag = "drag", (pt[0] - k["x"], pt[1] - k["y"])
            self.last_click = (now, i)
        self.rev += 1
        return None

    def _move(self, pt):
        if self.sel is None:
            return
        k, cw, ch = self.keys[self.sel], *self.canvas
        if self.mode == "drag" and self.drag:
            k["x"] = min(max(0, _snap(pt[0] - self.drag[0])), cw - k["w"])
            k["y"] = min(max(0, _snap(pt[1] - self.drag[1])), ch - k["h"])
        elif self.mode == "resize":
            k["w"] = min(max(8, _snap(pt[0] - k["x"])), cw - k["x"])
            k["h"] = min(max(8, _snap(pt[1] - k["y"])), ch - k["y"])
        self._touch()

    def _key(self, e):
        if self.mode == "text":
            if e.key == pygame.K_RETURN:
                self._commit()
            elif e.key == pygame.K_ESCAPE:
                self.mode = "idle"
                self.rev += 1
            elif e.key == pygame.K_BACKSPACE:
                self.buf = self.buf[:-1]
                self.rev += 1
            return None
        if self.mode == "bind":
            return None  # las teclas son lo que se quiere asignar (las recoge update())
        ctrl = bool(pygame.key.get_mods() & pygame.KMOD_CTRL)
        step = 4 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1
        if e.key == pygame.K_ESCAPE:
            return self._do("cancel")
        if ctrl and e.key == pygame.K_s:
            return self._do("save")
        if ctrl and e.key == pygame.K_d:
            return self._do("dup")
        if e.key == pygame.K_n:
            return self._do("add")
        if e.key == pygame.K_b:
            return self._do("bind")
        if e.key in (pygame.K_F2, pygame.K_RETURN):
            return self._do("label")
        if e.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
            return self._do("del")
        arrows = {pygame.K_LEFT: (-step, 0), pygame.K_RIGHT: (step, 0), pygame.K_UP: (0, -step), pygame.K_DOWN: (0, step)}
        if e.key in arrows and self.sel is not None:
            k, (dx, dy) = self.keys[self.sel], arrows[e.key]
            k["x"] = min(max(0, k["x"] + dx), self.canvas[0] - k["w"])
            k["y"] = min(max(0, k["y"] + dy), self.canvas[1] - k["h"])
            self._touch()
        return None

    # ---------------------------------------------------------------- acciones
    def _commit(self):
        if self.target == "name":
            self.layout["name"] = self.buf.strip() or "Layout"
        elif self.sel is not None:
            self.keys[self.sel]["label"] = self.buf
        self.mode = "idle"
        self._touch()

    def _free_spot(self, w=22, h=22):
        cw, ch = self.canvas
        y = 0.0
        while y + h <= ch:
            x = 0.0
            while x + w <= cw:
                if not any(x < k["x"] + k["w"] and x + w > k["x"] and y < k["y"] + k["h"] and y + h > k["y"]
                           for k in self.keys):
                    return x, y
                x += 26
            y += 26
        return 0.0, 0.0

    def _do(self, action):
        if action == "cancel":
            if self.dirty and not self.armed:
                self.armed = True
                self.rev += 1
                return None
            return "cancel"
        if action == "save":
            return "save"
        if action == "add":
            if len(self.keys) >= L.MAX_KEYS:
                self.msg = "Maximum number of keys reached"
                return None
            x, y = self._free_spot()
            self.keys.append({"label": "Key", "bind": "", "x": x, "y": y, "w": 22.0, "h": 22.0})
            self.sel = len(self.keys) - 1
            self._touch()
            return self._do("bind")  # lo normal es querer asignarla enseguida
        if action == "name":
            self.mode, self.target, self.buf = "text", "name", self.layout["name"]
            self.sel = None
            self.rev += 1
            return None
        if self.sel is None:
            self.msg = "Click a key first"
            self.rev += 1
            return None
        k = self.keys[self.sel]
        if action == "label":
            self.mode, self.target, self.buf = "text", "label", k["label"]
        elif action == "bind":
            if self.mode == "bind":  # segundo clic = cancelar
                self.mode = "idle"
            else:
                self.mode, self.bind_since = "bind", time.time()
                self.ignore = set(self._current_inputs)
        elif action == "del":
            del self.keys[self.sel]
            self.sel = None
            self._touch()
        elif action == "dup":
            c = dict(k)
            c["x"], c["y"] = min(k["x"] + 6, self.canvas[0] - k["w"]), min(k["y"] + 6, self.canvas[1] - k["h"])
            self.keys.append(c)
            self.sel = len(self.keys) - 1
            self._touch()
        self.rev += 1
        return None

    _current_inputs = ()

    def set_inputs(self, inputs):
        """Entradas activas ahora (para ignorar las que ya estaban pulsadas al empezar a mapear)."""
        self._current_inputs = tuple(inputs)
        self.update(inputs)
