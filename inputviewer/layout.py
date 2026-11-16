"""Diseños (layouts) de teclas: modelo, validación y guardado como JSON.

Un layout es:  {"schema": 1, "name": "...", "keys": [{"label", "bind", "x", "y", "w", "h"}, ...]}
  - label: texto que se ve en la tecla
  - bind:  entrada que la ilumina: "Q", "SPACE", "LShift", "LMB", "ScrollU"... o "PAD:A" para un
           botón de mando
  - x, y, w, h: posición y tamaño en unidades lógicas

Los diseños del usuario son archivos .json en <carpeta de configuración>/InputViewer/layouts/.
El diseño "default" viene incluido y no se puede borrar ni sobrescribir.
"""
import json
import math
import re
from pathlib import Path

from . import config
from .keyboard import KEY_H, ROW_H, ROWS, UNIT

BUILTIN = "default"
SCHEMA = 1
MAX_KEYS = 200
MARGIN = 2
CHIPS_H = 28       # franja reservada debajo para teclas fuera del diseño y mandos
MIN_CANVAS = (120, 40)


def builtin() -> dict:
    keys = []
    for r, row in enumerate(ROWS):
        x = 2
        for name, label, units in row:
            keys.append({"label": label, "bind": name, "x": x, "y": r * ROW_H + 1,
                         "w": round(units * UNIT - 4, 1), "h": KEY_H})
            x += units * UNIT
    return {"schema": SCHEMA, "name": "Default", "keys": keys}


def bounds(layout: dict):
    ks = layout["keys"]
    if not ks:
        return (0.0, 0.0, 0.0, 0.0)
    return (min(k["x"] for k in ks), min(k["y"] for k in ks),
            max(k["x"] + k["w"] for k in ks), max(k["y"] + k["h"] for k in ks))


def normalize(layout: dict) -> dict:
    """Desplaza las teclas para que la esquina superior izquierda quede en (MARGIN, MARGIN)."""
    if layout["keys"]:
        x0, y0, _, _ = bounds(layout)
        for k in layout["keys"]:
            k["x"] = round(k["x"] - x0 + MARGIN, 1)
            k["y"] = round(k["y"] - y0 + MARGIN, 1)
    return layout


def canvas_size(layout: dict):
    """Tamaño lógico del lienzo (con la franja de cajitas debajo)."""
    _, _, x1, y1 = bounds(layout)
    return (max(x1 + MARGIN, MIN_CANVAS[0]), max(y1 + MARGIN, MIN_CANVAS[1]) + CHIPS_H)


def validate(d):
    """Devuelve el layout limpio o None si no es válido (los archivos pueden venir de cualquiera)."""
    if not isinstance(d, dict) or not isinstance(d.get("keys"), list) or len(d["keys"]) > MAX_KEYS:
        return None
    out = []
    for k in d["keys"]:
        if not isinstance(k, dict):
            return None
        try:
            x, y, w, h = (float(k[a]) for a in "xywh")
        except (KeyError, TypeError, ValueError):
            return None
        if not all(math.isfinite(v) for v in (x, y, w, h)):
            return None
        if abs(x) > 2000 or abs(y) > 2000 or not 6 <= w <= 600 or not 6 <= h <= 600:
            return None
        out.append({"label": str(k.get("label", ""))[:12], "bind": str(k.get("bind", ""))[:32],
                    "x": x, "y": y, "w": w, "h": h})
    name = str(d.get("name", "")).strip()[:40] or "Layout"
    return {"schema": SCHEMA, "name": name, "keys": out}


# ------------------------------------------------------------------ archivos
def folder() -> Path:
    return config.dir() / "layouts"


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "layout"
    return "default-2" if s == BUILTIN else s


def _read(path: Path):
    try:
        return validate(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return None


def list_layouts():
    """[(id, nombre)] con el diseño incluido primero y después los del usuario."""
    out = [(BUILTIN, builtin()["name"])]
    try:
        for p in sorted(folder().glob("*.json")):
            lay = _read(p)
            if lay:
                out.append((p.stem, lay["name"]))
    except Exception:
        pass
    return out


def load(layout_id: str):
    if layout_id == BUILTIN:
        return builtin()
    if not re.fullmatch(r"[a-z0-9-]+", layout_id or ""):
        return None  # evita rutas raras
    lay = _read(folder() / f"{layout_id}.json")
    return lay


def save(layout: dict, layout_id=None) -> str:
    """Guarda el layout. Si es nuevo (o el incluido) crea un archivo con nombre único."""
    d = folder()
    d.mkdir(parents=True, exist_ok=True)
    if layout_id in (None, BUILTIN):
        base = slug(layout["name"])
        layout_id, n = base, 2
        while (d / f"{layout_id}.json").exists():
            layout_id, n = f"{base}-{n}", n + 1
    tmp = d / f"{layout_id}.json.tmp"
    tmp.write_text(json.dumps(layout, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(d / f"{layout_id}.json")
    return layout_id


def delete(layout_id: str) -> bool:
    if layout_id == BUILTIN or not re.fullmatch(r"[a-z0-9-]+", layout_id or ""):
        return False
    try:
        (folder() / f"{layout_id}.json").unlink()
        return True
    except Exception:
        return False


def unique_name(base: str) -> str:
    names = {n for _, n in list_layouts()}
    if base not in names:
        return base
    i = 2
    while f"{base} {i}" in names:
        i += 1
    return f"{base} {i}"
