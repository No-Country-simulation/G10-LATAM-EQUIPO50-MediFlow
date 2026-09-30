#Configuracion general de MediFlow

#Librerias usadas:
#En este archivo se utilizan las librerias centralizadas
#del archivo librerias.py
from librerias import *

#Obtencion de API_KEY Gemini:
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

#Comprobamos que si esta cargada la API_KEY:
if not GEMINI_API_KEY:

    raise ValueError(
        "\nNo se encontró GEMINI_API_KEY.\n\n"
        "Crea un archivo .env en la carpeta del proyecto "
        "con:\n\n"
        "GEMINI_API_KEY = TU_API_KEY"
    )

print("\nAPI KEY encontrada!!")

#Parte Nueva: Configuracion del Correo
#Obtencion de las Credenciales del correo:
EMAIL_USUARIO = os.getenv("EMAIL_USUARIO")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO")

#Creando Cliente de Gemini
#Creamos el cliente utilizando nuestra API KEY
#Este objeto será el encargado de comunicarse
#con los servicios de Gemini
cliente_gemini = genai.Client(api_key = GEMINI_API_KEY)

#Si todo esta bien:
print("Cliente de Gemini creado")

#Modelo de IA que usaremos
#Mantenemos el modelo en una variable independiente
#para poder cambiarlo facilmente
MODELO_GEMINI = "gemini-3.6-flash"

#Configuracion De Carpetas:
#Obtenemos la ubicación del archivo Python que estamos ejecutando.

#De esta manera MediFlow no depende de la carpeta
#desde la que ejecutemos el comando.
Carpeta_Base = os.path.dirname(os.path.abspath(__file__))

#Obtenemos la carpeta que contiene al backend
Carpeta_Proyecto = os.path.dirname(Carpeta_Base)

# Carpeta principal de almacenamiento
#Almacen_Local se guardara fuera de la carpeta backend
Carpeta_Almacen = os.path.join(Carpeta_Proyecto,"Almacen_Local")

# Carpeta donde guardaremos los originales
Carpeta_Originales = os.path.join(Carpeta_Almacen,"Archivos_Originales")

#Carpeta donde guradaremos los datos clinicos:
Carpeta_Datos_Clinicos = os.path.join(Carpeta_Almacen,"Datos_Clinicos")

#CReando Carpeta para guardar configuracion de umbrales y cargarlos:
Carpeta_Configuracion = os.path.join(Carpeta_Almacen, "configuracion_umbral.json")

#Parte de Reglas Modificables,
#Creacion de carpeta para gestion de reglas,
#si se modifican o no se almacenan las configuradas:
Carpeta_Configuracion_Reglas = os.path.join(Carpeta_Almacen,"configuracion_reglas.json")

#Modelo de IA que usaremos
#Mantenemos las extensiones permitidas centralizadas
Extensiones_Imagen = {
    ".jpg",
    ".jpeg",
    ".png",
    ".png",
    ".bmp",
    ".tiff",
    ".webp"
}

# PDF.
Extensiones_PDF= {".pdf"}

# JSON.
Extensiones_JSON = {".json"}

#Todas las extensiones permitidas juntas
Extensiones_Permitidas = (
    Extensiones_Imagen
    |
    Extensiones_PDF
    |
    Extensiones_JSON
)
