# Cambios en la rama `production` — Gemini en Vertex AI y despliegue en Cloud Run

La rama `production` contiene los cambios necesarios para desplegar MediFlow en Google Cloud Run. Este documento describe el commit `af2ccc7`, lo que cambió en el entorno de despliegue a raíz de él y los puntos que quedan pendientes.

| | |
|---|---|
| **Commit** | `af2ccc7` — `fix: configuración, librerías, gemini, app streamlit para producción` |
| **Rama** | `production` |
| **Autor** | Andrés Mustafá |
| **Fecha** | 19 de octubre de 2026 |
| **Alcance** | 6 archivos modificados, 96 inserciones, 60 eliminaciones |

## Resumen

El cambio de fondo es que el backend deja de autenticarse ante Gemini con una API key (Google AI Studio) y pasa a usar **Gemini a través de Vertex AI**, con las credenciales de la cuenta de servicio del servicio (Application Default Credentials). Esto es coherente con el criterio de [`infraestructura_cloud.md`](infraestructura_cloud.md): la aplicación no maneja claves. El resto del commit corrige un problema con el ícono de la pestaña de Streamlit y centraliza la validación de variables de entorno.

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `Backend_MediFlow/configuracion.py` | Cliente de Gemini sobre Vertex AI; nueva variable `GCP_PROJECT_ID`; validación centralizada de variables de entorno; `MODELO_GEMINI` con valor por defecto; `st.set_page_config` con ícono emoji |
| `Backend_MediFlow/gemini.py` | El archivo se envía como bytes dentro de la solicitud, sin subirlo antes a la Files API; reintentos ante error 503 sin cambios de lógica |
| `Backend_MediFlow/librerias.py` | Se importa `streamlit as st` (lo usa `configuracion.py`) |
| `Frontend/app_streamlit_backend.py` | `st.set_page_config` se mueve al inicio del archivo, antes de cualquier otra instrucción de Streamlit |
| `Frontend_Respaldo/app_streamlit.py` | `st.set_page_config` comentado (versión anterior, sin uso activo) |
| `.env.example` | Archivo nuevo en esta rama con las variables de entorno del proyecto |

## Detalle de los cambios

### 1. Gemini a través de Vertex AI

| | Antes | Ahora |
|---|---|---|
| Cliente | `genai.Client(api_key=GEMINI_API_KEY)` | `genai.Client(vertexai=True, project=GCP_PROJECT_ID, location="us-central1")` |
| Autenticación | API key de Google AI Studio | Application Default Credentials (cuenta de servicio en Cloud Run; `gcloud auth application-default login` en local) |
| Modelo | `MODELO_GEMINI`, sin valor por defecto | `MODELO_GEMINI`, con valor por defecto `gemini-2.5-flash` |
| Región | No aplicaba | `us-central1`, fija en el código |

Se elimina la comprobación que detenía el programa si faltaba `GEMINI_API_KEY`. El código ya no lee esa variable.

### 2. Envío del archivo como bytes

`procesar_con_gemini` ya no llama a `subir_archivo_a_gemini` (Files API). Ahora lee el archivo local, determina el tipo MIME por la extensión y lo envía dentro de la misma solicitud con `types.Part.from_bytes`.

| Extensión | Tipo MIME enviado |
|---|---|
| `.pdf` | `application/pdf` |
| `.png`, `.jpg`, `.jpeg`, `.webp` | `image/png`, `image/jpeg`, `image/webp` |
| Cualquier otra (`.json`, `.bmp`, `.tiff`) | `application/octet-stream` |

Si la lectura del archivo falla, se lanza un `RuntimeError` con el motivo.

### 3. Validación de variables de entorno

`configuracion.py` revisa en un solo punto `GCP_PROJECT_ID`, `EMAIL_USUARIO`, `EMAIL_PASSWORD` y `EMAIL_DESTINO`. Si falta alguna, imprime un aviso que indica dónde definirla (archivo `.env` en local, `--set-env-vars` en Cloud Run) y **no detiene** el programa.

### 4. Configuración de página de Streamlit

`st.set_page_config` define el ícono de la pestaña como emoji (🏥) para que el navegador no solicite `/favicon.png`. Según el comentario del código, esa solicitud rompía el hilo ASGI de Uvicorn. La llamada quedó en `configuracion.py` y al inicio del frontend.

### 5. `.env.example`

Plantilla versionada con las variables de entorno del proyecto. La versión incluida en el commit conservaba `GEMINI_API_KEY` y no tenía `GCP_PROJECT_ID`; se corrige junto con esta documentación.

## Impacto en las variables de entorno

| Variable | Antes | Ahora |
|---|---|---|
| `GEMINI_API_KEY` | Obligatoria (Secret Manager en Cloud Run) | El código ya no la lee |
| `GCP_PROJECT_ID` | No existía | **Nueva, obligatoria** |
| `MODELO_GEMINI` | Obligatoria, sin valor por defecto | Opcional; por defecto `gemini-2.5-flash` |
| `EMAIL_USUARIO`, `EMAIL_PASSWORD`, `EMAIL_DESTINO` | Obligatorias | Sin cambios en el código; en Cloud Run llegan desde Secret Manager (ver más abajo) |
| `GCS_BUCKET_RECIBIDOS`, `GCS_BUCKET_PROCESADOS`, `GCS_BUCKET_AUDITORIA` | Obligatorias | Sin cambios |

## Cambios en el entorno de despliegue

El despliegue real difiere de la primera versión de la guía de infraestructura. Las diferencias, ya incorporadas en [`infraestructura_cloud.md`](infraestructura_cloud.md):

| Tema | Guía original | Despliegue real |
|---|---|---|
| Servicio de Cloud Run | `mediflow` | `mediflow-service` |
| Imagen | `mediflow:latest` | `mediflow-app:latest` |
| Cuenta de servicio de ejecución | `mediflow-runtime` | `mediflow-backend` |
| Gemini | Secreto `mediflow-gemini-key` | Vertex AI, sin secreto; requiere `roles/aiplatform.user` y la API `aiplatform.googleapis.com` |
| `EMAIL_USUARIO` y `EMAIL_DESTINO` | Variables de entorno | Secretos (`mediflow-origin-email`, `mediflow-destinatary-email`) |
| Permisos de construcción | No incluidos | Roles para la cuenta del equipo y para la cuenta de servicio de Compute por defecto, que ejecuta Cloud Build |
| Buckets, cuenta de servicio y permisos | Se asumían creados | Creados desde la consola; la guía incluye los comandos equivalentes |
| Memoria | `--memory 1Gi` | Valor por defecto de Cloud Run |
| Variable nueva | — | `GCP_PROJECT_ID` |

## Diferencias entre las ramas

`production` y `main` comparten historia hasta el commit `5a6269a`. `production` agrega el commit `af2ccc7`; `main` tiene el commit `8a24928` (corrección parcial del README), que `production` no incluye. Mientras las ramas no se alineen, ejecutar `main` en local requiere una API key de Gemini y no reconoce `GCP_PROJECT_ID`.

## Puntos pendientes

| Punto | Detalle |
|---|---|
| **Catálogos de la validación clínica sin cargar** | `Backend_MediFlow/validacion_clinica.py` busca los catálogos en `Backend_MediFlow/casos/referencia/catalogos`, que no existe (los archivos están en `casos/referencia/catalogos` en la raíz), y el `Dockerfile` no copia `casos/` al contenedor. `cargar_catalogos` no falla: devuelve los tres catálogos vacíos (0 entradas frente a 21 de CIE-10, 20 de medicamentos y 7 de parámetros), por lo que las validaciones que dependen de ellos no tienen contra qué comparar. En una prueba con 13 JSON clínicos de ejemplo, la validación pasó de 31 a 35 conflictos al usar los catálogos reales. No es parte del commit `af2ccc7`: ya ocurre en `main`. Corrección: apuntar `CATALOGOS` a `RAIZ.parent / "casos" / "referencia" / "catalogos"` y agregar `COPY casos/referencia/catalogos ./casos/referencia/catalogos` al `Dockerfile` |
| **Tipos MIME de `.json`, `.bmp` y `.tiff`** | Ahora se envían como `application/octet-stream`; antes la Files API deducía el tipo. Conviene probar con un JSON de `casos/documents/` y con una imagen `.bmp` o `.tiff` contra Vertex AI |
| **`st.set_page_config` duplicado** | Se llama en `configuracion.py` y otra vez en el frontend. Si Streamlit (`1.58.0`) lo rechaza en algún flujo, basta dejar una sola llamada. Además, `librerias.py` ahora importa Streamlit también para el modo terminal (`main.py`) |
| **Validación que solo avisa** | Si falta `GCP_PROJECT_ID`, el aviso no detiene la ejecución; qué ocurre después depende de si el entorno aporta un proyecto por defecto |
| **Código sin uso** | `subir_archivo_a_gemini` ya no se llama desde ningún lado |
| **Destinatarios editados desde la interfaz** | Se guardan en `Almacen_Local/configuracion_correos.json`, que en Cloud Run se pierde al reiniciar la instancia. El valor permanente es `EMAIL_DESTINO` |
| **Documentación desactualizada** | `docs/contrato_datos.md` describe tres situaciones (Normal/Urgente/Ambiguo), `envio_correo.py` y el almacenamiento en OCI; `Backend_MediFlow/README_Backend.md` menciona la API key y la subida del archivo a Gemini; el docstring de `cloud/gcloud_storage.py` menciona `GOOGLE_APPLICATION_CREDENTIALS` |
| **Nombre del archivo de infraestructura** | El archivo se llama `docs/infraesctructura_cloud.md` (con error de tipeo) y los enlaces apuntan a `infraestructura_cloud.md`. Se renombra con `git mv` |
| **Correos dedicados** | Reemplazar las cuentas de prueba por cuentas dedicadas al proyecto (actualizar los tres secretos y desplegar una revisión nueva) |
| **Almacenamiento en OCI** | Planificado; ver [`infraestructura_cloud.md`](infraestructura_cloud.md#almacenamiento-en-oci-always-free--planificado) |

## Documentación que acompaña a este cambio

| Archivo | Cambio |
|---|---|
| `README.md` | Reescrito: Google Cloud Run y Vertex AI, variables de entorno actuales, requisitos de Google Cloud, ramas, OCI como planificado |
| `docs/arquitectura.md` | Diagrama y componentes actualizados; despliegue, autenticación e historial de decisiones |
| `docs/infraestructura_cloud.md` | Reescrito (antes `infraesctructura_cloud.md`): servicios, permisos, secretos, guía de despliegue con los comandos usados, OCI planificado y desarrollo local |
| `docs/cambios_produccion.md` | Archivo nuevo (este documento) |
| `.env.example` | Variables actuales: `GCP_PROJECT_ID`, sin `GEMINI_API_KEY` |
