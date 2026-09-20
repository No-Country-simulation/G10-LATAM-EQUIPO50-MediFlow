# MEDIFLOW - FASE 04
# Seleccion, Validadcion Y Alamacenamiento De Archivos

#Libreria para Manipular arhcivos
import os
import shutil

#Libreria de Tiempo, Agregaremos fecha
from datetime import datetime

#Libreria para buscar archivos dentro de la computadora
import tkinter as tk
from tkinter import filedialog

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


# Carpetas que tendra MediFlow:

#Ruta donde se guardara nuestro archivo de forma actual:
Carpeta_Base = os.path.dirname(os.path.abspath(__file__))

#Procedemos a ponerle nombre a las carpetas que se crearan para identificar los archivos de forma ordenada
#Carpeta Local donde se guardarán las demas carpetas creadas para tener un orden
Carpeta_Almacenamiento = os.path.join(Carpeta_Base,"Almacen_Local")

#Carpeta para guardar los archivos originales seleccionados
#Dentro de la carpeta Almacen_Local
Carpeta_Archivos_Originales = os.path.join(Carpeta_Almacenamiento,"Archivos_Originales") 

#Carpeta para guardar las imagenes procesadas 
#en caso que el archivo seleccionado sea una imagen
#Dentro de la carpeta local
Carpeta_Imagenes_Procesadas = os.path.join(Carpeta_Almacenamiento,"Imagenes_Procesadas")

#Carpeta para guardar el archivo json de los documentos subidos por el usuario
#Dentro de la Carpeta Local
Carpeta_Datos_Clinicos = os.path.join(Carpeta_Almacenamiento,"Datos_Clinicos")


#Estructura De Carpetas
#Creacion de Carpetas:
def crear_carpetas():

    os.makedirs(Carpeta_Almacenamiento,exist_ok = True)

    os.makedirs(Carpeta_Archivos_Originales, exist_ok = True)

    os.makedirs(Carpeta_Imagenes_Procesadas, exist_ok = True)

    os.makedirs(Carpeta_Datos_Clinicos, exist_ok = True)


#Funcion Seleccion De Archivos:
#Funcion de seleccion de archivos junto a su tipo de extension de archivo

def seleccionar_archivo():

    root = tk.Tk()
    root.withdraw()

    #Seleccionando archivo
    ruta_archivo = filedialog.askopenfilename(title = "Seleccionar un archivo para Mediflow_G-10_Equipo_50",filetypes = [("Archivos Compatibles", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp *.pdf *.json"),("Todos los Archivos", "*.*")])
    root.destroy()
    return ruta_archivo

# Obtencion de la extension de los archivos subidos

#Obteniendo la extension del archivo subido

def obtener_extension(ruta_archivo):
    return os.path.splitext(ruta_archivo)[1].lower()


# Pasamos a la Identificacion por tipo de archivo
# Acorde a su extension escogida por el usuario:

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

# Obtenemos la Fecha y hora par agregarlos al nombre del archivo a guardar
def obtener_fecha_hora():

    return datetime.now().strftime("%Y%m%d_%H%M%S")


# Solicitamos un ID del paciente para identificarlo

def solicitar_id_paciente():

    while True:

        id_paciente = input( "Introduce el ID del paciente: ").strip()

        if id_paciente:

            return id_paciente

        print("El ID no puede estar vacío, ERROR!")


# Procedemos a Guardar el archivo original en la carpeta correspondiente

def guardar_archivo_original( ruta_archivo,id_paciente):
    
    # Obtener nombre original
    nombre_original = os.path.basename(ruta_archivo)

    # Obtener fecha y hora
    fecha = obtener_fecha_hora()

    # Obtener extensión del archivo
    extension = obtener_extension(ruta_archivo)

    # Creamos nombre nuevo de archivo para conservar el original
    nombre_nuevo = (f"{fecha}_"f"paciente_{id_paciente}_"f"{nombre_original}")

    # Creamos la ruta de destino, caso Mantener Arhivo Nuevo:
    destino = os.path.join(Carpeta_Archivos_Originales,nombre_nuevo)

    #Copiamos el aechivo Original y lo guardamos en la carpeta original
    #Asi guardamos una copia del archivo origianl por precaucion
    shutil.copy2(ruta_archivo,destino)

    return os.path.abspath(destino)

#Mostrar informacion del archivo subido
def mostrar_informacion_archivo(ruta_archivo,tipo_archivo,extension):

########################################################
    #Testeando información:

    print("\nInformacion Dek Archivo Subido")

    print("\nArchivo seleccionado:")

    print(os.path.basename(ruta_archivo))

    print("\nRuta original:")

    print(os.path.abspath(ruta_archivo))

    print("\nExtensión:")

    print(extension)

    print("\nTipo de archivo detectado:")

    print(tipo_archivo)
#########################################################

# Testeando la estructura de las carpetas del proyecto MediFlow:

def mostrar_carpetas():

    print("\nEstructura de Almacenamiento de Archivos:")

    print("Carpeta de Almacén local:")
    print(os.path.abspath(Carpeta_Base))


    print("\nCarpeta de Archivos originales:")
    print(os.path.abspath(Carpeta_Archivos_Originales))


    print("\nCarpeta de Imágenes procesadas:")
    print(os.path.abspath(Carpeta_Imagenes_Procesadas))


    print("\nCarpeta de Datos clínicos:")
    print(os.path.abspath(Carpeta_Datos_Clinicos))

###############################################################
#Proprama Principal
def main():
    #
    print("\nFASE-04_MediFlow_G-10_LATAM_Equipo_50")
    print("Seleccion, Validadcion Y Alamacenamiento De Archivos")

    #Paso1 Creamos las Carpetas Correspondientes:
    crear_carpetas()
    print("\nEstructura de Carpetas Verificada")

    #Paso2 Seleccionamos un Archivo:
    print("\nSelecciona un archivo:")
    ruta_archivo = seleccionar_archivo()

    #Se puede optar por cancelar el subir un archivo,
    #Verificamos si se cancela la accion:
    if not ruta_archivo:

        print("\nNo Seleccionaste Ningún Archivo")

        return

    #Realizamos la Obtencion de la Extension del archivo para identificarlo:
    extension = obtener_extension(ruta_archivo)

    #Identificamos tipo de archivo subido por el usuario:
    tipo_archivo = identificar_tipo_archivo(ruta_archivo)

############################################################
    #Testeando Información del Archivo Subido
    mostrar_informacion_archivo(ruta_archivo,tipo_archivo,extension)
    ###################################################################

    #Comenzamos a Validar las extensiones de archivo permitidas por MediFlow
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

    #Solicitamos el ID del Paciente:

    id_paciente = solicitar_id_paciente()
    print("\nID del paciente recibido:")
    print(id_paciente)


    #Procedemos a Guardar el Arhivo Original:

    try:

        ruta_guardada = guardar_archivo_original(ruta_archivo,id_paciente)

    except Exception as error:

        print("\nNo fue posible guardar el archivo, ERROR!")
        print("\nDetalles del error:")
        print(error)

        return


    #Si todo sale bien, Se Guarda Correctamente:
    print("\nArchivo original guardado CORRECTAMENTE!!")
    print("\nRuta del archivo guardado:")
    print(ruta_guardada)

    #Se Muestran las Carpetas:
    mostrar_carpetas()

    #Mandando Mensaje de que todo Salio Bien
    print("\nPROCESO TERMINADO CORRECTAMENTE")

#Ejecutamos el Programa
if __name__ == "__main__":

    main()