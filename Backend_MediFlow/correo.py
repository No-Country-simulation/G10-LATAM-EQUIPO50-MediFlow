#Envio de alertas por correo

#Libreriras usadas:
from librerias import *

#Configuracion compartida:
from configuracion import *

#Cambio Nuevo:
#Ruta donde se guardara la configuracion de los correos agregados,
#que recibiran las alertas de MediFlow.
Carpeta_Configuracion_Correos = os.path.join(Carpeta_Almacen,"configuracion_correos.json")

#Respaldo PERSISTENTE de la lista de destinatarios en Cloud Storage.
#En Cloud Run el disco local es efimero: se borra cuando la instancia se reinicia,
#asi que la lista se guarda tambien en un objeto del bucket. Cloud Storage es la
#fuente de verdad; el archivo local es una copia y el ultimo recurso si la nube falla.
#El permiso necesario ya existe: la cuenta de servicio es objectAdmin de los buckets.
BUCKET_CONFIGURACION_CORREOS = os.getenv(
    "GCS_BUCKET_CONFIGURACION",
    os.getenv("GCS_BUCKET_RECIBIDOS","mediflow-recibidos")
)
OBJETO_CONFIGURACION_CORREOS = os.getenv(
    "GCS_OBJETO_CORREOS",
    "_configuracion/correos_destino.json"
)

def _normalizar_correos(datos):
    """
    Acepta una lista de correos, un diccionario {"correos_destino": [...]}
    o un texto separado por comas, y devuelve una lista limpia y sin repetidos.
    Devuelve None si el contenido no es valido.

    Asi el frontend (que antes guardaba una lista) y correo.py
    (que guardaba un diccionario) leen el mismo archivo sin pisarse.
    """
    if isinstance(datos,dict):
        datos = datos.get("correos_destino",[])

    if isinstance(datos,str):
        datos = datos.split(",")

    if not isinstance(datos,list):
        return None

    correos = []

    for correo in datos:
        correo = str(correo).strip()

        if correo and correo not in correos:
            correos.append(correo)

    return correos


def _leer_correos_local():
    """Lee la copia local. Devuelve la lista, o None si no existe o esta danada."""

    if not os.path.exists(Carpeta_Configuracion_Correos):
        return None

    try:
        with open(Carpeta_Configuracion_Correos,"r",encoding="utf-8") as archivo:
            return _normalizar_correos(json.load(archivo))

    except Exception as error:
        print("\nError al cargar la configuracion de correos:")
        print(error)
        return None


def _escribir_correos_local(correos):
    """Guarda la copia local. Devuelve True si pudo."""

    try:
        os.makedirs(Carpeta_Almacen,exist_ok=True)

        with open(Carpeta_Configuracion_Correos,"w",encoding="utf-8") as archivo:
            json.dump({"correos_destino": correos},archivo,ensure_ascii=False,indent=4)

        return True

    except Exception as error:
        print("\nNo se pudo guardar la copia local de los correos:")
        print(error)
        return False


def _leer_correos_gcs():
    """
    Lee la lista desde Cloud Storage.
    Devuelve ("ok", lista), ("no_existe", None) o ("error", None).
    """

    try:
        from cloud.gcloud_storage import obtener_cliente_gcs
        from google.api_core.exceptions import NotFound

        blob = (
            obtener_cliente_gcs()
            .bucket(BUCKET_CONFIGURACION_CORREOS)
            .blob(OBJETO_CONFIGURACION_CORREOS)
        )

        try:
            texto = blob.download_as_text(encoding="utf-8")
        except NotFound:
            return "no_existe", None

        correos = _normalizar_correos(json.loads(texto))

        if correos is None:
            logging.getLogger(__name__).warning(
                "La lista de correos en Cloud Storage tiene un formato no valido."
            )
            return "error", None

        return "ok", correos

    except Exception as error:
        logging.getLogger(__name__).warning(
            f"No se pudo leer la lista de correos desde Cloud Storage: {error}"
        )
        return "error", None


def _escribir_correos_gcs(correos):
    """Guarda la lista en Cloud Storage. Devuelve True si pudo."""

    try:
        from cloud.gcloud_storage import obtener_cliente_gcs

        blob = (
            obtener_cliente_gcs()
            .bucket(BUCKET_CONFIGURACION_CORREOS)
            .blob(OBJETO_CONFIGURACION_CORREOS)
        )

        blob.upload_from_string(
            json.dumps({"correos_destino": correos},ensure_ascii=False,indent=4),
            content_type="application/json"
        )

        return True

    except Exception as error:
        logging.getLogger(__name__).warning(
            f"No se pudo guardar la lista de correos en Cloud Storage: {error}"
        )
        return False


def cargar_correos_destino():
    """
    Devuelve la lista de correos que reciben las alertas.

    Orden de busqueda:
      1. Cloud Storage (fuente de verdad, sobrevive a los reinicios de Cloud Run).
      2. Copia local en Almacen_Local/configuracion_correos.json.
      3. EMAIL_DESTINO (secreto o .env). Solo sirve como valor inicial:
         una vez que existe la lista guardada, esta manda.
    """

    estado, correos = _leer_correos_gcs()

    if estado == "ok":
        #Dejamos la copia local al dia (si falla la nube, queda como respaldo)
        _escribir_correos_local(correos)
        return correos

    #La nube no tiene lista (primera vez) o no se pudo leer:
    #probamos con la copia local
    correos_local = _leer_correos_local()

    if correos_local is not None:

        #Solo sembramos la nube si de verdad no existe;
        #si fue un error pasajero NO se sobrescribe lo que haya guardado alli.
        if estado == "no_existe":
            _escribir_correos_gcs(correos_local)

        return correos_local

    #Primera vez: tomamos EMAIL_DESTINO como lista inicial
    correos_iniciales = []

    if EMAIL_DESTINO:
        correos_iniciales = _normalizar_correos(EMAIL_DESTINO) or []

    if correos_iniciales:
        _escribir_correos_local(correos_iniciales)

        if estado == "no_existe":
            _escribir_correos_gcs(correos_iniciales)

    return correos_iniciales


def guardar_correos_destino(correos):
    """
    Guarda la lista de correos que recibiran las alertas de MediFlow
    en Cloud Storage y en la copia local.

    Devuelve True si quedo guardada en Cloud Storage (persistente).
    Devuelve False si solo quedo en el disco local: en Cloud Run
    ese cambio se perderia al reiniciarse la instancia.
    """

    correos_limpios = _normalizar_correos(correos)

    if correos_limpios is None:
        raise ValueError("La lista de correos no es valida.")

    _escribir_correos_local(correos_limpios)

    return _escribir_correos_gcs(correos_limpios)


def agregar_correo_destino(correo):
    """
    Agrega un nuevo correo a la lista de destinatarios,
    Si el correo ya existe, no se vuelve a agregar.
    """
    #Quitamos espacios innecesarios
    correo = correo.strip()

    #Verificamos que se haya recibido un correo
    if not correo:
        raise ValueError("El correo no puede estar vacio.")

    #Cargamos los correos actuales
    correos = cargar_correos_destino()

    #Verificamos si el correo ya existe
    if correo in correos:
        return correos

    #Agregamos el nuevo correo
    correos.append(correo)

    #Guardamos la nueva configuracion
    guardar_correos_destino(correos)

    return correos

def eliminar_correo_destino(correo):
    """
    Elimina un correo de la lista de destinatarios.
    """

    #Quitamos espacios innecesarios
    correo = correo.strip()

    #Cargamos los correos actuales
    correos = cargar_correos_destino()


    #Verificamos si el correo existe
    if correo not in correos:

        raise ValueError("El correo indicado no se encuentra configurado.")

    #Eliminamos el correo
    correos.remove(correo)

    #Guardamos la nueva configuracion
    guardar_correos_destino(correos)


    return correos
# Traemos las variables globales necesarias del módulo configuracion
from configuracion import EMAIL_USUARIO, EMAIL_PASSWORD, EMAIL_DESTINO, GCP_PROJECT_ID
# Traemos las constantes de OCI creadas en el paso anterior
from cloud.oci_storage import OCI_NAMESPACE, OCI_REGION

logger = logging.getLogger(__name__)

# Vigencia de los enlaces temporales (debe coincidir con la que usa el puente de nube)
HORAS_VIGENCIA_ENLACES = int(os.getenv("HORAS_VIGENCIA_ENLACES", "2"))

def validar_configuracion_correo():
    """
    Verifica que las variables necesarias
    estén definidas.
    """

    if not EMAIL_USUARIO:
        raise ValueError("No se encontro EMAIL_USUARIO.")

    if not EMAIL_PASSWORD:
        raise ValueError("No se encontro EMAIL_PASSWORD.")

    #Los destinatarios ahora se obtienen desde
    #configuracion_correos.json.
    correos_destino = cargar_correos_destino()

    #Verificamos que exista por lo menos
    #un destinatario configurado.
    if not correos_destino:

        raise ValueError("No se encontraron correos destinatarios configurados.")


def enviar_alerta_correo(
    nombre_paciente,
    nombre_medico,
    tipo_documento,
    clasificacion_final,
    motivo,
    ruta_json,
    bucket_gcs_nombre=None,
    bucket_gcs_url=None,
    bucket_oci_nombre=None,
    bucket_oci_url=None
):
    """
    Envía un correo de alerta incorporando nombres de buckets y enlaces directos públicos.
    """
    validar_configuracion_correo()
    destinatarios = cargar_correos_destino()
    destinatarios_string = ", ".join(destinatarios)

    # 2. Extraer el nombre del objeto
    nombre_archivo_json = os.path.basename(ruta_json)

    # 3. LÓGICA DE RESPALDO (Fallback): Si Docker importó la función sin los nuevos datos,
    # resolvemos los buckets de forma idéntica a como lo hace el puente clínico
    if not bucket_gcs_nombre:
        if clasificacion_final == "urgente":
            bucket_gcs_nombre = "mediflow-urgencias"
            bucket_oci_nombre = "mediflow-urgencias"
        elif clasificacion_final in {"ambiguo", "datos_faltantes", "alerta", "revision_prioritaria", "revision"}:
            bucket_gcs_nombre = "mediflow-revision-humana"
            bucket_oci_nombre = "mediflow-revision-humana"
        else:
            bucket_gcs_nombre = "mediflow-historia-clinica"
            bucket_oci_nombre = "mediflow-historia-clinica"

    # 4. Enlaces temporales de descarga. Los buckets son privados: un enlace directo
    #    sin firma daria "Acceso denegado", asi que si no hay enlace firmado se avisa.
    sin_enlace = "No disponible (no se pudo generar el enlace temporal; revisar los logs)"
    url_gcs = bucket_gcs_url or sin_enlace
    url_oci = bucket_oci_url or sin_enlace

    # 5. Construir el contenedor del mensaje
    mensaje = EmailMessage()
    mensaje["Subject"] = f"⚠️ ALERTA MEDIFLOW - Requiere Revision Humana [{clasificacion_final.upper()}]"
    mensaje["From"] = EMAIL_USUARIO
    mensaje["To"] = destinatarios_string

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

Acceso Directo a los Repositorios Cloud:
====================================================================
[Google Cloud Storage]
Bucket Asignado: {bucket_gcs_nombre}
Enlace de Acceso Directo:
{url_gcs}

[Oracle Cloud Infrastructure]
Bucket Asignado: {bucket_oci_nombre}
Enlace de Acceso Directo:
{url_oci}
====================================================================
Los enlaces son temporales y vencen en {HORAS_VIGENCIA_ENLACES} hora(s).

Ruta Local de Respaldo:
{ruta_json}

Por favor, revise el documento pulsando los enlaces de acceso inmediato o en el sistema MediFlow.

Este mensaje fue generado automaticamente
por el sistema Inteligente de MediFlow.
"""
    mensaje.set_content(cuerpo)

    # 6. Conexión y envío SMTP
    try:
        print("\nConectando con el servidor de correo, espere...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(EMAIL_USUARIO, EMAIL_PASSWORD)
            servidor.send_message(mensaje)

        print("\nAlerta por correo enviada Exitosamente!!!")
        print(f"Destinatarios: {destinatarios_string}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("\nError de autenticacion: No se pudo enviar el correo.")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al enviar correo: {e}")
        return False