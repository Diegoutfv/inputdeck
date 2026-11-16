"""Backend USB del Nintendo Switch 2 Pro Controller (VID 057E, PID 2069).

Windows no lo expone como gamepad estándar: hay que enviar comandos de inicialización por la
interfaz bulk (WinUSB) y después leer los reportes HID (ID 0x05). Se suelta la interfaz tras
inicializar para no chocar con Steam. Protocolo según switchbrew.org y
ndeadly/switch2_controller_research. Probado solo en Windows por USB.
"""
import threading
import time

from .gamepad import PadState

try:
    import hid
    import libusb_package
    import usb.backend.libusb1 as libusb_backend
    import usb.core
    import usb.util
    AVAILABLE = True
except Exception:
    AVAILABLE = False

VID, PID = 0x057E, 0x2069
OFF = 1  # el byte 0 del reporte USB es el ID (0x05)
BUTTONS = {
    4: {0x80: "ZR", 0x40: "R", 0x08: "A", 0x04: "B", 0x02: "X", 0x01: "Y"},
    5: {0x40: "C", 0x20: "CAPTURE", 0x10: "HOME", 0x08: "LS", 0x04: "RS", 0x02: "PLUS", 0x01: "MINUS"},
    6: {0x80: "ZL", 0x40: "L", 0x08: "LEFT", 0x04: "RIGHT", 0x02: "UP", 0x01: "DOWN"},
    7: {0x02: "GL", 0x01: "GR"},
}
INIT_CMDS = [
    bytes.fromhex("0791010100000000"),
    bytes.fromhex("0391000d000800000100" + "317ec6ebf148"),
    bytes.fromhex("039100030004000001000000"),
]


def _unpack(b):  # dos valores de 12 bits en 3 bytes
    return b[0] | ((b[1] & 0x0F) << 8), (b[1] >> 4) | (b[2] << 4)


class _Cal:
    """Calibración automática: centro = primera lectura, rango = máxima desviación vista."""

    def __init__(self):
        self.c = None

    def norm(self, raw):
        if self.c is None:
            self.c = {"cx": raw[0], "cy": raw[1], "rx": 1400.0, "ry": 1400.0}
        c = self.c
        c["rx"] = max(c["rx"], abs(raw[0] - c["cx"]))
        c["ry"] = max(c["ry"], abs(raw[1] - c["cy"]))
        x, y = (raw[0] - c["cx"]) / c["rx"], (raw[1] - c["cy"]) / c["ry"]
        x = 0.0 if abs(x) < 0.05 else x
        y = 0.0 if abs(y) < 0.05 else y
        return (round(max(-1.0, min(1.0, x)), 3), round(max(-1.0, min(1.0, y)), 3))


def _init_controller():
    try:
        be = libusb_backend.get_backend(find_library=libusb_package.find_library)
        dev = usb.core.find(idVendor=VID, idProduct=PID, backend=be)
        if dev is None:
            return
        try:
            dev.set_configuration()
        except Exception:
            pass
        usb.util.claim_interface(dev, 1)
        try:
            for c in INIT_CMDS:
                dev.write(0x02, c, timeout=1000)
                try:
                    dev.read(0x82, 64, timeout=1000)
                except Exception:
                    pass
        finally:
            usb.util.dispose_resources(dev)
    except Exception:
        pass  # interfaz ocupada (p. ej. Steam): se asume que ya lo inicializó


class Switch2Gamepad:
    def __init__(self):
        self._state = PadState()
        self._lock = threading.Lock()
        self._stop = threading.Event()
        if AVAILABLE:
            threading.Thread(target=self._run, daemon=True).start()

    def poll(self) -> PadState:
        with self._lock:
            return self._state

    def _set(self, st):
        with self._lock:
            self._state = st

    def _run(self):
        while not self._stop.is_set():
            h = None
            try:
                if not hid.enumerate(VID, PID):  # no hay mando: no molestar a libusb
                    self._stop.wait(1.0)
                    continue
                _init_controller()
                h = hid.device()
                h.open(VID, PID)
                ls_cal, rs_cal = _Cal(), _Cal()
                last = time.time()
                while not self._stop.is_set():
                    d = h.read(64, 200)
                    if not d or d[0] != 0x05 or len(d) < 17:
                        if time.time() - last > 3:
                            raise RuntimeError("sin datos")
                        continue
                    last = time.time()
                    pressed = frozenset(n for i, ms in BUTTONS.items() for m, n in ms.items() if d[OFF + i] & m)
                    self._set(PadState(
                        connected=True, name="Switch 2 Pro Controller", kind="switch2", buttons=pressed,
                        ls=ls_cal.norm(_unpack(d[OFF + 10:OFF + 13])),
                        rs=rs_cal.norm(_unpack(d[OFF + 13:OFF + 16])),
                    ))
            except Exception:
                pass
            finally:
                self._set(PadState())
                try:
                    if h:
                        h.close()
                except Exception:
                    pass
            self._stop.wait(1.5)
