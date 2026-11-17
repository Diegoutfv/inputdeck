"""Ventana principal: teclado + ratón con diseños editables; los mandos aparecen como cajitas.

Clic derecho = menú (diseños: elegir / editar / crear / duplicar / borrar; fondo verde o negro).
Opciones de prueba:  --screenshot ruta.png   --demo   --edit-demo   --open-menu
"""
import os
import subprocess
import sys
import time

# Sin esto, SDL ignora el mando mientras la ventana no tiene el foco (siempre el caso en OBS).
os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")

import pygame

from . import chips, config, keys, switch2_usb
from . import layout as L
from .draw import FONT_NAMES, Painter
from .editor import Editor
from .gamepad import PadState, SDLGamepad
from .menu import ContextMenu
from .render import draw_chips, draw_layout

GREEN = (0, 177, 64)   # chroma key para OBS
EDIT_BG = (16, 18, 22)
AA = 2                 # supersampling
TOAST_SECONDS = 2.5


def _demo():
    pad = PadState(connected=True, name="demo", kind="playstation", rt=1.0, ls=(-0.8, 0.1),
                   buttons=frozenset({"A", "LB"}))
    return ("W", "LShift", "SPACE", "LMB", "1", "F2"), chips.pad_chips(pad)


def open_folder(path):
    path.mkdir(parents=True, exist_ok=True)
    try:
        if sys.platform == "win32":
            os.startfile(path)  # noqa: S606 - carpeta propia de la app
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        pass


def draw_dialog(win, font, text):
    ww, wh = win.get_size()
    lines = [text, "Enter = yes   ·   Esc = no"]
    w = max(font.size(t)[0] for t in lines) + 40
    box = pygame.Rect((ww - w) // 2, wh // 2 - 36, w, 72)
    pygame.draw.rect(win, (28, 30, 36), box, border_radius=10)
    pygame.draw.rect(win, (255, 200, 60), box, 2, border_radius=10)
    for i, t in enumerate(lines):
        img = font.render(t, True, (240, 242, 247) if i == 0 else (150, 156, 168))
        win.blit(img, img.get_rect(center=(box.centerx, box.y + 24 + i * 26)))


def main():
    argv = sys.argv
    shot = argv[argv.index("--screenshot") + 1] if "--screenshot" in argv else None
    demo = "--demo" in argv

    pygame.init()
    pygame.display.set_caption("InputDeck")
    win = pygame.display.set_mode((800, 569), pygame.RESIZABLE)
    painter = Painter()
    sdl_pad = SDLGamepad()
    sw2_pad = switch2_usb.Switch2Gamepad() if not demo else None
    keys.start()
    ui_font = pygame.font.SysFont(FONT_NAMES, 16, bold=True)

    # ----------------------------------------------------------- estado
    cfg = config.load()
    layout_id = cfg.get("layout", L.BUILTIN)
    layout = L.load(layout_id)
    if layout is None:
        layout_id, layout = L.BUILTIN, L.builtin()
    L.normalize(layout)
    layout_ver = 0
    editor, menu = Editor(), ContextMenu()
    bg_green = cfg.get("background", "green") != "black" and shot is None  # fondo preferido (chroma key)
    confirm = None                # ("delete", id) mientras se espera sí/no
    toast, toast_until = "", 0.0

    def set_layout(new_id):
        nonlocal layout_id, layout, layout_ver
        lay = L.load(new_id)
        if lay is None:
            return
        layout_id, layout = new_id, L.normalize(lay)
        layout_ver += 1
        config.save({**config.load(), "layout": layout_id})

    def say(msg):
        nonlocal toast, toast_until
        toast, toast_until = msg, time.time() + TOAST_SECONDS

    def begin_edit(base, base_id):
        editor.begin(base, base_id)

    def menu_items():
        items = [(None, "Layout", False)]
        items += [(f"layout:{i}", n, i == layout_id) for i, n in L.list_layouts()]
        items += [(None, "-", False),
                  ("edit", "Edit this layout" if layout_id != L.BUILTIN else "Edit (saves as a copy)", False),
                  ("new", "New blank layout", False), ("dup", "Duplicate this layout", False)]
        if layout_id != L.BUILTIN:
            items.append(("del", "Delete this layout…", False))
        items += [(None, "-", False), ("folder", "Open layouts folder", False),
                  (None, "-", False), (None, "Background", False),
                  ("bg:green", "Green (chroma key)", bg_green), ("bg:black", "Black", not bg_green)]
        return items

    def do_menu(key):
        nonlocal confirm, bg_green
        if key.startswith("bg:"):
            bg_green = key == "bg:green"
            config.save({**config.load(), "background": "green" if bg_green else "black"})
        elif key.startswith("layout:"):
            set_layout(key[7:])
        elif key == "edit":
            if layout_id == L.BUILTIN:
                base = L.builtin()
                base["name"] = L.unique_name("My layout")
                begin_edit(base, None)
            else:
                begin_edit(layout, layout_id)
        elif key == "new":
            begin_edit({"schema": L.SCHEMA, "name": L.unique_name("New layout"), "keys": []}, None)
        elif key == "dup":
            copy = {**layout, "name": L.unique_name(layout["name"] + " copy"), "keys": [dict(k) for k in layout["keys"]]}
            set_layout(L.save(copy))
            say("Duplicated")
        elif key == "del":
            confirm = ("delete", layout_id)
        elif key == "folder":
            open_folder(L.folder())

    def finish_edit(save):
        if save:
            lay = L.validate(L.normalize(editor.layout))
            if lay is None:
                say("Could not save this layout")
            else:
                set_layout(L.save(lay, editor.id))
                say("Saved")
        editor.end()

    if "--edit-demo" in argv:
        begin_edit(L.builtin(), None)
        editor.sel = 2

    if "--open-menu" in argv:
        menu.show((60, 60), menu_items())
        menu.hover = "edit"

    last_key, scaled = None, pygame.Surface((1, 1))
    clock = pygame.time.Clock()
    t0 = time.time()
    running = True
    while running:
        ww, wh = win.get_size()
        editing = editor.active
        if editing:
            cw, ch = editor.canvas
            top, bottom = editor.bar(ww), 24
        else:
            cw, ch = L.canvas_size(layout)
            top = bottom = 0
        view = pygame.Rect(0, top, ww, max(1, wh - top - bottom))
        fit = max(0.2, min(view.w / cw, view.h / ch))
        ox, oy = view.x + (view.w - cw * fit) / 2, view.y + (view.h - ch * fit) / 2

        def to_logical(pos):
            return ((pos[0] - ox) / fit, (pos[1] - oy) / fit)

        # ------------------------------------------------------- eventos
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif confirm:
                if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_y):
                    if L.delete(confirm[1]):
                        set_layout(L.BUILTIN)
                        say("Deleted")
                    confirm = None
                elif e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_n):
                    confirm = None
            elif editing:
                res = editor.handle(e, to_logical)
                if res:
                    finish_edit(res == "save")
                    editing = editor.active
            else:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    menu.hide()
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                    menu.show(e.pos, menu_items())
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and menu.open:
                    picked = menu.item_at(e.pos, win.get_size())
                    menu.hide()
                    if picked:
                        do_menu(picked)
                elif e.type == pygame.MOUSEMOTION and menu.open:
                    menu.hover = menu.item_at(e.pos, win.get_size())
        if editing and not editor.active:   # se acaba de salir del editor en este fotograma
            continue

        # ------------------------------------------------------- entradas
        if demo:
            kn, pad_names = _demo()
        else:
            kn = keys.active_keys()
            pad = sw2_pad.poll()  # Switch 2 (USB propio) y si no, cualquier mando SDL
            if not pad.connected:
                pad = sdl_pad.poll()
            pad_names = chips.pad_chips(pad)
        inputs = kn + tuple("PAD:" + n for n in pad_names)
        if editing:
            editor.set_inputs(inputs)

        # ------------------------------------------------------- dibujo
        bg = EDIT_BG if editing else (GREEN if bg_green else (0, 0, 0))
        toast_on = time.time() < toast_until and not editing
        state = (inputs, bg, ww, wh, editor.rev if editing else None, layout_ver, layout_id, toast_on)
        if state != last_key:
            last_key = state
            painter.begin(cw, ch, fit * AA, bg)
            if editing:
                editor.draw(painter)
            else:
                pressed = set(inputs)
                draw_layout(painter, layout, pressed)
                bound = {k["bind"] for k in layout["keys"]}
                extras = [n for n in kn if n not in bound] + [n for n in pad_names if "PAD:" + n not in bound]
                if extras:
                    draw_chips(painter, extras, cw, ch)
                elif not layout["keys"]:
                    painter.text("Empty layout: right-click → Edit", cw / 2, ch / 2 - 10, 11, (170, 176, 188))
            scaled = pygame.transform.smoothscale(painter.surf, (max(1, int(cw * fit)), max(1, int(ch * fit))))
        win.fill(bg)
        win.blit(scaled, (int(ox), int(oy)))
        if editing:
            editor.draw_ui(win)
        elif toast_on:
            img = ui_font.render(toast, True, (240, 242, 247))
            win.blit(img, img.get_rect(midbottom=(ww // 2, wh - 8)))
        if menu.open:
            menu.draw(win)
        if confirm:
            name = next((n for i, n in L.list_layouts() if i == confirm[1]), confirm[1])
            draw_dialog(win, ui_font, f'Delete the layout "{name}"?')
        pygame.display.flip()

        if shot:
            if time.time() - t0 > 1.5:
                pygame.image.save(win, shot)  # último fotograma
                running = False
        clock.tick(144)
    pygame.quit()
