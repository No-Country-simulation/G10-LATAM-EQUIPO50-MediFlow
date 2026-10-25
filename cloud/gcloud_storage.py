"""
Wrapper delgado sobre el SDK de Google Cloud Storage

Requiere:
  - El paquete `google-cloud-storage` instalado (ver requirements.txt)
  - Credenciales de una cuenta de servicio de GCP, vía la variable de
    entorno GOOGLE_APPLICATION_CREDENTIALS apuntando al archivo JSON
    de la cuenta de servicio (ver infraestructura_cloud.md, paso 3)

Los 6 contenedores de GCS que utiliza MediFlow son:
  - mediflow-recibidos                  -> documento recién ingresado
  - mediflow-historia-clinica           -> documentos con clasificación 'normal'
  - mediflow-revision-humana            -> casos ambiguos, datos faltantes o incoherencias
  - mediflow-urgencias                  -> documentos marcados explícitamente como urgentes
  - mediflow-farmacia                   -> recetas médicas
  - mediflow-auditoria-autorizaciones   -> órdenes de solicitud de procedimiento
"""

import os
from datetime import timedelta

from google.cloud import storage

# --- Variables de Entorno de los Buckets ---
BUCKET_RECIBIDOS = os.getenv("GCS_BUCKET_RECIBIDOS", "mediflow-recibidos")
BUCKET_HISTORIA_CLINICA = os.getenv("GCS_BUCKET_HISTORIA_CLINICA", "mediflow-historia-clinica")
BUCKET_REVISION_HUMANA = os.getenv("GCS_BUCKET_REVISION_HUMANA", "mediflow-revision-humana")
BUCKET_URGENCIAS = os.getenv("GCS_BUCKET_URGENCIAS", "mediflow-urgencias")
BUCKET_FARMACIA = os.getenv("GCS_BUCKET_FARMACIA", "mediflow-farmacia")
BUCKET_AUDITORIA_AUTORIZACIONES = os.getenv("GCS_BUCKET_AUDITORIA_AUTORIZACIONES", "mediflow-auditoria-autorizaciones")

_client = None


def _get_client():
    """Crea (una sola vez) el cliente de Cloud Storage.
    Usa GOOGLE_APPLICATION_CREDENTIALS automáticamente si está seteada.
    """
    global _client
    if _client is None:
        _client = storage.Client()
    return _client

def obtener_cliente_gcs():
    """Expone de forma pública el cliente storage.Client autenticado."""
    return _get_client()


def generar_url_firmada(bucket_name: str, nombre_objeto: str, horas: int = 2) -> str:
    """Devuelve una URL V4 temporal de descarga (GET) para un objeto de un bucket PRIVADO.

    Dos modalidades, según las credenciales disponibles:

    1) Con llave de cuenta de servicio (Docker local, GOOGLE_APPLICATION_CREDENTIALS apuntando
       al JSON de una CUENTA DE SERVICIO): la firma se calcula localmente.
    2) Sin llave (Cloud Run): las credenciales de Compute solo traen un token y no pueden
       firmar localmente. Se firma por IAM (signBlob) con el token de la cuenta de servicio de
       ejecución. Requiere:
         - API iamcredentials.googleapis.com habilitada en el proyecto.
         - roles/iam.serviceAccountTokenCreator de la cuenta de servicio sobre sí misma.

    En ambos casos, la cuenta que firma necesita storage.objects.get sobre el bucket.
    """
    blob = _get_client().bucket(bucket_name).blob(nombre_objeto)
    expiracion = timedelta(hours=horas)

    try:
        return blob.generate_signed_url(version="v4", expiration=expiracion, method="GET")
    except AttributeError:
        # Credenciales sin llave privada: se firma por IAM con el token de la cuenta de servicio.
        import google.auth
        from google.auth.transport.requests import Request

        credenciales, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        credenciales.refresh(Request())
        correo_sa = getattr(credenciales, "service_account_email", None)
        if not correo_sa or correo_sa == "default":
            raise RuntimeError(
                "No se pudo determinar la cuenta de servicio con la que firmar la URL por IAM"
            )
        return blob.generate_signed_url(
            version="v4",
            expiration=expiracion,
            method="GET",
            service_account_email=correo_sa,
            access_token=credenciales.token,
        )


def subir_objeto(bucket_name: str, nombre_objeto: str, contenido: bytes) -> None:
    """Sube (o sobrescribe) un objeto en el bucket indicado."""
    client = _get_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(nombre_objeto)
    blob.upload_from_string(contenido)


def descargar_objeto(bucket_name: str, nombre_objeto: str) -> bytes:
    """Devuelve el contenido (bytes) de un objeto."""
    client = _get_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(nombre_objeto)
    return blob.download_as_bytes()


def mover_objeto(bucket_origen: str, bucket_destino: str, nombre_objeto: str) -> None:
    """Mueve un objeto entre buckets: copia al destino y borra del origen."""
    client = _get_client()
    origen = client.bucket(bucket_origen)
    destino = client.bucket(bucket_destino)
    blob_origen = origen.blob(nombre_objeto)

    origen.copy_blob(blob_origen, destino, nombre_objeto)
    blob_origen.delete()


# --- Atajos para los buckets del proyecto (Enrutamiento de flujo) ---

def guardar_recibido(nombre_objeto: str, contenido: bytes) -> None:
    subir_objeto(BUCKET_RECIBIDOS, nombre_objeto, contenido)

def marcar_historia_clinica(nombre_objeto: str) -> None:
    mover_objeto(BUCKET_RECIBIDOS, BUCKET_HISTORIA_CLINICA, nombre_objeto)

def marcar_revision_humana(nombre_objeto: str) -> None:
    mover_objeto(BUCKET_RECIBIDOS, BUCKET_REVISION_HUMANA, nombre_objeto)

def enviar_a_urgencias(nombre_objeto: str) -> None:
    mover_objeto(BUCKET_RECIBIDOS, BUCKET_URGENCIAS, nombre_objeto)

def enviar_a_farmacia(nombre_objeto: str) -> None:
    mover_objeto(BUCKET_RECIBIDOS, BUCKET_FARMACIA, nombre_objeto)

def enviar_a_auditoria_autorizaciones(nombre_objeto: str) -> None:
    mover_objeto(BUCKET_RECIBIDOS, BUCKET_AUDITORIA_AUTORIZACIONES, nombre_objeto)


if __name__ == "__main__":
    ejemplo = b'{"prueba": "conexion GCS ok"}'
    guardar_recibido("prueba_conexion.json", ejemplo)
    print("Subido a", BUCKET_RECIBIDOS, "- revisa el bucket en la consola para confirmar.")