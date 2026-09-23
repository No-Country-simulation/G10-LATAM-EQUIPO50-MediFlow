# Contrato de datos — MediFlow

## Formatos de entrada aceptados
 
| Formato | Transferencia | Procesamiento |
|---|---|---|
| PDF | Archivo binario | Lectura directa mediante Gemini  |
| Imagen | Archivo binario | Lectura directa mediante Gemini |
| JSON | Payload con el documento ya estructurado por el sistema de origen | Procesamiento por Gemini/LangGraph como un PDF/imagen ya leído |

### Ejemplo real de entrada en formato JSON
 
Tomado de `casos/` (carpeta con 100 casos de prueba ya en el repo — PDF, imagen y JSON):
 
```json
{
  "sistema_origen": "HIS-SALUD",
  "fecha_documento": "2026-09-18",
  "paciente": {
    "nombre_completo": "Eduardo Mendoza Moreno",
    "identificacion": { "tipo": "CC", "numero": "583498908" },
    "fecha_nacimiento": "2002-06-12",
    "sexo": "M",
    "cobertura": "Particular"
  },
  "profesional": {
    "nombre": "Dr. Javier Navarro Silva",
    "registro": "RM 73532-16",
    "especialidad": "Endocrinología"
  },
  "contenido_texto": "RECETA MÉDICA\nDiagnóstico: Diabetes mellitus no insulinodependiente sin mención de complicación   CIE-10: E11.9\n1. Metformina 850 mg - tableta\n    Tomar 1 tableta cada 12 horas por 30 días.   Cantidad total: 60\nIndicaciones: Control en 15 días."
}
```

## 5 tipos de documento reales identificados (base para la taxonomía)
 
El equipo aportó ejemplos reales (fotografiados) de 5 documentos que emite el sistema de salud colombiano. Cada uno tiene una estructura de campos consistente y reconocible:
 
| Tipo real | Campos característicos |
|---|---|
| **Incapacidad** | Días de incapacidad, fecha inicial/final, diagnóstico principal y relacionado (CIE-10), tipo de incapacidad, prórroga, retroactiva |
| **Orden de Procedimientos** | Tabla de ítems: código, descripción, cantidad, bilateral, código SISPRO |
| **Fórmula / Receta** | Diagnóstico(s) CIE-10, tabla de medicamentos: prescripción, cantidad total, código MIPRES, entregas |
| **Informe de Estudio (Imágenes)** | Nombre del estudio, datos clínicos, técnica, reporte (hallazgos), opinión |
| **Resultado de Laboratorio** | Exámenes por categoría (química, hematología...), resultado, unidad, valor de referencia, método, fecha de validación |
 
## Salida — JSON estructurado
 
### Envolvente común (todos los tipos de documento)
 
```json
{
  "documento_id": "string",
  "fecha_procesamiento": "datetime ISO 8601",
  "formato_origen": "PDF | IMAGEN | JSON",
  "clasificacion": {
    "tipo_documento": "Receta | OrdenProcedimiento | InformeEstudio | Incapacidad | Otro",
    "situacion": "Normal | Urgente | Ambiguo",
    "puntaje_confianza": "float 0-1",
    "motivo_alerta": "string | null"
  },
  "institucion": {
    "nombre": "string",
    "nit": "string | null",
    "direccion": "string | null",
    "codigo_reps": "string | null"
  },
  "paciente": {
    "nombre_completo": "string",
    "identificacion": { "tipo": "string", "numero": "string" },
    "fecha_nacimiento": "string | null",
    "entidad_afiliacion": "string | null",
    "acompanante_responsable": {
      "nombre": "string | null",
      "parentesco": "string | null"
    }
  },
  "profesional": {
    "nombre": "string | null",
    "registro": "string | null",
    "especialidad": "string | null"
  },
  "detalle": {},
  "notificacion": { "enviada": "boolean", "destinatario": "string | null" },
  "almacenamiento_oci": { "bucket": "string", "ruta_objeto": "string" }
}
```
  
### `detalle` según `tipo_documento`
 
El contenido de `detalle` cambia según el tipo — cada uno modela lo que ese documento real de verdad trae:
 
**Receta:**
```json
{ "diagnosticos": ["E11.9"], "medicamentos": [
  { "nombre": "Metformina 850mg", "prescripcion": "Tomar 1 tableta cada 12 horas por 30 días", "cantidad_total": "60", "entregas": 1 }
]}
```
 
**OrdenProcedimiento:**
```json
{ "examenes_solicitados": [
  { "codigo": "903603", "descripcion": "Calcio automatizado", "cantidad": 1, "bilateral": false }
]}
```
 
**InformeEstudio** (imágenes o laboratorio):
```json
{
  "nombre_estudio": "string",
  "hallazgos": "string",
  "opinion": "string",
  "resultados_laboratorio": [
    { "examen": "string", "resultado": "string", "unidad": "string", "valor_referencia": "string" }
  ]
}
```
 
**Incapacidad:**
```json
{ "dias_incapacidad": 2, "fecha_inicial": "2026-04-23", "fecha_final": "2026-04-24", "diagnostico_principal": "I20.9", "diagnostico_relacionado": "R07.4", "prorroga": false }
```
 
## Reglas de enrutamiento
 
1. `situacion = Urgente` o `Ambiguo` → dispara `envio_correo.py`, caso marcado para revisión humana.
2. Si no, enrutamiento por `tipo_documento`:
| tipo_documento | destino sugerido |
|---|---|
| Receta | Farmacia Hospitalaria |
| OrdenProcedimiento | Auditoría de Autorizaciones |
| InformeEstudio | Historia Clínica Electrónica |
| Incapacidad | Administrativo / RRHH |
| Otro | Revisión humana |
 
> **`puntaje_confianza` sigue pendiente** — el cálculo y el umbral quedan a cargo de Anahí (grafo de decisión + orquestación).
 
## Almacenamiento
 
Los archivos de entrada y el JSON de salida se suben a OCI Object Storage, en el bucket correspondiente al estado (`recibidos` / `procesados` / `auditoria_humana` — ver [`infraestructura-cloud.md`](infraestructura-cloud.md)).