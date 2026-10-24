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

