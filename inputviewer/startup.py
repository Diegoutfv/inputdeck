"""Arrancar con Windows: una entrada en HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run.

Solo afecta al usuario actual (no pide permisos de administrador) y se puede quitar desde el mismo
menú o desde «Aplicaciones de inicio» de Windows. Solo está implementado para Windows.

Cada edición usa su propio nombre de entrada (el del .exe), así que las dos versiones pueden estar
activadas a la vez sin pisarse.
"""
import sys
from pathlib import Path

SUPPORTED = sys.platform == "win32"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def entry_name() -> str:
    """Nombre de la entrada: el del .exe (InputDeck-Controller...) o «InputDeck» desde el código."""
    return Path(sys.executable).stem if getattr(sys, "frozen", False) else "InputDeck"


def command() -> str:
    """Línea de comandos que Windows ejecutará al iniciar sesión."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    py = Path(sys.executable)
    pyw = py.with_name("pythonw.exe")  # sin ventana de consola
    run = Path(__file__).resolve().parent.parent / "run.py"
    return f'"{pyw if pyw.exists() else py}" "{run}"'


def is_enabled(name=None) -> bool:
    """True si la entrada existe y apunta a ESTE programa (si apunta a otra ruta, no cuenta)."""
    if not SUPPORTED:
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            value, _ = winreg.QueryValueEx(k, name or entry_name())
        return str(value).strip().lower() == command().lower()
    except OSError:
        return False


def set_enabled(on: bool, name=None) -> bool:
    """Activa o quita el arranque con Windows. Devuelve True si se aplicó."""
    if not SUPPORTED:
        return False
    try:
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            if on:
                winreg.SetValueEx(k, name or entry_name(), 0, winreg.REG_SZ, command())
            else:
                try:
                    winreg.DeleteValue(k, name or entry_name())
                except FileNotFoundError:
                    pass  # ya estaba quitada
        return True
    except OSError:
        return False
