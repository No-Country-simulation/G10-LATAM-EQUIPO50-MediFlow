
#Archivo Principal de FastAPI para MediFlow

#Librerias usadas:
#Permite crear la aplicacion y los endpoints de FastAPI.
from fastapi import FastAPI, UploadFile, File, HTTPException

#Permite trabajar con rutas y extensiones de archivos.
from pathlib import Path

#Permite trabajar con archivos y carpetas.
import os
import sys
import shutil


###
#Conectamos FASTAPI Conm los Modulos del BACKEND
#Obtenemos la carpeta principal del proyecto.
#app_fastapi.py esta dentro de Frontend,
#por lo que debemos subir un nivel.
# CAMBIO: Utilizamos un nombre exclusivo para evitar
#que los import * del Backend sobrescriban esta variable.
Carpeta_Proyecto_FastAPI = Path(__file__).resolve().parent.parent

#Obtenemos la carpeta Backend_MediFlow.
Carpeta_Backend = Carpeta_Proyecto_FastAPI / "Backend_MediFlow"

#Agregamos Backend_MediFlow a Python para poder importar
#los modulos existentes de MediFlow.
if str(Carpeta_Backend) not in sys.path:

    sys.path.insert(0,str(Carpeta_Backend))


#Importamos las funciones existentes,
#En el Backend
#Funciones para recibir, validar y guardar archivos.
from Backend_MediFlow.archivos import *

#Funciones para trabajar con Gemini.
from Backend_MediFlow.gemini import *

#Funciones de LangGraph.
from Backend_MediFlow.langgraph_mediflow import *

#Funciones para guardar el JSON Final.
from Backend_MediFlow.almacenamiento import *

#Funciones para enviar alertas por correo.
from Backend_MediFlow.correo import *

#Funciones para cargar y guardar las configuraciones actuales.
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

#Creamos la aplicacion FastAPI de MediFlow.
app = FastAPI(
    title="MediFlow API",
    description="API para el procesamiento de documentos clinicos de MediFlow.",
    version="1.0.0"
)

#Endpoint principal para comprobar que FastAPI
#y MediFlow estan funcionando.
@app.get("/")
def inicio():

    return {
        "mensaje": "MediFlow API funcionando correctamente.",
        "estado": "activo"
    }


#Endpoint para comprobar el estado de la API.
@app.get("/estado")
def estado():

    return {
        "proyecto": "MediFlow",
        "estado": "activo"
    }

#EndPoint Para consultar los umbrales actuales de MediFlow:
@app.get("/configuracion/umbrales")
def obtener_umbrales():

    try:

        #Cargamos los umbrales utilizando
        #la misma funcion que utiliza el Backend.
        umbrales = cargar_configuracion_umbrales()

        return {"estado":"ok","umbrales":umbrales}

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"No fue posible cargar los umbrales: {error}"
        )

#EndPoint Para modificar los umbrales de MediFlow:
@app.put("/configuracion/umbrales")
def actualizar_umbrales(umbrales: dict):

    try:

        #Validamos los valores recibidos
        #utilizando la funcion existente del Backend.
        if not validar_umbrales(umbrales):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Configuracion de umbrales invalida. "
                    "Debe cumplirse: "
                    "0 <= NORMAL < REVISIÓN < ALERTA <= 100."
                )
            )

        #Convertimos los valores a enteros
        #para mantener el mismo formato utilizado
        #por el Backend.
        nuevos_umbrales = {

            "umbral_normal":
                int(umbrales["umbral_normal"]),

            "umbral_revision":
                int(umbrales["umbral_revision"]),

            "umbral_alerta":
                int(umbrales["umbral_alerta"])
        }

        #Guardamos la nueva configuracion
        #utilizando la funcion existente.
        guardar_configuracion_umbrales(nuevos_umbrales)

        return {

            "estado":
                "ok",

            "mensaje":
                "Los umbrales fueron actualizados correctamente.",

            "umbrales":
                nuevos_umbrales
        }

    except HTTPException:

        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"No fue posible actualizar los umbrales: {error}"
        )

#EndPoint Para consultar las reglas actuales de MediFlow
@app.get("/configuracion/reglas")
def obtener_reglas():

    try:

        #Cargamos las reglas utilizando
        #la misma funcion que utiliza el Backend.
        reglas = cargar_configuracion_reglas()

        return {"estado":"ok","reglas":reglas}

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"No fue posible cargar las reglas: {error}"
        )


#EndPoint Para modificar las reglas de MediFlow
@app.put("/configuracion/reglas")
def actualizar_reglas(reglas: dict):

    try:

        #Validamos las reglas recibidas
        #utilizando la funcion existente del Backend.
        if not validar_reglas(reglas):

            raise HTTPException(
                status_code=400,
                detail=(
                    "La configuracion de reglas no es valida. "
                    "Los valores deben ser numeros enteros "
                    "entre 0 y 100."
                )
            )

        #Guardamos las nuevas reglas
        #utilizando la funcion existente.
        guardar_configuracion_reglas(reglas)

        return {

            "estado":
                "ok",

            "mensaje":
                "Las reglas fueron actualizadas correctamente.",

            "reglas":
                reglas
        }

    except HTTPException:

        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"No fue posible actualizar las reglas: {error}"
        )

#Endpoint para administrar el JSON Final generado por MediFlow.

#Este Endpoint permite que posteriormente Streamlit
#pueda decidir que hacer con el JSON Final:
#   conservar : Mantener el archivo donde MediFlow lo guardo.
#   mover     : Cambiar el JSON a otra carpeta.
#   eliminar  : Eliminar el JSON Final.
#
#IMPORTANTE:
#El archivo original NO se elimina.
#Solamente se administra el JSON Final.
@app.put("/json-final")
def administrar_json_final(
    ruta_json: str,
    accion: str,
    nueva_carpeta: str = None
):

    try:

        #Convertimos la ruta recibida
        #a una ruta absoluta.
        ruta_json = os.path.abspath(
            os.path.expanduser(ruta_json)
        )

        #Comprobamos que el JSON exista.
        if not os.path.isfile(ruta_json):

            raise HTTPException(
                status_code=404,
                detail="El JSON Final no existe en la ruta indicada."
            )


        #Normalizamos la accion recibida.
        accion = accion.strip().lower()


        #CAMBIO NUEVO:
        #OPCION 1:
        #Conservar el JSON donde MediFlow lo guardo.
        if accion == "conservar":

            return {

                "estado":
                    "ok",

                "mensaje":
                    "El JSON Final se conservara en su ubicacion actual.",

                "ruta_json_final":
                    ruta_json,

                "accion":
                    "conservar"
            }


        #CAMBIO NUEVO:
        #OPCION 2:
        #Mover el JSON a otra carpeta.
        elif accion == "mover":

            #Comprobamos que Streamlit
            #haya enviado una nueva carpeta.
            if not nueva_carpeta:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Debes indicar la carpeta "
                        "donde deseas guardar el JSON Final."
                    )
                )


            #Limpiamos posibles comillas
            #que puedan venir desde la ruta.
            nueva_carpeta = nueva_carpeta.strip("'\"")

            #Expandimos ~ por si el usuario
            #lo utiliza en la ruta.
            nueva_carpeta = os.path.expanduser(nueva_carpeta)

            #Convertimos la nueva ruta
            #a una ruta absoluta.
            nueva_carpeta = os.path.abspath(nueva_carpeta)


            #Comprobamos si la carpeta existe.
            if not os.path.isdir(nueva_carpeta):

                #Si no existe, la creamos.
                try:

                    os.makedirs(nueva_carpeta,exist_ok=True)

                except OSError as error:

                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"No fue posible crear "
                            f"la nueva carpeta: {error}"
                        )
                    )


            #Obtenemos el nombre original
            #del JSON Final.
            nombre_json = os.path.basename(ruta_json)

            #Construimos la nueva ruta.
            nueva_ruta = os.path.join(nueva_carpeta,nombre_json)


            #Comprobamos si ya existe
            #un archivo con el mismo nombre.
            if os.path.exists(nueva_ruta):

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Ya existe un archivo con el mismo "
                        "nombre en la carpeta seleccionada."
                    )
                )


            #Movemos el JSON Final
            #desde la ubicacion actual
            #hasta la nueva carpeta.
            shutil.move(ruta_json,nueva_ruta)


            return {

                "estado":
                    "ok",

                "mensaje":
                    "El JSON Final fue movido correctamente.",

                "ruta_json_anterior":
                    ruta_json,

                "ruta_json_final":
                    nueva_ruta,

                "accion":
                    "mover"
            }


        #CAMBIO NUEVO:
        #OPCION 3:
        #Eliminar solamente el JSON Final.
        elif accion == "eliminar":

            #Eliminamos el JSON Final.
            os.remove(ruta_json)


            return {

                "estado":
                    "ok",

                "mensaje":
                    "El JSON Final fue eliminado correctamente.",

                "ruta_json_final":
                    None,

                "accion":
                    "eliminar"
            }


        #CAMBIO NUEVO:
        #Si Streamlit envia una accion
        #que MediFlow no reconoce.
        else:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Accion no valida. "
                    "Debes utilizar: "
                    "conservar, mover o eliminar."
                )
            )


    except HTTPException:

        #Si FastAPI ya genero un error HTTP,
        #lo devolvemos sin modificarlo.
        raise


    except OSError as error:

        #Capturamos errores relacionados
        #con archivos y carpetas.
        raise HTTPException(
            status_code=500,
            detail=(
                f"No fue posible administrar "
                f"el JSON Final: {error}"
            )
        )


    except Exception as error:

        #Capturamos cualquier otro error.
        raise HTTPException(
            status_code=500,
            detail=(
                f"Error al administrar "
                f"el JSON Final: {error}"
            )
        )


#ENDPOINT Para procesar el documento completo
#Endpoint para recibir un archivo y ejecutar
#el flujo completo de MediFlow.
@app.post("/procesar")
async def procesar_archivo(
    archivo: UploadFile = File(...)
):

    try:

        #Paso 1:
        #Comprobamos que se obtiene el Documento:
        #Obtenemos el nombre del archivo recibido.
        nombre_archivo = archivo.filename

        #Comprobamos que se haya recibido un archivo.
        if not nombre_archivo:

            raise HTTPException(
                status_code=400,
                detail="No se recibio ningun archivo."
            )


        #Paso 2:
        #Validamos la Extension del documento subido:
        #Obtenemos la extension del archivo.
        extension = Path(nombre_archivo).suffix.lower()

        #Extensiones permitidas por MediFlow.
        extensiones_permitidas = {

            ".jpg",
            ".jpeg",
            ".png",
            ".bmp",
            ".tiff",
            ".webp",
            ".pdf",
            ".json"
        }

        #Comprobamos que la extension sea permitida.
        if extension not in extensiones_permitidas:

            raise HTTPException(
                status_code=400,
                detail="El formato del archivo no es compatible con MediFlow."
            )


        #Paso 3:
        #Creamos las carpetas
        #Utilizamos la funcion que ya existe
        #en archivos.py.
        crear_carpetas_base()


        #Paso 4:
        #Creamos carpeta temporal para ver si funciona
        #La carpeta Almacen_Local se encuentra fuera
        #de Backend_MediFlow y Frontend.
        Carpeta_Almacen = Carpeta_Proyecto_FastAPI / "Almacen_Local"

        #Creamos una carpeta temporal para recibir
        #el archivo enviado mediante FastAPI.
        # CAMBIO: Carpeta_Almacen es una cadena de texto,
        # por eso utilizamos os.path.join() para construir la ruta.
        #Carpeta_Temporales = os.path.join(Carpeta_Almacen,"Archivos_Temporales")
        Carpeta_Temporal = Carpeta_Almacen / "Archivos_Temporales"

        #Creamos la carpeta Temporal:
        Carpeta_Temporal.mkdir(parents=True,exist_ok=True)

        #Paso 5:
        #Testeamos si sirve el guardar el archivo 
        #Creamos la ruta temporal del archivo.
        ruta_temporal = Carpeta_Temporal / nombre_archivo

        #Guardamos el archivo recibido.
        with open(ruta_temporal,"wb") as archivo_destino:

            shutil.copyfileobj(archivo.file,archivo_destino)


        #Paso 6:
        #Validamos el archivo con la funcion que hicimos,
        #En el Backend
        #Convertimos la ruta a texto porque
        #las funciones existentes de MediFlow
        #trabajan con rutas.
        ruta_archivo = str(ruta_temporal)

        #Utilizamos la validacion existente.
        tipo_archivo = validar_extension(ruta_archivo)


        #Paso 7:
        #Guardamos la copia del archivo 
        #Utilizamos la funcion existente del Backend.
        #Esta funcion genera el nombre con fecha y hora
        #y guarda el archivo en Archivos_Originales.
        ruta_guardada,nombre_generado = (
            guardar_archivo_original(ruta_archivo)
        )

        #Paso 8:
        #Obtenemos el MIME type utilizando
        #la funcion existente de MediFlow Backend.
        mime_type = obtener_mime_type(ruta_archivo)


        # PASO 9:
        #Procesamos el archivo con Gemini
        #Enviamos a Gemini:
        # - Ruta del archivo
        # - Tipo del archivo
        # - Nombre generado por MediFlow
        
        #De esta manera Gemini utiliza exactamente
        #el mismo nombre generado por MediFlow Backend.
        datos_clinicos = procesar_con_gemini(
            ruta_archivo,
            tipo_archivo,
            nombre_generado
        )


        #Paso 10:
        #Cargamos los Umbrales

        #FastAPI NO utiliza input(),
        #por lo que cargamos automaticamente
        #los umbrales guardados por MediFlow backend.
        umbrales = cargar_configuracion_umbrales()


        #Paso 11:
        #Cargamos las Reglas

        #FastAPI carga automaticamente las reglas
        #guardadas por MediFlow backend.
        reglas = cargar_configuracion_reglas()

        #Paso 12:
        #Ejecutamos LangGraph utilizando
        #los mismos datos que utiliza main.py.
        resultado_langgraph = ejecutar_langgraph(datos_clinicos,umbrales,reglas)


        #Paso 13:
        #Obtenemos el JSON clinico despues
        #de pasar por LangGraph (Datos clinicos finales).
        datos_clinicos_finales = (resultado_langgraph["datos_clinicos"])

        #Paso 14:
        #Obtenemos la clasificacion final
        #generada por LangGraph.
        clasificacion_final = (resultado_langgraph["clasificacion_final"])

        #Paso 15:
        #Obtenemos la categoria del documento:
        categoria = (datos_clinicos_finales["clasificacion_documento"]["categoria"])

        #Paso 16:
        #Guardamos el JSON utilizando
        #la funcion existente de almacenamiento.py.
        ruta_json = guardar_json_clasificado(
            datos_clinicos_finales,
            nombre_generado,
            clasificacion_final,
            categoria
        )

        #Paso 17:
        #Comprobamos SI REQUIERE REVISION HUMANA:

        #Obtenemos la informacion de riesgo.
        riesgo = datos_clinicos_finales.get("clasificacion_riesgo",{})

        #Comprobamos si LangGraph determino
        #que requiere revision humana.
        requiere_revision_humana = riesgo.get("requiere_revision_humana",False)


        #Paso 18:
        #Enviamos Alerta por Correo;
        #El correo solamente se envia
        #cuando MediFlow determina
        #que requiere revision humana.
        correo_enviado = False

        if requiere_revision_humana:

            #Obtenemos los datos del paciente.
            paciente = datos_clinicos_finales.get("paciente",{})

            nombre_paciente = paciente.get("nombre_completo","No identificado")

            #Obtenemos los datos del medico.
            medico = datos_clinicos_finales.get("medico",{})

            nombre_medico = medico.get("nombre_completo","No identificado")

            #Obtenemos el tipo de documento.
            tipo_documento = (datos_clinicos_finales.get("documento", {}).get("tipo_documento"))

            #Si no existe el tipo de documento,
            #utilizamos la categoria.
            if not tipo_documento:

                tipo_documento = categoria

            #Obtenemos los motivos de revision.
            validacion = datos_clinicos_finales.get("validacion_coherencia",{})

            motivos_revision = list(validacion.get("motivos", []))

            #Obtenemos el motivo de urgencia.
            motivo_urgencia = riesgo.get("motivo_urgencia")

            if motivo_urgencia:
                motivos_revision.append(f"Motivo de urgencia: {motivo_urgencia}")

            #Obtenemos los datos ambiguos.
            datos_ambiguos = riesgo.get("datos_ambiguos",[])

            if datos_ambiguos:
                motivos_revision.append("Datos ambiguos detectados: "+ ", ".join(str(dato)for dato in datos_ambiguos))

            #Obtenemos los datos faltantes.
            datos_faltantes = riesgo.get("datos_faltantes",[])

            if datos_faltantes:
                motivos_revision.append(
                    "Datos faltantes detectados: "
                    + ", ".join(
                        str(dato)
                        for dato in datos_faltantes
                    )
                )


            #Si no existe ningun motivo,
            #agregamos un mensaje general.
            if not motivos_revision:
                motivos_revision.append(
                    "El documento fue clasificado "
                    "por LangGraph como un documento "
                    "que requiere revision humana."
                )

            #Convertimos los motivos
            #en un solo texto.
            motivo_correo = "\n".join(f"- {motivo}"for motivo in motivos_revision)

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

        #Paso 19:
        #Eliminamos el archivo temporal testeado,
        #El archivo original ya fue copiado
        #a Archivos_Originales.
        
        #Por lo tanto podemos eliminar
        #la copia temporal recibida por FastAPI.
        if os.path.exists(ruta_temporal):

            os.remove(ruta_temporal)

        #Paso 20:
        #Respuesta Finala que da FastApi,
        #Obtenemos la validacion final.
        validacion_final = datos_clinicos_finales.get("validacion_coherencia",{})

        #Devolvemos la informacion que posteriormente
        #podra utilizar Streamlit.
        return {

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


    except HTTPException:

        #Si FastAPI ya genero un error HTTP,
        #lo devolvemos sin modificarlo.
        raise


    except Exception as error:
        import traceback
        traceback.print_exc()

        #Si ocurre cualquier otro error durante
        #el procesamiento completo,
        #FastAPI devuelve un error 500.
        raise HTTPException(
            status_code=500,
            detail=f"Error durante el procesamiento de MediFlow: {error}"
        )