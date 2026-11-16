"""Teclado y ratón globales (multiplataforma) con pynput.

La escucha corre en un PROCESO aparte. Motivo: al arrastrar o redimensionar la ventana, Windows
deja el hilo principal dentro de su bucle modal con el GIL de Python tomado; un hook de ratón
en el mismo proceso se queda esperando el GIL en cada movimiento y el cursor de todo el sistema
va a tirones. En otro proceso no hay GIL compartido, así que no afecta.

Recibe cada pulsación/suelta como evento (sin muestreo). En macOS hace falta el permiso de
"Accesibilidad / Monitorización de entrada"; en Linux funciona con X11 (no con Wayland puro).
"""
import multiprocessing as mp
import queue
import sys
import threading
import time

MIN_VISIBLE = 0.025  # un toque muy corto se ve al menos este tiempo; luego se apaga al soltar

try:
    from pynput import keyboard, mouse
    AVAILABLE = True
except Exception:  # pynput no disponible o sin entorno gráfico
    AVAILABLE = False

_SUPER = {"win32": "WIN", "darwin": "CMD"}.get(sys.platform, "SUPER")
_SPECIAL = {
    "space": "SPACE", "enter": "ENTER", "tab": "TAB", "esc": "ESC", "backspace": "BACK",
    "delete": "DEL", "insert": "INS", "home": "HOME", "end": "END", "page_up": "PGUP",
    "page_down": "PGDN", "caps_lock": "CAPS", "up": "↑", "down": "↓", "left": "←", "right": "→",
    "shift": "SHIFT", "shift_l": "SHIFT", "shift_r": "SHIFT",
    "ctrl": "CTRL", "ctrl_l": "CTRL", "ctrl_r": "CTRL",
    "alt": "ALT", "alt_l": "ALT", "alt_r": "ALT", "alt_gr": "ALT",
    "cmd": _SUPER, "cmd_l": _SUPER, "cmd_r": _SUPER, "menu": "MENU", "print_screen": "PRTSC",
}
_MOUSE = {"left": "LMB", "right": "RMB", "middle": "MMB",
          "x1": "M4", "x2": "M5", "button8": "M4", "button9": "M5"}


def _ident(key):
    """(id estable, nombre a mostrar). El id no cambia entre pulsar y soltar."""
    if isinstance(key, keyboard.Key):
        n = key.name
        if n.startswith("f") and n[1:].isdigit():
            return n, n.upper()
        return n, _SPECIAL.get(n, n.upper())
    vk = getattr(key, "vk", None)
    ch = getattr(key, "char", None)
    ident = vk if vk is not None else ch
    if ch and ch.isprintable():
        return ident, ch.upper()
    if vk is not None:  # Ctrl+letra da un carácter de control: se usa el código de tecla
        if 0x41 <= vk <= 0x5A or 0x30 <= vk <= 0x39:
            return ident, chr(vk)
        if 0x60 <= vk <= 0x69:
            return ident, f"N{vk - 0x60}"
    return ident, None


def _child(q):
    """Proceso hijo: solo escucha y manda eventos por la cola (trabajo mínimo por evento)."""
    def kd(key):
        ident, name = _ident(key)
        if ident is not None and name:
            q.put(("p", ident, name))

    def ku(key):
        q.put(("r", _ident(key)[0]))

    def click(x, y, button, pressed):
        n = _MOUSE.get(button.name)
        if n:
            q.put(("p", "mouse_" + n, n) if pressed else ("r", "mouse_" + n))

    try:
        keyboard.Listener(on_press=kd, on_release=ku, daemon=True).start()
        mouse.Listener(on_click=click, daemon=True).start()
    except Exception:
        return
    parent = mp.parent_process()
    while parent is None or parent.is_alive():  # termina si el programa principal se cierra
        time.sleep(1.0)


# ------------------------------------------------------------------ proceso principal
_lock = threading.Lock()
_held = {}  # id -> [nombre, t_pulsación, visible_hasta_mínimo, pulsada]
_q = None
_proc = None


def _press(ident, name):
    now = time.time()
    with _lock:
        e = _held.get(ident)
        if e is None or not e[3]:  # ignora la repetición automática
            _held[ident] = [name, now, now + MIN_VISIBLE, True]


def _release(ident):
    with _lock:
        e = _held.get(ident)
        if e:
            e[3] = False


def start():
    global _q, _proc
    if _proc is not None or not AVAILABLE:
        return
    try:
        ctx = mp.get_context("spawn")
        _q = ctx.Queue()
        _proc = ctx.Process(target=_child, args=(_q,), daemon=True)
        _proc.start()
    except Exception:
        _proc = None


def _drain():
    if _q is None:
        return
    try:
        while True:
            m = _q.get_nowait()
            if m[0] == "p":
                _press(m[1], m[2])
            else:
                _release(m[1])
    except queue.Empty:
        pass
    except Exception:
        pass


def active_keys():
    """Teclas visibles ahora: pulsadas, o recién pulsadas dentro del tiempo mínimo."""
    _drain()
    now = time.time()
    with _lock:
        for k in [k for k, e in _held.items() if not e[3] and now > e[2]]:
            del _held[k]
        ents = sorted(_held.values(), key=lambda e: e[1])
    names = []
    for e in ents:
        if e[0] not in names:
            names.append(e[0])
    return tuple(names)
