#Funciones para seleccion y manejo de archivos

#Libreriras usadas:
from librerias import *

#Configuracion compartida:
from configuracion import *

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
