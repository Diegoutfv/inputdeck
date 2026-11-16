"""Ventana principal: mando (autodetectado) + teclas/ratón.

Tecla G = fondo verde / negro. Clic derecho = elegir la distribución (Auto por defecto: la del
mando conectado). La elección se guarda y se aplica aunque el mando conectado sea de otro tipo.

Opciones de prueba:  --screenshot ruta.png   --demo [xbox|playstation|switch2|none]
                     --layout [auto|xbox|playstation|switch2]   --open-menu
"""
import os
import sys
import time

# Sin esto, SDL ignora el mando mientras la ventana no tiene el foco (siempre el caso en OBS).
os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")

import pygame

from . import config, keys, playstation, switch2, switch2_usb, xbox
from .adapt import adapt
from .draw import Painter
from .gamepad import PadState, SDLGamepad
from .menu import ContextMenu

LAYOUTS = {"xbox": xbox, "playstation": playstation, "switch2": switch2}
LW = 270
GREEN = (0, 177, 64)  # chroma key para OBS
MUTED = (170, 176, 188)  # color del aviso "esperando mando"
AA = 2                # supersampling


def _demo_pad(kind):
    common = dict(connected=True, name="demo", kind=kind, lt=0.55, rt=1.0, ls=(0.6, 0.5), rs=(-0.8, -0.2))
    if kind == "switch2":
        return PadState(buttons=frozenset({"A", "L", "UP", "HOME", "ZR", "LS", "GL"}), **common)
    extra = {"playstation": {"TOUCHPAD", "VIEW"}, "xbox": {"GUIDE"}}[kind]
    return PadState(buttons=frozenset({"A", "Y", "LB", "UP", "LS", "MENU"} | extra), **common)


def draw_keys(p, names, y):
    """Fila de teclas/botones de ratón centrada; solo existe mientras se pulsa algo."""
    gap, pad, kh = 4, 7, 20
    shown, total = [], 0
    for n in names:
        w = max(kh, p.text_width(n, 11) + pad * 2)
        if total + w > LW - 6:
            break
        shown.append((n, w))
        total += w + gap
    x = (LW - (total - gap)) / 2
    for n, w in shown:
        p.rrect(x, y, w, kh, 6, True, n, 11)
        x += w + gap


def main():
    argv = sys.argv
    shot = argv[argv.index("--screenshot") + 1] if "--screenshot" in argv else None
    demo = None
    if "--demo" in argv:
        i = argv.index("--demo")
        demo = argv[i + 1] if i + 1 < len(argv) and (argv[i + 1] in LAYOUTS or argv[i + 1] == "none") else "xbox"

    pygame.init()
    pygame.display.set_caption("InputDeck")
    win = pygame.display.set_mode((800, int(800 * (xbox.PAD_H + 32) / LW)), pygame.RESIZABLE)
    painter = Painter()
    sdl_pad = SDLGamepad()
    sw2_pad = switch2_usb.Switch2Gamepad() if not demo else None
    keys.start()

    # Distribución elegida por el usuario: "auto" (por defecto) o una fija. Se guarda en disco.
    cfg = config.load()
    choice = argv[argv.index("--layout") + 1] if "--layout" in argv else cfg.get("layout", "auto")
    if choice != "auto" and choice not in LAYOUTS:
        choice = "auto"
    menu = ContextMenu()
    if "--open-menu" in argv:
        menu.show((60, 60))
        menu.hover = "xbox"

    bg_green = shot is None
    kind = "xbox"
    last_key, scaled = None, pygame.Surface((1, 1))
    clock = pygame.time.Clock()
    t0 = time.time()
    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_g:
                bg_green = not bg_green
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                menu.hide()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:  # clic derecho: abrir menú
                menu.show(e.pos)
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and menu.open:
                picked = menu.item_at(e.pos, win.get_size())
                if picked:
                    choice = picked
                    config.save({**cfg, "layout": choice})
                menu.hide()  # un clic en cualquier sitio cierra el menú
            elif e.type == pygame.MOUSEMOTION and menu.open:
                menu.hover = menu.item_at(e.pos, win.get_size())

        # Prioridad: Switch 2 (USB propio) y después cualquier mando SDL (Xbox, DualSense...)
        if demo == "none":
            pad = PadState()
        elif demo:
            pad = _demo_pad(demo)
        else:
            pad = sw2_pad.poll()
            if not pad.connected:
                pad = sdl_pad.poll()
        if pad.connected:
            kind = pad.kind
        # Auto = la distribución del mando conectado; si no, la elegida (con botones adaptados)
        shown = kind if choice == "auto" else choice
        pad = adapt(pad, shown)
        layout = LAYOUTS[shown]
        keys_y = layout.PAD_H + 6
        lh = keys_y + 26

        kn = ("CTRL", "SHIFT", "A", "LMB") if demo else keys.active_keys()
        bg = GREEN if bg_green else (0, 0, 0)
        ww, wh = win.get_size()
        state = (pad, shown, kn, bg, ww, wh)
        if state == last_key:  # nada cambió: reutiliza el último fotograma
            win.fill(bg)
            win.blit(scaled, ((ww - scaled.get_width()) // 2, (wh - scaled.get_height()) // 2))
            if menu.open:
                menu.draw(win, choice)
            pygame.display.flip()
            if shot and time.time() - t0 > 1.5:
                running = False
            clock.tick(144)
            continue
        last_key = state

        fit = max(0.2, min(ww / LW, wh / lh))
        painter.begin(LW, lh, fit * AA, bg)
        if pad.connected:
            layout.draw(painter, pad)
        else:  # sin mando: nada de dibujo, solo el aviso
            cy = layout.PAD_H / 2
            painter.text("Waiting for a controller", LW / 2, cy - 7, 12, MUTED)
            painter.text("to connect…", LW / 2, cy + 8, 12, MUTED)
        if kn:
            draw_keys(painter, kn, keys_y)
        scaled = pygame.transform.smoothscale(painter.surf, (max(1, int(LW * fit)), max(1, int(lh * fit))))
        win.fill(bg)
        win.blit(scaled, ((ww - scaled.get_width()) // 2, (wh - scaled.get_height()) // 2))
        if menu.open:
            menu.draw(win, choice)
        pygame.display.flip()

        if shot:
            pygame.image.save(win, shot)  # guarda el último fotograma renderizado
            with open(shot + ".txt", "w") as f:
                f.write(f"connected={pad.connected} kind={pad.kind} name={pad.name} "
                        f"buttons={sorted(pad.buttons)} lt={pad.lt} rt={pad.rt} ls={pad.ls} rs={pad.rs}\n")
        clock.tick(144)
    pygame.quit()
