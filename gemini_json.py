#Gemini y generacion de Archivo JSON

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

# Carpeta principal de almacenamiento
Carpeta_Almacen = os.path.join(Carpeta_Base,"Almacen_Local")

# Carpeta donde guardaremos los originales
Carpeta_Originales = os.path.join(Carpeta_Almacen,"Archivos_Originales")

#Carpeta donde guradaremos los datos clinicos:
Carpeta_Datos_Clinicos = os.path.join(Carpeta_Almacen,"Datos_Clinicos")

#Funcion para la creacion de Carpetas:
def crear_carpetas():
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
def mostrar_informacion(ruta_original,tipo_archivo,ruta_guardada):
    """
    Muestra un resumen de lo ocurrido,
    Esta función solamente informa al usuario pero
    No modifica archivos.
    """
    print("\nTesteando REsultados")
    print(f"\nArchivo seleccionado:"f"\n{ruta_original}")
    print(f"\nTipo:"f"\n{tipo_archivo}")
    print(f"\nArchivo guardado:"f"\n{ruta_guardada}")
    print("\nLa copia original está lista para las siguientes fases.")

#Parte nueva Gemini:
#Funcion para Obtener el  MIME TYPE para Gemini
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

    "observaciones": null
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

        print("\nRespuesta recibida de Gemini:")
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

#Funcion para generar el nombre del JSON clinico:
def generar_nombre_json_clinico(nombre_archivo):
    """
    Genera el nombre del JSON clinico
    utilizando el nombre generado del archivo original, que es el que guardamos
    """
    nombre_sin_extension = Path(nombre_archivo).stem

    nombre_json = (f"{nombre_sin_extension}" f"_Datos_Clinicos.json")

    return nombre_json

#Funcion para guardar el JSON generado por Gemini:
def guardar_json_clinico(datos_clinicos,nombre_archivo):
    """
    Guarda el JSON clínico generado por Gemini,
    en la carpeta: 
        archivo_datos_clinicos.json
    """

    #Generando nombre:
    nombre_json = (generar_nombre_json_clinico(nombre_archivo))

    #Construyendo ruta de guardado:
    ruta_json = os.path.join(Carpeta_Datos_Clinicos,nombre_json)

    #Guardando JSON:
    with open(ruta_json,"w",encoding="utf-8") as archivo_json:

        json.dump(
            datos_clinicos,
            archivo_json,
            ensure_ascii=False,
            indent=4
        )

    # Comprobar que exista.
    if not os.path.isfile(ruta_json):

        raise IOError("El JSON clínico no se pudo guardar correctamente.")

    #Si si se guardo bien:
    print("\nJSON gurdado exitosamente")

    #TEsteando Datos:
    print(f"\nNombre:\n" f"{nombre_json}")
    print(f"\nUbicación:\n" f"{ruta_json}")


    return ruta_json

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
    print("\nEspere El Agente Inteligente MediFlow con Gemini integrado:")
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
    datos_clinicos = (
            validar_json_clinico(
                texto_respuesta,
                nombre_archivo
            )
        )
    #Paso6 Devolvemos el diccionario JSON
    return datos_clinicos



#Funcion para mostrar la respuesta que dio GEmini:
def mostrar_respuesta(respuesta):
    """
    En esta Fase Mostramos en la Terminal lo que Gemini respondio acerca del archivo subido,
    En esta fase NO guardamos todavia el resultado,

    Primero queremos verificar visualmente
    que Gemini esta interpretando correctamente
    el documento subido por el usuario
    """

    print("\nRespuesta Clinica de Gemini:\n")
    #print(respuesta)
    print(json.dumps(respuesta,indent=4,ensure_ascii=False))
    

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
        
        Pasos Futuros:
        LandGraph(CLasificacion)
        Enviar correo si requiere revision Humana
        Frontend
        OCI
    """

    print("\nMEDIFLOW Equipo50 G-10 LATAM")
    print("Seleccion y Guardado de Archivo usando input")
    try:

        #PASO 1
        crear_carpetas()

        #PASO 2
        ruta_archivo = seleccionar_archivo()

        #PASO 3
        tipo_archivo = validar_extension(ruta_archivo)

        #PASO 4
        ruta_guardada,nombre_generado = guardar_archivo_original(ruta_archivo)

        #PASO 5 Testeando
        mostrar_informacion(ruta_archivo,tipo_archivo,ruta_guardada)

        #Parte nueva:
        #Paso 6 obteniendo MIne type archivo para gemini:
        obtener_mime_type(ruta_archivo)

        #Paso7 Obtencion de Respusta con Gemini:
        respuesta = procesar_con_gemini(ruta_archivo,tipo_archivo,nombre_generado)

        #Paso8 Mostramos la REspuesta de Gemini(JSON):
        mostrar_respuesta(respuesta)

        #Paso9 Guardamos el archivo JSON:
        ruta_json = guardar_json_clinico(respuesta,nombre_generado)

        #paso10 Resumen Final:
        print(f"\nArchivo original:" f"\n{ruta_guardada}")
        print(f"\nJSON clínico:" f"\n{ruta_json}")

        #Fase de subir un archivo con Gemini y mande un respuesta terminado
        print("\nIntegracion de Gemini y generacion de JSON: Guardado correctamente!")
        
        

    except Exception as error:

        print("\nERROR")
        print(f"{error}")


# Ejecutar Codigo:
if __name__ == "__main__":

    main()

