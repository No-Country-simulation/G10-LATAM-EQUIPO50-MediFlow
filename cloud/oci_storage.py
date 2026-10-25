"""
Wrapper inteligente sobre el SDK de OCI Object Storage para MediFlow.
Funciona de forma transparente tanto en Docker Local como en Google Cloud Run.
"""

import os
import logging
import uuid
from datetime import datetime, timedelta, timezone

import oci

# Importamos las variables centralizadas de tu módulo de configuración
from configuracion import (
    OCI_NAMESPACE, OCI_REGION, OCI_TENANCY_OCID, OCI_USER_OCID,
    OCI_FINGERPRINT, OCI_PRIVATE_KEY_FILE, OCI_PRIVATE_KEY_CONTENT
)

logger = logging.getLogger(__name__)

# Mapeo de nombres físicos de los 6 buckets para OCI
BUCKET_RECIBIDOS = os.getenv("OCI_BUCKET_RECIBIDOS", "mediflow-recibidos")
BUCKET_HISTORIA_CLINICA = os.getenv("OCI_BUCKET_HISTORIA_CLINICA", "mediflow-historia-clinica")
BUCKET_REVISION_HUMANA = os.getenv("OCI_BUCKET_REVISION_HUMANA", "mediflow-revision-humana")
BUCKET_URGENCIAS = os.getenv("OCI_BUCKET_URGENCIAS", "mediflow-urgencias")
BUCKET_FARMACIA = os.getenv("OCI_BUCKET_FARMACIA", "mediflow-farmacia")
BUCKET_AUDITORIA_AUTORIZACIONES = os.getenv("OCI_BUCKET_AUDITORIA_AUTORIZACIONES", "mediflow-auditoria-autorizaciones")

_client = None

def _get_client():
    """Inicializa el cliente de OCI adaptándose automáticamente al entorno."""
    global _client
    if _client is None:
        # Base de configuración obligatoria común
        config = {
            "tenancy": OCI_TENANCY_OCID,
            "user": OCI_USER_OCID,
            "fingerprint": OCI_FINGERPRINT,
            "region": OCI_REGION
        }

        # Estrategia Híbrida: Detectar el tipo de llave disponible
        if OCI_PRIVATE_KEY_FILE and os.path.exists(OCI_PRIVATE_KEY_FILE):
            # MODALIDAD LOCAL (DOCKER): Se pasa la ruta absoluta interna del volumen /tmp
            config["key_file"] = OCI_PRIVATE_KEY_FILE
            logger.info("Autenticando SDK de OCI mediante archivo de llave física (Local Docker).")
        elif OCI_PRIVATE_KEY_CONTENT:
            # MODALIDAD PROD (CLOUD RUN): Se pasa el string PEM crudo inyectado desde Secret Manager
            config["key_content"] = OCI_PRIVATE_KEY_CONTENT
            logger.info("Autenticando SDK de OCI mediante contenido de llave en memoria (Cloud Run).")
        else:
            raise ValueError("No se pudo inicializar OCI: Falta configurar una llave privada (.pem)")

        oci.config.validate_config(config)
        _client = oci.object_storage.ObjectStorageClient(config)

    return _client

def subir_objeto_oci(bucket_name: str, nombre_objeto: str, contenido: bytes) -> None:
    """Sube un objeto al bucket indicado en Oracle Cloud Infrastructure."""
    try:
        client = _get_client()
        client.put_object(
            namespace_name=OCI_NAMESPACE,
            bucket_name=bucket_name,
            object_name=nombre_objeto,
            put_object_body=contenido
        )
    except Exception as e:
        logger.error(f"Error crítico en put_object de OCI sobre el bucket {bucket_name}: {e}")
        raise e


def generar_url_par(bucket_name: str, nombre_objeto: str, horas: int = 2) -> str:
    """Devuelve una URL temporal (Pre-Authenticated Request, solo lectura) para un objeto
    de un bucket PRIVADO de OCI.

    El usuario de la API necesita PAR_MANAGE sobre el bucket y permiso de lectura de objetos
    (por ejemplo: "Allow group <grupo> to manage object-family in compartment <compartimento>").
    """
    client = _get_client()
    detalles = oci.object_storage.models.CreatePreauthenticatedRequestDetails(
        name=f"alerta-{uuid.uuid4().hex[:12]}",
        access_type="ObjectRead",
        object_name=nombre_objeto,
        time_expires=datetime.now(timezone.utc) + timedelta(hours=horas),
    )
    respuesta = client.create_preauthenticated_request(
        namespace_name=OCI_NAMESPACE,
        bucket_name=bucket_name,
        create_preauthenticated_request_details=detalles,
    )
    return f"https://objectstorage.{OCI_REGION}.oraclecloud.com{respuesta.data.access_uri}"