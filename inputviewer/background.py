"""Seguir funcionando (y siendo capturable por OBS) aunque se minimice la ventana.

Windows deja de dibujar las ventanas minimizadas, así que la «Captura de ventana» de OBS se queda
sin imagen. Por eso, en vez de dejar que se minimice, la ventana se restaura y se vuelve
**invisible** (opacidad 0) y **transparente a los clics**: sigue en su sitio y se sigue dibujando,
así que OBS la sigue capturando en vivo, pero no se ve ni estorba.

(Moverla fuera de la pantalla no sirve: Windows deja de actualizar el dibujo de una ventana
que no está en ningún monitor y OBS vería la imagen congelada.)

Para recuperarla basta pulsar su botón en la barra de tareas.
Solo está implementado para Windows.
"""
import sys
import time

import pygame

COOLDOWN = 0.7  # s: se ignoran los eventos que provoca la propia ventana al cambiarla
WS_EX_TRANSPARENT = 0x00000020
GWL_EXSTYLE = -20
SUPPORTED = sys.platform == "win32"


def _click_through(on: bool):
    """Hace que los clics atraviesen la ventana (Windows)."""
    try:
        import ctypes
        hwnd = pygame.display.get_wm_info()["window"]
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style = (style | WS_EX_TRANSPARENT) if on else (style & ~WS_EX_TRANSPARENT)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
    except Exception:
        pass


class KeepAlive:
    def __init__(self, enabled=True):
        self.enabled = enabled and SUPPORTED
        self.hidden = False
        self._ignore_until = 0.0
        self._win = None

    def _window(self):
        if self._win is None:
            from pygame._sdl2.video import Window
            self._win = Window.from_display_module()
        return self._win

    def handle(self, e):
        """Llamar con cada evento de pygame."""
        if e.type not in (pygame.WINDOWMINIMIZED, pygame.WINDOWFOCUSGAINED, pygame.WINDOWRESTORED):
            return
        if time.time() < self._ignore_until:
            return
        if self.hidden:
            # Pulsar su botón de la barra de tareas la minimiza (si ya estaba activa) o le da el
            # foco: en los dos casos el usuario la quiere ver otra vez.
            self.show()
        elif e.type == pygame.WINDOWMINIMIZED and self.enabled:
            self.hide()

    def hide(self):
        try:
            w = self._window()
            self._ignore_until = time.time() + COOLDOWN
            w.restore()          # deshace el minimizado: Windows volvería a dejar de dibujarla
            w.opacity = 0.0      # invisible, pero Windows sigue componiéndola (OBS la sigue viendo)
            _click_through(True)
            self.hidden = True
            self._ignore_until = time.time() + COOLDOWN
        except Exception:
            self.hidden = False  # si algo falla, que se comporte como una ventana normal

    def show(self):
        try:
            w = self._window()
            self._ignore_until = time.time() + COOLDOWN
            w.restore()          # primero salir del estado minimizado...
            _click_through(False)
            w.opacity = 1.0      # ...y después volver a hacerla visible
            w.focus()
        except Exception:
            pass
        self.hidden = False
        self._ignore_until = time.time() + COOLDOWN
