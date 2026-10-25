#Configuracion general de MediFlow

#Librerias usadas:
#En este archivo se utilizan las librerias centralizadas
#del archivo librerias.py
from librerias import *

#Variables importantes de configuracion de MediFlow:
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
MODELO_GEMINI = os.getenv("MODELO_GEMINI", "gemini-2.5-flash") # Valor por defecto seguro

#Parte Nueva: Configuracion del Correo
#Obtencion de las Credenciales del correo:
EMAIL_USUARIO = os.getenv("EMAIL_USUARIO")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO")

#Configuración de Oracle Cloud Infrastructure (OCI) ---
OCI_NAMESPACE = os.getenv("OCI_NAMESPACE")
OCI_REGION = os.getenv("OCI_REGION", "us-ashburn-1")
OCI_TENANCY_OCID = os.getenv("OCI_TENANCY_OCID")
OCI_USER_OCID = os.getenv("OCI_USER_OCID")
OCI_FINGERPRINT = os.getenv("OCI_FINGERPRINT")

# OCI puede venir como archivo físico (Docker local) o texto crudo (Cloud Run)
OCI_PRIVATE_KEY_FILE = os.getenv("OCI_PRIVATE_KEY_FILE")
OCI_PRIVATE_KEY_CONTENT = os.getenv("OCI_PRIVATE_KEY_CONTENT")

# 2. SISTEMA DE VALIDACIÓN PROFESIONAL
# Centralizamos la comprobación para evitar alertas genéricas o caídas inesperadas.
variables_criticas = {
    "GCP_PROJECT_ID": GCP_PROJECT_ID,
    "EMAIL_USUARIO": EMAIL_USUARIO,
    "EMAIL_PASSWORD": EMAIL_PASSWORD,
    "EMAIL_DESTINO": EMAIL_DESTINO,
    "OCI_NAMESPACE": OCI_NAMESPACE,
    "OCI_TENANCY_OCID": OCI_TENANCY_OCID,
    "OCI_USER_OCID": OCI_USER_OCID,
    "OCI_FINGERPRINT": OCI_FINGERPRINT
}

variables_faltantes = [nombre for nombre, valor in variables_criticas.items() if not valor]

if variables_faltantes:
    mensaje_error = (
        f"\n[🚨 CONFIGURATION ERROR] Faltan las siguientes variables de entorno: {', '.join(variables_faltantes)}\n"
        f"👉 Si estás en LOCAL: Asegúrate de definirlas en tu archivo '.env'.\n"
        f"👉 Si estás en CLOUD RUN: Asegúrate de inyectarlas usando la bandera '--set-env-vars' en el despliegue.\n"
    )
    # En lugar de romper el backend con un ValueError agresivo, lanzamos un aviso claro
    print(mensaje_error)

# Validación específica para la llave privada de OCI.
# Se informa la ausencia de la llave sin detener el arranque del backend.
if not OCI_PRIVATE_KEY_FILE and not OCI_PRIVATE_KEY_CONTENT:
    print(
        "\n[AVISO OCI] No se detectó una llave privada de OCI. "
        "Será necesaria si se utiliza ese almacenamiento.\n"
    )

#Creando Cliente de Gemini
#Creamos el cliente utilizando nuestra API KEY
#Este objeto será el encargado de comunicarse
#con los servicios de Gemini
cliente_gemini = genai.Client(
    vertexai=True,
    project=GCP_PROJECT_ID,
    #location="global"
    location="us-central1"
)
#Si todo esta bien:
print("Cliente de Gemini Vertex AI creado con éxito")

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
