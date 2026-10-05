# Casos de prueba y validación — MediFlow

Banco de pruebas para medir el desempeño del agente y catálogos que usa la
validación clínica en tiempo de ejecución.

> Todos los documentos son **sintéticos**. Ningún dato corresponde a personas
> reales. Cada documento lleva al pie la leyenda "DOCUMENTO SINTÉTICO GENERADO
> PARA PRUEBAS - NO VÁLIDO".

---

## Contenido

```
casos/
├── DOC-001 … DOC-100          100 documentos (65 PDF, 25 imagen, 10 JSON)
└── referencia/
    ├── ground_truth.jsonl     respuesta correcta de cada documento
    ├── manifest.csv           el mismo resumen en tabla (abrir en Excel)
    ├── generar_dataset.py     script que generó los documentos
    └── catalogos/
        ├── cie10_subconjunto.json      21 códigos CIE-10 con descripción
        ├── medicamentos.json           20 fármacos con dosis máxima diaria
        └── reglas_y_parametros.json    umbrales, formato de matrícula,
                                        valores críticos y reglas de ruteo
```

### Dos usos distintos, no confundirlos

| Archivo | ¿Lo usa el agente en ejecución? | Para qué |
|---|---|---|
| `ground_truth.jsonl` | **No** | Solo el evaluador, para calificar |
| `manifest.csv` | No | Consulta humana |
| `generar_dataset.py` | No | Regenerar o ampliar los casos |
| `catalogos/*.json` | **Sí** | Validación clínica en `validacion_clinica.py` |

El agente **nunca** lee el ground truth. Si lo leyera, estaría copiando la
respuesta en lugar de resolver el documento.

---

## Composición del dataset

| Categoría | Cantidad |
|---|---|
| Receta médica | 20 |
| Informe de estudio (laboratorio / imagen) | 20 |
| Orden de solicitud de procedimiento | 15 |
| Epicrisis / informe de alta | 15 |
| Certificado médico | 10 |
| No clínico (factura, citación, comunicado) | 5 |
| Casos adversariales ("trampa") | 15 |

**Formatos:** 40 PDF nativo, 25 PDF escaneado, 25 foto de celular simulada,
10 JSON. La mitad del dataset está degradado (rotación, ruido, sombra,
perspectiva, compresión) para probar la lectura multimodal de verdad.

**Split:** ~30 documentos marcados `dev` y ~70 marcados `test`. Los prompts y
las reglas se ajustan mirando **solo** los `dev`. Los `test` se usan
únicamente para la medición final; ajustar mirándolos invalida las métricas.

### Casos adversariales

| Trampa | Qué prueba | Destino esperado |
|---|---|---|
| `sin_matricula` (2) | Falta el registro del profesional | revisión humana |
| `cie10_inconsistente` (2) | Código que no corresponde al diagnóstico | revisión humana |
| `dosis_fuera_de_rango` (2) | Prescripción que supera el máximo diario | revisión humana |
| `fecha_futura` (1) | Documento con fecha posterior a hoy | revisión humana |
| `receta_vencida` (1) | Receta con más de 30 días | revisión humana |
| `paciente_inconsistente` (2) | Dos pacientes distintos en el mismo documento | revisión humana |
| `urgencia_implicita` (2) | Cuadro grave sin la palabra "urgente" | urgencias |
| `documento_mixto` (1) | Receta que además solicita estudios | revisión humana |
| `json_malformado` (1) | JSON inválido | revisión humana |
| `ilegible` (1) | Foto con desenfoque severo | revisión humana |

---

## Formato del ground truth

Una línea JSON por documento. Campos principales:

| Campo | Significado |
|---|---|
| `id`, `archivo` | Identificador y ruta del documento |
| `split`, `formato`, `calidad`, `trampa`, `dificultad` | Metadatos para cortar las métricas por grupo |
| `categoria` | receta_medica, informe_estudio, orden_procedimiento, epicrisis, certificado_medico, otro |
| `paciente`, `profesional`, `institucion` | Datos que deben extraerse (documento del paciente sin puntos) |
| `diagnostico` | Texto y código CIE-10 impresos en el documento |
| `medicamentos`, `estudios_solicitados`, `resultados` | Según la categoría |
| `urgencia` | baja, media, alta |
| `conflictos_esperados` | Inconsistencias que la validación debe detectar |
| `ruta_esperada` | urgencias, revision_humana, farmacia, auditoria_autorizaciones, historia_clinica_electronica |

Las fechas y la vigencia de recetas se evalúan contra `fecha_referencia`,
definida en `catalogos/reglas_y_parametros.json`.

---

## Cómo ejecutar la evaluación

Desde la **raíz del repositorio**, con el entorno activo y `GEMINI_API_KEY`
en el `.env`:

```bash
python evaluacion.py                 # los 100 documentos
python evaluacion.py --split dev     # solo los de desarrollo
python evaluacion.py --limite 20     # los primeros 20 (cuota gratuita: 20/día)
python evaluacion.py --solo-metricas # recalcula sin llamar a Gemini
python evaluacion.py --forzar        # ignora la caché y reprocesa
```

El evaluador llama directamente a `procesar_con_gemini()` y
`ejecutar_langgraph()`, por lo que **no envía correos** ni copia archivos al
almacén local.

**Caché:** cada respuesta de Gemini se guarda en
`evaluacion_resultados/cache/`. Las corridas siguientes la reutilizan, así
que se puede procesar en tandas sin repetir llamadas. Si se borra, hay que
volver a gastar cuota.

### Qué reporta

- Exactitud por campo: categoría, nombre, documento, matrícula, CIE-10, medicamentos
- Exactitud de enrutamiento
- **Recall de urgencias**, con el detalle de cuáles se escaparon
- Carga de revisión humana (qué porcentaje queda sin automatizar)
- Corte por formato y calidad (PDF limpio contra foto degradada)
- Resultado de cada caso adversarial
- Tabla de calibración de umbrales
- Matriz de confusión de categorías
- `evaluacion_resultados/detalle.csv` con el resultado documento por documento

---

## Validación clínica sin consumir cuota

`Backend_MediFlow/validacion_clinica.py` es determinista: no llama a ninguna
API. Se puede probar y ajustar sobre los JSON ya cacheados:

```bash
python Backend_MediFlow/validacion_clinica.py --hoy 2026-10-05
```

Imprime, por documento, los conflictos detectados y compara la ruta antes y
después de la validación contra la esperada.

Validaciones que aplica:

| Validación | Detecta | Peso |
|---|---|---|
| Fecha de emisión | Documento con fecha futura | 40 |
| Vigencia | Receta con más de 30 días | 30 |
| CIE-10 | Código inexistente en el catálogo | 30 |
| CIE-10 | Código que no corresponde al diagnóstico escrito | 35 |
| Dosis | Dosis diaria sobre el máximo del catálogo | 60 |
| Matrícula | Ausente | 40 |
| Matrícula | Formato inválido (acepta RM y MN/MP) | 20 |
| Documento múltiple | Receta que además solicita estudios | 35 |
| Identificación | Paciente sin número de documento | 25 |
| Valores críticos | Potasio, troponina o hemoglobina en rango crítico | fuerza urgencia |

Los pesos se ajustan en `PESOS_DEFECTO` y los valores críticos en
`catalogos/reglas_y_parametros.json`, sin tocar el resto del código.

---

## Regenerar o ampliar el dataset

```bash
pip install reportlab pypdfium2 pillow numpy opencv-python

python casos/referencia/generar_dataset.py --perfil CO --semilla 42
python casos/referencia/generar_dataset.py --perfil AR     # DNI, MN/MP, obras sociales
python casos/referencia/generar_dataset.py --semilla 7 --salida dataset_2
```

Los datos se crean primero y el documento se renderiza a partir de ellos, por
lo que el ground truth es correcto por construcción.

---

## Limitaciones conocidas

Los documentos salen de 3 plantillas y 21 diagnósticos, así que las métricas
son **optimistas** respecto a documentos reales con otros formatos. Sirven
para comparar versiones del agente y calibrar umbrales, no como promesa de
precisión en producción.

Para reducir ese sesgo conviene añadir fotografías reales de documentos
impresos y el caso de referencia del enunciado del reto, registrando su línea
correspondiente en `ground_truth.jsonl`.

En operación, el conjunto de evaluación se mantendría con las correcciones
del auditor humano y con muestreo de control sobre los casos automatizados.