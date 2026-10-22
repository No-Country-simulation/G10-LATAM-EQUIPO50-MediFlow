# G10-LATAM-EQUIPO50-MediFlow

Agente Autónomo para Triaje, Extracción y Enrutamiento de Documentos Clínicos

**Sector Empresarial:** HealthTech / Gestión Hospitalaria / Aseguradoras de Salud & Clínicas Médicas
**Hackathon ONE G10 — Oracle Next Education & Alura**

---

## Descripción del proyecto: 🏥 MediFlow

MediFlow resuelve desafíos complejos de visión multimodal, extracción estructurada de datos clínicos, lógica de decisión condicional y manejo de casos ambiguos o urgentes (como datos ilegibles, prescripciones de alto riesgo o solicitudes de urgencia).

El objetivo del proyecto es diseñar, construir e implementar un agente de inteligencia artificial autónomo, especializado en la automatización del flujo de trabajo documental para entornos de salud.

### Etapas del proyecto

- **Recepción y procesamiento multiformato:** el sistema procesa archivos PDF, imágenes (recetas manuscritas, órdenes de laboratorio, estudios diagnósticos) y documentos JSON ya estructurados.
- **Clasificación automatizada de documentos:** cada documento se clasifica en una de seis categorías (Receta Médica, Informe de Estudio de Diagnóstico por Imágenes/Laboratorio, Orden de Solicitud de Procedimiento, Epicrisis / Informe de Alta, Certificado Médico, Otro) y se evalúa mediante un puntaje de incoherencia documental y una validación clínica determinística.
- **Extracción de entidades y datos clínicos:** Gemini (en Vertex AI) lee el documento directamente y extrae los datos del paciente, del profesional médico, signos vitales, tratamiento, estudios y procedimientos, sin un paso de OCR independiente.
- **Enrutamiento inteligente:** un grafo de decisión en LangGraph determina la clasificación final del documento, lo organiza automáticamente y dispara una alerta por correo electrónico cuando el caso requiere revisión humana.
- **Despliegue en la nube:** la aplicación se despliega en Google Cloud Run, con Google Cloud Storage como almacenamiento persistente.
- **Almacenamiento en OCI (en implementación):** se agregará el almacenamiento en OCI Object Storage (Always Free). Todavía no está implementado; ver [`docs/infraestructura_cloud.md`](docs/infraestructura_cloud.md).

---

## Estado actual del proyecto

| Área | Decisión |
|---|---|
| Lenguaje / orquestación | Python + LangGraph (grafo de 7 nodos) |
| Extracción / clasificación | Gemini en Vertex AI (multimodal — lee PDF, imagen y JSON directamente), autenticado con las credenciales de Google Cloud, sin API key |
| Validación clínica | Capa determinística con catálogos de referencia (CIE-10, medicamentos, valores críticos) |
| Interfaz | Streamlit (`Frontend/app_streamlit_backend_directo.py`) |
| Despliegue | Google Cloud Run (contenedor Docker). OCI Compute se descartó por falta de capacidad |
| Almacenamiento | Google Cloud Storage — buckets `recibidos` / `procesados` / `auditoria-humana` (implementado). OCI Object Storage, Always Free (en implementación) |
| Notificaciones | Correo electrónico (SMTP/Gmail) para casos que requieren revisión, con cuentas dedicadas al proyecto; las credenciales viven en Secret Manager |
| Gestión de tareas | Trello |

## Equipo

| Integrante | Rol |
|---|---|
| José Moya | Backend, arquitectura y orquestación |
| Anahí Ramírez | LLM & ML, grafo de decisión, puntaje de confianza y orquestación |
| Andrés Mustafá | Cloud e infraestructura; contrato de datos, tablero de Trello y documentación/arquitectura |
| Juan Pablo Palacio | Ingesta de documentos, casos de prueba |
| Jonatan Cuero | Interfaz |

## Documentación

| Documento | Contenido |
|---|---|
| [`docs/arquitectura.md`](docs/arquitectura.md) | Diagrama del grafo de decisión, evaluación del documento, componentes e historial de decisiones |
| [`docs/contrato_datos.md`](docs/contrato_datos.md) | Formatos de entrada, tipos de documento y estructura del JSON de salida |
| [`docs/infraestructura_cloud.md`](docs/infraestructura_cloud.md) | Arquitectura de despliegue, identidad y permisos, correos de las alertas, guía de despliegue, OCI (planificado) y desarrollo local |
| [`docs/cambios_produccion.md`](docs/cambios_produccion.md) | Cambios de la rama `production` respecto de `main`, necesarios para el despliegue en Cloud Run |
| [`Backend_MediFlow/README_Backend.md`](Backend_MediFlow/README_Backend.md) | Documentación técnica del backend |

## Ramas

| Rama | Uso |
|---|---|
| `main` | Desarrollo |
| `production` | Despliegue en Google Cloud Run (Gemini en Vertex AI y ajustes de configuración). Ver [`docs/cambios_produccion.md`](docs/cambios_produccion.md) |

## Flujo de trabajo del equipo

- **Reunión obligatoria:** lunes y jueves
- **Reunión diaria (daily):** martes, miércoles y viernes
- **Gestión de tareas:** Trello — https://trello.com/invite/b/6aacb00e8ac49dd1ff659f13/ATTI57ded9186f44107980c9f4c455e4bef3E2FDC5AF/g10-latam-equipo50-mediflow
- **Commits:** prefijo por tipo — `feat:`, `fix:`, `docs:`, `test:`

### Estructura del tablero de Trello

- **Listas:** `Listos para iniciar` → `En desarrollo` → `Pausado` → `Concluido`
- **Etiquetas por área:** `Cloud`, `Arquitectura/Agente`, `Backend`, `Interfaz`, `Docs`
- **Convención de tarjetas:** una tarjeta por tarea concreta, no por persona ni por día, para ver de un vistazo qué está bloqueado y por qué.

---

## Instalación y configuración del entorno

Este proyecto requiere un ambiente virtual aislado para gestionar sus dependencias de forma segura y evitar conflictos entre librerías. Se recomienda **Anaconda** (o **Miniconda**) para administrarlo.

### 📌 Requisitos previos

1. **Git** instalado.
2. **Anaconda Distribution** o **Miniconda** (versión más ligera):
   - 📥 [Descargar Anaconda](https://www.anaconda.com/download)
   - 📥 [Descargar Miniconda](https://docs.conda.io/en/latest/miniconda.html)
3. **Google Cloud CLI** (en macOS: `brew install --cask google-cloud-sdk`). Es necesario para ejecutar la aplicación, porque Gemini corre en Vertex AI y se autentica con las credenciales de Google Cloud.
4. Una cuenta de Google con acceso al proyecto de Google Cloud de MediFlow (rol `roles/aiplatform.user`; la asigna quien administra el proyecto).
5. **Docker Desktop**, solo si se va a ejecutar la aplicación en contenedor.

### 🚀 Pasos para configurar el ambiente

Abrir la terminal (o **Anaconda Prompt** en Windows) y ejecutar:

```bash
git clone https://github.com/No-Country-simulation/G10-LATAM-EQUIPO50-MediFlow.git
cd G10-LATAM-EQUIPO50-MediFlow

# 1. Crear el ambiente virtual con la versión de Python del proyecto (incluye pip)
conda create --name mediflow_env python=3.11.13 pip -y
conda activate mediflow_env

# 2. Verificar que se usa el Python del ambiente y no el del sistema
python -c "import sys; print(sys.executable)"            # debe apuntar a una ruta que contenga /envs/mediflow_env/
python -m pip --version # debe mostrar la misma ruta del ambiente

# 3. Instalar las dependencias (siempre con "python -m pip")
python -m pip install -r requirements.txt

# 4. Autenticarse en Google Cloud (credenciales personales, sin claves de cuenta de servicio)
gcloud auth application-default login

# 5. Crear el archivo de variables de entorno a partir de la plantilla y completarlo
cp .env.example .env

# 6. Ejecutar la aplicación
python -m streamlit run Frontend/app_streamlit_backend_directo.py
```

El nombre `mediflow_env` puede reemplazarse por el que se prefiera.

`.env.example` es la plantilla versionada, sin valores secretos; `.env` es la copia personal con los valores reales y no se versiona.

Para ejecutar el proyecto en la rama `production` o desplegarlo en Google Cloud Run, ver [`docs/infraestructura_cloud.md`](docs/infraestructura_cloud.md).

#### Solución de problemas: `error: externally-managed-environment`

El mensaje lo emite el Python administrado por el sistema (en macOS, el instalado con Homebrew). Si aparece con el ambiente activado, significa que el `python` que se está ejecutando **no es el del ambiente de conda**: el prefijo `(mediflow_env)` del prompt indica que el ambiente está activo, no que contenga su propio Python. Esto ocurre cuando el ambiente se creó sin Python o cuando otro Python queda antes en el `PATH`. Para resolverlo:

1. Comprobar qué Python se está usando:

   ```bash
   python -c "import sys; print(sys.executable)"   # debe contener /envs/mediflow_env/
   ```

   Se consulta `sys.executable` y no `which python` porque en zsh `python` suele ser un alias de `python3` (`python: aliased to python3`), y `which` muestra el alias en vez de la ruta real del intérprete.

   Si la ruta termina en `/anaconda3/bin/python3` o `/miniconda3/bin/python3` (sin `/envs/`), el ambiente activo es `base`, no `mediflow_env`: verificar que `mediflow_env` existe con `conda env list` y activarlo con `conda activate mediflow_env`. Las dependencias no deben instalarse en `base`.

2. Si no apunta al ambiente, recrearlo incluyendo Python y pip de forma explícita:

   ```bash
   conda deactivate
   conda env remove -n mediflow_env -y
   conda create -n mediflow_env python=3.11 pip -y
   conda activate mediflow_env
   python -c "import sys; print(sys.executable)"
   ```

3. Si el intérprete mostrado sigue sin apuntar al ambiente, invocar su intérprete por ruta absoluta (`$CONDA_PREFIX` apunta a la carpeta del ambiente activo):

   ```bash
   "$CONDA_PREFIX/bin/python" -m pip install -r requirements.txt
   "$CONDA_PREFIX/bin/python" -m streamlit run Frontend/app_streamlit_backend_directo.py
   ```

4. No utilizar `--break-system-packages`: modifica el Python del sistema y no es necesario si se trabaja dentro de un ambiente que tenga su propio Python.

#### Solución de problemas: `command not found: streamlit` o `ModuleNotFoundError`

Indica que las dependencias no están instaladas en el ambiente activo. Los paquetes se instalan por ambiente (no por carpeta de proyecto), y activar un ambiente no instala nada: un ambiente nuevo comienza vacío. Para comprobarlo:

```bash
python -c "import sys; print(sys.executable)"                                         # debe contener /envs/mediflow_env/
python -m pip list | grep -i -E "streamlit|langgraph|google"
```

Si la lista está vacía, repetir la instalación desde la raíz del repositorio y revisar las últimas líneas de la salida en busca de errores:

```bash
conda install pip -y
python -m pip install -r requirements.txt
```

Para ejecutar la aplicación se recomienda `python -m streamlit run ...`, que garantiza el uso del Python del ambiente activo.

### Ejecución con Docker

```bash
docker compose up --build
```

La aplicación queda disponible en `http://localhost:8501`. Requiere Docker Desktop en ejecución, el archivo `.env` y credenciales de Google Cloud dentro del contenedor (Gemini se ejecuta en Vertex AI); el procedimiento está en [`docs/infraestructura_cloud.md`](docs/infraestructura_cloud.md#desarrollo-local).

### Variables de entorno

| Variable | Descripción |
|---|---|
| `GCP_PROJECT_ID` | ID del proyecto de Google Cloud donde se usa Gemini en Vertex AI (obligatoria) |
| `MODELO_GEMINI` | Modelo de Gemini que utiliza el backend (opcional; por defecto `gemini-2.5-flash`) |
| `EMAIL_USUARIO` | Cuenta de Gmail dedicada al proyecto que envía las alertas por correo |
| `EMAIL_PASSWORD` | Contraseña de aplicación de esa cuenta de Gmail (no la contraseña de acceso) |
| `EMAIL_DESTINO` | Destinatario(s) de las alertas, separados por comas |
| `GCS_BUCKET_RECIBIDOS` | Nombre del bucket de documentos recibidos |
| `GCS_BUCKET_PROCESADOS` | Nombre del bucket de documentos procesados |
| `GCS_BUCKET_AUDITORIA` | Nombre del bucket de auditoría humana |

`GEMINI_API_KEY` ya no se usa: Gemini se autentica con las credenciales de Google Cloud. Las variables de OCI se definirán cuando se implemente el almacenamiento en OCI. En Cloud Run, los valores de correo se leen desde Secret Manager; ver [`docs/infraestructura_cloud.md`](docs/infraestructura_cloud.md#variables-de-entorno).

---

## Funcionamiento del pipeline

### 1. Preparación del entorno

Antes de comenzar el procesamiento, el programa prepara las carpetas y configuraciones necesarias. La estructura utilizada permite separar los documentos originales, los datos clínicos generados, los documentos normales y los documentos que requieren revisión o atención:

```
Almacen_Local/
├── Archivos_Originales/    # archivos originales subidos por el usuario
└── Datos_Clinicos/         # JSON clínicos generados
```

Los resultados quedan organizados automáticamente según la clasificación obtenida.

### 2. Configuración de los niveles de evaluación

El sistema permite configurar los umbrales utilizados por LangGraph. Los valores representan un puntaje de incoherencia: cuántas inconsistencias o problemas se detectan en la información del documento. Por defecto:

| Puntaje | Nivel |
|---|---|
| 0 a 19 | Normal |
| 20 a 39 | Revisión |
| 40 a 59 | Revisión prioritaria |
| 60 a 100 | Alerta |

> Este puntaje no representa la gravedad médica del paciente, no es un diagnóstico y tampoco una probabilidad de enfermedad.

El usuario puede modificar estos valores al iniciar el programa, para adaptar el comportamiento del sistema a las necesidades del proyecto.

### 3. Configuración de reglas

Además de los umbrales, MediFlow permite configurar las reglas utilizadas durante la evaluación. Estas reglas ayudan a determinar si existe una posible inconsistencia entre:

- La categoría identificada.
- La información contenida en el documento.
- Los datos clínicos extraídos.
- Los datos faltantes.
- Los datos ambiguos.
- Las características esperadas para cada tipo de documento.

Por ejemplo, una Receta Médica debe contener determinada información propia de una receta; si el contenido extraído no coincide con lo esperado para esa categoría, el sistema aumenta el puntaje de incoherencia.

### 4. Selección del archivo

Desde la interfaz web, el usuario carga el documento que desea procesar. En modo terminal (`Backend_MediFlow/main.py`), el usuario selecciona el documento introduciendo la ruta manualmente o arrastrando el archivo sobre la terminal; el programa limpia la ruta recibida y valida que el archivo exista.

Tipos de archivo admitidos: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.webp`, `.pdf` y `.json`.

### 5. Validación del archivo

Antes de comenzar el procesamiento, MediFlow comprueba que el archivo tenga una extensión permitida. Esto evita procesar formatos que el sistema no contempla; si la extensión no es válida, el programa detiene el procesamiento y solicita un archivo compatible.

### 6. Conservación del documento original

El archivo original se conserva sin modificarse. Antes de comenzar el análisis, MediFlow realiza una copia del documento en `Almacen_Local/Archivos_Originales/` con un nombre controlado, para evitar problemas con archivos del mismo nombre. El nombre incorpora fecha, hora y nombre original, y mantiene una referencia del documento utilizado para generar la información clínica.

### 7. Identificación del tipo de archivo

MediFlow identifica el tipo de documento por su extensión para indicarle a Gemini cómo debe interpretarlo:

| Extensión | Tipo MIME enviado |
|---|---|
| `.pdf` | `application/pdf` |
| `.png` | `image/png` |
| `.jpg`, `.jpeg` | `image/jpeg` |
| `.webp` | `image/webp` |
| `.json`, `.bmp`, `.tiff` | `application/octet-stream` |

### 8. Envío del documento a Gemini

Una vez validado el archivo, MediFlow utiliza Gemini en Vertex AI como modelo multimodal para analizarlo. El archivo se lee como bytes y se envía dentro de la misma solicitud, junto con las instrucciones (prompt); no se sube antes a ningún servicio. Esto permite trabajar con información clínica en diferentes formatos: texto, imágenes, PDF e información estructurada. Si Gemini responde con un error temporal 503, MediFlow reintenta hasta tres veces, con una espera creciente entre intentos. El objetivo de esta etapa no es realizar un diagnóstico médico, sino extraer y estructurar la información que aparece en el documento subido por el usuario.

### 9. Extracción de información clínica

Gemini transforma la información encontrada en el documento en un objeto estructurado. Identifica, por ejemplo: paciente, médico, institución, fecha, tipo de documento, medicamentos, tratamientos, indicaciones, estudios y procedimientos. La información se organiza en JSON estructurado para ser procesada automáticamente por LangGraph. El esquema de la salida está descrito en [`docs/contrato_datos.md`](docs/contrato_datos.md).

### 10. Regla importante: no inventar información

El sistema está diseñado para que Gemini no complete información que no aparezca en el documento. Cuando un dato no está disponible se mantiene como `null` o, en el caso de listas, como `[]`. Esto permite distinguir entre *dato encontrado* y *dato no disponible*, y que un dato faltante pueda ser identificado posteriormente por LangGraph.

### 11. Clasificación del documento

Después de obtener el JSON generado por Gemini, el flujo pasa a LangGraph, que identifica la categoría del documento. Las categorías utilizadas son:

- Receta Médica
- Informe de Estudio de Diagnóstico por Imágenes/Laboratorio
- Orden de Solicitud de Procedimiento
- Epicrisis / Informe de Alta
- Certificado Médico
- Otro

### 12. Evaluación del documento

LangGraph analiza diferentes señales que pueden indicar que el documento necesita revisión: información urgente, información ambigua, datos faltantes, información que no coincide y problemas de coherencia del documento.

> Estas señales no representan un diagnóstico médico; su función es identificar documentos que pueden requerir una revisión adicional.

### 13. Validación de coherencia

El sistema utiliza las reglas configuradas para comprobar si la información encontrada tiene sentido con respecto al tipo de documento identificado. Por ejemplo, si el documento se identificó como Receta Médica pero la información encontrada no corresponde claramente a una receta, el resultado es una posible inconsistencia. Esto evita depender únicamente de la clasificación inicial realizada por Gemini.

### 14. Puntaje de incoherencia

A partir de las reglas y condiciones detectadas se obtiene un puntaje entre 0 y 100 que representa el nivel de incoherencia detectado en el documento. Un puntaje de 5 indica pocas inconsistencias; un puntaje de 75 indica más elementos que requieren atención.

> No representa gravedad médica, diagnóstico, riesgo de muerte ni probabilidad de enfermedad. Es exclusivamente un indicador del flujo de trabajo para decidir qué nivel de revisión requiere el documento.

### 15. Validación clínica determinística

Una capa adicional, sin llamadas a ninguna API, revisa con reglas y catálogos de referencia lo que Gemini extrajo: fechas, códigos CIE-10, medicamentos y dosis, valores críticos de laboratorio, formato de la matrícula profesional y documentos de doble propósito. Un valor crítico de laboratorio clasifica el documento como `urgente` aunque Gemini no lo haya indicado; conflictos críticos o un puntaje clínico alto lo clasifican como `revision_clinica`. Es código determinista y auditable.

### 16. Clasificación final

Con el puntaje obtenido, la validación clínica y los umbrales configurados, LangGraph determina la clasificación final, con la siguiente prioridad:

```
urgente > ambiguo > datos_faltantes > revision_clinica > alerta > revision_prioritaria > revision > normal
```

Esto permite que el sistema organice automáticamente los documentos. Toda clasificación distinta de `normal` requiere revisión humana.

### 17. Organización automática del JSON

Una vez terminada la evaluación, MediFlow genera el JSON clínico final. Dependiendo del resultado, el archivo se guarda automáticamente en una estructura como:

- `Datos_Clinicos/Normal/Receta_Medica/documento.json`
- `Datos_Clinicos/Alertas/Alerta/Receta_Medica/documento.json`

La ubicación del archivo refleja tanto la clasificación obtenida como el tipo de documento.

### 18. Sincronización con la nube

Además del almacenamiento local, desde la interfaz web el archivo original se sube al bucket `recibidos` de Google Cloud Storage y el JSON final al bucket `procesados` (clasificación `normal`) o `auditoria-humana` (cualquier otra clasificación). Si la sincronización falla, el error se registra en el log y el procesamiento continúa con el almacenamiento local. La sincronización con OCI Object Storage (Always Free) está planificada y aún no está implementada. Detalle en [`docs/infraestructura_cloud.md`](docs/infraestructura_cloud.md).

### 19. Resumen final para el usuario

Después de guardar el JSON, MediFlow muestra un resumen del procesamiento: categoría del documento, clasificación final, puntaje de incoherencia, nivel de coherencia, reglas utilizadas, información de riesgo detectada, datos faltantes, datos ambiguos, motivos de la clasificación y ruta donde se guardó el JSON. También se muestran todos los niveles de evaluación configurados, para que el usuario pueda entender por qué el sistema clasificó el documento de determinada manera, en lugar de recibir únicamente un resultado.

### 20. Decisión del usuario sobre el JSON clínico final

Una vez terminado el procesamiento, el usuario puede decidir qué hacer con el JSON generado:

1. **Conservar** el JSON en la ubicación indicada: permanece dentro de la estructura creada automáticamente por MediFlow.
2. **Mover** el JSON a otra ubicación: el usuario introduce otra ruta; MediFlow crea la carpeta de destino si es necesario y mueve el JSON.
3. **Eliminar** el JSON generado: el archivo original permanece conservado en `Almacen_Local/Archivos_Originales/`, por lo que eliminar el JSON no elimina el documento original utilizado para el procesamiento.

Estas acciones se aplican a la copia local; la copia sincronizada en Cloud Storage no se modifica.

### 21. Envío de correo (alertas)

Cuando el sistema detecta que el archivo requiere revisión humana, MediFlow envía un correo a la(s) persona(s) encargada(s), con: nombre del paciente, nombre del médico, tipo de documento, clasificación del documento, motivos por los cuales requiere revisión y ruta donde se guardó el documento generado. De esta forma alerta al personal responsable sobre las inconsistencias del archivo y señala los puntos clave para su revisión.

El correo se envía desde una cuenta de Gmail dedicada al proyecto (`EMAIL_USUARIO`, con su contraseña de aplicación `EMAIL_PASSWORD`) a los destinatarios de `EMAIL_DESTINO`. En Cloud Run esos tres valores se leen desde Secret Manager. La lista de destinatarios que se edita desde la interfaz se guarda en el disco local, que en Cloud Run no es persistente: el valor permanente es `EMAIL_DESTINO`. Detalle en [`docs/infraestructura_cloud.md`](docs/infraestructura_cloud.md#correos-de-las-alertas).

---

## Casos de prueba

La carpeta `casos/` contiene 100 documentos de prueba sintéticos en `casos/documents/` (65 PDF, 25 imágenes y 10 JSON), nombrados `DOC-001` a `DOC-100`. En `casos/referencia/` se encuentran los datos de referencia: `ground_truth.jsonl`, `manifest.csv` y los catálogos de la validación clínica (`catalogos/`).

## Tecnologías utilizadas

| Tecnología | Uso |
|---|---|
| Python 3.11 | Lenguaje principal; controla todo el flujo de procesamiento |
| Gemini (`google-genai`) en Vertex AI | Análisis multimodal del documento y extracción de información clínica estructurada |
| LangGraph | Organiza el flujo de evaluación y clasificación en nodos |
| Streamlit | Interfaz web |
| Google Cloud Run | Despliegue del contenedor |
| Google Cloud Storage | Almacenamiento persistente de documentos y resultados |
| Google Secret Manager | Correos y contraseña de las alertas en producción |
| OCI Object Storage (Always Free) | Almacenamiento adicional (planificado) |
| Docker / Docker Compose | Empaquetado y ejecución local del servicio |
| JSON | Formato estructurado de los datos clínicos |
| python-dotenv | Carga de variables de configuración desde `.env` (por ejemplo, el proyecto de Google Cloud y los correos) |
| `os`, `shutil`, `pathlib`, `datetime`, `json` | Administración de archivos, carpetas, rutas, fechas, copias y JSON |

## Estructura del repositorio

```
G10-LATAM-EQUIPO50-MediFlow/
├── README.md
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── Backend_MediFlow/
│   ├── README_Backend.md
│   ├── main.py                    # ejecución en modo terminal
│   ├── configuracion.py
│   ├── umbrales.py
│   ├── reglas.py
│   ├── archivos.py
│   ├── gemini.py
│   ├── langgraph_mediflow.py      # grafo de decisión
│   ├── validacion_clinica.py      # validación clínica determinística
│   ├── almacenamiento.py
│   ├── resultados.py
│   └── correo.py
├── Frontend/
│   └── app_streamlit_backend_directo.py
├── Frontend_Respaldo/             # versión anterior (FastAPI + Streamlit), sin uso activo
├── cloud/
│   ├── gcloud_storage.py
│   └── sincronizar_almacenamiento.py
├── casos/                         # documentos de prueba y datos de referencia
└── docs/
    ├── arquitectura.md
    ├── contrato_datos.md
    ├── infraestructura_cloud.md
    └── cambios_produccion.md
```

## Licencia

Proyecto académico — Hackathon ONE G10 Equipo50, Oracle Next Education & Alura.