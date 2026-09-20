#Importar libreria tkinter para seleccion de archivos
import tkinter as tk
from tkinter import filedialog

#Funcion seleccion de archivos:
def seleccionar_archivo():

    root = tk.Tk()
    root.withdraw()

    #Seleccion de archivo:
    ruta_archivo = filedialog.askopenfilename(title = "Selecciona un archivo para MediFlow")

    root.destroy()

    return ruta_archivo

def main():

    print("\nProyecto MediFlow Fase1")
    print("Seleccion de archivo\n")

    ruta_archivo = seleccionar_archivo()

    if not ruta_archivo:
        print("\nNo seleccionaste ningun archivo.")

    print("\nArchivo Seleccionado es:\n")
    print(ruta_archivo)

if __name__ == "__main__":
    main()

