# InputDeck

Input viewer multiplataforma (Windows / macOS / Linux) para OBS: muestra el mando, el teclado y
el ratón con un estilo minimalista de contornos blancos.

## Características

| Mando | Conexión | Estado |
|---|---|---|
| Xbox Series X\|S (y cualquier mando con mapeo SDL) | USB / Bluetooth | ✅ interfaz Xbox Series |
| DualSense (PS5) / DualShock 4 | USB / Bluetooth | ✅ interfaz PlayStation (vía SDL) |
| Nintendo Switch 2 Pro Controller | USB | ✅ backend propio, solo Windows |

- **Autodetección:** cambia de distribución según el mando conectado. Si hay un Switch 2 Pro
  Controller por USB tiene prioridad; si no, se usa el primer mando que vea SDL.
- **Selector manual:** clic derecho para elegir la distribución que prefieras, aunque el mando
  sea de otro tipo (se guarda).
- Gatillos analógicos que se rellenan según lo pulsado; sticks con brillo al moverse.
- Teclas y botones del ratón bajo el mando, **solo mientras se pulsan**.
- Ventana redimensionable que se dibuja a la resolución real (nítido en OBS).
- Sin mando conectado muestra «Waiting for a controller to connect…».

## Uso

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate      macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

**Clic derecho** abre el menú de distribución (Auto, Xbox, PlayStation o Switch 2). La elección
se guarda en `%APPDATA%\InputViewer\config.json` (macOS: `~/Library/Application Support/InputViewer`,
Linux: `~/.config/InputViewer`). Al forzar una distribución, los botones se convierten por
posición física (p. ej. la A de Xbox, abajo, ilumina la B de Nintendo, también abajo).

**G** alterna fondo verde (chroma key en OBS: Captura de ventana + filtro «Clave de color»
`#00B140`) y negro.

## Compilar un ejecutable

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name InputDeck --collect-all libusb_package --collect-binaries hid run.py
```

## Notas por plataforma

- **Mando:** usa SDL GameController, así que los nombres de botón son idénticos en todos los SO.
  El clic del touchpad del DualSense depende de que SDL lo exponga en tu sistema.
- **Teclado/ratón globales** (pynput, en un proceso aparte para no ralentizar el cursor al mover
  la ventana):
  - Windows: funciona sin permisos extra (los juegos como administrador pueden requerir ejecutar
    el viewer como administrador).
  - macOS: hay que dar permiso de *Accesibilidad* / *Monitorización de entrada* al programa.
  - Linux: requiere X11 (no funciona con Wayland puro).
- La rueda del ratón no se muestra.
- **Steam:** si Steam está abierto, su configuración de escritorio puede convertir el mando en
  ratón/teclado en Windows; es independiente de este programa (que solo lee el mando).
- **Switch 2 Pro Controller:** Windows no lo expone como gamepad estándar, así que se inicializa
  por USB con comandos propios y luego se leen sus reportes HID. El protocolo sale de la
  investigación de la comunidad y puede cambiar con actualizaciones de firmware.

## Estructura

```
inputviewer/
  gamepad.py       backend de mando SDL (Xbox, PlayStation...) -> PadState común
  switch2_usb.py   backend USB del Switch 2 Pro Controller -> PadState
  adapt.py         convierte botones entre familias de mandos (para el selector manual)
  keys.py          teclado y ratón globales (pynput, proceso aparte)
  draw.py          primitivas de dibujo
  xbox.py / playstation.py / switch2.py   distribuciones visuales
  menu.py          menú de clic derecho
  config.py        preferencias del usuario
  app.py           ventana, autodetección y bucle principal
run.py             punto de entrada
```

Para añadir otro mando: crear un backend que devuelva `PadState` (con su `kind`) y una
distribución con una función `draw(painter, pad)`, y registrarla en `LAYOUTS` (`app.py`).

Probar el aspecto sin mando: `python run.py --demo xbox|playstation|switch2|none`.

## Créditos y avisos

- Protocolo del Switch 2 Pro Controller:
  [switchbrew](https://switchbrew.org/wiki/Switch_2:_Pro_Controller) y
  [ndeadly/switch2_controller_research](https://github.com/ndeadly/switch2_controller_research).
- El logo de Xbox del botón Guide procede de [Simple Icons](https://simpleicons.org/) (CC0).
- Xbox, PlayStation, DualSense y Nintendo Switch son marcas de sus respectivos propietarios. Este
  proyecto es independiente y no está afiliado ni respaldado por ellos.

## Licencia

[MIT](LICENSE)
