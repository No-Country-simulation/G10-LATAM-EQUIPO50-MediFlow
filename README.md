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
 
Cuenta Always Free existente, compartment dedicado, 3 buckets segregados por estado, acceso del equipo vía IAM, y despliegue en Compute con VCN mínima. Detalle completo, en [`docs/infraestructura_cloud.md`](docs/infraestructura_cloud.md).
 
## Contrato de datos
 
Formatos de entrada aceptados (PDF / Imagen / JSON, con ejemplo real) y el JSON de salida estructurado. Detalle completo en [`docs/contrato-datos.md`](docs/contrato-datos.md).
 
## Flujo de trabajo del equipo
 
- **Reunión obligatoria:** lunes y jueves
- **Reunión diaria (daily):** martes, miércoles y viernes
- **Gestión de tareas:** Trello https://trello.com/invite/b/6aacb00e8ac49dd1ff659f13/ATTI57ded9186f44107980c9f4c455e4bef3E2FDC5AF/g10-latam-equipo50-mediflow
- **Commits:** prefijo por tipo — `feat:`, `fix:`, `docs:`, `test:`

### Estructura del tablero de Trello
 
- **Listas:** `Listos para iniciar` → `En desarrollo` → `Pausado` → `Concluido`
- **Etiquetas por área:** `Cloud`, `Arquitectura/Agente`, `Backend`, `Interfaz`, `Docs`. 
- **Convención de tarjetas:** una tarjeta por tarea concreta, no por persona ni por día — así se puede ver de un vistazo qué está bloqueado y por qué.

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
 
**100 documentos de prueba ya están en `casos/`** (65 PDF, 25 imagen, 10 JSON) — nombrados `DOC-001` a `DOC-100`.
 
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

```
conda create --name mi_proyecto_env python=3.11.13 -y 

Nota: Puedes cambiar mi_proyecto_env por el nombre que prefieras para tu entorno.

## Licencia
 
Proyecto académico — Hackathon ONE G10 Equipo50, Oracle Next Education & Alura.
# Configuración del Entorno de Desarrollo

------
### 2. Preparación de Entorno:

Antes de comenzar el procesamiento, el programa prepara las carpetas y configuraciones necesarias.

La estructura utilizada por MediFlow permite separar:

1. Los documentos originales.
2. Los datos clínicos generados.
3. Los documentos normales.
4. Los documentos que requieren revisión o atención.

La estructura general puede quedar de esta manera:

Almacen_Local:
* Carpeta Archivos_Originales: Aquí se guardan los archivos originales subidos por el usuario.
* Carpeta Datos_Clínicos: Aquí se guardan los JSON clínicos generados.

Esto permite que los resultados queden organizados automáticamente dependiendo de la clasificación obtenida.
---
### 3. Configuración de los Niveles de Evaluación:

El sistema permite configurar los valores de los umbrales utilizados por LangGraph,
Los valores representan un puntaje de incoherencia, es decir,
qué tantas inconsistencias o problemas detectados existen en la información del documento.

Por defecto, el sistema puede trabajar con los siguientes rangos:

*  0 a 19     Normal.
* 20 a 39     Revisión.
* 40 a 59     Revisión prioritaria.
* 50 a 100    Alerta.

*Nota: Es importante saber que este puntaje no representa la gravedad médica del paciente, no es un diagnóstico y tampoco representa una probabilidad de enfermedad.*

El usuario puede modificar estos valores al iniciar el programa;
Esto permite adaptar el comportamiento del sistema dependiendo de las necesidades del proyecto.

----

---
### 4. Configuración de Reglas:

Además de los umbrales, MediFlow permite configurar las reglas utilizadas durante la evaluación.

Estas reglas ayudan a determinar si existe una posible inconsistencia entre:

* La categoría identificada.
* La información contenida en el documento.
* Los datos clínicos extraídos.
* Los datos faltantes.
* Los datos ambiguos.
* Las características esperadas para cada tipo de documento.

Por ejemplo, una Receta Médica debería contener determinada información propia de una receta;
Si el contenido extraído no coincide con lo esperado para esa categoría, el sistema puede aumentar el puntaje de incoherencia.

---

---
### 5. Selección de Archivo:

El usuario selecciona desde la terminal el documento que desea procesar,
El programa permite trabajar con diferentes tipos de archivos, entre ellos:

* .jpg
* .png
* .jpeg
* .bmp
* .webb
* .pdf
* .json

El usuario puede introducir la ruta manualmente o utilizar una ruta obtenida mediante arrastrar y soltar el archivo sobre la terminal;
Después el programa limpia la ruta recibida y valida que el archivo exista.
---

---
### 6. Validación de Archivo:

Antes de comenzar el procesamiento, MediFlow comprueba que el archivo tenga una extensión permitida;
Esto evita intentar procesar formatos que el sistema no contempla;
Si el archivo no tiene una extensión válida, el programa detiene el procesamiento y solicita un archivo compatible.

---

---
### 7. Conservación del Documento Original:

Una de las características importantes del flujo es que el archivo original se conserva sin modificarse;
Antes de comenzar el análisis, MediFlow realiza una copia del documento dentro de:

*Almacen_Local/Archivos_Originales/*

Además, el sistema genera un nombre controlado para evitar problemas con archivos que tengan el mismo nombre;

El nombre se incorpora con la información siguiente:

* Fecha
* Hora
* Nombre original

La finalidad es mantener una referencia del documento original utilizado para generar la información clínica.
---

---
### 8. Identificación de Tipo de Archivo:

MediFlow identifica el tipo de documento para determinar cómo debe ser enviado a Gemini,
Por ejemplo:

* PDF application/pdf
* PNG  -> image/png
* JPEG -> image/jpeg
* JSON -> application/json

Esta información permite que Gemini reciba correctamente el archivo.
---

---
### 9. Envio del Documento a Gemini:

Una vez validado el archivo, MediFlow utiliza Gemini como modelo multimodal para analizar el documento;
Gemini recibe el archivo directamente y analiza su contenido;
Esto permite trabajar con documentos que pueden contener información clínica en diferentes formatos, como:

* Texto.
* Imágenes.
* PDFs.
* Información estructurada.

El objetivo de esta etapa no es realizar un diagnóstico médico;
Su función es extraer y estructurar la información que aparece en el documento subido por el usuario.
---

---
### 10. Extracción de información Clínica:

Gemini transforma la información encontrada en el documento en un objeto estructurado;
Por ejemplo, puede identificar información relacionada con:

* Paciente
* Médico
* Institución
* Fecha
* Tipo de documento
* Medicamentos
* Tratamientos
* Indicaciones
* Estudios
* Procedimientos

La información se organiza en formato JSON estructurado para que posteriormente pueda ser procesada automáticamente por LangGraph.
---

---
### 11. Regla IMPORTANTE: No inventar Información

El sistema está diseñado para que Gemini no complete información que no aparezca en el documento.
Cuando un dato no está disponible, debe mantenerse como:

* Null

o cuando se trata de una lista:

* []

Esto es importante porque el sistema trabaja con información clínica y debe distinguir entre: Dato encontrado y Dato NO disponible;
De esta manera, un dato faltante puede ser identificado posteriormente por LangGraph.
---

---
### 12. Clasificación del Documento:

Después de obtener el JSON generado por Gemini, el flujo pasa a LangGraph;
Una de sus responsabilidades es identificar la categoría que se encuentra en el documento.
Las categorías utilizadas por el sistema son:

* Receta Médica
* Informe de Estudio de Diagnóstico por Imágenes/Laboratorio
* Orden de Solicitud de Procedimiento
* Epicrisis / Informe de Alta
* Certificado Médico
* Otro

Esta clasificación permite organizar automáticamente los documentos.
---

---
### 13. Evaluación del Documento:

LangGraph también participa en la evaluación del documento;
El sistema analiza diferentes señales que pueden indicar que el documento necesita revisión;
Entre ellas pueden encontrarse:

* Información urgente
* Información ambigua
* Datos faltantes
* Información que no coincide
* Problemas de coherencia del documento

*Nota: Estas señales no representan un diagnóstico médico; Su función es identificar documentos que pueden requerir una revisión adicional.*
---

---
### 14. Validación de Coherencia:

Una de las partes importantes del flujo es la validación de coherencia entre el documento y su categoría;
El sistema utiliza las reglas configuradas para comprobar si la información encontrada tiene sentido con respecto al tipo de documento identificado.
Por ejemplo:

* Documento identificado:
  Receta Médica

* Información encontrada:
  Datos que no corresponden
  claramente a una receta

* Resultado:
  Posible inconsistencia

Esto evita depender únicamente de la clasificación inicial realizada por Gemini.
---


---
### 15. Puntaje de incoherencia:

A partir de las reglas y condiciones detectadas se obtiene un puntaje de rango entre: 0 a 100.

Este valor representa el nivel de incoherencia detectado en el documento.
Por ejemplo:

* Puntaje igual a 5:
  Significa que se encontraron pocas inconsistencias en el documento.

* Puntaje igual a 75:
  indica que se detectaron más elementos que requieren atención.

*Nota: NO representa gravedad médica, diagnóstico, riesgo de muerte ni probabilidad de enfermedad.*

Es exclusivamente un indicador utilizado por el flujo de trabajo, para decidir qué nivel de revisión requiere el documento.
---

---
### 16. Clasificación Final:
Con el puntaje obtenido y los umbrales configurados, LangGraph determina una clasificación final;
Por ejemplo:

* Normal.
* Revisión.
* Revisión Prioritaria.
* Alerta

Esto permite que el sistema organice automáticamente los documentos.
---

---
### 17. Organización Automatica del JSON:
Una vez terminada la evaluación, MediFlow genera el JSON clínico final;
Dependiendo del resultado, el archivo se guarda automáticamente en una estructura como:

* Datos_Clinicos/Normal/Receta_Medica/documento.json
o
* Datos_Clinicos/Alertas/Alerta/Receta_Medica/documento.json

De esta forma, la ubicación del archivo refleja tanto:

* La clasificación obtenida.
* El tipo de documento.
---

---
### 18. Resumen Final para el Usuario:

Después de guardar el JSON, MediFlow muestra un resumen del procesamiento;
El usuario puede conocer:

* Categoría del documento
* Clasificación final
* Puntaje de incoherencia
* Nivel de coherencia
* Reglas utilizadas
* Información de riesgo detectada
* Datos faltantes
* Datos ambiguos
* Motivos de la clasificación
* Ruta donde se guardó el JSON

También se muestran todos los niveles de evaluación configurados;
Esto permite que el usuario pueda entender por qué el sistema clasificó el documento de determinada manera, 
en lugar de recibir únicamente un resultado.
---

---
### 19. Decisión del Usuario sobre el JSON clínico final generado:

Una vez terminado el procesamiento, el usuario puede decidir qué hacer con el JSON generado;
MediFlow ofrece tres opciones:

1. Mantener el JSON en la ubicación indicada
2. Guardar el JSON en otra ubicación
3. Eliminar el JSON generado

Opción 1: Mantener
El JSON permanece dentro de la estructura creada automáticamente por MediFlow.

Opción 2: Guardar en otra ubicación
El usuario puede introducir otra ruta;
MediFlow puede crear la carpeta de destino si es necesario y mover el JSON hacia esa ubicación.

Opción 3: Eliminar
El usuario puede eliminar el JSON final si considera que no desea conservarlo.
El archivo original permanece conservado en:

*Almacen_Local/Archivos_Originales/*

Por lo tanto, eliminar el JSON generado no elimina el documento original utilizado para el procesamiento.
---

---
### 20. Envio de Correo (Alertas):

MediFlow tiene la capacidad de mandar un correo a la(s) persona(s) encargada(s),
en caso que el sistema detecte que el archivo subido requiere revisión humanada.
Manda un mensaje que contiene los siguientes puntos:

* Nombre del Paciente.
* Nombre del Médico.
* Tipo de documento.
* Clasificación del documento.
* Motivos por los cuales requiere revisión por una persona encargada del área.
* Muestra la ruta donde se guardo el documento generado.

De esta forma alerta al personal responsable que hay inconsistencias en el archivo, 
marcando puntos estrategicos para llevar a cabo su revisión.
---

----
### 21. Tecnologias Usadas:

El prototipo utiliza principalmente las siguientes herramientas:

* Python: Se utiliza como lenguaje principal para controlar todo el flujo de procesamiento.

* Gemini: Se utiliza para el análisis multimodal del documento y la extracción de información clínica estructurada.

* LangGraph: Se utiliza para organizar el flujo de evaluación y clasificación mediante diferentes etapas o nodos.

* JSON: Se utiliza como formato estructurado para almacenar los datos clínicos obtenidos.

* python-dotenv: Permite cargar de manera segura variables de configuración desde el archivo: .env;
Por ejemplo, la clave utilizada para acceder a Gemini.

También se utlizan:
Para Sistema de archivos de Python;

las Bibliotecas como:
* os
* shutil
* pathlib
* datetime
* json

Que Permiten administrar:

1. Archivos.
2. Carpetas.
3. Rutas.
4. Fechas.
5. Copias.
6. JSON.
---
