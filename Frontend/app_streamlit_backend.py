#Archivo Principal de Streamlit para MediFlow
#Librerias usadas:
#Permite crear la interfaz grafica de Streamlit.
import streamlit as st


#Permite trabajar con archivos y rutas.
import os

#Permite trabajar con las rutas del sistema.
import sys

#Permite copiar y mover archivos.
import shutil

#Permite trabajar con rutas del proyecto.
from pathlib import Path

#Permite trabajar con archivos JSON.
import json

# Permite cargar las variables del archivo .env
from dotenv import load_dotenv


# Permita calcular el tiempo de procesamiento de MediFlow.
# Punto 6. Flujo
import time

#Permite calcular la hora limite de atencion de cada documento.
from datetime import datetime, timedelta

#CAMBIO NUEVO:
#Obtenemos la ruta principal del usuario del Mac.
RUTA_MAC_USUARIO = os.getenv("RUTA_MAC_USUARIO", "")

#CAMBIO NUEVO:
#Ruta del usuario del Mac disponible dentro de Docker.
Carpeta_Usuario_Mac = Path("/host_home")

#Configuracion principal de MediFlow:
#Configuramos el titulo de la aplicacion.
st.set_page_config(
   page_title="MediFlow",
  page_icon="🏥",
 layout="wide"
)


# Carga las variables del archivo .env
load_dotenv()


#Cambio Nuevo:
#Ruta principal del proyecto para utilizar
#directamente las funciones del Backend de MediFlow.

Carpeta_Proyecto_Streamlit = Path(__file__).resolve().parent.parent
Carpeta_Backend = Carpeta_Proyecto_Streamlit / "Backend_MediFlow"

if str(Carpeta_Proyecto_Streamlit) not in sys.path:
    sys.path.insert(0,str(Carpeta_Proyecto_Streamlit))

if str(Carpeta_Backend) not in sys.path:
    sys.path.insert(0,str(Carpeta_Backend))


#Cambio Nuevo:
#Importamos directamente las funciones
#del Backend de MediFlow.

from Backend_MediFlow.archivos import *
from Backend_MediFlow.gemini import *
from Backend_MediFlow.langgraph_mediflow import *
from Backend_MediFlow.almacenamiento import *
from Backend_MediFlow.correo import *
import Backend_MediFlow.correo as correo_mediflow

from Backend_MediFlow.umbrales import (
    cargar_configuracion_umbrales,
    guardar_configuracion_umbrales,
    validar_umbrales
)

from Backend_MediFlow.reglas import (
    cargar_configuracion_reglas,
    guardar_configuracion_reglas,
    validar_reglas
)


#Cambio Nuevo:
#Creamos la carpeta de almacenamiento temporal
#utilizada directamente por Streamlit.

Carpeta_Almacen = Carpeta_Proyecto_Streamlit / "Almacen_Local"
Carpeta_Temporal = Carpeta_Almacen / "Archivos_Temporales"

#CAMBIO NUEVO:
#Carpeta interna de Docker conectada con el Escritorio del Mac.
Carpeta_Exportaciones_JSON = Path("/app/Exportaciones_JSON")

Carpeta_Temporal.mkdir(parents=True,exist_ok=True)


#CAMBIO NUEVO:
#Evita mostrar rutas internas de Docker en la interfaz.

#CAMBIO NUEVO:
#Muestra la ubicacion del JSON Final dentro de Almacen_Local.


#CAMBIO NUEVO:
#Muestra las rutas del JSON Final de forma comprensible
#para el usuario, utilizando la ruta del Escritorio del Mac.


#CAMBIO NUEVO:
#Muestra la ubicacion del JSON Final segun su carpeta real.

#CAMBIO NUEVO:
#Muestra la ubicacion del JSON Final
#sin mostrar las rutas internas de Docker.

def mostrar_ruta_json(ruta):

    if not ruta:
        return "Ubicacion no disponible."

    ruta_texto = str(ruta)
    ruta_archivo = Path(ruta_texto)

    #Si el archivo se encuentra en Almacen_Local,
    #mostramos su ubicacion dentro del proyecto.
    if "/app/Almacen_Local/" in ruta_texto:

        ruta_relativa = ruta_texto.split("/app/Almacen_Local/", 1)[1]

        return str(Carpeta_Almacen / ruta_relativa)

    #Si el archivo se encuentra en una carpeta
    #del usuario del Mac, mostramos su ruta original.
    if ruta_texto.startswith("/host_home/"):

        ruta_relativa = ruta_texto.split("/host_home/", 1)[1]

        return str(Path(RUTA_MAC_USUARIO) / ruta_relativa)

    #Si el archivo se encuentra en Exportaciones_JSON,
    #mostramos su ubicacion en el Escritorio.
    if ruta_texto.startswith("/app/Exportaciones_JSON/"):

        return str(Path("/Users/josemoya/Desktop/MediFlow_JSON")/ ruta_archivo.name)

    return ruta_texto



#Cambio Nuevo:
#Archivo donde Streamlit guardara la lista de correos
#configurados para que permanezca despues de reiniciar Docker.

Ruta_Configuracion_Correos = (
    Carpeta_Almacen / "configuracion_correos.json"
)


#Cambio Nuevo:
#Funcion para cargar los correos configurados.


#Cambio Nuevo:
#Funcion para cargar los correos configurados.

def cargar_correos_streamlit():

    if Ruta_Configuracion_Correos.exists():

        try:

            with open(
                Ruta_Configuracion_Correos,
                "r",
                encoding="utf-8"
            ) as archivo:

                configuracion = json.load(archivo)

                #CAMBIO NUEVO:
                #Aceptamos el formato compartido con el backend.
                if isinstance(configuracion, dict):

                    correos = configuracion.get(
                        "correos_destino",
                        []
                    )

                    if isinstance(correos, list):
                        return correos

                #Compatibilidad con archivos anteriores
                #que guardaban directamente una lista.
                elif isinstance(configuracion, list):

                    return configuracion

        except Exception as error:

            print(
                "\nError al cargar los correos en Streamlit:"
            )
            print(error)

    return [
        correo.strip()
        for correo in os.getenv(
            "EMAIL_DESTINO",
            ""
        ).split(",")
        if correo.strip()
    ]


#Cambio Nuevo:
#Funcion para guardar los correos configurados.

def guardar_correos_streamlit(correos):

    #CAMBIO NUEVO:
    #Usamos la misma estructura JSON que correo.py.
    configuracion = {
        "correos_destino": correos
    }

    with open(
        Ruta_Configuracion_Correos,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            configuracion,
            archivo,
            ensure_ascii=False,
            indent=4
        )



#CAMBIO NUEVO:
#Tiempo objetivo de atencion para cada nivel de clasificacion.
#No es una prediccion: es el tiempo maximo en que el area responsable
#deberia atender el documento segun su prioridad.
TIEMPOS_OBJETIVO_MINUTOS = {
    "urgente": 0,
    "alerta": 30,
    "revision_clinica": 60,
    "revision_prioritaria": 120,
    "revision": 240,
    "datos_faltantes": 240,
    "ambiguo": 120,
    "normal": 1440
}

# Piunto 6. Flujo
def texto_tiempo_objetivo(clasificacion):
    """
    Devuelve el tiempo objetivo de atencion y la hora limite
    correspondientes a la clasificacion recibida.
    """
    minutos = TIEMPOS_OBJETIVO_MINUTOS.get(clasificacion, 1440)

    if minutos == 0:
        return "Atencion inmediata"

    #Convertimos los minutos a un texto legible.
    if minutos < 60:
        duracion = f"{minutos} min"
    elif minutos < 1440:
        duracion = f"{minutos // 60} h"
    else:
        duracion = f"{minutos // 1440} dia(s)"

    hora_limite = datetime.now() + timedelta(minutes=minutos)

    return f"Atencion objetivo: {duracion} (antes de las {hora_limite:%H:%M del %d/%m})"


#Titulo principal de MediFlow.
#CAMBIO NUEVO: Utilizamos un encabezado personalizado para
#combinar el fondo blanco con los colores azules de MediFlow.
#Titulo principal de MediFlow.
#CAMBIO NUEVO: Utilizamos un encabezado personalizado para
#combinar el fondo blanco con los colores azules de MediFlow.
st.markdown("""
<div style="background-color: white; padding: 25px; border-radius: 15px; margin-bottom: 25px; border-left: 7px solid #1496C7;">
<h1 style="color: #0B4F6C; margin-bottom: 5px;">🏥 MediFlow Equipo50 LATAM G-10</h1>
<p style="color: #000000; font-size: 18px; margin-top: 0px;">Bienvenido a MediFlow. Sistema de procesamiento y validacion de documentos clinicos.</p>
</div>
""", unsafe_allow_html=True)

#Cambio nuevo: CONFIGURACION VISUAL DE MEDIFLOW
# Agregamos estilos CSS para darle a MediFlow una apariencia
# mas profesional, limpia y relacionada con un sistema medico.
st.markdown("""
<style>

    /*CAMBIO NUEVO: FONDO PRINCIPAL*/

    /* Cambiamos el fondo general por un azul celeste claro. */
    .stApp {background-color: #EAF7FC;}

    /*CAMBIO NUEVO: TITULOS*/

    /* Cambiamos el color de los titulos principales. */
    h1 {color: #0B4F6C;font-weight: 700;}

    /* Cambiamos el color de los subtitulos. */
    h2, h3 {color: #000000 !important;font-weight: 600;}

    /*CAMBIO NUEVO: TEXTOS PRINCIPALES */

    /* Cambiamos a negro los textos principales para que
       tengan un mejor contraste con el fondo azul celeste. */
    p, label, [data-testid="stWidgetLabel"] p {
        color: #000000;
    }

    /* Cambiamos a negro los textos que aparecen
       dentro del cargador de documentos clinicos. */
    /*CAMBIO NUEVO: TEXTO DEL CARGADOR DE ARCHIVOS */

    /* Cambiamos a blanco el texto del area de Upload
       para que contraste con el fondo del cargador. */

    /*CAMBIO NUEVO: AREA DE UPLOAD TRANSPARENTE */

    /* Dejamos transparente el rectangulo donde se suben los archivos
    para que se vea mejor con el fondo de MediFlow. */
    section[data-testid="stFileUploaderDropzone"] {
        background-color: transparent !important;
        border: 2px dashed #1496C7 !important;
        border-radius: 12px !important;
    }

    /*CAMBIO NUEVO: TEXTO DEL AREA DE UPLOAD */

    /* Dejamos el texto del area de Upload en color azul
    para que no aparezca negro. */
    section[data-testid="stFileUploaderDropzone"] span,
    section[data-testid="stFileUploaderDropzone"] small,
    section[data-testid="stFileUploaderDropzone"] label {
        color: #0B6F94 !important;
    }

    /*CAMBIO NUEVO: BOTON DE UPLOAD */

    /* Cambiamos el boton interno de Streamlit a azul
    para evitar que aparezca de color negro. */
    section[data-testid="stFileUploaderDropzone"] button {
        background-color: #1496C7 !important;
        color: white !important;
        border: 1px solid #1496C7 !important;
        border-radius: 8px !important;
    }

    /* Cambiamos tambien el texto del boton de Upload
    para que permanezca en blanco sobre el fondo azul. */
    section[data-testid="stFileUploaderDropzone"] button span {
        color: white !important;
    }


    /*CAMBIO NUEVO: PESTANAS*/

    /* Cambiamos el color de las pestañas de Streamlit. */
    button[data-baseweb="tab"] {
        color: #0B4F6C;
        font-weight: 600;
    }

    /* Marcamos visualmente la pestaña seleccionada. */
    button[data-baseweb="tab"][aria-selected="true"] {color: #1496C7;border-bottom-color: #1496C7;}

    /*CAMBIO NUEVO: BOTONES*/

    /* Cambiamos la apariencia de los botones. */
    .stButton > button {
        background-color: #1496C7;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
    }

    /* Cambiamos el color de los botones cuando pasamos
       el mouse sobre ellos. */
    .stButton > button:hover {
        background-color: #0B6F94;
        color: white;
        border: none;
    }

    /*CAMBIO NUEVO: CAMPOS DE ENTRADA */

    /* Redondeamos los campos de texto. */
    input, textarea {border-radius: 8px !important;}

    /* Redondeamos los selectores. */
    div[data-baseweb="select"] > div {border-radius: 8px;}

    /*CAMBIO NUEVO: CARGADOR DE ARCHIVOS */

    /* Mantenemos el area de Upload transparente para que
       no vuelva a aparecer con un fondo diferente. */
    section[data-testid="stFileUploaderDropzone"] {
        background-color: transparent !important;
        border: 2px dashed #1496C7 !important;
        border-radius: 12px !important;
    }

    /*CAMBIO NUEVO: MENSAJES*/

    /* Redondeamos los mensajes de informacion,
       advertencia, error y exito. */
    div[data-testid="stAlert"] {
        border-radius: 10px;
    }

    /*CAMBIO NUEVO: METRICAS */
    /* Damos una apariencia de tarjeta blanca a las metricas. */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #C7E7F2;
    }

    /*CAMBIO NUEVO: BARRA LATERAL */

    /* Cambiamos el fondo de la barra lateral. */
    section[data-testid="stSidebar"] {
        background-color: #DDF3FA;
    }

    /* Cambiamos el color de los titulos de la barra lateral. */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #0B4F6C;
    }

    /*CAMBIO NUEVO: EXPANDERS*/

    /* Agregamos fondo blanco y bordes suaves a los paneles
       expandibles que pueda utilizar Streamlit. */
    details {
        background-color: white;
        border-radius: 10px;
        border: 1px solid #C7E7F2;
    }

    /*CAMBIO NUEVO: BLOQUES DE CODIGO */

    /* Damos una apariencia mas limpia a las rutas y bloques
       de codigo que muestra MediFlow. */
    pre {border-radius: 10px;}

    /*CAMBIO NUEVO: TITULOS DE CONFIGURACION */

    /* Cambiamos a color negro los titulos de las configuraciones
       para que se puedan distinguir mejor del resto de MediFlow. */
    .titulo-configuracion {
        color: #000000 !important;
        font-weight: 600;
    }

</style>
""", unsafe_allow_html=True)




#Creamos las pestañas principales
#para organizar las funciones de MediFlow.
pestana_procesamiento, pestana_configuracion = st.tabs(
    [
        "Procesamiento de documentos",
        "Configuracion de MediFlow"
    ]
)


#Pestaña para procesar documentos
with pestana_procesamiento:

    #CAMBIO NUEVO: Cambiamos el color del titulo Procesar documento a negro.
    st.markdown('<h2 class="titulo-configuracion">Procesar documento</h2>', unsafe_allow_html=True)

    #Paso 1:
    #Permitimos al usuario seleccionar
    #el documento que desea procesar.
    archivo = st.file_uploader(
        "Selecciona un documento clinico",
        type=[
            "jpg",
            "jpeg",
            "png",
            "bmp",
            "tiff",
            "webp",
            "pdf",
            "json"
        ]
    )


    #Comprobamos si el usuario selecciono
    #un archivo.
    if archivo is not None:

        #Mostramos informacion del archivo.
        st.write("Archivo seleccionado:",archivo.name)

        #Obtenemos la extension del archivo.
        extension = os.path.splitext(archivo.name)[1].lower()

        #Mostramos el tipo de archivo.
        st.write("Tipo de archivo:",extension)

        #Boton para iniciar el procesamiento.
        boton_procesar = st.button("Procesar documento con MediFlow",type="primary")

        #Comprobamos si el usuario presiono
        #el boton de procesamiento.
        if boton_procesar:
            #Paso 2:
            #Mostramos un mensaje mientras
            #MediFlow procesa el documento.
            with st.spinner("MediFlow esta procesando el documento..."):
                try:


                    # Punto 6. Flujo
                    #Lista donde se registra la duracion de cada etapa
                    #del recorrido del documento (trazabilidad del triaje).
                    etapas = []
                    inicio_total = time.perf_counter()
                    inicio_etapa = time.perf_counter()

                    #CAMBIO NUEVO:
                    #Paso 3:
                    #Creamos la ruta temporal del archivo
                    #directamente desde Streamlit.

                    nombre_archivo = archivo.name
                    ruta_temporal = Carpeta_Temporal / nombre_archivo

                    #Guardamos el archivo recibido.
                    with open(ruta_temporal,"wb") as archivo_destino:

                        archivo_destino.write(
                            archivo.getvalue()
                        )


                    #CAMBIO NUEVO:
                    #Paso 4:
                    #Validamos la extension utilizando
                    #la funcion existente del Backend.

                    ruta_archivo = str(ruta_temporal)
                    tipo_archivo = validar_extension(ruta_archivo)


                    #CAMBIO NUEVO:
                    #Paso 5:
                    #Guardamos la copia del archivo original.
                    #El Backend genera el nombre con fecha y hora.

                    ruta_guardada,nombre_generado = (guardar_archivo_original(ruta_archivo))

                    from cloud.sincronizar_almacenamiento import sincronizar_archivo_original, sincronizar_json_final
                    sincronizar_archivo_original(ruta_guardada, nombre_generado)


                    #CAMBIO NUEVO:
                    #Paso 6:
                    #Obtenemos el MIME type utilizando
                    #la funcion existente del Backend.

                    mime_type = obtener_mime_type(ruta_archivo)

                    # Punto 6. Flujo
                    etapas.append({
                        "etapa": "Ingesta y validacion",
                        "detalle": f"Formato {tipo_archivo}",
                        "duracion_s": round(time.perf_counter() - inicio_etapa, 2)
                    })
                    inicio_etapa = time.perf_counter()


                    #CAMBIO NUEVO:
                    #Paso 7:
                    #Procesamos el documento directamente con Gemini.

                    datos_clinicos = procesar_con_gemini(
                        ruta_archivo,
                        tipo_archivo,
                        nombre_generado
                    )

                    # Punto 6. Flujo
                    etapas.append({
                        "etapa": "Extraccion con Gemini",
                        "detalle": "Lectura multimodal del documento",
                        "duracion_s": round(time.perf_counter() - inicio_etapa, 2)
                    })
                    inicio_etapa = time.perf_counter()


                    #Cambio Nuevo:
                    #Paso 8:
                    #Cargamos los umbrales guardados por MediFlow.

                    umbrales = cargar_configuracion_umbrales()


                    #CAMBIO NUEVO:
                    #Paso 9:
                    #Cargamos las reglas guardadas por MediFlow.

                    reglas = cargar_configuracion_reglas()


                    #CAMBIO NUEVO:
                    #Paso 10:
                    #Ejecutamos LangGraph directamente.
                    #Se utilizan los datos, umbrales y reglas.

                    resultado_langgraph = ejecutar_langgraph(
                        datos_clinicos,
                        umbrales,
                        reglas
                    )


                    #CAMBIO NUEVO:
                    #Paso 11:
                    #Obtenemos los datos clinicos finales.

                    datos_clinicos_finales = (
                        resultado_langgraph["datos_clinicos"]
                    )


                    #CAMBIO NUEVO:
                    #Paso 12:
                    #Obtenemos la clasificacion final.

                    clasificacion_final = (
                        resultado_langgraph["clasificacion_final"]
                    )


                    #CAMBIO NUEVO:
                    #Paso 13:
                    #Obtenemos la categoria del documento.

                    categoria = (
                        datos_clinicos_finales[
                            "clasificacion_documento"
                        ]["categoria"]
                    )
                    validacion_coherencia = datos_clinicos_finales.get("validacion_coherencia", {})
                    validacion_clinica = datos_clinicos_finales.get("validacion_clinica", {})

                    etapas.append({
                        "etapa": "Clasificacion LangGraph",
                        "detalle": categoria,
                        "duracion_s": round(time.perf_counter() - inicio_etapa, 2)
                    })
                    etapas.append({
                        "etapa": "Validacion de reglas",
                        "detalle": f"Puntaje {validacion_coherencia.get('puntaje_incoherencia', 0)} | "
                                   f"{len(validacion_coherencia.get('motivos', []))} motivo(s)",
                        "duracion_s": 0.0
                    })
                    etapas.append({
                        "etapa": "Validacion clinica",
                        "detalle": f"{len(validacion_clinica.get('conflictos', []))} conflicto(s)",
                        "duracion_s": 0.0
                    })
                    inicio_etapa = time.perf_counter()


                    #CAMBIO NUEVO:
                    #Paso 14:
                    #Guardamos el JSON Final utilizando
                    #la funcion existente del Backend.

                    ruta_json = guardar_json_clasificado(
                        datos_clinicos_finales,
                        nombre_generado,
                        clasificacion_final,
                        categoria
                    )
                    sincronizar_json_final(ruta_json, clasificacion_final, categoria)


                    #Determinar el nombre del bucket usando la misma lógica de negocio
                    if clasificacion_final == "urgente":
                        bucket_utilizado = "mediflow-urgencias"
                    elif clasificacion_final in {"ambiguo", "datos_faltantes", "alerta", "revision_prioritaria", "revision"}:
                            bucket_utilizado = "mediflow-revision-humana"
                    elif clasificacion_final == "normal":
                        if categoria == "Receta Médica":
                             bucket_utilizado = "mediflow-farmacia"
                        elif categoria == "Orden de Solicitud de Procedimiento":
                            bucket_utilizado = "mediflow-auditoria-autorizaciones"
                        else:
                            bucket_utilizado = "mediflow-historia-clinica"
                    else:
                        bucket_utilizado = "mediflow-revision-humana"

                    etapas.append({
                                "etapa": "Guardado y sincronizacion",
                                "detalle": f"JSON final almacenado en {bucket_utilizado} y sincronizado con la nube",
                                "duracion_s": round(time.perf_counter() - inicio_etapa, 2)
                                })


                    #CAMBIO NUEVO:
                    #Paso 15:
                    #Comprobamos si requiere revision humana.

                    riesgo = datos_clinicos_finales.get(
                        "clasificacion_riesgo",
                        {}
                    )

                    requiere_revision_humana = riesgo.get(
                        "requiere_revision_humana",
                        False
                    )


                    #CAMBIO NUEVO:
                    #Paso 16:
                    #El correo solamente se envia cuando
                    #MediFlow determina que requiere
                    #revision humana.

                    correo_enviado = False

                    if requiere_revision_humana:

                        paciente = datos_clinicos_finales.get(
                            "paciente",
                            {}
                        )

                        nombre_paciente = paciente.get(
                            "nombre_completo",
                            "No identificado"
                        )

                        medico = datos_clinicos_finales.get(
                            "medico",
                            {}
                        )

                        nombre_medico = medico.get(
                            "nombre_completo",
                            "No identificado"
                        )

                        tipo_documento = (
                            datos_clinicos_finales.get(
                                "documento",
                                {}
                            ).get("tipo_documento")
                        )

                        if not tipo_documento:

                            tipo_documento = categoria


                        validacion = datos_clinicos_finales.get(
                            "validacion_coherencia",
                            {}
                        )

                        motivos_revision = list(
                            validacion.get(
                                "motivos",
                                []
                            )
                        )


                        motivo_urgencia = riesgo.get(
                            "motivo_urgencia"
                        )

                        if motivo_urgencia:

                            motivos_revision.append(
                                f"Motivo de urgencia: {motivo_urgencia}"
                            )


                        datos_ambiguos = riesgo.get(
                            "datos_ambiguos",
                            []
                        )

                        if datos_ambiguos:

                            motivos_revision.append(
                                "Datos ambiguos detectados: "
                                + ", ".join(
                                    str(dato)
                                    for dato in datos_ambiguos
                                )
                            )


                        datos_faltantes = riesgo.get(
                            "datos_faltantes",
                            []
                        )

                        if datos_faltantes:

                            motivos_revision.append(
                                "Datos faltantes detectados: "
                                + ", ".join(
                                    str(dato)
                                    for dato in datos_faltantes
                                )
                            )


                        if not motivos_revision:

                            motivos_revision.append(
                                "El documento fue clasificado "
                                "por LangGraph como un documento "
                                "que requiere revision humana."
                            )


                        motivo_correo = "\n".join(
                            f"- {motivo}"
                            for motivo in motivos_revision
                        )


                        #CAMBIO NUEVO:
                        #Utilizamos los correos configurados
                        #actualmente en Streamlit para la alerta.

                        correos_alerta = st.session_state.get(
                            "correos",
                            [
                                correo.strip()
                                for correo in os.getenv(
                                    "EMAIL_DESTINO",
                                    ""
                                ).split(",")
                                if correo.strip()
                            ]
                        )

                        correo_mediflow.EMAIL_DESTINO = ",".join(
                            correos_alerta
                        )

                    correo_enviado = True

                    #CAMBIO NUEVO:
                    #Paso 17:
                    #Eliminamos el archivo temporal.
                    #El archivo original permanece guardado.

                    if os.path.exists(ruta_temporal):

                        os.remove(ruta_temporal)


                    #CAMBIO NUEVO:
                    #Paso 18:
                    #Obtenemos la validacion final.

                    validacion_final = (
                        datos_clinicos_finales.get(
                            "validacion_coherencia",
                            {}
                        )
                    )


                    #CAMBIO NUEVO:
                    #Guardamos en la sesion la misma informacion
                    #que anteriormente devolvia FastAPI.

                    resultado = {

                        "mensaje":
                            "Documento procesado correctamente por MediFlow.",

                        "estado":
                            "procesado",

                        "archivo_recibido":
                            nombre_archivo,

                        "nombre_generado":
                            nombre_generado,

                        "tipo_archivo":
                            tipo_archivo,

                        "mime_type":
                            mime_type,

                        "archivo_original":
                            ruta_guardada,

                        "categoria_documental":
                            categoria,

                        "clasificacion_final":
                            clasificacion_final,

                        "puntaje_inconsistencia":
                            validacion_final.get(
                                "puntaje_incoherencia",
                                0
                            ),

                        "nivel_coherencia":
                            validacion_final.get(
                                "nivel_coherencia",
                                "normal"
                            ),

                        "requiere_revision_humana":
                            requiere_revision_humana,

                        "correo_enviado":
                            correo_enviado,

                        "ruta_json_final":
                            ruta_json,

                        "datos_clinicos":
                            datos_clinicos_finales,

                         "trazabilidad": {
                            "tiempo_total_s": round(time.perf_counter() - inicio_total, 2),
                            "etapas": etapas
                        },

                        "umbrales_utilizados":
                            umbrales
                    }


                    st.session_state["resultado_mediflow"] = (
                        resultado
                    )

                    st.success(
                        "Documento procesado correctamente por MediFlow."
                    )


                except Exception as error:

                    #CAMBIO NUEVO:
                    #Capturamos cualquier error que ocurra
                    #durante el procesamiento directo.

                    st.error(
                        f"Error durante el procesamiento de MediFlow: {error}"
                    )

    #Mostramos el resultado final
    #Comprobamos si existe un resultado
    #guardado en la sesion.
    if "resultado_mediflow" in st.session_state:

        resultado = st.session_state["resultado_mediflow"]

        st.divider()

        st.header("Resultado final de MediFlow")

        #Paso 5:
        #Obtenemos los datos principales
        #que devolvio FastAPI.

        #Obtenemos la clasificacion final.
        clasificacion_final = resultado.get("clasificacion_final","No disponible")

        #Obtenemos la categoria documento:
        categoria_documental = resultado.get("categoria_documental","No disponible")

        #Obtenemos el puntaje de inconsistencia.
        puntaje_inconsistencia = resultado.get("puntaje_inconsistencia",0)

        #Obtenemos el nivel de coherencia.
        nivel_coherencia = resultado.get("nivel_coherencia","No disponible")

        #Obtenemos si requiere revision humana.
        requiere_revision_humana = resultado.get("requiere_revision_humana",False)

        #Obtenemos si se envio el correo.
        correo_enviado = resultado.get("correo_enviado",False)

        #Obtenemos la ruta del JSON Final.
        ruta_json_final = resultado.get("ruta_json_final")

        #Mostramos La Informacion Principal:
        st.subheader("Informacion del documento")

        #Mostramos los resultados en columnas.
        columna_1, columna_2, columna_3 = st.columns(3)

        with columna_1:

            st.write("**Categoria documental:**")

            st.info(categoria_documental)

        with columna_2:

            st.write("**Clasificacion final:**")

            st.info(clasificacion_final)

        with columna_3:

            st.write("**Nivel de coherencia:**")

            st.info(nivel_coherencia)


        # Punto 6. flujo - cambio final para mostrar la trazabilidad del documento
        #CAMBIO NUEVO:
        #Recorrido del documento (trazabilidad del triaje).
        #Se muestra como una cuadricula de tarjetas con iconos y tiempos,
        #y debajo un panel desplegable por etapa con el detalle completo.
        #IMPORTANTE: el HTML va sin indentacion, porque Streamlit interpreta
        #las lineas indentadas como bloques de codigo y no las renderiza.
        trazabilidad = resultado.get("trazabilidad", {})
        datos_clinicos_traza = resultado.get("datos_clinicos", {})

        if trazabilidad:

            st.subheader("Recorrido del documento")

            #Datos que alimentan el resumen y el detalle de cada etapa.
            coherencia = datos_clinicos_traza.get("validacion_coherencia", {})
            clinica = datos_clinicos_traza.get("validacion_clinica", {})
            riesgo_traza = datos_clinicos_traza.get("clasificacion_riesgo", {})

            #Icono de cada etapa. Se busca por el nombre registrado
            #en la trazabilidad durante el procesamiento.
            iconos = {
                "Ingesta y validacion": "📄",
                "Extraccion con Gemini": "🤖",
                "Clasificacion LangGraph": "🏷️",
                "Validacion de reglas": "📋",
                "Validacion clinica": "🩺",
                "Guardado y sincronizacion": "💾"
            }

            #Color del borde segun el resultado de cada etapa:
            #verde sin hallazgos, naranja con hallazgos, rojo si es critico.
            VERDE = "#2E7D32"
            NARANJA = "#EF6C00"
            ROJO = "#C62828"

            def estado_etapa(nombre):
                """
                Devuelve el color del borde y el texto resumen de una etapa,
                usando unicamente datos que MediFlow ya genero.
                """
                if nombre == "Ingesta y validacion":
                    return VERDE, f"Formato {resultado.get('tipo_archivo', '-')}"

                if nombre == "Extraccion con Gemini":
                    campos = (
                        len(datos_clinicos_traza.get("diagnosticos", []))
                        + len(datos_clinicos_traza.get("medicamentos", []))
                        + len(datos_clinicos_traza.get("estudios", []))
                    )
                    ambiguos = len(datos_clinicos_traza.get("datos_no_legibles_o_ambiguos", []))
                    color = NARANJA if ambiguos else VERDE
                    return color, f"{campos} elemento(s) | {ambiguos} ambiguo(s)"

                if nombre == "Clasificacion LangGraph":
                    color = ROJO if riesgo_traza.get("urgente") else VERDE
                    return color, categoria_documental

                if nombre == "Validacion de reglas":
                    puntaje = coherencia.get("puntaje_incoherencia", 0)
                    motivos = len(coherencia.get("motivos", []))
                    color = NARANJA if puntaje > 0 else VERDE
                    return color, f"Puntaje {puntaje} | {motivos} motivo(s)"

                if nombre == "Validacion clinica":
                    conflictos = len(clinica.get("conflictos", []))
                    criticos = len(clinica.get("hallazgos_criticos", []))
                    if criticos:
                        return ROJO, f"{criticos} hallazgo(s) critico(s)"
                    color = NARANJA if conflictos else VERDE
                    return color, f"{conflictos} conflicto(s)"

                return VERDE, "Completado"

            etapas = trazabilidad.get("etapas", [])

            #Dibujamos las tarjetas en filas de tres para que todo
            #quepa en pantalla sin desplazamiento horizontal.
            for inicio in range(0, len(etapas), 3):

                fila = etapas[inicio:inicio + 3]
                columnas = st.columns(3)

                for posicion, etapa in enumerate(fila):

                    nombre_etapa = etapa["etapa"]
                    color, resumen = estado_etapa(nombre_etapa)
                    icono = iconos.get(nombre_etapa, "•")
                    numero = inicio + posicion + 1

                    with columnas[posicion]:

                        st.markdown(
                             f'<div style="background:white;border-left:8px solid {color};'
                            f'border-radius:12px;padding:18px 16px;margin-bottom:12px;'
                            f'min-height:215px;box-sizing:border-box;overflow-wrap:anywhere;'
                            f'box-shadow:0 1px 4px rgba(0,0,0,0.08);">'
                            f'<div style="font-size:clamp(28px,2.4vw,40px);line-height:1;">{icono}</div>'
                            f'<div style="color:#0B4F6C;font-weight:700;'
                            f'font-size:clamp(16px,1.3vw,22px);line-height:1.25;margin-top:8px;">'
                            f'{numero}. {nombre_etapa}</div>'
                            f'<div style="color:#000;font-size:clamp(14px,1.05vw,18px);'
                            f'line-height:1.35;margin:10px 0;min-height:72px;">{resumen}</div>'
                            f'<div style="color:{color};font-weight:700;'
                            f'font-size:clamp(20px,1.7vw,28px);">{etapa["duracion_s"]} s</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

            #Barra final con la cola de destino asignada al documento.
            if clasificacion_final == "urgente":
                color_destino = ROJO
                texto_destino = "🚨 COLA DE URGENCIAS MEDICAS"
            elif requiere_revision_humana:
                color_destino = NARANJA
                texto_destino = "👤 COLA DE REVISION HUMANA"
            else:
                color_destino = VERDE
                texto_destino = "✅ PROCESAMIENTO AUTOMATICO"
            st.markdown(
                f'<div style="background:{color_destino};border-radius:14px;padding:24px 20px;'
                f'text-align:center;margin-top:8px;">'
                f'<div style="color:white;font-weight:700;'
                f'font-size:clamp(24px,2.1vw,34px);line-height:1.2;">{texto_destino}</div>'
                f'<div style="color:white;font-size:clamp(16px,1.3vw,22px);margin-top:8px;">'
                f'{categoria_documental}</div>'
                f'<div style="color:white;font-size:clamp(15px,1.15vw,19px);margin-top:6px;">'
                f'Clasificacion final: {clasificacion_final} &nbsp;|&nbsp; '
                f'Procesado en {trazabilidad.get("tiempo_total_s", 0)} s</div>'
                f'<div style="color:white;font-weight:700;'
                f'font-size:clamp(17px,1.4vw,24px);margin-top:14px;'
                f'border-top:1px solid rgba(255,255,255,0.4);padding-top:12px;">'
                f'⏱️ {texto_tiempo_objetivo(clasificacion_final)}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            #Detalle completo de cada etapa, desplegable bajo las tarjetas.
            st.write("")
            st.caption("Detalle de cada etapa")

            for numero, etapa in enumerate(etapas, start=1):

                nombre_etapa = etapa["etapa"]
                icono = iconos.get(nombre_etapa, "•")

                with st.expander(f"{icono}  {numero}. {nombre_etapa}  —  {etapa['duracion_s']} s"):

                    if nombre_etapa == "Ingesta y validacion":
                        st.write("**Archivo recibido:**", resultado.get("archivo_recibido"))
                        st.write("**Tipo detectado:**", resultado.get("tipo_archivo"))
                        st.write("**MIME type:**", resultado.get("mime_type"))

                    elif nombre_etapa == "Extraccion con Gemini":
                        st.write("**Diagnosticos extraidos:**",
                                 len(datos_clinicos_traza.get("diagnosticos", [])))
                        st.write("**Medicamentos extraidos:**",
                                 len(datos_clinicos_traza.get("medicamentos", [])))
                        st.write("**Estudios extraidos:**",
                                 len(datos_clinicos_traza.get("estudios", [])))

                        ambiguos = datos_clinicos_traza.get("datos_no_legibles_o_ambiguos", [])
                        if ambiguos:
                            st.warning("Datos no legibles o ambiguos:")
                            for dato in ambiguos:
                                st.write(f"- {dato}")

                    elif nombre_etapa == "Clasificacion LangGraph":
                        st.write("**Categoria asignada:**", categoria_documental)
                        st.write("**Urgencia declarada por Gemini:**",
                                 riesgo_traza.get("urgente", False))
                        if riesgo_traza.get("motivo_urgencia"):
                            st.warning(riesgo_traza["motivo_urgencia"])

                    elif nombre_etapa == "Validacion de reglas":
                        st.write("**Puntaje de inconsistencia:**",
                                 coherencia.get("puntaje_incoherencia", 0))
                        st.write("**Nivel:**", coherencia.get("nivel_coherencia", "normal"))

                        motivos = coherencia.get("motivos", [])
                        if motivos:
                            st.write("**Motivos detectados:**")
                            for motivo in motivos:
                                st.write(f"- {motivo}")
                        else:
                            st.success("No se detectaron inconsistencias documentales.")

                        st.write("**Reglas aplicadas:**")
                        st.json(coherencia.get("reglas_utilizadas", {}))

                    elif nombre_etapa == "Validacion clinica":
                        conflictos = clinica.get("conflictos", [])
                        if conflictos:
                            for conflicto in conflictos:
                                st.error(f"{conflicto['tipo']}: {conflicto['detalle']}")
                        else:
                            st.success("No se detectaron conflictos clinicos.")

                        for hallazgo in clinica.get("hallazgos_criticos", []):
                            st.error(f"Valor critico: {hallazgo}")

                        st.write("**Puntaje clinico:**", clinica.get("puntaje_clinico", 0))

                    elif nombre_etapa == "Guardado y sincronizacion":
                        st.write("**JSON final:**")
                        st.write(
                            mostrar_ruta_json(
                                resultado.get("ruta_json_final")
                            )
                        )

        #Ruta del JSON Final:
        st.subheader("JSON Final")

        if ruta_json_final:

            st.write("MediFlow guardo el JSON Final en:")

            st.code(mostrar_ruta_json(ruta_json_final))


        #Datos Clinicos:
        st.subheader("Datos clinicos obtenidos")

        #Obtenemos los datos clinicos,
        #devueltos por FastAPI.
        datos_clinicos = resultado.get("datos_clinicos",{})

        #Mostramos el JSON clinico
        #para que pueda ser revisado.
        st.json(datos_clinicos)

        #Administrar el JSON Final:
        if ruta_json_final:

            st.divider()

            st.header("Administrar JSON Final")

            st.write(
                "Selecciona que deseas hacer con el JSON Final generado por MediFlow."
            )

            #Mostramos la ubicacion sin revelar rutas internas de Docker.
            st.write("**Ubicacion actual del JSON Final:**")
            st.code(mostrar_ruta_json(ruta_json_final))

            #Creamos las opciones disponibles.
            accion_json = st.radio(
                "Accion para el JSON Final:",
                ["Conservar", "Mover", "Eliminar"],
                horizontal=True,
                key="accion_administrar_json"
            )

            #Si el usuario decide Conservarlo:
            if accion_json == "Conservar":

                st.write("El JSON Final permanecera en su ubicacion actual.")

                if st.button("Conservar JSON Final", key="boton_conservar_json"):

                    st.success(
                        "El JSON Final permanece en su ubicacion actual."
                    )

            #Si el usuario desea Mover el archivo JSON de lugar:
            
            #Si el usuario desea Mover el archivo JSON de lugar:
            elif accion_json == "Mover":

                st.write(
                    "Indica la carpeta del Mac donde deseas "
                    "guardar el JSON Final."
                )

                #CAMBIO NUEVO:
                #Permitimos escribir una ruta del Mac.
                nueva_carpeta = st.text_input(
                    "Ruta de la nueva carpeta:",
                    placeholder="~/Documents/Documentos_Medicos"
                )

                st.caption(
                    "Puedes indicar una carpeta existente "
                    "o escribir una nueva para que MediFlow la cree."
                )

                if st.button(
                    "Mover JSON Final",
                    key="boton_mover_json"
                ):

                    if not nueva_carpeta.strip():

                        st.warning(
                            "Debes indicar la carpeta de destino."
                        )

                    elif not RUTA_MAC_USUARIO:

                        st.error(
                            "No se configuro la ruta del usuario del Mac "
                            "en Docker Compose."
                        )

                    else:

                        try:

                            #Comprobamos que el JSON original exista.
                            ruta_origen = Path(
                                ruta_json_final
                            ).resolve()

                            if not ruta_origen.is_file():

                                st.error(
                                    "No se encontro el JSON Final "
                                    "en su ubicacion actual."
                                )

                            else:

                                #CAMBIO NUEVO:
                                #Convertimos la ruta escrita por el usuario
                                #en una ruta accesible desde Docker.

                                ruta_mac = nueva_carpeta.strip()

                                if ruta_mac == "~":
                                    ruta_mac = RUTA_MAC_USUARIO

                                elif ruta_mac.startswith("~/"):
                                    ruta_mac = os.path.join(
                                        RUTA_MAC_USUARIO,
                                        ruta_mac[2:]
                                    )

                                #Normalizamos la ruta de destino.
                                ruta_mac = os.path.normpath(ruta_mac)

                                #Comprobamos que el destino se encuentre
                                #dentro de la carpeta del usuario del Mac.
                                ruta_mac_normalizada = os.path.normpath(
                                    RUTA_MAC_USUARIO
                                )

                                if os.path.commonpath(
                                    [
                                        ruta_mac_normalizada,
                                        ruta_mac
                                    ]
                                ) != ruta_mac_normalizada:

                                    st.error(
                                        "Por seguridad, el destino debe "
                                        "estar dentro de tu carpeta de "
                                        "usuario del Mac."
                                    )

                                else:

                                    #Obtenemos la ruta relativa
                                    #para utilizarla dentro de Docker.
                                    ruta_relativa = os.path.relpath(
                                        ruta_mac,
                                        ruta_mac_normalizada
                                    )

                                    carpeta_destino = (
                                        Carpeta_Usuario_Mac
                                        / ruta_relativa
                                    ).resolve()

                                    #Comprobamos que el destino
                                    #permanezca dentro del volumen.
                                    if not carpeta_destino.is_relative_to(
                                        Carpeta_Usuario_Mac.resolve()
                                    ):

                                        st.error(
                                            "La carpeta de destino "
                                            "no es valida."
                                        )

                                    else:

                                        #Creamos la carpeta si no existe.
                                        carpeta_destino.mkdir(
                                            parents=True,
                                            exist_ok=True
                                        )

                                        #Creamos la nueva ruta del JSON.
                                        nueva_ruta_json = (
                                            carpeta_destino
                                            / ruta_origen.name
                                        )

                                        #Evitamos sobrescribir otro archivo.
                                        if nueva_ruta_json.exists():

                                            st.error(
                                                "Ya existe un archivo con "
                                                "ese nombre en la carpeta "
                                                "de destino. No se movio "
                                                "el JSON."
                                            )

                                        else:

                                            #Movemos el JSON Final.
                                            shutil.move(
                                                str(ruta_origen),
                                                str(nueva_ruta_json)
                                            )

                                            #Actualizamos la ruta del JSON.
                                            resultado[
                                                "ruta_json_final"
                                            ] = str(nueva_ruta_json)

                                            st.session_state[
                                                "resultado_mediflow"
                                            ] = resultado

                                            st.success(
                                                "El JSON Final se movio "
                                                "correctamente."
                                            )

                                            st.write(
                                                "**Nueva ubicacion del "
                                                "JSON Final:**"
                                            )

                                            st.code(
                                                mostrar_ruta_json(
                                                    nueva_ruta_json
                                                )
                                            )

                        except Exception as error:

                            st.error(
                                f"Error al mover el JSON: {error}"
                            )


            #Si el usuario decide eliminar el JSON Final:
            elif accion_json == "Eliminar":

                st.warning(
                    "Esta opcion eliminara solamente "
                    "el JSON Final. El archivo original "
                    "no sera eliminado."
                )

                if st.button("Eliminar JSON Final", key="boton_eliminar_json"):

                    try:

                        #Eliminamos directamente el JSON Final.
                        #El archivo original permanece guardado.
                        os.remove(ruta_json_final)

                        st.success(
                            "El JSON fue eliminado correctamente."
                        )

                        #Eliminamos la ruta de la informacion mostrada.
                        resultado["ruta_json_final"] = None

                        st.session_state[
                            "resultado_mediflow"
                        ] = resultado

                    except Exception:

                        #No mostramos la excepcion porque podria contener
                        #una ruta interna de Docker.
                        st.error(
                            "No fue posible eliminar el JSON Final."
                        )

#Pestaña de configuracion de Umbrales:
with pestana_configuracion:

    #CAMBIO NUEVO: Cambiamos el color del titulo de configuracion a negro.
    st.markdown('<h2 class="titulo-configuracion">Configuracion de MediFlow</h2>', unsafe_allow_html=True)

    #Creamos pestañas para organizar
    #las diferentes configuraciones.
    pestaña_umbrales, pestaña_reglas, pestaña_correos = st.tabs(["Umbrales","Reglas","Correos"])

    #Hacemos la configuración de Umbrales:
    with pestaña_umbrales:
        #CAMBIO NUEVO: Cambiamos el color del titulo de Umbrales a negro.
        st.markdown('<h3 class="titulo-configuracion">Configuracion de Umbrales!</h3>', unsafe_allow_html=True)

        # NUEVO: Explicación de los umbrales
        with st.expander("ℹ️ ¿Qué significan los umbrales?"):
            st.markdown("""
            ### Interpretación de los umbrales

            Los umbrales permiten determinar el nivel de inconsistencia
            encontrado en el documento procesado por MediFlow.

            **NORMAL**

            El puntaje se encuentra dentro de un nivel bajo de
            inconsistencias y no requiere una revisión especial.

            **REVISIÓN**

            El documento presenta inconsistencias que deben ser
            revisadas por una persona.

            **REVISIÓN PRIORITARIA**

            El documento presenta un nivel mayor de inconsistencias,
            por lo que se recomienda realizar una revisión humana
            con mayor prioridad.

            **ALERTA**

            El documento presenta un nivel alto de inconsistencias
            y requiere atención y revisión humana.

            ### Importante

            El puntaje de **0 a 100 representa el nivel de
            inconsistencia detectado en el documento, ENTRE MAYOR PUNTAJE más inconsistente es**.

            Este puntaje **NO representa la gravedad médica del
            paciente y no constituye un diagnóstico médico**.

            Los valores de los umbrales pueden modificarse desde
            esta sección de configuración.
            """)

        #CAMBIO NUEVO:
        #Boton para consultar los umbrales directamente
        #desde el Backend de MediFlow.

        if st.button("Cargar umbrales"):

            try:

                umbrales = cargar_configuracion_umbrales()

                #Guardamos los umbrales
                #en la sesion de Streamlit.

                st.session_state["umbrales"] = umbrales

            except Exception as error:

                st.error(
                    f"Error al cargar los umbrales: {error}"
                )

        #Comprobamos si los umbrales
        #fueron cargados.
        if "umbrales" in st.session_state:

            umbrales = st.session_state["umbrales"]

            #Mostramos los valores actuales.
            st.write("Valores actuales:")

            st.write(umbrales)

            #Creamos campos para modificar
            #los valores.
            umbral_normal = st.number_input(

                "Umbral NORMAL",

                min_value=0,
                max_value=100,

                value=int(
                    umbrales["umbral_normal"]
                )
            )


            umbral_revision = st.number_input(

                "Umbral REVISIÓN",

                min_value=0,
                max_value=100,

                value=int(
                    umbrales["umbral_revision"]
                )
            )


            umbral_alerta = st.number_input(

                "Umbral ALERTA",

                min_value=0,
                max_value=100,

                value=int(
                    umbrales["umbral_alerta"]
                )
            )


            if st.button("Guardar umbrales"):

                #Creamos el diccionario
                #con los nuevos valores.
                nuevos_umbrales = {

                    "umbral_normal":
                        int(umbral_normal),

                    "umbral_revision":
                        int(umbral_revision),

                    "umbral_alerta":
                        int(umbral_alerta)
                }


                try:

                    #CAMBIO NUEVO:
                    #Guardamos los nuevos valores directamente
                    #utilizando la funcion del Backend.

                    if not validar_umbrales(nuevos_umbrales):

                        st.error(
                            "Configuracion invalida. "
                            "Debe cumplirse: "
                            "0 <= NORMAL < REVISIÓN < ALERTA <= 100."
                        )

                    else:

                        guardar_configuracion_umbrales(
                            nuevos_umbrales
                        )

                        st.success(
                            "Los umbrales fueron actualizados."
                        )

                        #Actualizamos los valores
                        #guardados en Streamlit.

                        st.session_state["umbrales"] = (
                            nuevos_umbrales
                        )

                except Exception as error:

                    st.error(
                        f"Error al guardar los umbrales: {error}"
                    )

    #Configuracion de las Reglas LangGraph:
    with pestaña_reglas:
        #CAMBIO NUEVO: Cambiamos el color del titulo de Reglas a negro.
        st.markdown('<h3 class="titulo-configuracion">Configuracion de Reglas!</h3>', unsafe_allow_html=True)

        # NUEVO: Explicación de las reglas
        with st.expander("ℹ️ ¿Cómo funcionan las reglas?"):
            st.markdown("""
            ### Interpretación de las reglas

            Las reglas permiten establecer cuánto aporta cada tipo de
            inconsistencia al puntaje final del documento.

            Cada regla tiene un peso que MediFlow utiliza durante el
            análisis del documento.

            Por ejemplo, una regla puede evaluar:

            -Información faltante.

            -Información ambigua.

            -Información inconsistente.

            -Datos importantes que no fueron encontrados.

            -Situaciones que requieren una revisión humana.

            ### ¿Qué significa modificar un peso?

            Un peso más alto significa que esa condición tendrá una
            mayor influencia sobre el puntaje final de inconsistencia.

            Un peso más bajo significa que esa condición tendrá una
            menor influencia sobre el puntaje final.

            ### Importante

            Las reglas **no realizan un diagnóstico médico**.

            Su función es ayudar a MediFlow a identificar documentos
            que presentan posibles inconsistencias y determinar cuándo
            es recomendable realizar una revisión humana.

            Los pesos de las reglas pueden modificarse desde esta
            sección sin necesidad de modificar directamente el código.
            """)

        #CAMBIO NUEVO:
        #Boton para cargar las reglas directamente
        #desde el Backend de MediFlow.

        if st.button("Cargar reglas"):

            try:

                reglas = cargar_configuracion_reglas()

                st.session_state["reglas"] = reglas

            except Exception as error:

                st.error(
                    f"Error al cargar las reglas: {error}"
                )

        #Comprobamos si las reglas
        #fueron cargadas.
        if "reglas" in st.session_state:
            reglas = st.session_state["reglas"]


            #Mostramos las reglas actuales.
            st.write("Reglas actuales:")

            st.json(reglas)

            #Creamos un area de texto
            #para modificar las reglas.
            reglas_texto = st.text_area(

                "Configuracion de reglas en formato JSON:",

                value=(
                    __import__("json").dumps(
                        reglas,
                        indent=4,
                        ensure_ascii=False
                    )
                ),

                height=400
            )

            if st.button("Guardar reglas"):
                try:

                    #Convertimos el texto
                    #nuevamente a un diccionario.
                    reglas_nuevas = (__import__("json").loads(reglas_texto))

                    #CAMBIO NUEVO:
                    #Guardamos las nuevas reglas directamente
                    #utilizando la funcion del Backend.

                    if not validar_reglas(reglas_nuevas):

                        st.error(
                            "Configuracion invalida."
                        )

                    else:

                        guardar_configuracion_reglas(
                            reglas_nuevas
                        )

                        st.success(
                            "Las reglas fueron actualizadas."
                        )

                        #Actualizamos las reglas
                        #guardadas en Streamlit.

                        st.session_state["reglas"] = (
                            reglas_nuevas
                        )

                except ValueError:

                    #El usuario no introdujo
                    #un JSON valido.
                    st.error("La configuracion de reglas no tiene un formato JSON valido.")


                except Exception as error:

                    st.error(f"Error al guardar las reglas: {error}")


    #Confifuracion de Correos:
    with pestaña_correos:

        #CAMBIO NUEVO:
        #La configuracion de correos ahora se maneja
        #directamente desde Streamlit.
        st.markdown(
            '<h3 class="titulo-configuracion">Correos para Alertas de MediFlow</h3>',
            unsafe_allow_html=True
        )

        #CAMBIO NUEVO:
        #Obtenemos los destinatarios configurados
        #directamente desde las variables de entorno.

        correos_configurados = cargar_correos_streamlit()

        if st.button("Cargar correos"):

            st.session_state["correos"] = (
                correos_configurados
            )

            #CAMBIO NUEVO:
            #Sincronizamos los correos con correo.py.

            correo_mediflow.EMAIL_DESTINO = ",".join(
                correos_configurados
            )

        if "correos" in st.session_state:

            correos = st.session_state["correos"]

            st.write("Correos configurados:")

            #Mostramos cada correo.
            for correo in correos:

                st.write(
                    f"Correo, {correo}"
                )

            st.divider()

            #Por si el Usuario quiere Agregar mas correos:
            st.write("Agregar nuevo correo:")

            nuevo_correo = st.text_input(
                "Correo:"
            )

            if st.button("Agregar correo"):

                if not nuevo_correo:

                    st.warning(
                        "Debes escribir un correo."
                    )

                else:

                    nuevo_correo = nuevo_correo.strip()

                    if nuevo_correo in correos:

                        st.warning(
                            "El correo ya se encuentra configurado."
                        )

                    else:

                        #CAMBIO NUEVO:
                        #Actualizamos la lista que utiliza
                        #la aplicacion durante la ejecucion actual.

                        correos.append(
                            nuevo_correo
                        )

                        st.session_state["correos"] = (
                            correos
                        )

                        #CAMBIO NUEVO:
                        #Actualizamos tambien la configuracion
                        #que utiliza correo.py durante la ejecucion.

                        correo_mediflow.EMAIL_DESTINO = ",".join(
                            correos
                        )

                        guardar_correos_streamlit(
                            correos
                        )

                        st.success(
                            "Correo agregado correctamente."
                        )


            #Si el Usuario desea Eliminar Correos:
            st.write("Eliminar correo:")

            if correos:

                correo_eliminar = st.selectbox(
                    "Selecciona el correo:",
                    correos
                )

                if st.button("Eliminar correo"):

                    correos.remove(
                        correo_eliminar
                    )

                    st.session_state["correos"] = (
                        correos
                    )

                    #CAMBIO NUEVO:
                    #Actualizamos tambien la configuracion
                    #que utiliza correo.py durante la ejecucion.

                    correo_mediflow.EMAIL_DESTINO = ",".join(
                        correos
                    )

                    guardar_correos_streamlit(
                        correos
                    )

                    st.success(
                        "Correo eliminado correctamente."
                    )
#PIE DE PAGINA
st.divider()

st.caption(
    "MediFlow - Sistema de procesamiento "
    "y validacion de documentos clinicos,"
    "Equipo 50, LATAM G-10."
)
