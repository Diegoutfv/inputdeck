"""Ventana principal: teclado + ratón dibujados; los mandos aparecen como cajitas (estilo Skeys).

Tecla G = fondo verde / negro.
Opciones de prueba:  --screenshot ruta.png   --demo
"""
import os
import sys
import time

# Sin esto, SDL ignora el mando mientras la ventana no tiene el foco (siempre el caso en OBS).
os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")

import pygame

from . import chips, keyboard, keys, switch2_usb
from .draw import Painter
from .gamepad import PadState, SDLGamepad

GREEN = (0, 177, 64)  # chroma key para OBS
AA = 2                # supersampling


def _demo():
    pad = PadState(connected=True, name="demo", kind="playstation", rt=1.0, ls=(-0.8, 0.1),
                   buttons=frozenset({"A", "LB"}))
    return ("W", "LShift", "SPACE", "LMB", "1", "F2"), chips.pad_chips(pad)


def draw_chips(p, names, y):
    """Fila de cajitas centrada con lo que no cabe en la cuadrícula (teclas extra y mandos)."""
    gap, pad, kh = 4, 7, 20
    shown, total = [], 0
    for n in names:
        w = max(kh, p.text_width(n, 11) + pad * 2)
        if total + w > keyboard.LW - 6:
            break
        shown.append((n, w))
        total += w + gap
    x = (keyboard.LW - (total - gap)) / 2
    for n, w in shown:
        p.rrect(x, y, w, kh, 6, True, n, 11)
        x += w + gap


def main():
    argv = sys.argv
    shot = argv[argv.index("--screenshot") + 1] if "--screenshot" in argv else None
    demo = "--demo" in argv

    pygame.init()
    pygame.display.set_caption("InputDeck")
    win = pygame.display.set_mode((800, int(800 * keyboard.LH / keyboard.LW)), pygame.RESIZABLE)
    painter = Painter()
    sdl_pad = SDLGamepad()
    sw2_pad = switch2_usb.Switch2Gamepad() if not demo else None
    keys.start()

    bg_green = shot is None
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

        if demo:
            kn, pad_names = _demo()
        else:
            kn = keys.active_keys()
            pad = sw2_pad.poll()  # Switch 2 (USB propio) y si no, cualquier mando SDL
            if not pad.connected:
                pad = sdl_pad.poll()
            pad_names = chips.pad_chips(pad)

        bg = GREEN if bg_green else (0, 0, 0)
        ww, wh = win.get_size()
        state = (kn, pad_names, bg, ww, wh)
        if state == last_key:  # nada cambió: reutiliza el último fotograma
            win.fill(bg)
            win.blit(scaled, ((ww - scaled.get_width()) // 2, (wh - scaled.get_height()) // 2))
            pygame.display.flip()
            if shot and time.time() - t0 > 1.5:
                running = False
            clock.tick(144)
            continue
        last_key = state

        fit = max(0.2, min(ww / keyboard.LW, wh / keyboard.LH))
        painter.begin(keyboard.LW, keyboard.LH, fit * AA, bg)
        keyboard.draw(painter, set(kn))
        extras = [n for n in kn if n not in keyboard.GRID_NAMES] + list(pad_names)
        if extras:
            draw_chips(painter, extras, keyboard.CHIPS_Y)
        scaled = pygame.transform.smoothscale(
            painter.surf, (max(1, int(keyboard.LW * fit)), max(1, int(keyboard.LH * fit))))
        win.fill(bg)
        win.blit(scaled, ((ww - scaled.get_width()) // 2, (wh - scaled.get_height()) // 2))
        pygame.display.flip()

        if shot:
            pygame.image.save(win, shot)  # guarda el último fotograma renderizado
        clock.tick(144)
    pygame.quit()
