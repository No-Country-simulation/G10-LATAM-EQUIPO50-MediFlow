# MEDIFLOW - FASE 05
# Seleccion, Validadcion con Extensió, Almacenamiento De Archivos Y Procesamiento de Imagen

#Libreria para Manipular arhcivos
import os
import shutil

#Libreria de Tiempo, Agregaremos fecha
from datetime import datetime

#Libreria para buscar archivos dentro de la computadora
import tkinter as tk
from tkinter import filedialog

# Librería OpenCV para procesamiento de imágenes
import cv2


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

#Ruta donde se encuentra nuestro archivo de forma actual:
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


#Funcion Seleccion De Archivos Ya sea Imagen,PDF o JSON:
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

    return datetime.now().strftime("Fecha_Creación_Dia%d_Mes%m_Año%Y;" "Hora%H_Minutos%M_Segundos%S")
    #Probando cual Fecha se ve mejor
    #return datetime.now().strftime("Fecha_Creación:_Dia:%d_Mes:%m_Año:%Y_Horario:_Hora:%H_Minuto:%M_Segundo:%S")


# Solicitamos un ID del paciente para identificarlo
def solicitar_id_paciente():

    while True:

        id_paciente = input( "Introduce el ID del Paciente: ").strip()

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
    nombre_nuevo = (f"{fecha}_"f"Paciente_{id_paciente}_"f"{nombre_original}")

    # Creamos la ruta de destino, caso Mantener Arhivo Nuevo:
    destino = os.path.join(Carpeta_Archivos_Originales,nombre_nuevo)

    #Copiamos el aechivo Original y lo guardamos en la carpeta original
    #Asi guardamos una copia del archivo origianl por precaucion
    shutil.copy2(ruta_archivo,destino)

    return os.path.abspath(destino)


#Procesamiento de imagen si el usuario sube una:
def preprocesamiento_imagen(ruta_imagen, ruta_salida):

    print("\nIniciando Pre-Procesamiento de Imagen")

    #Abriendo imagen recibida:
    print("Abriendo Imagen recibida para pre-procesamiento")
    imagen = cv2.imread(ruta_imagen)

    #Si no hay o no se pudo leer,abrir,etc...
    if imagen is None:
        raise ValueError("Error, No fue posible abrir la imagen con Open CV")

    #Si si se abrio correctamente:
    print("La imagen se abrio y leyo correctamente!")
    print("Le aplicaremos unas mejorias a la imagen")

    #Paso1 pasamos la imagen a escala de grises para aplicar filtros:
    gris = cv2.cvtColor(imagen,cv2.COLOR_BGR2GRAY)
    print("Se aplico escala de grises a la imagen")

    #Aplicamos Filtro Clahe:
    clahe = cv2.createCLAHE(clipLimit = 2.0,tileGridSize = (8,8))
    #Mejorando imagen con filtro clahe
    mejorada = clahe.apply(gris)
    print("Filtro clahe aplicado")

    #Aplicamos filtro Gaussiano para reducir Ruido:
    suavizada = cv2.GaussianBlur(mejorada,(3,3),0) #->Cero por que esta en escala de grises
    print("Filtro Gaussiano Aplicado")

    #Aplicamos filtro de enfoque:
    enfoque = cv2.addWeighted(mejorada,1.5,suavizada,-0.5,0)
    print("Filtro de Enfoque aplicado")

    #Guardando imagen pre-procesada:
    print("Guardando Imagen con FILTRO APLICADOS")
    resultado = cv2.imwrite(ruta_salida,enfoque)

    #Por si no se guarda la imagen:
    if not resultado:
        raise ValueError("NO Fue posible Guardar la Imagen Pre-PRocesada")

    #Si todo Salio bien:
    print("Imagen con Filtros Aplicados Guardada Correctamente")

    return os.path.abspath(ruta_salida)

#Creando Nombre de la imagen Pre-Procesada Para Guardarla:
def crear_nombre_imagen_procesada(ruta_original):

    #Imagen Original:
    nombre_archivo = os.path.basename(ruta_original)

    nombre_sin_extension = os.path.splitext(nombre_archivo)[0]

    extension = os.path.splitext(nombre_archivo)[1]

    nombre_procesada = (f"{nombre_sin_extension}" f"_PROCESADA" f"{extension}")

    return nombre_procesada



#Mostrar informacion del archivo subido
def mostrar_informacion_archivo(ruta_archivo,tipo_archivo,extension):
########################################################
    #Testeando información:

    print("\nInformacion Del Archivo Subido")

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
    print("\nFASE-05_MediFlow_G-10_LATAM_Equipo_50")
    print("Seleccion, Validadcion, Alamacenamiento De Archivos y Pre-Procesamiento de Imagen")

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

    #Paso3 Obtenoendo Extension
    #Realizamos la Obtencion de la Extension del archivo para identificarlo:
    extension = obtener_extension(ruta_archivo)

    #Paso4 Identificar Tipo
    #Identificamos tipo de archivo subido por el usuario:
    tipo_archivo = identificar_tipo_archivo(ruta_archivo)

############################################################
    #Testeando Información del Archivo Subido
    mostrar_informacion_archivo(ruta_archivo,tipo_archivo,extension)
    ###################################################################

    #Comenzamos a Validar las extensiones de archivo permitidas por MediFlow
    #Validamos el tipo de archivo subido por el usuario:
    #Paso5 Validamos el archivo que subimos con las extensiones propuestas:

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

    #Paso6 Solicitamos el ID del Paciente:
    id_paciente = solicitar_id_paciente()
    print("\nID del paciente recibido:")
    print(id_paciente)


    #Paso7 Procedemos a Guardar el Arhivo Original Nuevo,
    #Para no afectar los archivos que suba el usuario:
    try:

        ruta_guardada = guardar_archivo_original(ruta_archivo,id_paciente)

    except Exception as error:

        print("\nNo fue posible guardar el archivo, ERROR!")
        print("\nDetalles del error:")
        print(error)

        return


    #Si todo sale bien, Se Guarda Correctamente los nuevos archivos originales:
    print("\nArchivo original guardado CORRECTAMENTE!!")
    print("\nRuta del archivo guardado:")
    print(ruta_guardada)

    #Paso8 Si El archivo subido es una imagen se aplica pre-procesamiento:
    if tipo_archivo == "Imagen":
        print("\nIniciando Aplicacion de Filtros a la Imagen")
        #Creando nombre filtrada
        nombre_procesado = (crear_nombre_imagen_procesada(ruta_guardada))
        #Creando direccion donde se guardara la imagen filtrada:
        ruta_salida = os.path.join(Carpeta_Imagenes_Procesadas,nombre_procesado)

        #Procesar Imagen:
        try:
            #Ejecutamos la funcion:
            # ruta_guardada = imagen original almacenada
            # ruta_salida = ubicación donde queremos crear la imagen procesada
            ruta_imagen_procesada = preprocesamiento_imagen(ruta_guardada,ruta_salida)

        except Exception as error:
            print("\nNO Fue posible procesar la imagen, ERROR")
            print("Detalles del Error")
            print(error)

            print("\nIMPORTANTE")
            print("El archivo Original se guardo Correctamen")
            return

    #   Testeando resultados de pre-procesamiento
        print("\nFiltros aplicado a la imagen terminado correctamente")

        print("\nImagen Original")
        print(ruta_guardada)

        print("\nImagen Filtrada")
        print(ruta_imagen_procesada)

    else:
        print("\nEl archivo no era una imagen")
        print("No se aplicara pre-procesamiento")
    
#############################################
    #Se Muestran las Carpetas:
    mostrar_carpetas()

    #Mandando Mensaje de que todo Salio Bien
    print("\nPROCESO TERMINADO CORRECTAMENTE")

#Ejecutamos el Programa
if __name__ == "__main__":

    main()