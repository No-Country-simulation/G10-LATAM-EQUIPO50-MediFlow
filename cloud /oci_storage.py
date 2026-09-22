"""
Wrapper delgado sobre el SDK de OCI para que el resto del equipo suba/mueva
objetos entre los 3 buckets del proyecto sin tener que aprenderse el SDK.
 
Requiere:
  - El paquete `oci` instalado (ver requirements.txt)
  - Un config file de OCI válido (ver OCI_CONFIG_FILE en .env.example) con un
    usuario que tenga permisos de lectura/escritura sobre el compartment del proyecto
    
Los 3 buckets (nombres configurables por variable de entorno):
  - recibidos          -> documento recién ingresado, antes de procesar
  - procesados         -> documento con el JSON de salida ya generado
  - auditoria_humana   -> casos que requieren revisión humana
"""
 
import os
import oci
 
# --- Configuración ---
 
OCI_CONFIG_FILE = os.getenv("OCI_CONFIG_FILE", "~/.oci/config")
BUCKET_RECIBIDOS = os.getenv("OCI_BUCKET_RECIBIDOS", "mediflow-recibidos")
BUCKET_PROCESADOS = os.getenv("OCI_BUCKET_PROCESADOS", "mediflow-procesados")
BUCKET_AUDITORIA = os.getenv("OCI_BUCKET_AUDITORIA", "mediflow-auditoria-humana")
 
_client = None
_namespace = None
 
 
def _get_client():
    """Crea (una sola vez) el cliente de Object Storage a partir del config file de OCI."""
    global _client, _namespace
    if _client is None:
        config = oci.config.from_file(file_location=os.path.expanduser(OCI_CONFIG_FILE))
        _client = oci.object_storage.ObjectStorageClient(config)
        _namespace = _client.get_namespace().data
    return _client
 
 
def _get_namespace():
    _get_client()  
    return _namespace
 
 
def subir_objeto(bucket_name: str, nombre_objeto: str, contenido: bytes) -> None:
    """Sube (o sobrescribe) un objeto en el bucket indicado.
 
    contenido: bytes del archivo (leer con open(ruta, "rb").read() si viene de disco).
    """
    client = _get_client()
    client.put_object(
        namespace_name=_get_namespace(),
        bucket_name=bucket_name,
        object_name=nombre_objeto,
        put_object_body=contenido,
    )
 
 
def descargar_objeto(bucket_name: str, nombre_objeto: str) -> bytes:
    """Devuelve el contenido (bytes) de un objeto."""
    client = _get_client()
    respuesta = client.get_object(
        namespace_name=_get_namespace(),
        bucket_name=bucket_name,
        object_name=nombre_objeto,
    )
    return respuesta.data.content
 
 
def mover_objeto(bucket_origen: str, bucket_destino: str, nombre_objeto: str) -> None:
    """Mueve un objeto entre buckets (OCI no tiene 'mover' nativo entre buckets:
    se copia al destino y se borra del origen, en ese orden, para no perder el
    archivo si algo falla a mitad de camino).
    """
    client = _get_client()
    namespace = _get_namespace()
 
    client.copy_object(
        namespace_name=namespace,
        bucket_name=bucket_origen,
        copy_object_details=oci.object_storage.models.CopyObjectDetails(
            source_object_name=nombre_objeto,
            destination_region=client.base_client.get_config().get("region"),
            destination_namespace=namespace,
            destination_bucket=bucket_destino,
            destination_object_name=nombre_objeto,
        ),
    )
    client.delete_object(
        namespace_name=namespace,
        bucket_name=bucket_origen,
        object_name=nombre_objeto,
    )
 
 
# --- Atajos para los 3 buckets del proyecto, para no repetir el nombre en cada llamada ---
 
def guardar_recibido(nombre_objeto: str, contenido: bytes) -> None:
    subir_objeto(BUCKET_RECIBIDOS, nombre_objeto, contenido)
 
 
def marcar_procesado(nombre_objeto: str) -> None:
    mover_objeto(BUCKET_RECIBIDOS, BUCKET_PROCESADOS, nombre_objeto)
 
 
def marcar_auditoria_humana(nombre_objeto: str) -> None:
    mover_objeto(BUCKET_RECIBIDOS, BUCKET_AUDITORIA, nombre_objeto)
 
 
if __name__ == "__main__":
    # Prueba rápida y manual: sube un archivo de ejemplo y confirma que llegó.
  
    # solo para probar la conexión. BORRAR ANTES DEL PIPELINE FINAL
    ejemplo = b'{"prueba": "conexion OCI ok"}'
    guardar_recibido("prueba_conexion.json", ejemplo)
    print("Subido a", BUCKET_RECIBIDOS, "- revisa el bucket en la consola para confirmar.")
 
