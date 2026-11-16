"""Punto de entrada para ejecutar y para empaquetar con PyInstaller."""
import multiprocessing

from inputviewer.app import main

if __name__ == "__main__":
    multiprocessing.freeze_support()  # necesario en el .exe: el proceso hijo reejecuta el programa
    main()
