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

Carpeta_Temporal.mkdir(parents=True,exist_ok=True)


#Cambio Nuevo:
#Archivo donde Streamlit guardara la lista de correos
#configurados para que permanezca despues de reiniciar Docker.

Ruta_Configuracion_Correos = (
    Carpeta_Almacen / "configuracion_correos.json"
)


#Cambio Nuevo:
#Funcion para cargar los correos configurados.

def cargar_correos_streamlit():

    if Ruta_Configuracion_Correos.exists():

        try:

            with open(Ruta_Configuracion_Correos,"r",encoding="utf-8") as archivo:

                correos = json.load(archivo)

                if isinstance(correos,list):

                    return correos

        except Exception:

            pass


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

    with open(
        Ruta_Configuracion_Correos,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            correos,
            archivo,
            ensure_ascii=False,
            indent=4
        )


#Configuracion principal de MediFlow:
#Configuramos el titulo de la aplicacion.
st.set_page_config(
   page_title="MediFlow",
  page_icon="🏥",
 layout="wide"
)

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


                    #CAMBIO NUEVO:
                    #Paso 6:
                    #Obtenemos el MIME type utilizando
                    #la funcion existente del Backend.

                    mime_type = obtener_mime_type(ruta_archivo)


                    #CAMBIO NUEVO:
                    #Paso 7:
                    #Procesamos el documento directamente con Gemini.

                    datos_clinicos = procesar_con_gemini(
                        ruta_archivo,
                        tipo_archivo,
                        nombre_generado
                    )


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


                        #Enviamos la alerta utilizando
                        #la funcion existente de correo.py.

                        enviar_alerta_correo(
                            nombre_paciente,
                            nombre_medico,
                            tipo_documento,
                            clasificacion_final,
                            motivo_correo,
                            ruta_json
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

        #Puntajes de Inconsistencia:
        st.subheader("Puntaje de inconsistencia")

        st.metric("Puntaje",puntaje_inconsistencia)

        #Revision Humana:
        st.subheader("Revision humana")

        if requiere_revision_humana:

            st.warning("MediFlow determino que el documento requiere revision humana.")

        else:

            st.success("MediFlow determino que el documento no requiere revision humana.")

        #Alerta por Correo:
        if requiere_revision_humana:

            if correo_enviado:

                st.success("La alerta por correo fue enviada correctamente!")

            else:

                st.warning("El documento requiere revision humana, pero no se confirmo el envio del correo.")

        #Ruta del JSON Final:
        st.subheader("JSON Final")

        if ruta_json_final:

            st.write("MediFlow guardo el JSON Final en: ")

            st.code(ruta_json_final)


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

            st.write("Selecciona que deseas hacer con el JSON Final generado por MediFlow.")

            #Creamos las opciones disponibles.
            accion_json = st.radio("Accion para el JSON Final:",["Conservar","Mover","Eliminar"],horizontal=True)

            #Si el usuario decide Conservarlo:
            if accion_json == "Conservar":

                st.write("El JSON Final permanecera en su ubicacion actual.")

                if st.button("Conservar JSON Final"):

                    st.success(
                        "El JSON Final permanece en su ubicacion actual."
                    )


            #Si el usuario desea Mover el archivo JSON de lugar:
            elif accion_json == "Mover":

                st.write("Indica la carpeta donde deseas guardar el JSON Final.")

                #Permitimos introducir
                #la nueva ruta.
                nueva_carpeta = st.text_input(
                    "Ruta de la nueva carpeta:"
                )

                if st.button("Mover JSON Final"):

                    if not nueva_carpeta:

                        st.warning("Debes indicar una carpeta.")

                    else:

                        try:

                            #CAMBIO NUEVO:
                            #Movemos el JSON directamente
                            #sin utilizar el endpoint de FastAPI.

                            nueva_carpeta = os.path.abspath(
                                os.path.expanduser(
                                    nueva_carpeta
                                )
                            )

                            os.makedirs(
                                nueva_carpeta,
                                exist_ok=True
                            )

                            nombre_json = os.path.basename(
                                ruta_json_final
                            )

                            nueva_ruta_json = os.path.join(
                                nueva_carpeta,
                                nombre_json
                            )

                            shutil.move(
                                ruta_json_final,
                                nueva_ruta_json
                            )

                            st.success(
                                "El JSON fue movido correctamente."
                            )

                            st.code(
                                nueva_ruta_json
                            )

                            #Actualizamos la informacion
                            #guardada en Streamlit.

                            resultado["ruta_json_final"] = (
                                nueva_ruta_json
                            )

                            st.session_state[
                                "resultado_mediflow"
                            ] = resultado


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

                if st.button("Eliminar JSON Final"):

                    try:

                        #CAMBIO NUEVO:
                        #Eliminamos directamente el JSON Final.
                        #El archivo original permanece guardado.

                        os.remove(
                            ruta_json_final
                        )

                        st.success(
                            "El JSON fue eliminado correctamente."
                        )

                        #Eliminamos la ruta
                        #de la informacion mostrada.

                        resultado["ruta_json_final"] = None

                        st.session_state[
                            "resultado_mediflow"
                        ] = resultado


                    except Exception as error:

                        st.error(
                            f"Error al eliminar el JSON: {error}"
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
