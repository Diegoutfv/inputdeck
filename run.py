"""Punto de entrada para ejecutar y para empaquetar con PyInstaller."""
import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()  # necesario en el .exe: el proceso hijo reejecuta el programa
    # La app se importa aquí dentro (y no arriba) para que el proceso hijo del teclado, que vuelve
    # a importar este archivo, no cargue pygame y compañía: así arranca mucho antes.
    from inputviewer.app import main

    main()
