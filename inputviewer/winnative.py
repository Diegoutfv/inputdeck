"""Lector de teclado y ratón para Windows SIN hooks.

Por qué no hooks (pynput): un hook de bajo nivel obliga a Windows a esperar al programa en cada
pulsación. Si ese programa tarda (por ejemplo porque un juego pesado acapara la CPU), Windows
descarta el evento o incluso quita el hook en silencio. El resultado es justo lo que se veía con
RE4: pulsaciones que no llegan y un «soltar» perdido que deja un botón pegado.

Aquí se hace al revés:
  * Teclas y botones del ratón: cada pocos milisegundos se pregunta a Windows el estado REAL de
    cada uno (GetAsyncKeyState). Un cambio genera pulsar/soltar; un botón que ya no está pulsado
    se suelta aunque nunca hubiera llegado el aviso. Nada se puede perder ni quedarse pegado.
    Una pulsación más corta que el intervalo se detecta con el bit «pulsada desde la última
    consulta» de la propia API.
  * Rueda del ratón: Raw Input (mensajes asíncronos, sin hook), que no retrasa el ratón del juego.

Corre en el proceso hijo de keys.py y manda los mismos eventos que la versión con pynput.
"""
import ctypes
import time
from ctypes import wintypes

POLL = 0.004          # s entre consultas (250 Hz)
VK_NAMES = {          # teclas fijas (código de tecla virtual -> nombre)
    0x20: "SPACE", 0x0D: "ENTER", 0x09: "TAB", 0x1B: "ESC", 0x08: "BACK", 0x2E: "DEL", 0x2D: "INS",
    0x24: "HOME", 0x23: "END", 0x21: "PGUP", 0x22: "PGDN", 0x14: "CAPS", 0x25: "←", 0x26: "↑",
    0x27: "→", 0x28: "↓", 0x2C: "PRTSC", 0x5D: "MENU", 0x5B: "WIN", 0x5C: "WIN",
}
OEM_FALLBACK = {0xBA: ";", 0xBB: "=", 0xBC: ",", 0xBD: "-", 0xBE: ".", 0xBF: "/", 0xC0: "`",
                0xDB: "[", 0xDC: "\\", 0xDD: "]", 0xDE: "'"}
MOUSE = {0x01: "LMB", 0x02: "RMB", 0x04: "MMB", 0x05: "M4", 0x06: "M5"}
DEFAULT_MODS = {"LSHIFT": "LShift", "RSHIFT": "RShift", "LCTRL": "LCtrl", "RCTRL": "RCtrl",
                "LALT": "LAlt", "RALT": "RAlt"}


def build_table(mods=None, map_char=None):
    """[(vk, ident, nombre)] de todo lo que se vigila.

    `mods`: nombres de los modificadores (para la edición que no distingue izquierda/derecha).
    `map_char(vk)`: carácter que produce una tecla OEM en el teclado del usuario (para que «Ñ»
    salga como «Ñ» y no como «`»)."""
    mods = {**DEFAULT_MODS, **(mods or {})}
    t = []
    for vk in range(0x41, 0x5B):
        t.append((vk, f"vk{vk}", chr(vk)))
    for vk in range(0x30, 0x3A):
        t.append((vk, f"vk{vk}", chr(vk)))
    for i in range(10):
        t.append((0x60 + i, f"vk{0x60 + i}", f"N{i}"))
    for i in range(24):
        t.append((0x70 + i, f"vk{0x70 + i}", f"F{i + 1}"))
    for vk, name in VK_NAMES.items():
        t.append((vk, f"vk{vk}", name))
    for vk, fb in OEM_FALLBACK.items():
        ch = map_char(vk) if map_char else None
        t.append((vk, f"vk{vk}", ch or fb))
    for vk, key in ((0xA0, "LSHIFT"), (0xA1, "RSHIFT"), (0xA2, "LCTRL"), (0xA3, "RCTRL"),
                    (0xA4, "LALT"), (0xA5, "RALT")):
        t.append((vk, f"vk{vk}", mods[key]))
    for vk, name in MOUSE.items():
        t.append((vk, "mouse_" + name, name))
    return t


def _layout_char(vk):
    """Carácter que produce la tecla OEM `vk` con la distribución de teclado actual."""
    try:
        r = ctypes.windll.user32.MapVirtualKeyW(vk, 2)  # MAPVK_VK_TO_CHAR
        if r and not (r & 0x80000000) and chr(r & 0xFFFF).isprintable():
            return chr(r & 0xFFFF).upper()
    except Exception:
        pass
    return None


# ------------------------------------------------------------------------- sondeo
class Poller:
    """Convierte el estado real de teclas/botones en eventos pulsar/soltar."""

    def __init__(self, table, gas, emit):
        self.table, self.gas, self.emit = table, gas, emit
        self.down = {vk: False for vk, _, _ in table}
        for vk, _, _ in table:  # limpia el bit «pulsada desde la última consulta» heredado
            gas(vk)

    def step(self):
        gas, emit, down = self.gas, self.emit, self.down
        for vk, ident, name in self.table:
            s = gas(vk)
            if s & 0x8000:                       # pulsada ahora
                if not down[vk]:
                    down[vk] = True
                    emit(("p", ident, name))
            elif down[vk]:                       # estaba pulsada y ya no: se suelta SIEMPRE
                down[vk] = False
                emit(("r", ident))
            elif s & 1:                          # pulsada y soltada entre dos consultas
                emit(("p", ident, name))
                emit(("r", ident))


# ----------------------------------------------------------------- rueda (Raw Input)
class _RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [("dwType", wintypes.DWORD), ("dwSize", wintypes.DWORD),
                ("hDevice", wintypes.HANDLE), ("wParam", wintypes.WPARAM)]


class _RAWMOUSE(ctypes.Structure):
    _fields_ = [("usFlags", wintypes.USHORT), ("pad", wintypes.USHORT),
                ("usButtonFlags", wintypes.USHORT), ("usButtonData", wintypes.USHORT),
                ("ulRawButtons", wintypes.ULONG), ("lLastX", wintypes.LONG),
                ("lLastY", wintypes.LONG), ("ulExtraInformation", wintypes.ULONG)]


class _RAWINPUT(ctypes.Structure):
    _fields_ = [("header", _RAWINPUTHEADER), ("mouse", _RAWMOUSE)]


RIM_TYPEMOUSE = 0
RI_MOUSE_WHEEL = 0x0400


def wheel_delta(ri):
    """Pasos de rueda de un RAWINPUT de ratón: >0 hacia arriba, <0 hacia abajo, 0 si no hay rueda."""
    if ri.header.dwType != RIM_TYPEMOUSE or not (ri.mouse.usButtonFlags & RI_MOUSE_WHEEL):
        return 0
    return ctypes.c_short(ri.mouse.usButtonData).value


def wheel_thread(emit, on_raw=None):
    """Hilo con una ventana invisible (solo mensajes) que recibe la rueda por Raw Input."""
    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    LRESULT = ctypes.c_ssize_t
    WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

    class WNDCLASSW(ctypes.Structure):
        _fields_ = [("style", wintypes.UINT), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int),
                    ("cbWndExtra", ctypes.c_int), ("hInstance", wintypes.HINSTANCE),
                    ("hIcon", wintypes.HANDLE), ("hCursor", wintypes.HANDLE),
                    ("hbrBackground", wintypes.HANDLE), ("lpszMenuName", wintypes.LPCWSTR),
                    ("lpszClassName", wintypes.LPCWSTR)]

    class RAWINPUTDEVICE(ctypes.Structure):
        _fields_ = [("usUsagePage", wintypes.USHORT), ("usUsage", wintypes.USHORT),
                    ("dwFlags", wintypes.DWORD), ("hwndTarget", wintypes.HWND)]

    user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.DefWindowProcW.restype = LRESULT
    user32.GetRawInputData.argtypes = [wintypes.HANDLE, wintypes.UINT, ctypes.c_void_p,
                                       ctypes.POINTER(wintypes.UINT), wintypes.UINT]
    user32.GetRawInputData.restype = wintypes.UINT
    user32.CreateWindowExW.restype = wintypes.HWND
    user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
                                       ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                       wintypes.HWND, wintypes.HANDLE, wintypes.HINSTANCE, ctypes.c_void_p]
    kernel32.GetModuleHandleW.restype = wintypes.HINSTANCE

    def proc(hwnd, msg, wp, lp):
        if msg == 0x00FF:  # WM_INPUT
            try:
                ri, size = _RAWINPUT(), wintypes.UINT(ctypes.sizeof(_RAWINPUT))
                got = user32.GetRawInputData(lp, 0x10000003, ctypes.byref(ri), ctypes.byref(size),
                                             ctypes.sizeof(_RAWINPUTHEADER))  # RID_INPUT
                if got != 0xFFFFFFFF:
                    if on_raw:
                        on_raw(ri)
                    d = wheel_delta(ri)
                    if d:
                        emit(("t", "scroll_up", "ScrollU") if d > 0 else ("t", "scroll_down", "ScrollD"))
            except Exception:
                pass
        return user32.DefWindowProcW(hwnd, msg, wp, lp)

    cb = WNDPROC(proc)  # referencia viva mientras corra el hilo
    hinst = kernel32.GetModuleHandleW(None)
    name = f"InputDeckRaw{id(cb) & 0xFFFFFF}"
    wc = WNDCLASSW(0, cb, 0, 0, hinst, None, None, None, None, name)
    if not user32.RegisterClassW(ctypes.byref(wc)):
        return False
    hwnd = user32.CreateWindowExW(0, name, name, 0, 0, 0, 0, 0, wintypes.HWND(-3), None, hinst, None)  # HWND_MESSAGE
    if not hwnd:
        return False
    rid = RAWINPUTDEVICE(0x01, 0x02, 0x100, hwnd)  # ratón genérico, RIDEV_INPUTSINK: también sin foco
    if not user32.RegisterRawInputDevices(ctypes.byref(rid), 1, ctypes.sizeof(rid)):
        return False
    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))
    return True


# ---------------------------------------------------------------------------- proceso hijo
def run(q, mods=None, parent=None):
    """Bucle del proceso hijo: prioridad algo mayor + sondeo + rueda. Termina si el padre muere."""
    import threading
    try:  # un poco más de prioridad: que un juego que acapara la CPU no deje sin turno al lector
        k = ctypes.windll.kernel32
        k.GetCurrentProcess.restype = wintypes.HANDLE   # sin declarar los tipos, en 64 bits el
        k.GetCurrentThread.restype = wintypes.HANDLE    # «proceso actual» (-1) llega truncado
        k.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        k.SetThreadPriority.argtypes = [wintypes.HANDLE, ctypes.c_int]
        k.SetPriorityClass(k.GetCurrentProcess(), 0x8000)       # ABOVE_NORMAL_PRIORITY_CLASS
        k.SetThreadPriority(k.GetCurrentThread(), 1)            # THREAD_PRIORITY_ABOVE_NORMAL
    except Exception:
        pass
    emit = q.put
    threading.Thread(target=wheel_thread, args=(emit,), daemon=True).start()
    poller = Poller(build_table(mods, _layout_char), ctypes.windll.user32.GetAsyncKeyState, emit)
    last_check = time.time()
    while True:
        t0 = time.perf_counter()
        poller.step()
        if time.time() - last_check > 1.0:   # ¿sigue vivo el programa principal?
            last_check = time.time()
            if parent is not None and not parent.is_alive():
                return
        left = POLL - (time.perf_counter() - t0)
        if left > 0:
            time.sleep(left)
