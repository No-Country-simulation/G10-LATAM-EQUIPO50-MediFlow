"""
Puente entre el guardado local (Backend_MediFlow/archivos.py,
Backend_MediFlow/almacenamiento.py) y Google Cloud Storage
(cloud/gcloud_storage.py).
"""

import logging
import os

from cloud.gcloud_storage import (
    BUCKET_HISTORIA_CLINICA,
    BUCKET_REVISION_HUMANA,
    BUCKET_URGENCIAS,
    BUCKET_FARMACIA,
    BUCKET_AUDITORIA_AUTORIZACIONES,
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


def sincronizar_json_final(ruta_json: str, clasificacion: str, categoria: str = "Otro") -> bool:
    """Sube el JSON final clasificado al bucket que corresponda según la jerarquía
    de clasificación final de LangGraph y la categoría del documento.
    
    Compatible con la llamada actual de Streamlit.
    """
    try:
        # 1. Aplicar reglas de enrutamiento con jerarquía de prioridades
        if clasificacion == "urgente":
            bucket_destino = BUCKET_URGENCIAS
            
        elif clasificacion in {"ambiguo", "datos_faltantes", "alerta", "revision_prioritaria", "revision"}:
            bucket_destino = BUCKET_REVISION_HUMANA
            
        elif clasificacion == "normal":
            # El caso es normal, decidimos por categoría de documento
            if categoria == "Receta Médica":
                bucket_destino = BUCKET_FARMACIA
            elif categoria == "Orden de Solicitud de Procedimiento":
                bucket_destino = BUCKET_AUDITORIA_AUTORIZACIONES
            else:
                # 'Informe de Estudio...', 'Epicrisis...', 'Certificado Médico' y 'Otro'
                bucket_destino = BUCKET_HISTORIA_CLINICA
        else:
            # Plan de escape preventivo
            bucket_destino = BUCKET_REVISION_HUMANA

        nombre_objeto = os.path.basename(ruta_json)
        with open(ruta_json, "rb") as archivo:
            contenido = archivo.read()
            
        subir_objeto(bucket_destino, nombre_objeto, contenido)
        logger.info(f"JSON sincronizado con éxito en el bucket: {bucket_destino}")
        return True
        
    except Exception as error:
        logger.warning(
            "No se pudo sincronizar el JSON final '%s' con Cloud Storage: %s",
            ruta_json,
            error,
        )
        return False
