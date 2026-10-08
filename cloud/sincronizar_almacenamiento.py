"""
Puente entre el guardado local (Backend_MediFlow/archivos.py,
Backend_MediFlow/almacenamiento.py) y Google Cloud Storage
(cloud/gcloud_storage.py).
 
Por qué un módulo aparte en vez de tocar archivos.py/almacenamiento.py:
- Esos dos siguen guardando en local exactamente igual que antes (nadie
  tiene que tocarlos ni resolver conflictos de merge ahí).
- Este módulo solo LEE lo que ya se guardó en disco y lo sube a GCS —
  si Cloud Storage falla, el flujo local no se ve afectado.
 
Dos objetos distintos, dos destinos distintos:
  - el archivo ORIGINAL subido por el usuario -> bucket `recibidos`
  - el JSON final ya clasificado               -> `procesados` o `auditoria_humana`,
    según la clasificación (son dos archivos distintos, no el mismo objeto
    "movido" de uno a otro bucket).
 
Uso (ver Frontend/app_streamlit_backend_directo.py):
    from cloud.sincronizar_almacenamiento import (
        sincronizar_archivo_original,
        sincronizar_json_final,
    )
"""
 
import os
from cloud.gcloud_storage import subir_objeto, BUCKET_PROCESADOS, BUCKET_AUDITORIA
 
 
def sincronizar_archivo_original(ruta_guardada: str, nombre_generado: str) -> None:
    """Sube el archivo original (ya guardado en Almacen_Local/Archivos_Originales)
    al bucket `recibidos`. Se llama justo después de guardar_archivo_original().
    """
    from cloud.gcloud_storage import guardar_recibido
 
    with open(ruta_guardada, "rb") as archivo:
        contenido = archivo.read()
    guardar_recibido(nombre_generado, contenido)
 
 
def sincronizar_json_final(ruta_json: str, clasificacion: str) -> None:
    """Sube el JSON final ya clasificado al bucket que corresponda —
    mismo criterio que usa almacenamiento.py para elegir la carpeta local
    (Normal -> procesados, cualquier otra clasificación -> auditoria_humana).
    Se llama justo después de guardar_json_clasificado(), con la ruta que
    esa función devuelve.
    """
    bucket_destino = BUCKET_PROCESADOS if clasificacion == "normal" else BUCKET_AUDITORIA
    nombre_objeto = os.path.basename(ruta_json)
 
    with open(ruta_json, "rb") as archivo:
        contenido = archivo.read()
    subir_objeto(bucket_destino, nombre_objeto, contenido)