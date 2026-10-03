#Archivo Principal de Streamlit para MediFlow
#Streamlit ahora llama directamente al Backend,
#ya no depende de FastAPI ni de requests.

import json
import os
import shutil
import sys
import traceback
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

#Configuracion principal de MediFlow.
#IMPORTANTE: debe ser el primer comando de Streamlit.
st.set_page_config(
    page_title="MediFlow",
    page_icon="🏥",
    layout="wide"
)

#Carga las variables del archivo .env (Gemini, correo, etc.)
load_dotenv()

#Paleta MediFlow:
#fondo #EAF7FB | bordes #BFEAF2 | detalles #63C9D6
#accion #1E7F8C | texto #20343A
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

    html, body, .stApp, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        color: #20343A;
    }

    /* Fondo general */
    .stApp { background-color: #EAF7FB; }

    /* Titulos */
    h1, h2, h3, h4 { color: #20343A; font-weight: 700; }
    h1 { letter-spacing: -0.5px; }
    .stCaption, [data-testid="stCaptionContainer"] { color: #1E7F8C; }

    /* Divisores */
    hr { border-color: #BFEAF2 !important; }

    /* Pestañas */
    [role="tablist"] { border-bottom: 1px solid #BFEAF2; }
    [role="tab"] , [role="tab"] * { color: #20343A !important; }
    [role="tab"][aria-selected="true"],
    [role="tab"][aria-selected="true"] * {
        color: #1E7F8C !important;
        font-weight: 700;
    }
    [role="tab"] [class*="SelectionIndicator"] {
        background-color: #1E7F8C !important;
    }

    /* Etiquetas y textos auxiliares de los controles */
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] *,
    [data-testid="stFileUploaderDropzone"] p,
    [data-testid="stFileUploaderDropzone"] small,
    [data-testid="stFileUploaderDropzone"] span {
        color: #20343A !important;
    }

    /* Boton principal (accion) */
    .stButton > button[kind="primary"] {
        background-color: #1E7F8C;
        color: #FFFFFF;
        border: none;
        border-radius: 12px;
        font-weight: 700;
        padding: 0.6rem 1.4rem;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #20343A;
        color: #FFFFFF;
    }

    /* Botones secundarios */
    .stButton > button[kind="secondary"] {
        background-color: #FFFFFF;
        color: #1E7F8C;
        border: 1px solid #63C9D6;
        border-radius: 12px;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: #BFEAF2;
        border-color: #1E7F8C;
        color: #20343A;
    }

    /* Zona para subir archivos */
    [data-testid="stFileUploaderDropzone"] {
        background-color: #EAF7FB;
        border: 2px dashed #63C9D6;
        border-radius: 16px;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background-color: #FFFFFF;
        color: #1E7F8C !important;
        border: 1px solid #63C9D6;
    }
    [data-testid="stFileUploaderDropzone"] button * {
        color: #1E7F8C !important;
    }

    /* Campos de texto, numeros y listas */
    [data-baseweb="input"], [data-baseweb="select"] > div, textarea {
        background-color: #FFFFFF !important;
        border-color: #BFEAF2 !important;
        border-radius: 10px !important;
    }
    [data-baseweb="input"] input,
    [data-baseweb="select"] *,
    textarea {
        color: #20343A !important;
    }
    input::placeholder, textarea::placeholder {
        color: #61777D !important;
        opacity: 1;
    }

    /* Metricas como tarjeta */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #BFEAF2;
        border-radius: 14px;
        padding: 1rem 1.2rem;
    }
    [data-testid="stMetricLabel"] { color: #1E7F8C; }

    /* Bloques de codigo y JSON */
    [data-testid="stCode"], [data-testid="stJson"] {
        border: 1px solid #BFEAF2;
        border-radius: 12px;
    }

    /* Radio */
    [data-testid="stRadio"] label { color: #20343A; }

    /* Barra superior de Streamlit */
    [data-testid="stToolbar"] button { color: #1E7F8C !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


###
#Conexion con el BACKEND
#Este archivo esta dentro de Frontend, subimos un nivel.
Carpeta_Proyecto = Path(__file__).resolve().parent.parent
Carpeta_Backend = Carpeta_Proyecto / "Backend_MediFlow"

#Con uvicorn la carpeta raiz ya estaba en sys.path,
#con "streamlit run" NO, por eso la agregamos.
for ruta in (Carpeta_Proyecto, Carpeta_Backend):
    if str(ruta) not in sys.path:
        sys.path.insert(0, str(ruta))

#Imports explicitos (evitamos "import *" para que el Backend
#no sobrescriba variables como st, os o Path).
from Backend_MediFlow.archivos import (
    crear_carpetas_base,
    validar_extension,
    guardar_archivo_original,
    obtener_mime_type,
)
from Backend_MediFlow.gemini import procesar_con_gemini
from Backend_MediFlow.langgraph_mediflow import ejecutar_langgraph
from Backend_MediFlow.almacenamiento import guardar_json_clasificado
from Backend_MediFlow.correo import (
    enviar_alerta_correo,
    cargar_correos_destino,
    agregar_correo_destino,
    eliminar_correo_destino,
)
from Backend_MediFlow.umbrales import (
    cargar_configuracion_umbrales,
    guardar_configuracion_umbrales,
    validar_umbrales,
)
from Backend_MediFlow.reglas import (
    cargar_configuracion_reglas,
    guardar_configuracion_reglas,
    validar_reglas,
)

EXTENSIONES_PERMITIDAS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp", ".pdf", ".json"
}


###
#FUNCIONES (antes eran los endpoints de FastAPI)

def procesar_documento(nombre_original, contenido):
    """Ejecuta el flujo completo de MediFlow. Antes: POST /procesar."""

    #Paso 1 y 2: nombre y extension.
    nombre_archivo = Path(nombre_original).name
    if not nombre_archivo:
        raise ValueError("No se recibio ningun archivo.")

    extension = Path(nombre_archivo).suffix.lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        raise ValueError("El formato del archivo no es compatible con MediFlow.")

    #Paso 3 y 4: carpetas.
    crear_carpetas_base()
    Carpeta_Temporal = Carpeta_Proyecto / "Almacen_Local" / "Archivos_Temporales"
    Carpeta_Temporal.mkdir(parents=True, exist_ok=True)

    #Paso 5: guardamos el archivo subido en la carpeta temporal.
    ruta_temporal = Carpeta_Temporal / nombre_archivo

    try:
        ruta_temporal.write_bytes(contenido)

        #Paso 6 y 7: validamos y guardamos la copia original.
        ruta_archivo = str(ruta_temporal)
        tipo_archivo = validar_extension(ruta_archivo)
        ruta_guardada, nombre_generado = guardar_archivo_original(ruta_archivo)

        #Paso 8: MIME type.
        mime_type = obtener_mime_type(ruta_archivo)

        #Paso 9: Gemini.
        datos_clinicos = procesar_con_gemini(
            ruta_archivo, tipo_archivo, nombre_generado
        )

        #Paso 10 y 11: umbrales y reglas guardados.
        umbrales = cargar_configuracion_umbrales()
        reglas = cargar_configuracion_reglas()

        #Paso 12: LangGraph.
        resultado_langgraph = ejecutar_langgraph(datos_clinicos, umbrales, reglas)

        #Paso 13 a 15: datos finales, clasificacion y categoria.
        datos_finales = resultado_langgraph["datos_clinicos"]
        clasificacion_final = resultado_langgraph["clasificacion_final"]
        categoria = datos_finales["clasificacion_documento"]["categoria"]

        #Paso 16: guardamos el JSON final.
        ruta_json = guardar_json_clasificado(
            datos_finales, nombre_generado, clasificacion_final, categoria
        )

        #Paso 17: revision humana.
        riesgo = datos_finales.get("clasificacion_riesgo", {})
        requiere_revision_humana = riesgo.get("requiere_revision_humana", False)

        #Paso 18: alerta por correo (solo si requiere revision).
        correo_enviado = False

        if requiere_revision_humana:
            paciente = datos_finales.get("paciente", {})
            nombre_paciente = paciente.get("nombre_completo", "No identificado")

            medico = datos_finales.get("medico", {})
            nombre_medico = medico.get("nombre_completo", "No identificado")

            tipo_documento = datos_finales.get("documento", {}).get("tipo_documento")
            if not tipo_documento:
                tipo_documento = categoria

            validacion = datos_finales.get("validacion_coherencia", {})
            motivos_revision = list(validacion.get("motivos", []))

            motivo_urgencia = riesgo.get("motivo_urgencia")
            if motivo_urgencia:
                motivos_revision.append(f"Motivo de urgencia: {motivo_urgencia}")

            datos_ambiguos = riesgo.get("datos_ambiguos", [])
            if datos_ambiguos:
                motivos_revision.append(
                    "Datos ambiguos detectados: "
                    + ", ".join(str(d) for d in datos_ambiguos)
                )

            datos_faltantes = riesgo.get("datos_faltantes", [])
            if datos_faltantes:
                motivos_revision.append(
                    "Datos faltantes detectados: "
                    + ", ".join(str(d) for d in datos_faltantes)
                )

            if not motivos_revision:
                motivos_revision.append(
                    "El documento fue clasificado por LangGraph "
                    "como un documento que requiere revision humana."
                )

            motivo_correo = "\n".join(f"- {m}" for m in motivos_revision)

            #CORREGIDO: antes se hacia "correo_enviado = True" despues,
            #lo que ocultaba si el envio fallaba.
            correo_enviado = bool(
                enviar_alerta_correo(
                    nombre_paciente,
                    nombre_medico,
                    tipo_documento,
                    clasificacion_final,
                    motivo_correo,
                    ruta_json,
                )
            )

        #Paso 20: respuesta final (mismo formato que devolvia FastAPI).
        validacion_final = datos_finales.get("validacion_coherencia", {})

        return {
            "mensaje": "Documento procesado correctamente por MediFlow.",
            "estado": "procesado",
            "archivo_recibido": nombre_archivo,
            "nombre_generado": nombre_generado,
            "tipo_archivo": tipo_archivo,
            "mime_type": mime_type,
            "archivo_original": ruta_guardada,
            "categoria_documental": categoria,
            "clasificacion_final": clasificacion_final,
            "puntaje_inconsistencia": validacion_final.get("puntaje_incoherencia", 0),
            "nivel_coherencia": validacion_final.get("nivel_coherencia", "normal"),
            "requiere_revision_humana": requiere_revision_humana,
            "correo_enviado": correo_enviado,
            "ruta_json_final": ruta_json,
            "datos_clinicos": datos_finales,
            "umbrales_utilizados": umbrales,
        }

    finally:
        #Paso 19: borramos la copia temporal (con exito o con error).
        if ruta_temporal.exists():
            ruta_temporal.unlink()


def administrar_json_final(ruta_json, accion, nueva_carpeta=None):
    """Conservar, mover o eliminar el JSON Final. Antes: PUT /json-final."""

    ruta_json = os.path.abspath(os.path.expanduser(ruta_json))

    if not os.path.isfile(ruta_json):
        raise FileNotFoundError("El JSON Final no existe en la ruta indicada.")

    accion = accion.strip().lower()

    if accion == "conservar":
        return {
            "mensaje": "El JSON Final se conservara en su ubicacion actual.",
            "ruta_json_final": ruta_json,
        }

    if accion == "mover":
        if not nueva_carpeta:
            raise ValueError(
                "Debes indicar la carpeta donde deseas guardar el JSON Final."
            )

        nueva_carpeta = nueva_carpeta.strip("'\"")
        nueva_carpeta = os.path.abspath(os.path.expanduser(nueva_carpeta))
        os.makedirs(nueva_carpeta, exist_ok=True)

        nueva_ruta = os.path.join(nueva_carpeta, os.path.basename(ruta_json))

        if os.path.exists(nueva_ruta):
            raise FileExistsError(
                "Ya existe un archivo con el mismo nombre en la carpeta seleccionada."
            )

        shutil.move(ruta_json, nueva_ruta)

        return {
            "mensaje": "El JSON Final fue movido correctamente.",
            "ruta_json_final": nueva_ruta,
        }

    if accion == "eliminar":
        os.remove(ruta_json)
        return {
            "mensaje": "El JSON Final fue eliminado correctamente.",
            "ruta_json_final": None,
        }

    raise ValueError("Accion no valida. Debes utilizar: conservar, mover o eliminar.")


###
#INTERFAZ

st.title("🏥 MediFlow")

st.write("Sistema de procesamiento y validacion de documentos clinicos.")

pestana_procesamiento, pestana_configuracion = st.tabs(
    ["Procesamiento de documentos", "Configuracion de MediFlow"]
)


#Pestaña para procesar documentos
with pestana_procesamiento:

    st.header("Procesar documento")

    archivo = st.file_uploader(
        "Selecciona un documento clinico",
        type=["jpg", "jpeg", "png", "bmp", "tiff", "webp", "pdf", "json"]
    )

    if archivo is not None:

        st.write("Archivo seleccionado:", archivo.name)

        extension = os.path.splitext(archivo.name)[1].lower()
        st.write("Tipo de archivo:", extension)

        boton_procesar = st.button("Procesar documento con MediFlow", type="primary")

        if boton_procesar:
            with st.spinner("MediFlow esta procesando el documento..."):
                try:
                    resultado = procesar_documento(archivo.name, archivo.getvalue())

                    st.session_state["resultado_mediflow"] = resultado
                    st.success("Documento procesado correctamente por MediFlow.")

                except ValueError as error:
                    #Archivo invalido o formato no compatible.
                    st.error(str(error))

                except Exception as error:
                    traceback.print_exc()
                    st.error(f"Error durante el procesamiento de MediFlow: {error}")

    #Mostramos el resultado final
    if "resultado_mediflow" in st.session_state:

        resultado = st.session_state["resultado_mediflow"]

        st.divider()
        st.header("Resultado final de MediFlow")

        clasificacion_final = resultado.get("clasificacion_final", "No disponible")
        categoria_documental = resultado.get("categoria_documental", "No disponible")
        puntaje_inconsistencia = resultado.get("puntaje_inconsistencia", 0)
        nivel_coherencia = resultado.get("nivel_coherencia", "No disponible")
        requiere_revision_humana = resultado.get("requiere_revision_humana", False)
        correo_enviado = resultado.get("correo_enviado", False)
        ruta_json_final = resultado.get("ruta_json_final")

        st.subheader("Informacion del documento")

        columna_1, columna_2, columna_3 = st.columns(3)

        with columna_1:
            st.write("**Categoria del documento:**")
            st.info(categoria_documental)

        with columna_2:
            st.write("**Clasificacion final:**")
            st.info(clasificacion_final)

        with columna_3:
            st.write("**Nivel de coherencia:**")
            st.info(nivel_coherencia)

        st.subheader("Puntaje de inconsistencia")
        st.metric("Puntaje", puntaje_inconsistencia)

        st.subheader("Revision humana")

        if requiere_revision_humana:
            st.warning("MediFlow determino que el documento requiere revision humana.")

            if correo_enviado:
                st.success("La alerta por correo fue enviada correctamente!")
            else:
                st.warning(
                    "El documento requiere revision humana, "
                    "pero no se confirmo el envio del correo."
                )
        else:
            st.success("MediFlow determino que el documento no requiere revision humana.")

        st.subheader("JSON Final")

        if ruta_json_final:
            st.write("MediFlow guardo el JSON Final en: ")
            st.code(ruta_json_final)

        st.subheader("Datos clinicos obtenidos")
        st.json(resultado.get("datos_clinicos", {}))

        #Administrar el JSON Final
        if ruta_json_final:

            st.divider()
            st.header("Administrar JSON Final")

            st.write("Selecciona que deseas hacer con el JSON Final generado por MediFlow.")

            accion_json = st.radio(
                "Accion para el JSON Final:",
                ["Conservar", "Mover", "Eliminar"],
                horizontal=True
            )

            if accion_json == "Conservar":

                st.write("El JSON Final permanecera en su ubicacion actual.")

                if st.button("Conservar JSON Final"):
                    try:
                        r = administrar_json_final(ruta_json_final, "conservar")
                        st.success(r["mensaje"])
                    except Exception as error:
                        st.error(f"Error al conservar el JSON: {error}")

            elif accion_json == "Mover":

                st.write("Indica la carpeta donde deseas guardar el JSON Final.")

                nueva_carpeta = st.text_input("Ruta de la nueva carpeta:")

                if st.button("Mover JSON Final"):
                    if not nueva_carpeta:
                        st.warning("Debes indicar una carpeta.")
                    else:
                        try:
                            r = administrar_json_final(
                                ruta_json_final, "mover", nueva_carpeta
                            )
                            st.success(r["mensaje"])
                            st.code(r["ruta_json_final"])

                            resultado["ruta_json_final"] = r["ruta_json_final"]
                            st.session_state["resultado_mediflow"] = resultado

                        except Exception as error:
                            st.error(f"Error al mover el JSON: {error}")

            elif accion_json == "Eliminar":

                st.warning(
                    "Esta opcion eliminara solamente "
                    "el JSON Final. El archivo original "
                    "no sera eliminado."
                )

                if st.button("Eliminar JSON Final"):
                    try:
                        r = administrar_json_final(ruta_json_final, "eliminar")
                        st.success(r["mensaje"])

                        resultado["ruta_json_final"] = None
                        st.session_state["resultado_mediflow"] = resultado

                    except Exception as error:
                        st.error(f"Error al eliminar el JSON: {error}")


#Pestaña de configuracion
with pestana_configuracion:

    st.header("Configuracion de MediFlow")

    pestaña_umbrales, pestaña_reglas, pestaña_correos = st.tabs(
        ["Umbrales", "Reglas", "Correos"]
    )

    #UMBRALES
    with pestaña_umbrales:
        st.subheader("Configuracion de Umbrales!")

        if st.button("Cargar umbrales"):
            try:
                st.session_state["umbrales"] = cargar_configuracion_umbrales()
            except Exception as error:
                st.error(f"Error al consultar los umbrales: {error}")

        if "umbrales" in st.session_state:

            umbrales = st.session_state["umbrales"]

            st.write("Valores actuales:")
            st.write(umbrales)

            umbral_normal = st.number_input(
                "Umbral NORMAL", min_value=0, max_value=100,
                value=int(umbrales["umbral_normal"])
            )

            umbral_revision = st.number_input(
                "Umbral REVISIÓN", min_value=0, max_value=100,
                value=int(umbrales["umbral_revision"])
            )

            umbral_alerta = st.number_input(
                "Umbral ALERTA", min_value=0, max_value=100,
                value=int(umbrales["umbral_alerta"])
            )

            if st.button("Guardar umbrales"):

                nuevos_umbrales = {
                    "umbral_normal": int(umbral_normal),
                    "umbral_revision": int(umbral_revision),
                    "umbral_alerta": int(umbral_alerta),
                }

                try:
                    if not validar_umbrales(nuevos_umbrales):
                        st.error(
                            "Configuracion de umbrales invalida. "
                            "Debe cumplirse: "
                            "0 <= NORMAL < REVISIÓN < ALERTA <= 100."
                        )
                    else:
                        guardar_configuracion_umbrales(nuevos_umbrales)
                        st.success("Los umbrales fueron actualizados correctamente.")
                        st.session_state["umbrales"] = nuevos_umbrales

                except Exception as error:
                    st.error(f"Error al guardar los umbrales: {error}")

    #REGLAS
    with pestaña_reglas:
        st.subheader("Configuracion de Reglas!")

        if st.button("Cargar reglas"):
            try:
                st.session_state["reglas"] = cargar_configuracion_reglas()
            except Exception as error:
                st.error(f"Error al consultar las reglas: {error}")

        if "reglas" in st.session_state:

            reglas = st.session_state["reglas"]

            st.write("Reglas actuales:")
            st.json(reglas)

            reglas_texto = st.text_area(
                "Configuracion de reglas en formato JSON:",
                value=json.dumps(reglas, indent=4, ensure_ascii=False),
                height=400
            )

            if st.button("Guardar reglas"):
                try:
                    reglas_nuevas = json.loads(reglas_texto)

                    if not validar_reglas(reglas_nuevas):
                        st.error(
                            "La configuracion de reglas no es valida. "
                            "Los valores deben ser numeros enteros "
                            "entre 0 y 100."
                        )
                    else:
                        guardar_configuracion_reglas(reglas_nuevas)
                        st.success("Las reglas fueron actualizadas correctamente.")
                        st.session_state["reglas"] = reglas_nuevas

                except json.JSONDecodeError:
                    st.error("La configuracion de reglas no tiene un formato JSON valido.")

                except Exception as error:
                    st.error(f"Error al guardar las reglas: {error}")

    #CORREOS
    with pestaña_correos:

        st.subheader("Correos para Alertas de MediFlow")

        if st.button("Cargar correos"):
            try:
                st.session_state["correos"] = cargar_correos_destino()
            except Exception as error:
                st.error(f"Error al consultar los correos: {error}")

        if "correos" in st.session_state:

            correos = st.session_state["correos"]

            st.write("Correos configurados:")

            for correo in correos:
                st.write(f"Correo, {correo}")
            st.divider()

            st.write("Agregar nuevo correo:")

            nuevo_correo = st.text_input("Correo:")

            if st.button("Agregar correo"):
                if not nuevo_correo:
                    st.warning("Debes escribir un correo.")
                else:
                    try:
                        st.session_state["correos"] = agregar_correo_destino(nuevo_correo)
                        st.success("Correo agregado correctamente.")

                    except ValueError as error:
                        st.error(str(error))

                    except Exception as error:
                        st.error(f"Error al agregar el correo: {error}")

            st.write("Eliminar correo:")

            if correos:
                correo_eliminar = st.selectbox("Selecciona el correo:", correos)

                if st.button("Eliminar correo"):
                    try:
                        st.session_state["correos"] = eliminar_correo_destino(correo_eliminar)
                        st.success("Correo eliminado correctamente.")

                    except ValueError as error:
                        st.error(str(error))

                    except Exception as error:
                        st.error(f"Error al eliminar el correo: {error}")

#PIE DE PAGINA
st.divider()

st.caption(
    "MediFlow - Sistema de procesamiento "
    "y validacion de documentos clinicos, "
    "Equipo 50, LATAM G-10."
)