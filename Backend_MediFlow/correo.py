#Envio de alertas por correo

#Libreriras usadas:
from librerias import *

#Configuracion compartida:
from configuracion import *

#Cambio Nuevo:
#Ruta donde se guardara la configuracion de los correos agregados,
#que recibiran las alertas de MediFlow.
Carpeta_Configuracion_Correos = os.path.join(Carpeta_Almacen,"configuracion_correos.json")

def cargar_correos_destino():
    """
    Carga los correos que recibiran las alertas
    desde el archivo configuracion_correos.json.

    Si el archivo no existe, utiliza el correo que
    actualmente se encuentra configurado en EMAIL_DESTINO
    dentro del archivo .env.

    De esta manera mantenemos compatibilidad con la
    configuracion anterior de MediFlow.
    """

    #Verificamos si ya existe el archivo de configuracion
    if os.path.exists(Carpeta_Configuracion_Correos):

        try:

            #Abrimos el archivo de configuracion
            with open(
                Carpeta_Configuracion_Correos,
                "r",
                encoding="utf-8"
            ) as archivo:

                configuracion = json.load(archivo)

            #Obtenemos la lista de correos
            correos = configuracion.get("correos_destino", [])

            #Verificamos que sea una lista
            if isinstance(correos, list):

                return correos

        except Exception as error:

            print("\nError al cargar la configuracion de correos:")
            print(error)


    #CAMBIO NUEVO:
    #Si el archivo todavia no existe,
    #utilizamos EMAIL_DESTINO del archivo .env
    #para crear la configuracion inicial.

    correos_iniciales = []

    if EMAIL_DESTINO:

        #Permitimos colocar varios correos separados por coma
        correos_iniciales = [
            correo.strip()
            for correo in EMAIL_DESTINO.split(",")
            if correo.strip()
        ]


    #CAMBIO NUEVO:
    #Guardamos automaticamente la configuracion inicial
    #en el nuevo archivo JSON.

    if correos_iniciales:

        guardar_correos_destino(correos_iniciales)


    return correos_iniciales

def guardar_correos_destino(correos):
    """
    Guarda la lista de correos que recibiran
    las alertas de MediFlow.
    """

    #Nos aseguramos de que exista la carpeta Almacen_Local
    os.makedirs(Carpeta_Almacen,exist_ok=True)

    #Creamos la estructura que tendra el archivo JSON
    configuracion = {"correos_destino": correos}

    #Guardamos la configuracion
    with open(Carpeta_Configuracion_Correos,"w",encoding="utf-8") as archivo:

        json.dump(configuracion,archivo,ensure_ascii=False,indent=4)


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

    # 4. Asegurar las URLs de descarga pública directa
    url_gcs = bucket_gcs_url if bucket_gcs_url else f"https://googleapis.com{bucket_gcs_nombre}/{nombre_archivo_json}"
    url_oci = bucket_oci_url if bucket_oci_url else f"https://objectstorage.{OCI_REGION}://{OCI_NAMESPACE}/b/{bucket_oci_nombre}/o/{nombre_archivo_json}"

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
        with smtplib.SMTP_SSL("://gmail.com", 465) as servidor:
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