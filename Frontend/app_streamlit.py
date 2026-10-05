#Archivo Principal de Streamlit para MediFlow
#Librerias usadas:
#Permite crear la interfaz grafica de Streamlit.
import streamlit as st

#Permite realizar solicitudes HTTP
#hacia los endpoints de FastAPI.
import requests

#Permite trabajar con archivos y rutas.
import os

# Permite cargar las variables del archivo .env
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv()

# URL donde se encuentra funcionando la API de FastAPI
URL_API = os.getenv("URL_API")

#Verificando que la URL de FastAPI exista:
if not URL_API:
    st.error("No se encontró la variable URL_API en el archivo .env")
    st.stop()

#Configuracion principal de MediFlow:
#Configuramos el titulo de la aplicacion.
#st.set_page_config(
#   page_title="MediFlow",
#  page_icon="🏥",
# layout="wide"
#)

#Titulo principal de MediFlow.
#CAMBIO NUEVO: Utilizamos un encabezado personalizado para
#combinar el fondo blanco con los colores azules de MediFlow.
#Titulo principal de MediFlow.
#CAMBIO NUEVO: Utilizamos un encabezado personalizado para
#combinar el fondo blanco con los colores azules de MediFlow.
st.markdown("""
<div style="background-color: white; padding: 25px; border-radius: 15px; margin-bottom: 25px; border-left: 7px solid #1496C7;">
<h1 style="color: #0B4F6C; margin-bottom: 5px;">🏥 MediFlow</h1>
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
                    #Paso 3:
                    #Enviamos el archivo al endpoint
                    #/procesar de FastAPI.
                    #
                    #FastAPI recibira el archivo
                    #utilizando UploadFile.
                    respuesta = requests.post(
                        f"{URL_API}/procesar",
                        files={
                            "archivo": (
                                archivo.name,
                                archivo.getvalue(),
                                archivo.type
                            )
                        },
                        timeout=600
                    )


                    #Paso 4:
                    #Comprobamos si FastAPI respondio
                    #correctamente.
                    if respuesta.status_code == 200:

                        #Convertimos la respuesta
                        #de FastAPI a JSON.
                        resultado = respuesta.json()

                        #Guardamos el resultado
                        #en la sesion de Streamlit.
                        st.session_state["resultado_mediflow"] = (resultado)

                        #Mostramos mensaje de procesamiento.
                        st.success("Documento procesado correctamente por MediFlow.")

                    else:

                        #Intentamos obtener el mensaje
                        #de error enviado por FastAPI.
                        try:

                            error_api = respuesta.json()

                            mensaje_error = error_api.get("detail","Error desconocido.")

                        except Exception:
                            mensaje_error = respuesta.text

                        #Mostramos el error en Streamlit.
                        st.error(f"Error durante el procesamiento: " f"{mensaje_error}")

                except requests.exceptions.ConnectionError:

                    #Este error aparece cuando
                    #FastAPI no esta funcionando.
                    st.error(
                        "No fue posible conectarse con FastAPI. "
                        "Comprueba que la API este funcionando "
                        "en http://127.0.0.1:8000."
                    )


                except requests.exceptions.Timeout:

                    #Este error aparece cuando
                    #el procesamiento tarda demasiado.
                    st.error("El procesamiento de MediFlow tardo demasiado tiempo.")

                except Exception as error:
                    #Capturamos cualquier otro error.
                    st.error(f"Error al comunicarse con MediFlow: {error}")

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
                    try:
                        #Enviamos la solicitud
                        #al endpoint /json-final.
                        respuesta_json = requests.put(f"{URL_API}/json-final",params={"ruta_json": ruta_json_final,"accion": "conservar"},timeout=30)

                        if respuesta_json.status_code == 200:
                            resultado_json = (respuesta_json.json())

                            st.success(resultado_json.get("mensaje","El JSON fue conservado correctamente."))

                        else:

                            try:

                                error_api = (respuesta_json.json())

                                mensaje_error = (error_api.get("detail","Error desconocido."))

                            except Exception:

                                mensaje_error = (respuesta_json.text)

                            st.error(mensaje_error)

                    except Exception as error:

                        st.error(f"Error al conservar el JSON: {error}")

            #Si el usuario desea Mover el archivo JSON de lugar:
            elif accion_json == "Mover":

                st.write("Indica la carpeta donde deseas guardar el JSON Final.")

                #Permitimos introducir
                #la nueva ruta.
                nueva_carpeta = st.text_input("Ruta de la nueva carpeta:")

                if st.button("Mover JSON Final"):

                    if not nueva_carpeta:

                        st.warning("Debes indicar una carpeta.")

                    else:

                        try:

                            #Enviamos la nueva ruta
                            #al endpoint /json-final.
                            respuesta_json = requests.put(f"{URL_API}/json-final",params={"ruta_json":ruta_json_final,"accion":"mover","nueva_carpeta":nueva_carpeta},timeout=30)

                            if respuesta_json.status_code == 200:

                                resultado_json = (respuesta_json.json())

                                #Actualizamos la ruta
                                #del JSON Final.
                                nueva_ruta_json = (resultado_json.get("ruta_json_final"))

                                st.success(
                                    resultado_json.get("mensaje","El JSON fue movido correctamente."))

                                st.code(nueva_ruta_json)

                                #Actualizamos la informacion
                                #guardada en Streamlit.
                                resultado["ruta_json_final"] = nueva_ruta_json

                                st.session_state["resultado_mediflow"] = resultado

                            else:

                                try:

                                    error_api = (respuesta_json.json())

                                    mensaje_error = (error_api.get("detail","Error desconocido."))

                                except Exception:

                                    mensaje_error = (respuesta_json.text)

                                st.error(mensaje_error)

                        except Exception as error:

                            st.error(f"Error al mover el JSON: {error}")

            #Si el usuario decide eliminar el JSON Final:
            elif accion_json == "Eliminar":

                st.warning(
                    "Esta opcion eliminara solamente "
                    "el JSON Final. El archivo original "
                    "no sera eliminado."
                )

                if st.button("Eliminar JSON Final"):

                    try:

                        #Enviamos la solicitud
                        #al endpoint /json-final.
                        respuesta_json = requests.put(f"{URL_API}/json-final",params={"ruta_json":ruta_json_final,"accion":"eliminar"},timeout=30)

                        if respuesta_json.status_code == 200:

                            resultado_json = (respuesta_json.json())

                            st.success(
                                resultado_json.get("mensaje","El JSON fue eliminado correctamente."))

                            #Eliminamos la ruta
                            #de la informacion mostrada.
                            resultado["ruta_json_final"] = None

                            st.session_state["resultado_mediflow"] = resultado

                        else:

                            try:

                                error_api = (respuesta_json.json())

                                mensaje_error = (error_api.get("detail","Error desconocido."))

                            except Exception:

                                mensaje_error = (respuesta_json.text)

                            st.error(mensaje_error)

                    except Exception as error:

                        st.error(f"Error al eliminar el JSON: {error}")

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

        #Boton para consultar los umbrales.
        if st.button("Cargar umbrales"):
            try:

                #Consultamos el endpoint
                #GET /configuracion/umbrales.
                respuesta = requests.get(f"{URL_API}/configuracion/umbrales",timeout=30)

                if respuesta.status_code == 200:

                    datos_umbrales = (respuesta.json())

                    umbrales = datos_umbrales["umbrales"]

                    #Guardamos los umbrales
                    #en la sesion de Streamlit.
                    st.session_state["umbrales"] = umbrales

                else:

                    st.error("No fue posible cargar los umbrales.")

            except Exception as error:

                st.error(f"Error al consultar los umbrales: {error}")

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

                    #Enviamos los nuevos valores
                    #al endpoint PUT.
                    respuesta = requests.put(f"{URL_API}/configuracion/umbrales",json=nuevos_umbrales,timeout=30)

                    if respuesta.status_code == 200:
                        resultado = (respuesta.json())
                        st.success(resultado.get("mensaje","Los umbrales fueron actualizados."))

                        #Actualizamos los valores
                        #guardados en Streamlit.
                        st.session_state["umbrales"] = nuevos_umbrales

                    else:

                        try:

                            error_api = (respuesta.json())

                            mensaje_error = (error_api.get("detail","Configuracion invalida."))

                        except Exception:
                            mensaje_error = (respuesta.text)

                        st.error(mensaje_error)

                except Exception as error:

                    st.error(f"Error al guardar los umbrales: {error}")

    #Configuracion de las Reglas LangGraph:
    with pestaña_reglas:
        #CAMBIO NUEVO: Cambiamos el color del titulo de Reglas a negro.
        st.markdown('<h3 class="titulo-configuracion">Configuracion de Reglas!</h3>', unsafe_allow_html=True)

        #Boton para cargar las reglas actuales.
        if st.button("Cargar reglas"):
            try:

                #Consultamos el endpoint
                #GET /configuracion/reglas.
                respuesta = requests.get(f"{URL_API}/configuracion/reglas",timeout=30)

                if respuesta.status_code == 200:

                    datos_reglas = (respuesta.json())

                    st.session_state["reglas"] = datos_reglas["reglas"]

                else:
                    st.error("No fue posible cargar las reglas.")

            except Exception as error:

                st.error(f"Error al consultar las reglas: {error}")

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

                    #Enviamos las nuevas reglas
                    #al endpoint PUT.
                    respuesta = requests.put(f"{URL_API}/configuracion/reglas",json=reglas_nuevas,timeout=30)


                    if respuesta.status_code == 200:

                        resultado = (respuesta.json())

                        st.success(resultado.get("mensaje","Las reglas fueron actualizadas."))

                        #Actualizamos las reglas
                        #guardadas en Streamlit.
                        st.session_state["reglas"] = reglas_nuevas

                    else:

                        try:

                            error_api = (respuesta.json())

                            mensaje_error = (error_api.get("detail","Configuracion invalida."))

                        except Exception:

                            mensaje_error = (respuesta.text)

                        st.error(mensaje_error)

                except ValueError:

                    #El usuario no introdujo
                    #un JSON valido.
                    st.error("La configuracion de reglas no tiene un formato JSON valido.")


                except Exception as error:

                    st.error(f"Error al guardar las reglas: {error}")


    #Confifuracion de Correos:
    with pestaña_correos:

        #CAMBIO NUEVO: Cambiamos el color del titulo de Correos a negro.
        st.markdown('<h3 class="titulo-configuracion">Correos para Alertas de MediFlow</h3>', unsafe_allow_html=True)

        #Boton para consultar
        #los correos configurados.
        if st.button("Cargar correos"):
            try:

                #Consultamos el endpoint
                #GET /configuracion/correos.
                respuesta = requests.get(f"{URL_API}/configuracion/correos",timeout=30)

                if respuesta.status_code == 200:
                    datos_correos = (respuesta.json())

                    st.session_state["correos"] = datos_correos.get("correos_destino",[])

                else:

                    st.error("No fue posible cargar los correos.")

            except Exception as error:

                st.error(f"Error al consultar los correos: {error}")

        #Comprobamos si los correos
        #fueron cargados.
        if "correos" in st.session_state:
            correos = st.session_state["correos"]

            st.write("Correos configurados:")

            #Mostramos cada correo.
            for correo in correos:
                st.write(f"Correo, {correo}")
            st.divider()

            #Por si el Usuraio quiere Agregar mas correos:
            st.write("Agregar nuevo correo:")

            nuevo_correo = st.text_input("Correo:")

            if st.button("Agregar correo"):
                if not nuevo_correo:
                    st.warning("Debes escribir un correo.")
                else:

                    try:

                        #Enviamos el correo
                        #al endpoint POST.
                        respuesta = requests.post(
                            f"{URL_API}/configuracion/correos",
                            params={"correo": nuevo_correo},
                            timeout=30
                        )

                        if respuesta.status_code == 200:

                            resultado = (respuesta.json())

                            st.success(resultado.get("mensaje","Correo agregado correctamente."))

                            #Actualizamos la lista
                            #de correos.
                            st.session_state["correos"] = resultado.get("correos_destino",[])

                        else:
                            try:
                                error_api = (respuesta.json())

                                mensaje_error = (error_api.get("detail","No fue posible agregar el correo."))

                            except Exception:

                                mensaje_error = (respuesta.text)

                            st.error(mensaje_error)

                    except Exception as error:

                        st.error(f"Error al agregar el correo: {error}")

            #si el Usuraio desea Eliminar Correos:
            st.write("Eliminar correo:")

            if correos:
                correo_eliminar = st.selectbox("Selecciona el correo:",correos)

                if st.button("Eliminar correo"):
                    try:

                        #Enviamos el correo
                        #al endpoint DELETE.
                        respuesta = requests.delete(
                            f"{URL_API}/configuracion/correos",
                            params={"correo": correo_eliminar},
                            timeout=30
                        )

                        if respuesta.status_code == 200:
                            resultado = (respuesta.json())

                            st.success(resultado.get("mensaje","Correo eliminado correctamente."))

                            #Actualizamos la lista
                            #de correos.
                            st.session_state["correos"] = resultado.get("correos_destino",[])

                        else:
                            try:
                                error_api = (respuesta.json())
                                mensaje_error = (error_api.get("detail","No fue posible eliminar el correo."))

                            except Exception:

                                mensaje_error = (respuesta.text)

                            st.error(mensaje_error)

                    except Exception as error:

                        st.error(f"Error al eliminar el correo: {error}")

#PIE DE PAGINA
st.divider()

st.caption(
    "MediFlow - Sistema de procesamiento "
    "y validacion de documentos clinicos,"
    "Equipo 50, LATAM G-10."
)
