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

    # 4. Lógica de alertas para casos que requieren revisión o son urgentes
    if clasificacion != "normal" and (exito_gcs or exito_oci):
        import json
        from datetime import datetime, timedelta, timezone

        # Valores por defecto por si el JSON no tiene las llaves exactas
        datos_paciente_nombre = "No especificado"
        datos_medico_nombre = "No especificado"
        motivos_lista = ["Revisión requerida por flujo analítico"]

        try:
            payload_clinico = json.loads(contenido.decode("utf-8"))
            paciente_info = payload_clinico.get("paciente", {})
            datos_paciente_nombre = paciente_info.get("nombre", paciente_info.get("nombre_completo", "No especificado"))

            medico_info = payload_clinico.get("medico", {})
            datos_medico_nombre = medico_info.get("nombre", medico_info.get("nombre_completo", "No especificado"))

            alertas = payload_clinico.get("motivos", payload_clinico.get("alertas", []))
            if alertas:
                motivos_lista = alertas if isinstance(alertas, list) else [str(alertas)]
        except Exception as err_json:
            logger.warning(f"No se pudo extraer la metadata del JSON para el correo: {err_json}")

        # --- GENERACIÓN DE ENLACES TEMPORALES AUTENTICADOS (FIRMADOS) ---
        url_gcs_final = "No disponible (Fallo en GCS)"
        url_oci_final = "No disponible (Fallo en OCI)"

        # A. Firmar URL de Google Cloud Storage usando tu wrapper nativo
        if exito_gcs:
            try:
                from cloud.gcloud_storage import obtener_cliente_gcs
                cliente_gcs = obtener_cliente_gcs()
                
                bucket_gcs_obj = cliente_gcs.bucket(gcs_destino)
                blob_obj = bucket_gcs_obj.blob(nombre_objeto)
                
                # Genera la URL firmada de descarga directa (Válida por 2 horas)
                url_gcs_final = blob_obj.generate_signed_url(expiration=timedelta(hours=2))
            except Exception as e_gcs_sign:
                logger.warning(f"No se pudo firmar la URL de GCS: {e_gcs_sign}")

        # B. Generar Petición Preautenticada (PAR) en OCI usando tu wrapper nativo
        if exito_oci:
            try:
                import oci
                from cloud.oci_storage import obtener_cliente_oci, OCI_NAMESPACE, OCI_REGION
                cliente_oci = obtener_cliente_oci()
                
                detalles_par = oci.object_storage.models.CreatePreauthenticatedRequestDetails(
                    name=f"AccesoDemo_{nombre_objeto}",
                    access_type="ObjectRead",
                    object_name=nombre_objeto,
                    time_expires=datetime.now(timezone.utc) + timedelta(hours=2)
                )
                
                respuesta_par = cliente_oci.create_preauthenticated_request(
                    namespace_name=OCI_NAMESPACE,
                    bucket_name=oci_destino,
                    create_preauthenticated_request_details=detalles_par
                )
                
                url_oci_final = f"https://objectstorage.{OCI_REGION}.oraclecloud.com{respuesta_par.data.access_uri}"
            except Exception as e_oci_sign:
                logger.warning(f"No se pudo generar la URL firmada de OCI: {e_oci_sign}")

        # --- ENVÍO DEL CORREO MEDIANTE SALTO DE CARPETA DINÁMICO ---
        try:
            # Importamos sys de forma diferida para manipular las rutas de búsqueda
            import sys
            
            # Obtenemos la ruta absoluta de la carpeta padre (Backend_Mediflow)
            ruta_padre = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            
            # Si no está registrada en las rutas de búsqueda de Python, la agregamos
            if ruta_padre not in sys.path:
                sys.path.insert(0, ruta_padre)

            # Ahora Python encontrará 'correo.py' en la raíz sin problemas
            from correo import enviar_alerta_correo

            # Ejecutamos la función pasando los 8 argumentos requeridos
            enviar_alerta_correo(
                nombre_paciente=datos_paciente_nombre,
                nombre_medico=datos_medico_nombre,
                tipo_documento=categoria,
                clasificacion_final=clasificacion,
                motivo=", ".join(motivos_lista),
                ruta_json=ruta_json,
                bucket_gcs_nombre=gcs_destino,
                bucket_gcs_url=url_gcs_final,
                bucket_oci_nombre=oci_destino,
                bucket_oci_url=url_oci_final,
            )
        except Exception as error_alerta:
            logger.error(f"Fallo crítico al llamar al módulo de alertas por correo: {error_alerta}")