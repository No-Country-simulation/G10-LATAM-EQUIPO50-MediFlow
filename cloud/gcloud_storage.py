"""
Wrapper delgado sobre el SDK de Google Cloud Storage
 
Requiere:
  - El paquete `google-cloud-storage` instalado (ver requirements.txt)
  - Credenciales de una cuenta de servicio de GCP, vía la variable de
    entorno GOOGLE_APPLICATION_CREDENTIALS apuntando al archivo JSON
    de la cuenta de servicio (ver infraestructura_cloud.md, paso 3)
 
Los 3 contenedores de GCS que utiliza MediFlow son:
  - recibidos          -> documento recién ingresado, antes de procesar
  - procesados         -> documento con el JSON de salida ya generado
  - auditoria_humana   -> casos que requieren revisión humana
"""
 
import os
from google.cloud import storage
 
BUCKET_RECIBIDOS = os.getenv("GCS_BUCKET_RECIBIDOS", "mediflow-recibidos")
BUCKET_PROCESADOS = os.getenv("GCS_BUCKET_PROCESADOS", "mediflow-procesados")
BUCKET_AUDITORIA = os.getenv("GCS_BUCKET_AUDITORIA", "mediflow-auditoria-humana")
 
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
    """Sube (o sobrescribe) un objeto en el bucket indicado.
 
    contenido: bytes del archivo (leerlo con open(ruta, "rb").read() si viene de disco).
    """
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
    """Mueve un objeto entre buckets: copia al destino y borra del origen,
    en ese orden, para no perder el archivo si algo falla a mitad de camino.
    """
    client = _get_client()
    origen = client.bucket(bucket_origen)
    destino = client.bucket(bucket_destino)
    blob_origen = origen.blob(nombre_objeto)
 
    origen.copy_blob(blob_origen, destino, nombre_objeto)
    blob_origen.delete()
 
 
# --- Atajos para los 3 buckets del proyecto, para no repetir el nombre en cada llamada ---
 
def guardar_recibido(nombre_objeto: str, contenido: bytes) -> None:
    subir_objeto(BUCKET_RECIBIDOS, nombre_objeto, contenido)
 
 
def marcar_procesado(nombre_objeto: str) -> None:
    mover_objeto(BUCKET_RECIBIDOS, BUCKET_PROCESADOS, nombre_objeto)
 
 
def marcar_auditoria_humana(nombre_objeto: str) -> None:
    mover_objeto(BUCKET_RECIBIDOS, BUCKET_AUDITORIA, nombre_objeto)
 
 
if __name__ == "__main__":
    # Prueba rápida y manual: subir un archivo de ejemplo y confirma que llegó.
    ejemplo = b'{"prueba": "conexion GCS ok"}'
    guardar_recibido("prueba_conexion.json", ejemplo)
    print("Subido a", BUCKET_RECIBIDOS, "- revisa el bucket en la consola para confirmar.")
 
