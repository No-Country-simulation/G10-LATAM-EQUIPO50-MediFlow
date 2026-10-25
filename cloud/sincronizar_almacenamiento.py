"""
Puente unificado entre el guardado local, Google Cloud Storage y OCI Object Storage.
"""

import logging
import os

# Importaciones de Google Cloud Storage
from cloud.gcloud_storage import (
    BUCKET_HISTORIA_CLINICA as GCS_HISTORIA_CLINICA,
    BUCKET_REVISION_HUMANA as GCS_REVISION_HUMANA,
    BUCKET_URGENCIAS as GCS_URGENCIAS,
    BUCKET_FARMACIA as GCS_FARMACIA,
    BUCKET_AUDITORIA_AUTORIZACIONES as GCS_AUDITORIA_AUTORIZACIONES,
    guardar_recibido as gcs_guardar_recibido,
    subir_objeto as gcs_subir_objeto,
    generar_url_firmada as gcs_generar_url_firmada,
)

# Importaciones de OCI Object Storage
from cloud.oci_storage import (
    BUCKET_RECIBIDOS as OCI_RECIBIDOS,
    BUCKET_HISTORIA_CLINICA as OCI_HISTORIA_CLINICA,
    BUCKET_REVISION_HUMANA as OCI_REVISION_HUMANA,
    BUCKET_URGENCIAS as OCI_URGENCIAS,
    BUCKET_FARMACIA as OCI_FARMACIA,
    BUCKET_AUDITORIA_AUTORIZACIONES as OCI_AUDITORIA_AUTORIZACIONES,
    subir_objeto_oci,
    generar_url_par as oci_generar_url_par,
)

logger = logging.getLogger(__name__)


def sincronizar_archivo_original(ruta_guardada: str, nombre_generado: str) -> bool:
    """Sube el archivo original a los buckets de recibidos tanto de GCS como de OCI."""
    exito_gcs = False
    exito_oci = False
    
    try:
        with open(ruta_guardada, "rb") as archivo:
            contenido = archivo.read()
    except Exception as e:
        logger.error(f"No se pudo leer el archivo local original para sincronizar: {e}")
        return False

    # --- Sincronización GCS ---
    try:
        gcs_guardar_recibido(nombre_generado, contenido)
        exito_gcs = True
    except Exception as error:
        logger.warning(f"No se pudo sincronizar el archivo original '{nombre_generado}' con GCS: {error}")

    # --- Sincronización OCI ---
    try:
        subir_objeto_oci(OCI_RECIBIDOS, nombre_generado, contenido)
        exito_oci = True
    except Exception as error:
        logger.warning(f"No se pudo sincronizar el archivo original '{nombre_generado}' con OCI: {error}")

    return exito_gcs or exito_oci


def sincronizar_json_final(ruta_json: str, clasificacion: str, categoria: str = "Otro") -> bool:
    """Sube el JSON final clasificado al destino correcto en espejo (GCS y OCI)."""
    try:
        nombre_objeto = os.path.basename(ruta_json)
        with open(ruta_json, "rb") as archivo:
            contenido = archivo.read()
    except Exception as e:
        logger.error(f"No se pudo leer el JSON local final para sincronizar: {e}")
        return False

    # 1. Resolver los destinos correspondientes de forma independiente
    if clasificacion == "urgente":
        gcs_destino = GCS_URGENCIAS
        oci_destino = OCI_URGENCIAS
    elif clasificacion in {"ambiguo", "datos_faltantes", "alerta", "revision_prioritaria", "revision"}:
        gcs_destino = GCS_REVISION_HUMANA
        oci_destino = OCI_REVISION_HUMANA
    elif clasificacion == "normal":
        if categoria == "Receta Médica":
            gcs_destino = GCS_FARMACIA
            oci_destino = OCI_FARMACIA
        elif categoria == "Orden de Solicitud de Procedimiento":
            gcs_destino = GCS_AUDITORIA_AUTORIZACIONES
            oci_destino = OCI_AUDITORIA_AUTORIZACIONES
        else:
            gcs_destino = GCS_HISTORIA_CLINICA
            oci_destino = OCI_HISTORIA_CLINICA
    else:
        gcs_destino = GCS_REVISION_HUMANA
        oci_destino = OCI_REVISION_HUMANA

    # 2. Ejecutar la subida a Google Cloud Storage
    exito_gcs = False
    try:
        gcs_subir_objeto(gcs_destino, nombre_objeto, contenido)
        logger.info(f"JSON sincronizado con éxito en GCS bucket: {gcs_destino}")
        exito_gcs = True
    except Exception as error:
        logger.warning(f"Fallo de sincronización en GCS para '{nombre_objeto}': {error}")

    # 3. Ejecutar la subida a OCI Object Storage
    exito_oci = False
    try:
        subir_objeto_oci(oci_destino, nombre_objeto, contenido)
        logger.info(f"JSON sincronizado con éxito en OCI bucket: {oci_destino}")
        exito_oci = True
    except Exception as error:
        logger.warning(f"Fallo de sincronización en OCI para '{nombre_objeto}': {error}")

    # 4. Alerta por correo para casos que requieren revisión humana o son urgentes.
    #    No depende de que las subidas hayan salido bien: si una nube falla, el correo
    #    igual se envía y el enlace de esa nube aparece como "No disponible".
    if clasificacion != "normal":
        import json

        horas_vigencia = int(os.getenv("HORAS_VIGENCIA_ENLACES", "2"))

        # Valores por defecto por si el JSON no trae las llaves esperadas
        nombre_paciente = "No especificado"
        nombre_medico = "No especificado"
        motivos = []

        try:
            payload = json.loads(contenido.decode("utf-8"))

            paciente = payload.get("paciente") or {}
            medico = payload.get("medico") or {}
            nombre_paciente = paciente.get("nombre_completo") or paciente.get("nombre") or nombre_paciente
            nombre_medico = medico.get("nombre_completo") or medico.get("nombre") or nombre_medico

            # Los motivos reales viven en validacion_coherencia y clasificacion_riesgo
            motivos_coherencia = (payload.get("validacion_coherencia") or {}).get("motivos") or []
            if isinstance(motivos_coherencia, str):
                motivos_coherencia = [motivos_coherencia]
            motivos.extend(str(m) for m in motivos_coherencia)

            riesgo = payload.get("clasificacion_riesgo") or {}
            if riesgo.get("motivo_urgencia"):
                motivos.append(f"Urgencia: {riesgo['motivo_urgencia']}")
            if riesgo.get("datos_faltantes"):
                motivos.append("Datos faltantes: " + ", ".join(str(d) for d in riesgo["datos_faltantes"]))
            if riesgo.get("datos_ambiguos"):
                motivos.append("Datos ambiguos: " + ", ".join(str(d) for d in riesgo["datos_ambiguos"]))
        except Exception as err_json:
            logger.warning(f"No se pudo extraer la metadata del JSON para el correo: {err_json}")

        if not motivos:
            motivos = ["Revisión requerida por flujo analítico"]

        # --- Enlaces temporales: los buckets son privados, solo se comparten URLs firmadas ---
        url_gcs_final = None
        url_oci_final = None

        if exito_gcs:
            try:
                url_gcs_final = gcs_generar_url_firmada(gcs_destino, nombre_objeto, horas_vigencia)
            except Exception as error:
                logger.warning(f"No se pudo firmar la URL de GCS para '{nombre_objeto}': {error}")

        if exito_oci:
            try:
                url_oci_final = oci_generar_url_par(oci_destino, nombre_objeto, horas_vigencia)
            except Exception as error:
                logger.warning(f"No se pudo generar el enlace (PAR) de OCI para '{nombre_objeto}': {error}")

        # --- Envío del correo ---
        try:
            try:
                # Mismo módulo que usa el frontend (evita cargar una segunda copia)
                from Backend_MediFlow.correo import enviar_alerta_correo
            except ImportError:
                from correo import enviar_alerta_correo

            enviar_alerta_correo(
                nombre_paciente=nombre_paciente,
                nombre_medico=nombre_medico,
                tipo_documento=categoria,
                clasificacion_final=clasificacion,
                motivo="\n".join(f"- {m}" for m in motivos),
                ruta_json=ruta_json,
                bucket_gcs_nombre=gcs_destino,
                bucket_gcs_url=url_gcs_final,
                bucket_oci_nombre=oci_destino,
                bucket_oci_url=url_oci_final,
            )
        except Exception as error_alerta:
            logger.error(f"Fallo al llamar al módulo de alertas por correo: {error_alerta}")

    return exito_gcs or exito_oci