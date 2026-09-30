#LangGraph y generacion de JSON FINAL, Umbrales, Reglas, 
#Enrutamiento, Correo listo

#Libreriras usadas:
#Permite trabajar con rutas, archivos y carpetas.
import os

#Permite copiar el archivo original.
import shutil

# Permite obtener fecha y hora para generar
from datetime import datetime

# Facilita trabajar con nombres y extensiones.
from pathlib import Path

#Parte Nueva:
#JSON: 
#Nos permitira comprobar posteriormente si Gemini,devuelve JSON valido 
import json

#SDK oficial de Gemini 
from google import genai

#CARGAR VARIABLES DE ENTORNO DESDE EL ARCHIVO .ENV
#Esto busca el archivo .env y carga sus variables
#en la memoria del sistema. Cargando la API_KEY de Gemini:
#No olvidar 
from dotenv import load_dotenv
load_dotenv()

#Parte Nueva: Envio de alertas por correo
#Librerias incluidas en Python para crear y enviar correos
import smtplib
from email.message import EmailMessage

#LangGraph:
from langgraph.graph import StateGraph, START, END

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

#Funcion para asegurarse que las credenciales del correo existen:
def validar_configuracion_correo():
    """
    Verifica que las variables necesarias
    estén definidas en el archivo .env.
    """

    if not EMAIL_USUARIO:
        raise ValueError("No se encontro EMAIL_USUARIO en el archivo .env")

    if not EMAIL_PASSWORD:
        raise ValueError("No se encontro EMAIL_PASSWORD en el archivo .env")

    if not EMAIL_DESTINO:
        raise ValueError("No se encontro EMAIL_DESTINO en el archivo .env")

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

#Cambio Nuevo Parte1: CONFIGURACIÓN DE UMBRALES
#Los umbrales NO representan gravedad médica,
#Representan el puntaje de INCONSISTENCIAS en el DOCUMENTO,
#Que detecta LangGraph mediante reglas de validación establecidas
#Ejemplo con los valores por defecto(Prueba por ahora):
#   0 - 19  -> NORMAL
#   20 - 59 -> REVISIÓN
#   60 -100 -> ALERTA

#El usuario podrá modificar estos valores al iniciar el programa,
#Se guardarán en un archivo JSON para no tener que escribirlos
#nuevamente en cada ejecución.

#CReando Carpeta para guardar configuracion de umbrales y cargarlos:
Carpeta_Configuracion = os.path.join(Carpeta_Almacen, "configuracion_umbral.json")

UMBRALES_DEFECTO = {
    "umbral_normal"  :  20,
    "umbral_revision":  40,
    "umbral_alerta"  :  60
}


def validar_umbrales(umbrales):
    """
    Cambio Nuevo Parte2
    Menos peso agregado significa que tiene mas inforamción el documento,
    Comprueba que los tres umbrales estén entre 0 y 100
    y que respeten el orden lógico establecido:

        NORMAL < REVISIÓN < ALERTA

    Esto evita configuraciones imposibles como:
        normal   = 60
        revision = 40
        alerta   = 20
    """
    try:
        normal      = int(umbrales["umbral_normal"])
        revision    = int(umbrales["umbral_revision"])
        alerta      = int(umbrales["umbral_alerta"])
    except (KeyError, TypeError, ValueError):
        return False

    return (0 <= normal < revision < alerta <= 100)


def guardar_configuracion_umbrales(umbrales):
    """
    Cambio Nuevo Parte3

    Guarda los umbrales elegidos por el usuario en:
        Almacen_Local/configuracion_umbral.json

    Así la configuración permanece disponible para la siguiente ejecución
    """
    if not validar_umbrales(umbrales):
        raise ValueError(
            "Los umbrales deben cumplir: "
            "0 <= NORMAL < REVISIÓN < ALERTA <= 100."
        )

    with open(Carpeta_Configuracion, "w", encoding="utf-8") as archivo:
        json.dump(umbrales, archivo, ensure_ascii=False, indent=4)


def cargar_configuracion_umbrales():
    """
    Cambio Nuevo Parte4

    Carga una configuración previamente guardada,
    Si no existe o está dañada, utiliza los valores por defecto establecidos
    """
    if not os.path.isfile(Carpeta_Configuracion):
        return UMBRALES_DEFECTO.copy()

    try:
        with open(Carpeta_Configuracion, "r", encoding="utf-8") as archivo:
            umbrales = json.load(archivo)

        if validar_umbrales(umbrales):
            return {
                "umbral_normal"  :  int(umbrales["umbral_normal"]),
                "umbral_revision":  int(umbrales["umbral_revision"]),
                "umbral_alerta"  :  int(umbrales["umbral_alerta"])
            }

    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass

    print("\nLa configuración de umbrales no es válida.")
    print("Se utilizarán los valores por defecto!!\n")
    return UMBRALES_DEFECTO.copy()


def mostrar_explicacion_umbrales(umbrales):
    """
    Cambio Nuevo Parte5

    Explicando al usuario qué significa cada rango antes de pedirle
    si desea modificarlo el rango de cada umbral
    """
    normal      =   umbrales["umbral_normal"]
    revision    =   umbrales["umbral_revision"]
    alerta      =   umbrales["umbral_alerta"]

    print("\nCONFIGURACIÓN DE UMBRALES DE COHERENCIA DEL DOCUMENTO SUBIDO: ")
    print("\nMediFlow calcula un PUNTAJE DE INCONSISTENCIA con rango de: 0 a 100")
    print("Este puntaje NO es una Calificación Médica y Tampoco mide la gravedad")
    print("de un paciente. Mide cuántas inconsistencias tiene el documento subido por el usuario,")
    print("que se detectan mediante las reglas de validación de MediFlow IA Equipo50 G-10 LATAM.")
    print("\nMientras MAYOR sea el puntaje establecido: ")
    print("Quiere decir que hay mayor cantidad/peso de inconsistencias detectadas en el documento dado")
    print("\nRANGOS ACTUALES: \n")
    print(f"0 - {normal - 1}        :   NORMAL")
    print(f"{normal} - {revision - 1}       :   REVISIÓN")
    print(f"{revision} - {alerta - 1}       :   REVISIÓN PRIORITARIA")
    print(f"{alerta} - 100      :   ALERTA")
    print("\nNOTA: tanto REVISIÓN como REVISIÓN PRIORITARIA requieren la")
    print("revisión humana; La segunda indica un puntaje más alto.")
    print("La ALERTA se alcanza cuando el puntaje es igual o mayor")
    print("que el umbral_alerta establecido.")
    print("\nEjemplo:")
    print(f"Si un documento obtiene {normal - 1} puntos Se Asigna:      NORMAL")
    print(f"Si obtiene {normal} puntos Se Asigna:                   Comienzar la zona de REVISIÓN")
    print(f"Si obtiene {alerta} puntos Se Asigna:                   ALERTA\n")


def solicitar_configuracion_umbrales():
    """
    Cambio Nuevo Parte6

    Pregunta al usuario si desea modificar los umbrales y
    Valida los valores introducidos para despues guardar estos
    """
    umbrales = cargar_configuracion_umbrales()

    mostrar_explicacion_umbrales(umbrales)

    respuesta = input("\n¿Deseas modificar estos valores? (Responde con: si o no): ").strip().lower()

    if respuesta not in {"s", "si", "sí", "Si"}:
        print("\nSe conservarán los umbrales actuales!")
        return umbrales

    while True:
        try:
            print("\nIntroduce los nuevos valores en el Rango de entre 0 y 100, por favor.")
            print("Recuerda, la prioridad establecida es: NORMAL < REVISIÓN < ALERTA \n")

            normal      =   int(input("Nuevo umbral NORMAL: ").strip())
            revision    =   int(input("Nuevo umbral REVISIÓN: ").strip())
            alerta      =   int(input("Nuevo umbral ALERTA: ").strip())

            nuevos_umbrales = {
                "umbral_normal":    normal,
                "umbral_revision":  revision,
                "umbral_alerta":    alerta
            }

            if not validar_umbrales(nuevos_umbrales):
                print("\nConfiguración inválida!!!")
                print("IMPORTANTE!: Debe cumplirse: 0 <= NORMAL < REVISIÓN < ALERTA <= 100")
                continue

            guardar_configuracion_umbrales(nuevos_umbrales)

            print("\nUmbrales actualizados correctamente!!")
            print(f"NORMAL:                 0 a {normal - 1}")
            print(f"REVISIÓN:               {normal} a {revision - 1}")
            print(f"REVISIÓN PRIORITARIA:   {revision} a {alerta - 1}")
            print(f"ALERTA:                 {alerta} a 100")

            return nuevos_umbrales

        except ValueError:
            print("\nDebes introducir únicamente números enteros.")


#Parte de Reglas Modificables,
#Creacion de carpeta para gestion de reglas,
#si se modifican o no se almacenan las configuradas:
Carpeta_Configuracion_Reglas = os.path.join(Carpeta_Almacen,"configuracion_reglas.json")
 
#Reglas por defecto para LangGraph:
#Cada categoria tiene sus propias reglas,
#El valor representa cuantos puntos se agregan al puntaje de incoherencia,
#Cuando se encuentra esa condicion,
#LangGraph seleccionara automaticamente el bloque correcto
#Dependiendo de la categoria clasificada por Gemini

REGLAS_DEFECTO = {

    "Receta Médica": {

        "sin_medicamentos": 30,

        "sin_medicamentos_tratamiento": 20,

        "sin_id_paciente": 5,

        "sin_nombre_paciente": 10,

        "sin_nombre_medico": 5,

        "recomendaciones_sin_medicamentos": 20
    },

    "Informe de Estudio de Diagnóstico por Imágenes/Laboratorio": {

        "sin_estudios": 40,

        "estudio_sin_resultado": 10,

        "maximo_estudio_sin_resultado": 20
    },

    "Orden de Solicitud de Procedimiento": {

        "sin_procedimientos": 40
    },

    "Epicrisis / Informe de Alta": {

        "sin_diagnosticos": 20,

        "sin_tratamiento": 20,

        "sin_seguimiento": 10
    },

    "Certificado Médico": {

        "sin_nombre_paciente": 20,

        "sin_nombre_medico": 20
    },

    "ambiguidad": {

        "por_dato": 5,

        "maximo": 20
    }
}

#Funcion para Validar Reglas:
#Verifica que la configuracion de reglas tenga la estructura
#necesaria antes de entregarla a LangGraph
def validar_reglas(reglas):

    if not isinstance(reglas, dict):

        return False

    categorias = [
        "Receta Médica",
        "Informe de Estudio de Diagnóstico por Imágenes/Laboratorio",
        "Orden de Solicitud de Procedimiento",
        "Epicrisis / Informe de Alta",
        "Certificado Médico",
        "ambiguidad"
    ]

    for categoria in categorias:

        if categoria not in reglas:

            return False

        if not isinstance(reglas[categoria], dict):

            return False

        for valor in reglas[categoria].values():

            if not isinstance(valor, int):

                return False

            if valor < 0 or valor > 100:

                return False

    return True

#Funcion para Guardar la Configuracion De Reglas:
def guardar_configuracion_reglas(reglas):

    try:

        with open(Carpeta_Configuracion_Reglas,"w",encoding="utf-8") as archivo:
            json.dump(reglas,archivo,ensure_ascii=False,indent=4)

        print("\nConfiguracion de reglas guardada CORRECTAMENTE!")

    except Exception as error:

        print(f"\nNo se pudo guardar la configuracion de reglas: {error}")


#Funcion para Cargar Configuracion De Reglas:
def cargar_configuracion_reglas():

    if not os.path.exists(Carpeta_Configuracion_Reglas):

        return json.loads(json.dumps(REGLAS_DEFECTO,ensure_ascii=False))

    try:

        with open(Carpeta_Configuracion_Reglas,"r",encoding="utf-8") as archivo:
            reglas = json.load(archivo)

        if validar_reglas(reglas):

            return reglas

        print("\nLa configuracion guardada de reglas no es valida")

        return json.loads(json.dumps(REGLAS_DEFECTO,ensure_ascii=False))

    except Exception as error:

        print(f"\nError al cargar las reglas: {error}")

        return json.loads(json.dumps(REGLAS_DEFECTO,ensure_ascii=False))


#Funcion para explicar las Reglas
def mostrar_explicacion_reglas(reglas):

    print("\nREGLAS ACTUALES DE LANGGRAPH")

    print("\nCada regla agrega puntos al puntaje de incoherencia del documento subido,")

    print("Entre mayor sea el valor, mayor sera el impacto de esa inconsistencia")

    print("\nLangGraph NO aplica todas las reglas al mismo tiempo,")

    print("Primero identifica la categoria y despues selecciona automaticamente las reglas correspondientes\n")

    for categoria, reglas_categoria in reglas.items():

        print(f"\n[{categoria}]")

        for nombre_regla, valor in reglas_categoria.items():

            print(f"  {nombre_regla}: +{valor} puntos")


#Funcion para Configurar de manera Interativa las Reglas
# El usuario puede modificar los pesos de las reglas,
#IMPORTANTE:
#El usuario modifica los valores,
#pero NO modifica la logica de LangGraph
#Esto permite mantener controlada la logica del sistema y no pase algo malo jejeje
def solicitar_configuracion_reglas():

    reglas = cargar_configuracion_reglas()

    mostrar_explicacion_reglas(reglas)

    respuesta = input("\n¿Deseas modificar las reglas de LangGraph? (Responde: si/no): ").strip().lower()

    if respuesta not in ["s", "si", "sí", "Si"]:

        print("\nSe utilizaran las reglas actuales!!")

        return reglas

    print("\nMODIFICACION DE REGLAS")

    print("\nPuedes introducir un nuevo valor")

    print("Si presionas ENTER, se conservara el valor actual ")

    print("\nEjemplo: ")

    print(
        "Una regla de +30 significa que esa inconsistencia, "
        "AGREGA 30 puntos al puntaje"
    )

    for categoria in reglas:

        print("\n" + "-" * 70)

        print(f"CATEGORIA: {categoria}")

        for nombre_regla in reglas[categoria]:

            valor_actual = reglas[categoria][nombre_regla]

            while True:

                nuevo_valor = input(f"\n{nombre_regla} " f"[actual {valor_actual}]: ").strip()

                if nuevo_valor == "":
                    break

                try:

                    nuevo_valor = int(nuevo_valor)

                    if 0 <= nuevo_valor <= 100:

                        reglas[categoria][nombre_regla] = nuevo_valor

                        break

                    print("ERROR: El valor debe estar en un rango entre 0 y 100")

                except ValueError:

                    print("ERROR: Introduce un numero entero!!!")

    if validar_reglas(reglas):

        guardar_configuracion_reglas(reglas)

        print("\nLas nuevas reglas se guardaron EXITOSAMENTE!!!")

    else:

        print("\nLa configuracion NO es valida!!!!: ")

        print("Se utilizaran las reglas por DEFECTO!!")

        reglas = json.loads(json.dump(REGLAS_DEFECTO,ensure_ascii=False))

    mostrar_explicacion_reglas(reglas)

    return reglas


#Funcion para la creacion de Carpetas:
def crear_carpetas_base():
    """
    Crea todas las carpetas necesarias para MediFlow Equipo50 G-10 LATAM

    exist_ok=True significa:

        - Si la carpeta NO existe, la crea.
        - Si la carpeta YA existe, no genera error.
    """

    print("\nCreando Estructura del Proyecto MediFlow Equipo50 G-10 LATAM")

    #Creacion de carpeta de almacenamiento
    os.makedirs(Carpeta_Almacen,exist_ok=True)
    print("Almacen_Local/")

    #Creacion de Carpeta de Archivos Originales sin modificarlos (REspaldo)
    os.makedirs(Carpeta_Originales,exist_ok=True)
    print("\nAlmacen_Local/Archivos_Originales/")


    #Creacion de carpeta de Datos clinicos 
    os.makedirs(Carpeta_Datos_Clinicos,exist_ok=True)
    print("Almacen_Local/Datos_Clinicos/")
    print("Estructura creada correctamente.")

#Extensiones Permitida,
#Imagenes que el Proyecto MediFlow aceptara: 
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

# Solicitar Ruta de Archivo:
def seleccionar_archivo():
    """
    Solicita al usuario la ubicación del archivo
    desde la Terminal.
    
    Ejemplo:

        /Users/usuario/Desktop/receta.pdf

    También puedes arrastrar un archivo desde el Escritorio
    directamente a la Terminal.
    """
    print("\nSeleccion De Archivo")
    print("Introduce la ruta completa del archivo.")
    print("También puedes arrastrar el archivo desde El Escritorio hasta esta Terminal\n")

    ruta_archivo = input("\nRuta del archivo: ").strip()

    #Comprobar que el usuario haya introducido algo:
    if not ruta_archivo:

        raise ValueError("No se introdujo ninguna ruta.")

    #quitando las comillas para que reconozca la ruta bien:
    ruta_archivo = ruta_archivo.strip("'\"")

    # Expandir ~ APLICAR ESTO POR QUE ME CASUSA ERROR
    # Por ejemplo:
    # ~/Desktop/receta.pdf
    # se convierte en:
    # /Users/usuario/Desktop/receta.pdf
    ruta_archivo = os.path.expanduser(ruta_archivo)

    # Convertir a ruta absoluta.
    ruta_archivo = os.path.abspath(ruta_archivo)

    # Comprobar que realmente exista el archivo
    if not os.path.isfile(ruta_archivo):

        raise FileNotFoundError("\nEl archivo no existe:\n"f"{ruta_archivo}")

    print("Archivo encontrado")

    return ruta_archivo

# Obtencion de la Extension del Archivo:
def obtener_extension(ruta_archivo):
    """
    Obtiene únicamente la extensión del archivo.

    Ejemplo:
        receta.PDF
    
    devuelve:
        .pdf

    Utilizamos lower() para que:
        .PDF
        .Pdf
        .pdf

    sean tratados de la misma manera y no cometer errores de lectura
    """

    extension = Path(ruta_archivo).suffix.lower()

    return extension

# Validamos la Extension del Archivo:
def validar_extension(ruta_archivo):
    """
    Comprueba que el archivo tenga una extensión
    aceptada por MediFlow.
    Devuelve el tipo de archivo:
        imagen
        pdf
        json

    Si no es compatible, genera un error.
    """

    extension = obtener_extension(ruta_archivo)
    print(f"\nExtensión detectada: {extension}")

    # Comprobar si la extensión está permitida.
    if extension not in Extensiones_Permitidas:

        raise ValueError(

            "\nArchivo no compatible con MediFlow.\n"

            f"Extensión recibida: {extension}\n\n"

            "Extensiones permitidas:\n"

            f"{sorted(Extensiones_Permitidas)}\n\n"

            "HEIC y HEIF no están permitidos."
        )

    #Identificando tipo de Archivos:

    if extension in Extensiones_Imagen:
        tipo_archivo = "imagen"

    # Identificar PDF.
    elif extension in Extensiones_PDF:
        tipo_archivo = "pdf"

    # Identificar JSON.
    elif extension in Extensiones_JSON:
        tipo_archivo = "json"

    else:
        raise ValueError("\nNo fue posible identificar el tipo de archivo subido")

    print(f"Tipo de archivo\n: {tipo_archivo}")

    return tipo_archivo


#Generando nombre del archivo
def generar_nombre_archivo(ruta_archivo):
    """
    Genera un nuevo nombre para el archivo,
    Por ejemplo tenemos:
        receta.pdf

    Este se convierte en:
        Fecha_Creacion_Dia1_Mes9_Año206_receta.pdf

    Esto nos ayuda a:
         conservar el nombre original,
         evitar colisiones,
         identificar cuando fue almacenado
    """

    # Obteniendo el nombre original
    nombre_original = os.path.basename(ruta_archivo)

    # Obteniendo nombre sin extensión
    nombre_sin_extension = Path(nombre_original).stem

    # Obteniendo extensión
    extension = Path(nombre_original).suffix.lower()

    #ESTO PASA MUCHO
    #Reemplazar espacios.
    #Ejemplo:    
    #"Receta Juan Perez.pdf"
    #se convierte en:
    #"Receta_Juan_Perez.pdf"
    #Limpiando nombre de archivo:
    nombre_limpio = (nombre_sin_extension.replace(" ", "_"))

    #Generar fecha y hora del Archivo
    fecha_hora = datetime.now().strftime("Fecha_Creacion_Dia%d_Mes%m_Año%Y;Horario_Hora%H_Minutos%M_Segundos%S")

    #Construir nombre final del archivo ya limpio
    nombre_nuevo = (f"{fecha_hora}_"f"{nombre_limpio}"f"{extension}")

    return nombre_nuevo

#Gardamos el Archivo Original subido por el usuario:
def guardar_archivo_original(ruta_archivo):
    """
    Copia el archivo original a:
        almacen_local/archivos_originales/

    IMPORTANTE:
    No modificamos el archivo original.
    Solamente hacemos una copia.
    """

    #Generando el nuevo nombre del Archivo subido por el Usuario:
    nombre_nuevo = generar_nombre_archivo(ruta_archivo)

    #Construyendo ruta final del archivo para despues guardarlo
    ruta_destino = os.path.join(Carpeta_Originales,nombre_nuevo)

    #Copiando archivo Original
    shutil.copy2(ruta_archivo,ruta_destino)

    #Verificamos que realmente se haya creado el lugar donde se guardara el archivo copiado
    if not os.path.isfile(ruta_destino):

        raise IOError("El archivo no se pudo guardar correctamente.")

    print("\nArchivo guardado correctamente!!")

    #Testeando:
    print(f"\nNombre generado:\n"f"{nombre_nuevo}")
    print(f"\nUbicación:\n"f"{ruta_destino}")

    return ruta_destino, nombre_nuevo

#Mostrando informacion del archivo: TESTEANDO!!!!!!!
def mostrar_informacion(ruta_original,tipo_archivo,ruta_guardada,nombre_generado):
    """
    Muestra un resumen de lo ocurrido,
    Esta función solamente informa al usuario pero
    No modifica archivos.
    """
    print("\nTesteando REsultados")
    print(f"\nArchivo seleccionado:"f"\n{ruta_original}")
    print(f"\nTipo:"f"\n{tipo_archivo}")
    print(f"\nNombre Generado:"f"\n{nombre_generado}")
    print(f"\nArchivo guardado:"f"\n{ruta_guardada}")
    print("\nLa copia original está lista para las siguientes fases.")

#Parte nueva Gemini:
#Funcion para Obtener el  MIME TYPE para Gemini CHECAR
def obtener_mime_type(ruta_archivo):
    """
    Esta funcion, obtiene el MIME type del archivo,
    ya que Gemini necesita conocer el tipo de contenido
    cuando enviamos archivos
    Ejemplos de los archivos:

        PDF  -> application/pdf
        JPG  -> image/jpeg
        PNG  -> image/png
        JSON -> application/json
    """

    extension = Path(ruta_archivo).suffix.lower()
    mapa_mime = {

        ".jpg": "image/jpeg",

        ".jpeg": "image/jpeg",

        ".png": "image/png",

        ".bmp": "image/bmp",

        ".tiff": "image/tiff",

        ".webp": "image/webp",

        ".pdf": "application/pdf",

        ".json": "application/json"
    }

    mime_type = mapa_mime.get(extension)

    #Si se sube otro tipo de archivo mandamos alerta
    if not mime_type:

        raise ValueError(
            f"No existe MIME type configurado "
            f"para {extension}"
        )
    #Testeando que el MIME type bien
    print(f"MIME type: {mime_type} Aceptado por MediFlow")

    return mime_type

#Funcion para subir archivo a gemini:
def subir_archivo_a_gemini(ruta_archivo):
    """
    Envia el archivo a Gemini.
    IMPORTANTE:
    Aqui NO estamos analizando todavia el documento
    Después utilizaremos el archivo subido
    para realizar el analisis
    """

    #Testeando:
    print("\nSubiendo Archivo a Gemini")
    print(f"\nArchivo:\n{ruta_archivo}")

    # Subimos el Archivo
    archivo_gemini = cliente_gemini.files.upload(file = ruta_archivo)
    print("\nArchivo subido correctamente!!!")

    #Mostramos la informacion proporcionada por Gemini:
    print(f"\nNombre asignado por Gemini:" f"\n{archivo_gemini.name}")

    return archivo_gemini

#Funcion de Prompt:
#Creando Prompt de prueba
#Creando Prompt Clinico
def crear_prompt_prueba(tipo_archivo,nombre_archivo):
    """
    Pidiendo Estructura clinica Gemini
    """

    prompt = f"""


Eres el sistema de análisis documental Medico de MediFlow, eres critico, experto en area medica, empatico y
y tú función es analizar cuidadosamente el archivo proporcionado y extraer información clínica estructurada,
Has recibido un archivo de tipo:

{tipo_archivo}

Aplicando regla fundamental para la generacion del nombre de archivo:
Debes copiar EXACTAMENTE este nombre en:

"nombre_archivo"

NO debes modificarlo.

NO debes traducirlo.

NO debes resumirlo.

NO debes cambiar fechas.

NO debes cambiar números.

NO debes cambiar mayúsculas o minúsculas.

El valor debe ser exactamente:

{nombre_archivo}

Aplicando Reglas de Extracción del archivo:

Analiza TODO el contenido de manera meticulosamente que este disponible del archivo,
Puede tratarse de:
- Imagen médica
- PDF médifo
- Archivo JSON con información médica

Pero Extrae únicamente información que aparezca
explícitamente en el documento,
ESTÁ ESTRICTAMENTE PROHIBIDO INVENTAR INFORMACIÓN.

Si un dato individual NO aparece,
utiliza:
null

Si una lista no contiene información,
utiliza:
[]

Si una sección no tiene información,
utiliza:
null

Si existe información pero no puede leerse con
seguridad, NO intentes adivinarla ni inventes nada,
Agrégala a:
"datos_no_legibles_o_ambiguos"


Aplicando Reglas sobre información a extraer del CLASIFICACIÓN DEL DOCUMENTO,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:
Identifica la categoría del documento.

Utiliza únicamente una de estas categorías:

1. Receta Médica

2. Informe de Estudio de
   Diagnóstico por Imágenes/Laboratorio

3. Orden de Solicitud de Procedimiento

4. Epicrisis / Informe de Alta

5. Certificado Médico

6. Otro

Queda estrictamente prohibido invertar alguna categoria de clasificacion del documento.

Aplicando Reglas sobre información a extraer del CLASIFICACIÓN DE RIESGO DOCUMENTAL,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:

IMPORTANTE:

No realices un diagnóstico médico.

No inventes una urgencia.

Solamente identifica señales explícitas
presentes en el documento.

Determina:

- urgente
- datos ambiguos
- datos faltantes

Si existe información explícita que indique
una situación urgente o que requiere atención
inmediata, registra:

urgente = true

y explica el motivo.

Si existe información ilegible,
contradictoria o dudosa:

agregarla a datos_ambiguos.

Si falta información necesaria para comprender
o procesar correctamente el documento:

agregarla a datos_faltantes.


Aplicando Reglas sobre información a extraer del PACIENTE,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:

- ID del paciente
- Nombre completo
- Fecha de nacimiento
- Edad
- Sexo
- CURP
- Teléfono
- Correo
- Dirección
- Peso
- Altura
- Alergias
- Antecedentes médicos
- Antecedentes quirúrgicos
- Antecedentes familiares

Aplicando Reglas sobre información a extraer del MEDICO,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:

- Nombre completo
- Especialidad
- Cédula profesional
- Institución
- Teléfono
- Correo

Aplicando Reglas sobre información a extraer de la INFORMACION DE LA CONSULTA MEDICA,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:

- Fecha
- Hora
- Motivo de consulta
- Síntomas
- Signos
- Observaciones

Aplicando Reglas sobre información a extraer de los DIAGNÓSTICOS,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible,
Para cada diagnóstico intenta obtener:

- Nombre
- Descripción
- Código
- Tipo

Extrae los diagnósticos explícitamente presentes.
NO generes diagnósticos propios.


Aplicando Reglas sobre información a extraer de los SIGNOS VITALES,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:

- Presión arterial
- Frecuencia cardiaca
- Frecuencia respiratoria
- Temperatura
- Saturación de oxígeno
- Glucosa

Aplicando Reglas sobre información a extraer de los MEDICAMENTOS,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:

Extrae TODOS los medicamentos encontrados.

Para cada medicamento intenta identificar:

- Nombre
- Principio activo
- Presentación
- Concentración
- Dosis
- Unidad de dosis
- Vía de administración
- Frecuencia
- Duración
- Cantidad
- Indicaciones

Aplicando Reglas sobre información a extraer del TRATAMIENTO,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:

- Descripción
- Medicamentos
- Procedimientos
- Terapias
- Recomendaciones
- Cuidados
- Restricciones
- Dieta
- Actividad física

Aplicando Reglas sobre información a extraer de los ESTUDIOS MEDICOS,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:

- Tipo
- Nombre
- Fecha
- Resultado
- Unidades
- Rango de referencia
- Interpretación

Aplicando Reglas sobre información a extraer de los PROCEDIMIENTOS,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:

- Nombre
- Fecha
- Descripción
- Resultado

Aplicando Reglas sobre información a extraer del SEGUIMIENTO,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:

- Próxima cita
- Indicaciones de seguimiento
- Signos de alarma
- Observaciones

Aplicando Reglas sobre el FORMATO DE RESPUESTA:
Devuelve ÚNICAMENTE JSON válido.

NO utilices Markdown.

NO escribas:

```json

NO agregues explicaciones antes o después
del JSON.


La estructura debe ser EXACTAMENTE:

{{
    "nombre_archivo": "{nombre_archivo}",

    "tipo_archivo": "{tipo_archivo}",

    "documento": {{
        "es_documento_medico": null,
        "tipo_documento": null,
        "fecha_documento": null,
        "numero_documento": null,
        "institucion_medica": null
    }},

    "paciente": {{
        "id_paciente": null,
        "nombre_completo": null,
        "fecha_nacimiento": null,
        "edad": null,
        "sexo": null,
        "curp": null,
        "telefono": null,
        "correo": null,
        "direccion": null,
        "peso_kg": null,
        "altura_cm": null,
        "alergias": [],
        "antecedentes_medicos": [],
        "antecedentes_quirurgicos": [],
        "antecedentes_familiares": []
    }},

    "medico": {{
        "nombre_completo": null,
        "especialidad": null,
        "cedula_profesional": null,
        "institucion": null,
        "telefono": null,
        "correo": null
    }},

    "consulta": {{
        "fecha": null,
        "hora": null,
        "motivo_consulta": null,
        "sintomas": [],
        "signos": [],
        "observaciones": null
    }},

    "diagnosticos": [],

    "signos_vitales": {{
        "presion_arterial": null,
        "frecuencia_cardiaca_lpm": null,
        "frecuencia_respiratoria_rpm": null,
        "temperatura_c": null,
        "saturacion_oxigeno_porcentaje": null,
        "glucosa_mg_dl": null
    }},

    "medicamentos": [],

    "tratamiento": {{
        "descripcion": null,
        "medicamentos": [],
        "procedimientos": [],
        "terapias": [],
        "recomendaciones": [],
        "cuidados": [],
        "restricciones": [],
        "dieta": null,
        "actividad_fisica": null
    }},

    "estudios": [],

    "procedimientos": [],

    "seguimiento": {{
        "proxima_cita": null,
        "indicaciones_seguimiento": [],
        "signos_alarma": [],
        "observaciones": null
    }},

    "datos_no_legibles_o_ambiguos": [],

    "observaciones": null,

    "clasificacion_riesgo": {{
            "urgente": false,
            "motivo_urgencia": null,
            "datos_ambiguos": [],
            "datos_faltantes": []
        }},
    
        "clasificacion_documento": {{
            "categoria": "Otro"
        }}
}}


RECUERDA:

1. NO INVENTAR INFORMACIÓN.
2. USAR null SI EL DATO NO EXISTE.
3. USAR [] SI NO EXISTEN ELEMENTOS.
4. INFORMAR DATOS ILEGIBLES EN
   "datos_no_legibles_o_ambiguos".
5. CONSERVAR EXACTAMENTE EL NOMBRE DE ARCHIVO.
6. DEVOLVER ÚNICAMENTE JSON VÁLIDO.

"""

    return prompt

#Por si Gemini devuelve un json sucio,
#Funcion para limpiar JSON:
def limpiar_respuesta_json(texto_respuesta):
    """
    Limpia posibles bloques Markdown
    alrededor del JSON.
    """
    texto = texto_respuesta.strip()

    # Si Gemini devuelve ```json
    if texto.startswith( "```json"):

        texto = texto[len("```json"):]

    # Si devuelve solamente ```
    elif texto.startswith("```"):
        texto = texto[len("```"):]

    # Eliminar cierre Markdown.
    if texto.endswith("```"):
        texto = texto[:-len("```")]

    return texto.strip()

#Funcion para validar el JSON clinico:
def validar_json_clinico(texto_respuesta,nombre_archivo):
    """
    Convierte la respuesta de Gemini
    en un diccionario y valida
    los datos básicos que pedimos se generaran
    """

    if not texto_respuesta:

        raise ValueError("Gemini no devolvió ninguna respuesta")

    #Aplicando Limpiar Markdown.
    texto_limpio = limpiar_respuesta_json(texto_respuesta)

    #Intentar convertir texto a JSON del texto limpiado:
    try:

        datos_clinicos = json.loads(texto_limpio)

    except json.JSONDecodeError as error:

        print("\nRespuesta recibida de Gemini: ")
        print(texto_respuesta)

        raise ValueError("\nGemini no devolvió JSON válido.\n" f"Error: {error}")

    #Comprobando que el JSON sea un objeto.
    if not isinstance(datos_clinicos,dict):

        raise ValueError("\nLa respuesta de Gemini no es un objeto JSON")

    #Comprobando el nombre del JSON:
    nombre_respuesta = (datos_clinicos.get("nombre_archivo"))

    if nombre_respuesta != nombre_archivo:

        raise ValueError(

            "\nEl nombre del archivo "
            "devuelto por Gemini "
            "no coincide con el generado "
            "por MediFlow.\n\n"

            f"Nombre esperado:\n"
            f"{nombre_archivo}\n\n"

            f"Nombre recibido:\n"
            f"{nombre_respuesta}"

        )


    print("\nJSON clínico validado correctamente")

    return datos_clinicos

#Procesar Archivo:
#Funcion para Procesar el Archivo con Gemini:
def procesar_con_gemini(ruta_archivo,tipo_archivo,nombre_archivo):
    """
    Realizando estos procesos con Gemini:
        1. Sube archivo.
        2. Crea prompt.
        3. Envía archivo + instrucciones.
        4. Recibe respuesta.
        5. Valida JSON.
        6. Devuelve JSON clínico.
    """
    #Realiza el análisis completo con Gemini.

    #Paso1 Subir archivo:
    archivo_gemini = subir_archivo_a_gemini(ruta_archivo)

    #Paso2 Creamos las instrucciones a realiar para analizar el archivo subido:
    prompt = crear_prompt_prueba(tipo_archivo,nombre_archivo)

    #Testeamos:
    print("\nEspere El Agente Inteligente MediFlow con Gemini integrado: ")
    print("Por el Equipo50_LATAM_G10, esta analizando el archivo subido\n")

    #Paso3 Enviamos el prompt + archivo subido a Gemini
    respuesta = cliente_gemini.models.generate_content(
        model = MODELO_GEMINI,
        contents = [prompt,archivo_gemini]
    )

    #Paso 4 Obtenemos el texto de respuesta que genero Gemini:
    texto_respuesta = respuesta.text

    #Comprobamos que Gemini haya respondido
    if not texto_respuesta:

        raise ValueError("Gemini no devolvió ninguna respuesta.")

    #Paso 5 Validamos la respueta(JSON):
    datos_clinicos = (validar_json_clinico(texto_respuesta,nombre_archivo))
    #Paso6 Devolvemos el diccionario JSON
    return datos_clinicos

#Funcion para generar el nombre del JSON clinico:
def generar_nombre_json_clinico(nombre_archivo):
    """
    Genera el nombre del JSON clinico
    utilizando el nombre generado del archivo original, que es el que guardamos
    """
    nombre_sin_extension = Path(nombre_archivo).stem

    nombre_json = (f"{nombre_sin_extension}" f"_Datos_Clinicos.json")

    return nombre_json

#Funcion de Crecion de LandGraph
#Cambio Nuevo Parte7: Normalizamos la Categoria del documento recibido:
def normalizar_categoria(categoria):
    """Valida la categoría entregada por Gemini: """
    categorias_permitidas = {
        "Receta Médica",
        "Informe de Estudio de Diagnóstico por Imágenes/Laboratorio",
        "Orden de Solicitud de Procedimiento",
        "Epicrisis / Informe de Alta",
        "Certificado Médico",
        "Otro" #Habia Otro
    }
    #Si el documento no esta en ninguna categoria dada regresa Otro
    if not isinstance(categoria, str):
        return "Otro"#Otro

    categoria = categoria.strip()

    if categoria in categorias_permitidas:
        return categoria

    return "Otro"#CHECAR


#Cambio Nuevo Parte8: Asegurandonos de la estructura del JSON:
def asegurar_estructura_clasificacion(datos):
    """
    Crea las estructuras que LangGraph necesita si Gemini no las
    devuelve. Esto evita KeyError y permite que LangGraph complete
    la clasificación de forma determinista
    """
    if not isinstance(datos.get("clasificacion_documento"), dict):
        datos["clasificacion_documento"] = {}

    if not isinstance(datos.get("clasificacion_riesgo"), dict):
        datos["clasificacion_riesgo"] = {}

    documento = datos.get("documento", {})

    if not datos["clasificacion_documento"].get("categoria"):
        datos["clasificacion_documento"]["categoria"] = normalizar_categoria(
            documento.get("tipo_documento")
        )

    riesgo = datos["clasificacion_riesgo"]
    riesgo.setdefault("urgente", False)
    riesgo.setdefault("motivo_urgencia", None)
    riesgo.setdefault("datos_ambiguos", [])
    riesgo.setdefault("datos_faltantes", [])
    riesgo.setdefault("clasificacion_final", None)
    riesgo.setdefault("requiere_revision_humana", False)

    return datos

#Inicciando Nodos de LangGraph:
#Nodo 1: Clasificacion de Documento
def nodo_clasificar_documento(estado):
    """
    Valida la categoría del documento entregada por Gemini:
    """
    datos = asegurar_estructura_clasificacion(estado["datos_clinicos"])

    categoria = datos["clasificacion_documento"].get("categoria")
    categoria = normalizar_categoria(categoria)
    datos["clasificacion_documento"]["categoria"] = categoria

    estado["datos_clinicos"] = datos

    print(f"\n[LangGraph] Categoría: {categoria}")
    return estado

#Nodo 2: Validacion de coherencia del documento subido:
def nodo_validar_coherencia_documental(estado):

    datos = estado["datos_clinicos"]

    umbrales = estado["umbrales"]

    #Obtenemos las Reglas desde el estado de LangGraph
    # LangGraph recibe las reglas desde el nodo inicial,
    
    #Posteriormente seleccionaremos automaticamente
    #las reglas de acuerdo con la categoria
    reglas = estado.get("reglas",REGLAS_DEFECTO)

    datos = asegurar_estructura_clasificacion(datos)

    categoria = datos["clasificacion_documento"].get("categoria","Otro")

    categoria = normalizar_categoria(categoria)

    #Aqui ocurre la seleccion automatica:
    #Si Gemini clasifico como:
    #Receta Médica
    #LangGraph utilizara:
    #reglas["Receta Médica"]
    #Si clasifico como Epicrisis:
    #reglas["Epicrisis / Informe de Alta"]
    #El usuario NO necesita seleccionar manualmente la categoria
    
    reglas_categoria = reglas.get(categoria,{})

    puntaje = 0

    motivos = []

    paciente = datos.get("paciente",{})

    medico = datos.get("medico",{})

    tratamiento = datos.get("tratamiento",{})

    #Aplicando Reglas para la categoria: RECETA MEDICA
    if categoria == "Receta Médica":

        if not datos.get("medicamentos"):
            puntaje += reglas_categoria.get("sin_medicamentos",0)

            motivos.append("La receta no contiene medicamentos.")

        if not tratamiento.get("medicamentos"):
            puntaje += reglas_categoria.get("sin_medicamentos_tratamiento",0)

            motivos.append("No se encontraron medicamentos en el tratamiento.")

        if not paciente.get("id_paciente"):
            puntaje += reglas_categoria.get("sin_id_paciente",0)

            motivos.append("Falta el identificador del paciente.")

        if not paciente.get("nombre_completo"):
            puntaje += reglas_categoria.get("sin_nombre_paciente",0)

            motivos.append("Falta el nombre del paciente.")

        if not medico.get("nombre_completo"):
            puntaje += reglas_categoria.get("sin_nombre_medico",0)

            motivos.append("Falta el nombre del medico.")

        recomendaciones = tratamiento.get("recomendaciones",[])

        medicamentos = tratamiento.get("medicamentos",[])

        if recomendaciones and not medicamentos:
            puntaje += reglas_categoria.get("recomendaciones_sin_medicamentos",0)

            motivos.append("Existen recomendaciones pero no se encontraron medicamentos.")


    #Aplicando Reglas para la categoria: INFORME DE ESTUDIO
    elif categoria == ("Informe de Estudio de Diagnóstico por Imágenes/Laboratorio"):
        estudios = datos.get("estudios",[])

        if not estudios:
            puntaje += reglas_categoria.get("sin_estudios",0)

            motivos.append("No se encontraron estudios.")

        else:
            estudios_sin_resultado = 0
            for estudio in estudios:
                if not estudio.get("resultado"):
                    estudios_sin_resultado += 1

            regla_por_estudio = reglas_categoria.get("estudio_sin_resultado",0)

            regla_maxima = reglas_categoria.get("maximo_estudio_sin_resultado",0)

            puntaje += min(regla_maxima,estudios_sin_resultado * regla_por_estudio)

            if estudios_sin_resultado > 0:
                motivos.append(f"{estudios_sin_resultado} estudio(s) sin resultado.")


    #Aplicando Reglas para la categoria: ORDEN DE PROCEDIMIENTO
    elif categoria == ("Orden de Solicitud de Procedimiento"):
        procedimientos = datos.get("procedimientos",[])

        if not procedimientos:
            puntaje += reglas_categoria.get("sin_procedimientos",0)

            motivos.append("No se encontraron procedimientos.")

    #Aplicando Reglas para la categoria: EPICRISIS
    elif categoria == ("Epicrisis / Informe de Alta"):
        diagnosticos = datos.get("diagnosticos",[])

        if not diagnosticos:
            puntaje += reglas_categoria.get("sin_diagnosticos",0)

            motivos.append("No se encontraron diagnosticos.")

        descripcion_tratamiento = tratamiento.get("descripcion")

        medicamentos = tratamiento.get("medicamentos",[])

        if not descripcion_tratamiento and not medicamentos:
            puntaje += reglas_categoria.get("sin_tratamiento",0)

            motivos.append("No se encontro informacion de tratamiento.")

        seguimiento = datos.get("seguimiento",[])

        if not seguimiento:
            puntaje += reglas_categoria.get("sin_seguimiento",0)

            motivos.append("No se encontraron indicaciones de seguimiento.")

    #Aplicando Reglas para la categoria: CERTIFICADO MEDICO
    elif categoria == "Certificado Médico":
        if not paciente.get("nombre_completo"):
            puntaje += reglas_categoria.get("sin_nombre_paciente",0)

            motivos.append("Falta el nombre del paciente.")

        if not medico.get("nombre_completo"):
            puntaje += reglas_categoria.get("sin_nombre_medico",0)

            motivos.append("Falta el nombre del medico.")

    #Aplicando Reglas para la categoria: DATOS AMBIGUOS
    riesgo = datos["clasificacion_riesgo"]

    ambiguos = riesgo.get("datos_ambiguos",[])
    #Cambio
    datos_ilegibles = datos.get("datos_no_legibles_o_ambiguos")

    cantidad_ambiguedades = (len(ambiguos) + len(datos_ilegibles))
    
    #Aqui esta la Regla de Ambiguedad Configurable:
    regla_ambiguedad = reglas.get("ambiguidad",REGLAS_DEFECTO["ambiguidad"])

    puntos_ambiguedad = min(regla_ambiguedad.get("maximo",20),cantidad_ambiguedades * regla_ambiguedad.get("por_dato",5))

    puntaje += puntos_ambiguedad

    if cantidad_ambiguedades > 0:

        motivos.append(f"Se detectaron " f"{cantidad_ambiguedades} dato(s) ambiguo(s).")

    #Limitando PUNTAJE A 100
    puntaje = min(puntaje,100)

    #Determinando el nivel de urgencia:
    if puntaje < umbrales["umbral_normal"]:
        nivel = "normal"

    elif puntaje < umbrales["umbral_revision"]:
        nivel = "revision"

    elif puntaje < umbrales["umbral_alerta"]:
        nivel = "revision_prioritaria"

    else:
        nivel = "alerta"

    #Guardando Validacion de coherencia de documento
    datos["validacion_coherencia"] = {

        "puntaje_incoherencia": puntaje,

        "nivel_coherencia": nivel,

        "categoria_reglas_aplicadas": categoria,

        "umbrales_utilizados": umbrales,

        "reglas_utilizadas": reglas_categoria,

        "motivos": motivos,

        "requiere_revision_humana":nivel != "normal"
    }

    #Clasificacion De estados de alerta:
    if not riesgo.get("urgente",False):
        if nivel == "alerta":
            estado["clasificacion_final"] = "alerta"

        elif nivel == "revision_prioritaria":
            estado["clasificacion_final"] = "revision_prioritaria"

        elif nivel == "revision":
            estado["clasificacion_final"] = "revision"

        else:
            estado["clasificacion_final"] = "normal"

    estado["datos_clinicos"] = datos

    return estado


#Nodo 3: Decteccion de Urgencia:
def nodo_detectar_urgencia(estado):
    """
    Comprueba una urgencia explícita reportada por Gemini,
    La urgencia siempre tiene prioridad sobre la coherencia.
    """
    datos = estado["datos_clinicos"]
    riesgo = datos.get("clasificacion_riesgo", {})

    urgente = riesgo.get("urgente", False)

    if urgente is True:
        estado["clasificacion_final"] = "urgente"
        print("\n[LangGraph] Documento marcado como URGENTE!!\n")

    return estado

#NODO 4: Deteccion de Ambigüedad:
def nodo_detectar_ambiguedad(estado):
    """La urgencia tiene prioridad sobre la ambigüedad."""
    if estado.get("clasificacion_final") == "urgente":
        return estado

    datos = estado["datos_clinicos"]
    riesgo = datos.get("clasificacion_riesgo", {})

    ambiguos = riesgo.get("datos_ambiguos", [])
    datos_ilegibles = datos.get("datos_no_legibles_o_ambiguos", [])

    if ambiguos or datos_ilegibles:
        estado["clasificacion_final"] = "ambiguo"
        print("\n[LangGraph] Documento marcado como AMBIGUO\n")

    return estado

#NODO 5: Deteccion de datos Faltantes:
def nodo_detectar_datos_faltantes(estado):
    """Prioridad: urgente > ambiguo > datos faltantes > coherencia > normal."""
    if estado.get("clasificacion_final") in {"urgente", "ambiguo"}:
        return estado

    datos = estado["datos_clinicos"]
    riesgo = datos.get("clasificacion_riesgo", {})
    faltantes = riesgo.get("datos_faltantes", [])

    if faltantes:
        estado["clasificacion_final"] = "datos_faltantes"
        print("\n[LangGraph] Documento marcado como DATOS FALTANTES\n")

    return estado


#Nodo 6: Decision Final aplicando prioridades:
def nodo_decidir_ruta(estado):
    """
    Determina la clasificación final respetando esta prioridad:

        1. urgente
        2. ambiguo
        3. datos_faltantes
        4. alerta_coherencia
        5. revision_coherencia
        6. normal

    De esta forma, una urgencia explícita nunca es reemplazada por
    una clasificación de coherencia del documento
    """
    clasificacion = estado.get("clasificacion_final")

    if not clasificacion:
        clasificacion = "normal"

    estado["clasificacion_final"] = clasificacion

    datos = asegurar_estructura_clasificacion(estado["datos_clinicos"])
    riesgo = datos["clasificacion_riesgo"]

    riesgo["clasificacion_final"] = clasificacion
    riesgo["requiere_revision_humana"] = clasificacion != "normal"

    estado["datos_clinicos"] = datos

    print(f"\n[LangGraph] Clasificación final: {clasificacion}")

    return estado


#Construyendo GRafo:
def construir_grafo_clasificacion():
    """
    Flujo actualizado:
    
    1. START,
    2. clasificar_documento,
    3. validar_coherencia_documental,
    4. detectar_urgencia,
    5. detectar_ambiguedad,
    6. detectar_datos_faltantes,
    7. decidir_ruta,
    8. END
    """

    grafo = StateGraph(dict)

    grafo.add_node("clasificar_documento", nodo_clasificar_documento)
    grafo.add_node("validar_coherencia_documental", nodo_validar_coherencia_documental)
    grafo.add_node("detectar_urgencia", nodo_detectar_urgencia)
    grafo.add_node("detectar_ambiguedad", nodo_detectar_ambiguedad)
    grafo.add_node("detectar_datos_faltantes", nodo_detectar_datos_faltantes)
    grafo.add_node("decidir_ruta", nodo_decidir_ruta)

    grafo.add_edge(START, "clasificar_documento")
    grafo.add_edge("clasificar_documento", "validar_coherencia_documental")
    grafo.add_edge("validar_coherencia_documental", "detectar_urgencia")
    grafo.add_edge("detectar_urgencia", "detectar_ambiguedad")
    grafo.add_edge("detectar_ambiguedad", "detectar_datos_faltantes")
    grafo.add_edge("detectar_datos_faltantes", "decidir_ruta")
    grafo.add_edge("decidir_ruta", END)

    return grafo.compile()

#CAMBIO NUEVO 12: 
#Ejecucion de los umbrales decididos por el usuraio y 
#esta aplicados a los estados que se tienen en LangGraph:
# EJECUTAR LANGGRAPH CON REGLAS
# Ahora LangGraph recibe:
# - datos_clinicos
# - umbrales
# - reglas
# Los tres elementos viajan dentro del estado.
#Funcion de ejecutar LangGraph:
def ejecutar_langgraph(datos_clinicos,umbrales,reglas):
    estado_inicial = {

        "datos_clinicos":
            datos_clinicos,

        "clasificacion_final":
            None,

        "umbrales":
            umbrales,

        "reglas":
            reglas
    }

    grafo = construir_grafo_clasificacion()

    resultado = grafo.invoke(estado_inicial)

    return resultado

#Creamos el nombre de las categorias de la carpeta:
def convertir_categoria_a_nombre_carpeta(categoria):

    """
    Convierte la categoría documento
    en un nombre adecuado para una carpeta
    """
    categorias = {

        "Receta Médica":"Receta_Medica",

        "Informe de Estudio de Diagnóstico por Imágenes/Laboratorio":"Informe_Estudio_Diagnostico",

        "Orden de Solicitud de Procedimiento":"Orden_Solicitud_Procedimiento",

        "Epicrisis / Informe de Alta":"Epicrisis_Informe_Alta",

        "Certificado Médico":"Certificado_Medico",

        "Otro":"Otro Tipo de Documento"
    }

    return categorias.get(categoria,"Otro")

#Funcion para crear las carpetas de clasificacion para que las tenga el medico
#si quiere ver los archivos:
def crear_carpeta_clasificacion(clasificacion,categoria):

    """
    Crea la carpeta final donde se almacenará
    el JSON Final, Ejemplo:

    NORMAL:Datos_Clinicos/Normal/Receta_Medica/

    ALERTA:Datos_Clinicos/Alertas/Urgente/Receta_Medica/
    """

    categoria_carpeta = (convertir_categoria_a_nombre_carpeta(categoria))

    if clasificacion == "normal":
        carpeta = os.path.join(Carpeta_Datos_Clinicos,"Normal",categoria_carpeta)
    
    else:
        carpeta = os.path.join(Carpeta_Datos_Clinicos,"Alertas",clasificacion.capitalize(),categoria_carpeta)

    os.makedirs(carpeta,exist_ok=True)

    return carpeta #Regresa la ruta de la carpeta creada

#Funcion para guardar el JSON Final
def guardar_json_clasificado(datos_clinicos,nombre_archivo,clasificacion,categoria):
    """
    Guarda el JSON final dependiendo
    de la clasificación de LangGraph.
    """
    carpeta = crear_carpeta_clasificacion(clasificacion,categoria)

    ruta_json = os.path.join(carpeta,generar_nombre_json_clinico(nombre_archivo))

    with open(ruta_json,"w",encoding="utf-8") as archivo:
        json.dump(datos_clinicos,archivo,ensure_ascii=False,indent=4)

    print("\nJSON clasificado guardado en: ")
    print(ruta_json)

    return ruta_json

#Funcion para mostar Los Resultados Testeando!!!:
def mostrar_resultado_final(resultado_langgraph,ruta_json):
    """
    Muestra el resultado final
    del procesamiento.
    """
    datos = resultado_langgraph["datos_clinicos"]

    categoria = datos["clasificacion_documento"]["categoria"]

    clasificacion = resultado_langgraph["clasificacion_final"]

    validacion = datos.get("validacion_coherencia",{})

    print("\nRESULTADO FINAL MEDIFLOW: ")
    print(f"\nCategoria documental: \n" f"{categoria}")
    print(f"Clasificacion final: \n" f"{clasificacion}")
    print(f"Puntaje de incoherencia: \n" f"{validacion.get('puntaje_incoherencia', 0)}")
    print(f"Nivel de coherencia: \n" f"{validacion.get('nivel_coherencia', 'normal')}")

    print(f"Reglas utilizadas: \n" f"{validacion.get('categoria_reglas_aplicadas', categoria)}")
    print(f"\nArchivo JSON: ")
    print(ruta_json)

#Aqui va la parte de cambiar direccion de guardado del archivo generado,
#Funcion para Mostar Todos Los Niveles de Evaluacion obtenidos Finales:
def mostrar_niveles_evaluacion(umbrales, nivel_actual, puntaje):
    """
    Muestra al usuario todos los niveles que puede tener
    el documento según los umbrales configurados,

    IMPORTANTE:
    Estos niveles representan INCONSISTENCIAS en el DOCUMENTO,
    NO representan gravedad médica ni una confianza médica
    """

    normal      = umbrales["umbral_normal"]
    revision    = umbrales["umbral_revision"]
    alerta      = umbrales["umbral_alerta"]

    print("\nNIVELES DE EVALUACIÓN DE MEDIFLOW: ")

    print("\nEl puntaje utilizado por MediFlow va en un rango de 0 a 100,")
    print("Este puntaje representa INCONSISTENCIAS detectadas")
    print("en el documento mediante las reglas configuradas,")
    print("NO representa una calificación médica ni la gravedad")
    print("del estado de salud del paciente.\n")

    print("NIVELES CONFIGURADOS por el usuario o dejados por Default: \n")

    print(f"0 - {normal - 1} : NORMAL")

    print(f"{normal} - {revision - 1} : REVISIÓN")

    print(f"{revision} - {alerta - 1} : REVISIÓN PRIORITARIA")

    print(f"{alerta} - 100 : ALERTA")

    print(f"\nPuntaje obtenido por este documento: {puntaje}")
    print(f"\nNivel obtenido: {nivel_actual.upper()}")

#Mostrando el  Resultado COMPLETO que da MEDIFLOW
def mostrar_resultado_final_completo(resultado_langgraph, ruta_json, umbrales):
    """
    Muestra al usuario el resultado final completo de MediFlow,

    Además de mostrar la ruta del JSON, informa:
        La Categoría del documento,
        La Clasificación final del documento,
        El Puntaje de inconsistenciadel documento,
        El Nivel de coherencia del documento,
        El Nivel de  Urgencia que tiene el documento,
        Los Datos ambiguos del documento,
        Los Datos faltantes del documento,
        Los Motivos de inconsistencias del documento,
        LA Ruta donde se guardó el JSON del documenti Final generado,
        Todos los niveles posibles hasta ahora se mostraran en pantalla.
    """

    datos = resultado_langgraph["datos_clinicos"]

    categoria = datos["clasificacion_documento"]["categoria"]

    clasificacion = resultado_langgraph["clasificacion_final"]

    validacion = datos.get("validacion_coherencia", {})

    puntaje = validacion.get("puntaje_incoherencia",0)

    nivel_coherencia = validacion.get("nivel_coherencia","normal")

    riesgo = datos.get("clasificacion_riesgo",{})

    motivos = validacion.get("motivos",[])

    print("\nEl Resultado Final De MEDIFLOW es: \n")
    
    print(f"\nCategoría documental:")
    print(f"  {categoria}")

    print(f"\nClasificación final:")
    print(f"  {clasificacion.upper()}")

    print(f"\nPuntaje de inconsistencia:")
    print(f"  {puntaje} / 100")

    print(f"\nNivel de coherencia:")
    print(f"  {nivel_coherencia.upper()}")

    # Información de riesgo detectada por Gemini
    print("\nInformacion de Riesgo Detectadas: \n")

    urgente = riesgo.get("urgente",False)

    if urgente:
        print("  - URGENCIA: SÍ")

        motivo_urgencia = riesgo.get("motivo_urgencia")

        if motivo_urgencia:
            print(f"    Motivo: {motivo_urgencia}")

    else:
        print("  - URGENCIA: NO")

    #Informacion sobre: Datos ambiguos
    datos_ambiguos = riesgo.get("datos_ambiguos",[])

    datos_no_legibles = datos.get("datos_no_legibles_o_ambiguos",[])

    print(f"  - Datos ambiguos: {len(datos_ambiguos)}")

    if datos_ambiguos:
        for dato in datos_ambiguos:
            print(f"      • {dato}")

    print(f"  - Datos no legibles/ambiguos: " f"{len(datos_no_legibles)}")

    if datos_no_legibles:
        for dato in datos_no_legibles:
            print(f"      • {dato}")

    #Información sobre: Datos faltantes
    datos_faltantes = riesgo.get("datos_faltantes",[])

    print(f"  - Datos faltantes: {len(datos_faltantes)}")

    if datos_faltantes:
        for dato in datos_faltantes:
            print(f"      • {dato}")

    
    #Informacion de: Motivos de inconsistencias
    print("\nMotivos de la Evaluacion Del Documento")

    if motivos:
        for motivo in motivos:
            print(f"  • {motivo}")

    else:
        print("  No se detectaron inconsistencias mediante las reglas configuradas.")

    #Mostrando todos los niveles obtenidos para clasificar el documento:
    mostrar_niveles_evaluacion(umbrales,nivel_coherencia,puntaje)

    #Obtenmos la Ruta actual del JSON Final
    print("\nJSON FINAL GENERADO: ")

    print(f"Nombre: \n")
    print(f"  {os.path.basename(ruta_json)}")

    print(f"\nUbicación actual:")
    print(f"  {ruta_json}\n")

#Toma de Decision por parte del Usuario, se guarda, se mueve o se elimina:
def gestionar_json_final(ruta_json):
    """
    Permite al usuario decidir qué hacer con el JSON final:

        1.- Conservarlo donde MediFlow lo guardó.
        2.- Guardarlo en otra ubicación.
        3.- Eliminarlo.

    El archivo original subido por el usuario NO se elimina,
    Esta función solamente administra el JSON clínico final.
    """

    while True:
        print("\n¿QUÉ DESEAS HACER CON EL JSON FINAL?")

        print("\n1 - Conservarlo donde MediFlow lo guardó")
        print("2 - Guardarlo en otra ubicación")
        print("3 - Eliminar el JSON final")

        opcion = input("\nSelecciona una opción: (1 /2 /3): ").strip()

        #Opcion 1
        if opcion == "1":

            print("\nHas Escogido Conservar el JSON FINAL.")
            print("\nEl Agente MediFlow mantendrá el archivo en: ")
            print(f"{ruta_json}")

            return ruta_json

        #Opcion 2
        elif opcion == "2":
            print("\nIntroduce la carpeta donde deseas guardar el JSON Final generado")
            print("También puedes arrastrar la carpeta desde el Finder hasta la Terminal.")

            nueva_carpeta = input("\nNueva ubicación: ").strip()
            if not nueva_carpeta:

                print("\nNo se introdujo ninguna ubicación.")
                continue

            # Eliminar comillas que pueda agregar la mac pedos con el macOS
            nueva_carpeta = nueva_carpeta.strip("'\"")

            # Expandir ~
            nueva_carpeta = os.path.expanduser(nueva_carpeta)

            # Convertir a ruta absoluta
            nueva_carpeta = os.path.abspath(nueva_carpeta)

            # Comprobar que la carpeta exista
            if not os.path.isdir(nueva_carpeta):
                respuesta = input("\nLa carpeta no existe. ¿Deseas crearla? (Responde: si/no): ").strip().lower()

                if respuesta in {"s", "si", "sí", "Si", "Sí"}:
                    try:

                        os.makedirs(nueva_carpeta,exist_ok=True)

                        print("\nCarpeta creada correctamente.")

                    except OSError as error:

                        print(f"\nNo fue posible crear " f"la carpeta: {error}")
                        continue

                else:

                    print("\nNo se modificará la ubicación.")
                    continue

            # Nombre original del JSON
            nombre_json = os.path.basename(ruta_json)

            nueva_ruta = os.path.join(nueva_carpeta,nombre_json)

            # Si ya existe por que somos pendejos, preguntar
            if os.path.exists(nueva_ruta):

                respuesta = input("\nYa existe un archivo con ese nombre ¿Deseas reemplazarlo? (Responde: si/no): ").strip().lower()

                if respuesta not in {"s","si","sí", "Si", "Sí"}:
                    print("\nOperación cancelada!!!")
                    continue

                try:
                    os.remove(nueva_ruta)

                except OSError as error:
                    print(f"\nNo fue posible reemplazar " f"el archivo: {error}")
                    continue

            try:

                # Mover el JSON desde la ubicación
                # automática hasta la nueva ubicación.
                shutil.move(ruta_json,nueva_ruta)

                print("\nJSON Final Guardado en la Nueva Ubicacion: ")
                print(f"{nueva_ruta}")

                return nueva_ruta

            except OSError as error:

                print(f"\nNo fue posible mover " f"el JSON: {error}")
                continue

        #Opcion 3
        elif opcion == "3":
            respuesta = input("\n¿ESTÁS SEGURO de eliminar el JSON final? " "(Responde: si/no): ").strip().lower()

            if respuesta in {"s","si","sí","Si","Sí"}:

                try:

                    os.remove(ruta_json)
                    print("\nJSON Final ELIMINADO CORRECTAMENTE!!!")
                    print("Prohibido Llorar!!!")

                    print("\nNota Mega Importante:")
                    print("El archivo original subido por el usuario permanece en Archivos_Originales, Ponte Verga!")

                    return None

                except OSError as error:

                    print(f"\nNo fue posible eliminar " f"el JSON: {error}")
                    return ruta_json

            else:
                print("\nEl JSON NO será eliminado.")
                return ruta_json

        #Para los chistosos!!!! Por no Decir Pendejos!
        else:

            print("\nOpción no válida!!!")
            print("Debes seleccionar 1, 2 o 3!!!")
            print("Que la verga NO LEES LAS INSTRUCCIONES??!!")

#Aqui va a ir la parte del envio de correo:  
#
#Aqui va la parte del envio de correo:

#Funcion Para Enviar el Correo
def enviar_alerta_correo(nombre_paciente,nombre_medico,tipo_documento,clasificacion_final,motivo,ruta_json):
    """
    Envía un correo de alerta cuando MediFlow determina
    que el documento requiere revision humana.

    Parametros:
        nombre_paciente:
            Nombre del paciente obtenido por Gemini.

        nombre_medico:
            Nombre del medico obtenido por Gemini.

        tipo_documento:
            Tipo de documento analizado.

        clasificacion_final:
            Clasificacion final determinada por LangGraph.

        motivo:
            Motivos por los cuales el documento requiere
            revision humana.
    """

    #Primero verificamos que exista la configuracion para enviar el correo
    validar_configuracion_correo()

    #Creamos el mensaje a enviar por correo
    mensaje = EmailMessage()

    #Ponemos Asunto al correo:
    mensaje["Subject"] = ("ALERTA MEDIFLOW - Requiere Revision Humana")

    #Cuenta de correo desde la cual se enviara:
    mensaje["From"] = EMAIL_USUARIO

    #Medico o responsable del area que recibira la alerta por correo
    #Convertir la cadena en una lista de correos
    destinatarios = [
        correo.strip()
        for correo in EMAIL_DESTINO.split(",")
    ]

    #Agregar destinatarios
    mensaje["To"] = destinatarios

    #Agregamos el mensaje del correo
    cuerpo = f"""ALERTA MEDIFLOW

Se ha detectado un documento clinico que requiere
REVISION HUMANA por parte del personal encargado.

Datos del Documento:

Paciente:
{nombre_paciente}

Medico:
{nombre_medico}

Tipo de Documento:
{tipo_documento}

Clasificacion Final:
{clasificacion_final}

Motivos de Revision:
{motivo}

Ruta donde se guardo el JSON Final:
{ruta_json}

Por favor, revise el documento en el sistema MediFlow.

Este mensaje fue generado automaticamente
por el sistema Inteligente de MediFlow.
"""

    mensaje.set_content(cuerpo)

    #Hacemos la conexion a los servidores del correo:
    try:

        #Testeando:
        print("\nConectando con el servidor de correo, espere")

        #Para usar Gmail se utiliza:
        #SMTP:
        #smtp.gmail.com
        #Puerto SSL:
        #465
        #SMTP_SSL crea una conexión cifrada.

        with smtplib.SMTP_SSL("smtp.gmail.com",465) as servidor:

            #Iniciamos Sesion
            servidor.login(EMAIL_USUARIO,EMAIL_PASSWORD)

            #Enviamos el mensaje creado
            servidor.send_message(mensaje)

        #Verificamos que se haya enviado el correo:
        print("\nAlerta por correo enviada Exitosamente!!!")

        #Vemos a quien le mandamos el correo:
        print(f"Destinatario: {EMAIL_DESTINO}")

        return True

    #Si no se pudo enviar manda alerta:
    except smtplib.SMTPAuthenticationError:

        print("\nError de autenticacion no se pudo enviar el correo")
        print("\nPosibles motivos")
        print("\nVerifica:")
        print("El correo de Gmail este bien configurado")
        print("La contraseña del correo que hara el envio")
        print("La verificación en dos pasos este configurada")
        print("Y que se este utilizando una contraseña de aplicacion")

        return False

    except Exception as error:

        print("\nError al enviar el correo:")
        print(error)

        return False



# Funcion Principal de trabajo
def main():
    """
    Ejecuta toda la Fase de trabajo del backend hasta ahora,
    Flujo de trabajo actual:
        Paso1 Creacion de carpetas
        Paso2 El usuario Seleciona Archivo a subir
        Paso3 Valida la extension del archivo para ver si es permitida o no
        Paso4 Generacion del nombre del archivo subido para evitar dañar el archivo original
        Paso5 Copiamos el archivo nuevo creado
        Paso6 Testeamos Resultados Obtenidos
        PAso7 Integracion de Gemini
        Paso8 Envio de Archivo y Respuesta de interpretacion con GEmini
        Paso9 Gemini(Extraccion de texto para devolver JSON del archivo subido, 
        paso10 LandGraph CLasificacion y Genración de JSON Final
        Paso11 Umbrales, Reglas y Ennrutamiento de manera Modificables Realizado
        Paso12 Enviar Alertas por correo cuando sea distinto de Normal el documento

        Pasos Futuros:
        Frontend
        OCI
    """

    print("\nMEDIFLOW Equipo50 G-10 LATAM")
    print("Seleccion y Guardado de Archivo usando input")
    try:

        #Paso1
        crear_carpetas_base()

        #Paso2: configuración de umbrales al iniciar.
        # Se pregunta al usuario ANTES de analizar el documento para que
        # LangGraph utilice los valores elegidos durante toda la ejecución.
        umbrales = solicitar_configuracion_umbrales()

        #Paso3 CONFIGURAR REGLAS DE LANGGRAPH
        # El usuario decide si desea modificar los pesos.
        #Si responde NO:
        #se utilizan las reglas guardadas.
        
        #Si responde SI:
        #puede modificar los valores.
        
        #Posteriormente LangGraph seleccionara
        #automaticamente las reglas segun la categoria.        
        reglas = (solicitar_configuracion_reglas())

        #Paso4 Seleccion de Archivo
        ruta_archivo = seleccionar_archivo()

        #Validando Extensiones:
        validar_extension(ruta_archivo)
        print("Extension Valida")

        #Paso6 Guardamos Archivo Original para no modificarlo:
        ruta_guardada,nombre_generado = (guardar_archivo_original(ruta_archivo))

        #Paso5 Tipo de Archivo
        tipo_archivo = validar_extension(ruta_archivo)

        #Paso6  Testeando
        mostrar_informacion(ruta_archivo,tipo_archivo,ruta_guardada,nombre_generado)

        #Paso7 obteniendo MIne type archivo para gemini:
        mine_type = obtener_mime_type(ruta_archivo)
        print(f"\nMine Type: {mine_type}")

        print("\nAnalizando con Gemini el Documento")
        #Paso8 Obtencion de Datos Clinicos con Gemini:
        datos_clinicos = (procesar_con_gemini(ruta_archivo,tipo_archivo,nombre_generado))
        
        #Paso9 Mostramos la REspuesta de Gemini(JSON):
        print("\nTesteando El JSON Generado por Gemini: ")
        print(json.dumps(datos_clinicos,indent=4,ensure_ascii=False))

        #Paso10 Ejecutamos LAndGraph:
        print("Estamos Ejecutando LandgGraph!!!")
        resultado_langgraph = (ejecutar_langgraph(datos_clinicos, umbrales,reglas))

        #Paso11 Obtencion de Datos Clinico Finales
        datos_clinicos_finales = (resultado_langgraph["datos_clinicos"])

        #Paso12 Clasificacion Final:
        clasificacion_final = (resultado_langgraph["clasificacion_final"])

        #Obtencion de categoria:
        categoria = (datos_clinicos_finales["clasificacion_documento"]["categoria"])

        #Paso13 Guardamos el archivo JSON FINAL:
        ruta_json = guardar_json_clasificado(datos_clinicos_finales,nombre_generado,clasificacion_final,categoria)
                

        #Envio de correo:
        #Cambio Nuevo: Revision Humana Y Envio De Alerta Por Correo
        #Obtenemos la informacion de riesgo generada por LangGraph:
        riesgo = datos_clinicos_finales.get("clasificacion_riesgo",{})

        #Obtenemos si el documento necesita revision humana:
        requiere_revision_humana = riesgo.get("requiere_revision_humana",False)

        #Solo se enviara el correo cuando LangGraph determine
        #que el documento requiere revision humana.
        if requiere_revision_humana:
            print("\nEl documento requiere REVISION HUMANA.")

            #Obtenemos los datos del paciente:
            paciente = datos_clinicos_finales.get("paciente",{})

            nombre_paciente = paciente.get("nombre_completo","No identificado")

            #Obtenemos los datos del medico:
            medico = datos_clinicos_finales.get("medico",{})

            nombre_medico = medico.get("nombre_completo","No identificado")

            #Obtenemos el tipo de documento:
            tipo_documento = (datos_clinicos_finales.get("documento",{}).get("tipo_documento"))

            if not tipo_documento: 
                tipo_documento = categoria if "categoria" in locals() else "No identificado"

            #Obtenemos los motivos detectados por la validacion
            #de coherencia de LangGraph:
            validacion = datos_clinicos_finales.get("validacion_coherencia",{})

            motivos_revision = validacion.get("motivos",[])

            #Obtenemos el motivo de urgencia detectado por Gemini:
            motivo_urgencia = riesgo.get("motivo_urgencia")

            if motivo_urgencia:
                motivos_revision.append(f"Motivo de urgencia: {motivo_urgencia}")

            #Obtenemos los datos ambiguos:
            datos_ambiguos = riesgo.get("datos_ambiguos",[])

            if datos_ambiguos:
                motivos_revision.append("Datos ambiguos detectados: "+ ", ".join(str(dato) for dato in datos_ambiguos))

            #Obtenemos los datos faltantes:
            datos_faltantes = riesgo.get("datos_faltantes",[])

            if datos_faltantes:
                motivos_revision.append("Datos faltantes detectados: "+ ", ".join(str(dato) for dato in datos_faltantes))

            #Si por alguna razon no existe un motivo,
            #se coloca uno general para informar al responsable:
            if not motivos_revision:
                motivos_revision.append("El documento fue clasificado por LangGraph como un documento que requiere revision humana.")

            #Convertimos todos los motivos en un solo texto
            #para poder enviarlos dentro del correo:
            motivo_correo = "\n".join(f"- {motivo}"
                                      for motivo in motivos_revision)

            #Enviamos el correo de alerta:
            enviar_alerta_correo(
            nombre_paciente = nombre_paciente,
            nombre_medico = nombre_medico,
            tipo_documento = tipo_documento,
            clasificacion_final = clasificacion_final,
            motivo = motivo_correo,
            ruta_json = ruta_json
            )
        else:
            #Si el documento es NORMAL,
            #NO se envia ningun correo.
            print("\nEl documento NO requiere revision humana.")
            print("No se enviara alerta por correo.")
        #
        
        #paso14 Resumen Final:
        #mostrar_resultado_final(resultado_langgraph, ruta_json)

        #print(f"\nArchivo original:" f"\n{ruta_guardada}")
        #print(f"\nJSON clínico:" f"\n{ruta_json}")

        #PARTE FINAL BIEN:
        mostrar_resultado_final_completo(resultado_langgraph,ruta_json,umbrales)

        #Decision Final del Usuario:
        ruta_json_final = gestionar_json_final(ruta_json)
        if ruta_json_final:
            print("\nProceso MediFlow Finalizado Exitosamente!!")
            print("\nJSON clínico final disponible en: ")
            print(ruta_json_final)
        else:
            print("\nPROCESO MEDIFLOW FINALIZADO Borrado Exitosamente")
            print("El JSON clínico final fue eliminado por decisión del usuario!!!\n")
        
        print("\nEl archivo original permanece en Archivos_Originales\n")

        ##
        #Fase de subir un archivo con Gemini y mande un respuesta terminado
        print("\nIntegracion de Gemini, LandGraph y generacion de JSON Final: Guardado correctamente!\n")
        

    except Exception as error:

        print("\nERROR")
        print(f"{error}")


# Ejecutar Codigo:
if __name__ == "__main__":

    main()
