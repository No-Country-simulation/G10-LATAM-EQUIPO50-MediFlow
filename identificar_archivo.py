#Importar libreria tkinter para seleccion de archivos
import tkinter as tk
from tkinter import filedialog

import os

#Definiendo extensiones de los archivos a reconocer:

#Imagen
Extensiones_imagen = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tiff",
    ".webp"
}

#PDF
Extensiones_pdf = {".pdf"}

#JSON
Extensiones_json = {".json"}

#Probando no permitir extensiones.
Extensiones_NO_permitidas = {".heic",".heif"}

#Funcion de seleccion de archivos junto a su tipo de extension de archivo

def seleccionar_archivo():

    root = tk.Tk()
    root.withdraw()

    #Seleccionando archivo
    ruta_archivo = filedialog.askopenfilename(
        title = "Seleccionar un archivo para Mediflow_G-10_Equipo_50",
        filetypes = [("Archivos Compatibles", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp *.pdf *.json"),("Todos los Archivos", "*.*")]
        
    )
    root.destroy()
    return ruta_archivo

#Obteniendo la extension del archivo subido

def obtener_extension(ruta_archivo):
    return os.path.splitext(ruta_archivo)[1].lower()

#Pasamos a la identificacion del tipo de archivo subido

def identificar_tipo_archivo(ruta_archivo):
    #Obteniendo extension del archivo subido
    extension = obtener_extension(ruta_archivo)

    #Verificando extension del archivo permitido a subir

    if extension in Extensiones_NO_permitidas:
        return "Extension_NO_Permitida"

    elif extension in Extensiones_imagen:
        return "Imagen"

    elif extension in Extensiones_pdf:
        return "PDF"

    elif extension in Extensiones_json:
        return "JSON"

    return "Extension_Desconocida"


def main():

    print("\nProyecto MediFlow Fase2")
    print("Seleccion de archivo\n")

    #Seleccionar Archivo
    ruta_archivo = seleccionar_archivo()

    #Verificamos si cancelo el usuario al querer subir un archivo
    if not ruta_archivo:
        print("\nNo seleccionaste ningun archivo.")
        return

    #tipo de archivo cuando seleccionamos este en nuestra computadora
    tipo_archivo = identificar_tipo_archivo(ruta_archivo)

    #Tipo de extension del archivo 
    extension = obtener_extension(ruta_archivo)


    #Imprimimos informacion para confirmar:

    print("\nArchivo Seleccionado es:\n")
    print(ruta_archivo)

    #Aqui obtenemos la extension del archivo subido
    print("\nExtension del tipo de archivo es:\n")
    print(extension)

    print("\nTipo de archivo detectado es:\n")
    print(tipo_archivo)

    #Validamos el tipo de archivo subido por el usuario:

    if tipo_archivo == "Imagen":
        print("\nTipo de archivo imagen")
        print("Archivo Compatible con el Proyecto MediFlow_G-10_Equipo_50\n")

    elif tipo_archivo == "PDF" :
        print("\nTipo de archivo pdf")
        print("Compatible con el Proyecto MediFlow_G-10_Equipo_50\n")


    elif tipo_archivo == "JSON":
        print("\nTipo de archivo json compatible")
        print("Compatible con el Proyecto MediFlow_G-10_Equipo_50\n")

    elif tipo_archivo == "Extension_NO_permitida":
        print("\nError Fatal ese tipo de archivo no esta permitido")

    else:
        print("\nFormato no compatible")

#Ejecutamos el programa
if __name__ == "__main__":
    main()

