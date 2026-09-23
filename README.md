# G10-LATAM-EQUIPO50-MediFlow:

Agente Autónomo para Triaje, Extracción y Enrutamiento de Documentos Clínicos

# Sector Empresarial: HealthTech / Gestión Hospitalaria / Aseguradoras de Salud & Clínicas Médicas.
# Hackathon ONE G10 — Oracle Next Education & Alura

--

# Descripción del Proyecto 2: 🏥 MediFlow

MediFlow; Debe resolver desafíos complejos de visión multimodal, extracción estructurada de datos clínicos,
lógica de decisión condicional y manejo de casos ambiguos o urgentes (como datos ilegibles,
prescripciones de alto riesgo o solicitudes de urgencia).

El objetivo del proyecto es diseñar, construir e implementar un agente de inteligencia artificial autónomo, especializado en la automatización del flujo de trabajo documental para entornos de salud.
El desarrollo técnico y funcional de este sistema comprende las siguientes fases básicas detalladas:

--

## Etapas del proyecto:

- **Módulo de Recepción y Procesamiento MultiFormato:** el sistema procesa archivos PDF, imágenes (recetas manuscritas, órdenes de laboratorio, estudios diagnósticos) y documentos JSON ya estructurados — ver [formatos de entrada aceptados](docs/contrato-datos.md#formatos-de-entrada-aceptados).

- **Motor de Clasificación Automatizada de Documentos:** el sistema clasifica cada documento en dos dimensiones — **Tipo de Documento** (Clínico / Receta / Otro) y **Situación** (Normal / Urgente / Ambiguo) — y asigna el destino correspondiente. Ver [`docs/contrato_datos.md`](docs/contrato_datos.md).

- **Componente de Extracción de Entidades y Datos Clínicos:** Gemini lee el documento directamente (PDF, imagen o JSON) y extrae los datos del paciente (nombre, diagnósticos, medicamentos, dosis, fechas) y del médico (nombre, matrícula, especialidad).

- **Flujo de Enrutamiento Inteligente:** LangGraph orquesta la clasificación y decide el enrutamiento; los casos Urgente o Ambiguo disparan una alerta por correo (`envio_correo.py`) y quedan marcados para revisión humana.

- **Despliegue en OCI:** proyecto desplegado en una instancia OCI Compute (Ampere A1, Always Free), para demostración y uso público. Detalle en [`docs/infraestructura_cloud.md`](docs/infraestructura_cloud.md).

## Estado actual del proyecto
 
| Área | Decisión |
|---|---|
| Lenguaje / orquestación | Python puro + LangGraph |
| Extracción / clasificación | Gemini (multimodal — lee PDF/imagen/JSON directo) |
| Despliegue | OCI Compute, Ampere A1 Always Free |
| Almacenamiento | OCI Object Storage — buckets `recibidos` / `procesados` / `auditoria_humana` |
| Notificaciones | Correo (SMTP/Gmail) en casos Urgente/Ambiguo |
| Gestión de tareas | Trello |
| Framework de interfaz | Por definir — Streamlit vs. FastAPI |
 
> **Cambio de arquitectura (semana 1):** el plan original usaba Qwen2.5 + mDeBERTa corriendo en máquina virtual vía PyTorch/Transformers. El equipo confirmó el cambio a Gemini + LangGraph para reducir el riesgo de latencia en la CPU limitada de OCI Always Free y simplificar el pipeline (ya no hace falta OCR aparte). Historial completo en [`docs/arquitectura.md`](docs/arquitectura.md).
 
## Equipo

| Integrante | Rol |
|---|---|
| José Moya | Backend, arquitectura y orquestación |
| Anahí Ramírez| LLM & ML, grafo de decisión, puntaje de confianza y orquestación|
| Andrés Mustafá | Cloud & Infraestructura (OCI); contrato de datos, tablero de Trello y documentación/arquitectura |
| Juan Pablo Palacio | Ingesta de documentos, Casos de prueba |
| Jonatan Cuero | Interfaz |
 
## Arquitectura
 
Gemini lee el documento (PDF/imagen/JSON) y extrae la información; LangGraph clasifica por Tipo de Documento y Situación, y decide el enrutamiento — incluyendo la alerta por correo en casos Urgente/Ambiguo. Diagrama completo en [`docs/arquitectura.md`](docs/arquitectura.md).
 
## Cloud & Infraestructura (OCI)
 
Cuenta Always Free existente, compartment dedicado, 3 buckets segregados por estado, acceso del equipo vía IAM, y despliegue en Compute con VCN mínima. Detalle completo, en [`docs/infraestructura-cloud.md`](docs/infraestructura-cloud.md).
 
## Contrato de datos
 
Formatos de entrada aceptados (PDF / Imagen / JSON, con ejemplo real) y el JSON de salida estructurado. Detalle completo en [`docs/contrato-datos.md`](docs/contrato-datos.md).
 
## Flujo de trabajo del equipo
 
- **Reunión obligatoria:** lunes y jueves
- **Reunión diaria (daily):** martes, miércoles y viernes
- **Gestión de tareas:** Trello
- **Commits:** prefijo por tipo — `feat:`, `fix:`, `docs:`, `test:`

## Instrucciones de ejecución
 
> TODO — completar cuando el backend esté armado.
 
```bash
# Clonar el repo
git clone <url-del-repo>
cd mediflow
 
# Entorno local (conda)
conda create --name mediflow_env python=3.11.13 -y
conda activate mediflow_env
pip install -r requirements.txt
 
# Entorno de despliegue en la instancia OCI (venv)
# python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
 
cp .env.example .env    # completar OCI, GEMINI_API_KEY y credenciales de correo
```
 
Ya no hace falta instalar Tesseract ni Poppler en el servidor — Gemini lee PDF/imagen directamente, sin OCR local.
 
### Variables de entorno necesarias
 
| Variable | Descripción |
|---|---|
| `OCI_CONFIG_FILE` | Ruta al config file de OCI (`~/.oci/config`) |
| `OCI_BUCKET_RECIBIDOS` | Nombre del bucket de documentos recibidos |
| `OCI_BUCKET_PROCESADOS` | Nombre del bucket de documentos procesados |
| `OCI_BUCKET_AUDITORIA` | Nombre del bucket de la cola de auditoría humana |
| `GEMINI_API_KEY` | API key de Gemini (Google AI Studio) |
| `Email_Usuario` / `Email_Password` / `Email_Destino` | Credenciales de la cuenta que envía las alertas por correo (`envio_correo.py`) |
 
## Casos de prueba
 
**100 documentos de prueba ya están en `casos/`** (65 PDF, 25 imagen, 10 JSON) — nombrados `DOC-001` a `DOC-100`. Es la base de pruebas real del equipo; los 5 casos sintéticos originales (rutina/urgencia/ambigüedad) siguen sirviendo como referencia rápida en `tests/casos/`.
 
## Estructura del repositorio
 
```
G10-LATAM-EQUIPO50-MediFlow/
├── README.md
├── requirements.txt
├── .env
├── app.py                    # interfaz (Streamlit/FastAPI)
├── agent/
│   ├── ingesta_archivos.py
│   ├── extraccion.py          # llamada a Gemini
│   └── grafo_decision.py      # LangGraph — Tipo de Documento / Situación
├── cloud/
│   └── oci_storage.py         # wrapper de subida/movimiento de objetos
├── envio_correo.py            # alertas por correo (Urgente/Ambiguo)
├── casos/                 # 100 casos de prueba (PDF/imagen/JSON)
└── docs/
    ├── arquitectura.md
    ├── contrato-datos.md
    └── infraestructura-cloud.md
```
 
## Licencia
 
Proyecto académico — Hackathon ONE G10, Oracle Next Education & Alura.
# Configuración del Entorno de Desarrollo

Este proyecto requiere un ambiente virtual aislado para gestionar sus dependencias de forma segura y evitar conflictos entre librerías. Se recomienda el uso de **Anaconda** (o **Miniconda**) para la administración del entorno.

---

## 📌 Requisitos Previos

1. Tener **Git** instalado.
2. Descargar e instalar **Anaconda Distribution** (o **Miniconda** si prefieres una versión más ligera):
   - 📥 [Descargar Anaconda](https://www.anaconda.com/download)
   - 📥 [Descargar Miniconda](https://docs.conda.io/en/latest/miniconda.html)

---

## 🚀 Pasos para Configurar el Ambiente Virtual

Abre tu terminal (o **Anaconda Prompt** en Windows) y ejecuta los siguientes comandos:

### 1. Crear el ambiente virtual
Crea un ambiente de Conda especificando la versión de Python recomendada para este proyecto:

```bash
conda create --name mi_proyecto_env python=3.11.13 -y 

Nota: Puedes cambiar mi_proyecto_env por el nombre que prefieras para tu entorno.
