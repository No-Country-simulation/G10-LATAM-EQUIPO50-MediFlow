"""
Puente entre el guardado local (Backend_MediFlow/archivos.py,
Backend_MediFlow/almacenamiento.py) y Google Cloud Storage
(cloud/gcloud_storage.py).
 
- El guardado local no se modifica: este módulo solo lee lo que ya se guardó
  en disco y lo sube a Cloud Storage.
- Si la subida falla (por ejemplo, por falta de credenciales en un entorno
  local), el error se registra en el log y el procesamiento continúa con el
  almacenamiento local. Cada función devuelve True si la subida se completó
  y False en caso contrario.
 
Destinos:
  - archivo ORIGINAL subido por el usuario -> bucket `recibidos`
  - JSON final clasificado                 -> `procesados` (clasificación
    `normal`) o `auditoria_humana` (cualquier otra clasificación)
 
Uso (ver Frontend/app_streamlit_backend_directo.py):
    from cloud.sincronizar_almacenamiento import (
        sincronizar_archivo_original,
        sincronizar_json_final,
    )
"""
 
import logging
import os
 
from cloud.gcloud_storage import (
    BUCKET_AUDITORIA,
    BUCKET_PROCESADOS,
    guardar_recibido,
    subir_objeto,
)
 
logger = logging.getLogger(__name__)
 
 
def sincronizar_archivo_original(ruta_guardada: str, nombre_generado: str) -> bool:
    """Sube el archivo original (ya guardado en Almacen_Local/Archivos_Originales)
    al bucket `recibidos`. Se llama justo después de guardar_archivo_original().
    """
    try:
        with open(ruta_guardada, "rb") as archivo:
            contenido = archivo.read()
        guardar_recibido(nombre_generado, contenido)
        return True
    except Exception as error:
        logger.warning(
            "No se pudo sincronizar el archivo original '%s' con Cloud Storage: %s",
            nombre_generado,
            error,
        )
        return False
 
 
def sincronizar_json_final(ruta_json: str, clasificacion: str) -> bool:
    """Sube el JSON final clasificado al bucket que corresponda: `procesados`
    si la clasificación es `normal`, `auditoria_humana` en cualquier otro caso.
    Se llama justo después de guardar_json_clasificado(), con la ruta que esa
    función devuelve.
    """
    try:
        bucket_destino = BUCKET_PROCESADOS if clasificacion == "normal" else BUCKET_AUDITORIA
        nombre_objeto = os.path.basename(ruta_json)
        with open(ruta_json, "rb") as archivo:
            contenido = archivo.read()
        subir_objeto(bucket_destino, nombre_objeto, contenido)
        return True
    except Exception as error:
        logger.warning(
            "No se pudo sincronizar el JSON final '%s' con Cloud Storage: %s",
            ruta_json,
            error,
        )
        return False