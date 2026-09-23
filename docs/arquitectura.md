# Arquitectura — MediFlow

## Diagrama

```mermaid
flowchart TD
    A["Archivos\nPDF / Imagen / JSON"] --> B["Gemini (multimodal)\nlee el documento directo"]
    B --> C["Información del documento"]
    C --> D["LangGraph"]
    D --> E["Tipo de Documento"]
    D --> F["Situación"]
    E --> E1["Receta"]
    E --> E2["OrdenProcedimiento"]
    E --> E3["InformeEstudio"]
    E --> E4["Incapacidad"]
    E --> E5["Otro"]
    F --> F1["Normal"]
    F --> F2["Urgente"]
    F --> F3["Ambiguo"]
    E1 --> G["Archivo Estructurado JSON"]
    E2 --> G
    E3 --> G
    E4 --> G
    E5 --> G
    F1 --> G
    F2 --> G
    F3 --> G
    G --> H["Interfaz"]
    G --> I["OCI Object Storage"]
    F2 --> J["Alerta por correo\n(envio_correo.py)"]
    F3 --> J
```

## Componentes
 
| Componente | Función | Tecnología |
|---|---|---|
| Ingesta | Recibe el archivo (PDF, imagen o JSON) | ingesta_archivos.py |
| Extracción | Lee el documento directo (multimodal) y devuelve la información estructurada | Gemini |
| Orquestación | Clasifica por dos dimensiones y decide el enrutamiento | LangGraph |
| Notificación | Alerta por correo en casos Urgente/Ambiguo | `envio_correo.py` (smtplib + Gmail) |
| Almacenamiento | Guarda los archivos | ingesta_archivos.py y OCI Object Storage |
| Persistencia | Guarda el JSON final | OCI Object Storage |
| Interfaz | Muestra el resultado / panel HITL | Por definir (Streamlit/FastAPI) |
 
## Las dos dimensiones de clasificación
 
- **Tipo de Documento**: `Receta` / `OrdenProcedimiento` / `InformeEstudio` / `Incapacidad` / `Otro`
- **Situación**: `Normal` / `Urgente` / `Ambiguo`
Un documento queda descrito por la combinación de ambas — por ejemplo, una Receta en situación Normal se enruta distinto a un InformeEstudio en situación Urgente.

