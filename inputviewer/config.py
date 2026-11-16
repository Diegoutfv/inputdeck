"""Preferencias del usuario (se guardan en un JSON en la carpeta de configuración del sistema)."""
import json
import os
import sys
from pathlib import Path


def _dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "InputViewer"


def load() -> dict:
    try:
        return json.loads((_dir() / "config.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def save(cfg: dict) -> None:
    try:
        d = _dir()
        d.mkdir(parents=True, exist_ok=True)
        (d / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    except Exception:
        pass  # si no se puede guardar, la preferencia solo vale para esta sesión
