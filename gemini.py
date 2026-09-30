#Integracion de Gemini y generacion del JSON clinico
#Prueba
#Libreriras usadas:
from librerias import *

#Configuracion compartida:
from configuracion import *

def subir_archivo_a_gemini(ruta_archivo):
    """
    Envia el archivo a Gemini.
    IMPORTANTE:
    Aqui NO estamos analizando todavia el documento
    Después utilizaremos el archivo subido
    para realizar el analisis
    """

    #Testeando:
    print("\nSubiendo Archivo a Gemini")
    print(f"\nArchivo:\n{ruta_archivo}")

    # Subimos el Archivo
    archivo_gemini = cliente_gemini.files.upload(file = ruta_archivo)
    print("\nArchivo subido correctamente!!!")

    #Mostramos la informacion proporcionada por Gemini:
    print(f"\nNombre asignado por Gemini:" f"\n{archivo_gemini.name}")

    return archivo_gemini

def crear_prompt_prueba(tipo_archivo,nombre_archivo):
    """
    Pidiendo Estructura clinica Gemini
    """

    prompt = f"""


Eres el sistema de análisis documental Medico de MediFlow, eres critico, experto en area medica, empatico y
y tú función es analizar cuidadosamente el archivo proporcionado y extraer información clínica estructurada,
Has recibido un archivo de tipo:

{tipo_archivo}

Aplicando regla fundamental para la generacion del nombre de archivo:
Debes copiar EXACTAMENTE este nombre en:

"nombre_archivo"

NO debes modificarlo.

NO debes traducirlo.

NO debes resumirlo.

NO debes cambiar fechas.

NO debes cambiar números.

NO debes cambiar mayúsculas o minúsculas.

El valor debe ser exactamente:

{nombre_archivo}

Aplicando Reglas de Extracción del archivo:

Analiza TODO el contenido de manera meticulosamente que este disponible del archivo,
Puede tratarse de:
- Imagen médica
- PDF médifo
- Archivo JSON con información médica

Pero Extrae únicamente información que aparezca
explícitamente en el documento,
ESTÁ ESTRICTAMENTE PROHIBIDO INVENTAR INFORMACIÓN.

Si un dato individual NO aparece,
utiliza:
null

Si una lista no contiene información,
utiliza:
[]

Si una sección no tiene información,
utiliza:
null

Si existe información pero no puede leerse con
seguridad, NO intentes adivinarla ni inventes nada,
Agrégala a:
"datos_no_legibles_o_ambiguos"


Aplicando Reglas sobre información a extraer del CLASIFICACIÓN DEL DOCUMENTO,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:
Identifica la categoría del documento.

Utiliza únicamente una de estas categorías:

1. Receta Médica

2. Informe de Estudio de
   Diagnóstico por Imágenes/Laboratorio

3. Orden de Solicitud de Procedimiento

4. Epicrisis / Informe de Alta

5. Certificado Médico

6. Otro

Queda estrictamente prohibido invertar alguna categoria de clasificacion del documento.

Aplicando Reglas sobre información a extraer del CLASIFICACIÓN DE RIESGO DOCUMENTAL,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:

IMPORTANTE:

No realices un diagnóstico médico.

No inventes una urgencia.

Solamente identifica señales explícitas
presentes en el documento.

Determina:

- urgente
- datos ambiguos
- datos faltantes

Si existe información explícita que indique
una situación urgente o que requiere atención
inmediata, registra:

urgente = true

y explica el motivo.

Si existe información ilegible,
contradictoria o dudosa:

agregarla a datos_ambiguos.

Si falta información necesaria para comprender
o procesar correctamente el documento:

agregarla a datos_faltantes.


Aplicando Reglas sobre información a extraer del PACIENTE,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:

- ID del paciente
- Nombre completo
- Fecha de nacimiento
- Edad
- Sexo
- CURP
- Teléfono
- Correo
- Dirección
- Peso
- Altura
- Alergias
- Antecedentes médicos
- Antecedentes quirúrgicos
- Antecedentes familiares

Aplicando Reglas sobre información a extraer del MEDICO,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:

- Nombre completo
- Especialidad
- Cédula profesional
- Institución
- Teléfono
- Correo

Aplicando Reglas sobre información a extraer de la INFORMACION DE LA CONSULTA MEDICA,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:

- Fecha
- Hora
- Motivo de consulta
- Síntomas
- Signos
- Observaciones

Aplicando Reglas sobre información a extraer de los DIAGNÓSTICOS,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible,
Para cada diagnóstico intenta obtener:

- Nombre
- Descripción
- Código
- Tipo

Extrae los diagnósticos explícitamente presentes.
NO generes diagnósticos propios.


Aplicando Reglas sobre información a extraer de los SIGNOS VITALES,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:

- Presión arterial
- Frecuencia cardiaca
- Frecuencia respiratoria
- Temperatura
- Saturación de oxígeno
- Glucosa

Aplicando Reglas sobre información a extraer de los MEDICAMENTOS,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:

Extrae TODOS los medicamentos encontrados.

Para cada medicamento intenta identificar:

- Nombre
- Principio activo
- Presentación
- Concentración
- Dosis
- Unidad de dosis
- Vía de administración
- Frecuencia
- Duración
- Cantidad
- Indicaciones

Aplicando Reglas sobre información a extraer del TRATAMIENTO,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:

- Descripción
- Medicamentos
- Procedimientos
- Terapias
- Recomendaciones
- Cuidados
- Restricciones
- Dieta
- Actividad física

Aplicando Reglas sobre información a extraer de los ESTUDIOS MEDICOS,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:

- Tipo
- Nombre
- Fecha
- Resultado
- Unidades
- Rango de referencia
- Interpretación

Aplicando Reglas sobre información a extraer de los PROCEDIMIENTOS,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:

- Nombre
- Fecha
- Descripción
- Resultado

Aplicando Reglas sobre información a extraer del SEGUIMIENTO,
Del archivo subido y sin inventar nada, Extrae esta información cuando esté disponible:

- Próxima cita
- Indicaciones de seguimiento
- Signos de alarma
- Observaciones

Aplicando Reglas sobre el FORMATO DE RESPUESTA:
Devuelve ÚNICAMENTE JSON válido.

NO utilices Markdown.

NO escribas:

```json

NO agregues explicaciones antes o después
del JSON.


La estructura debe ser EXACTAMENTE:

{{
    "nombre_archivo": "{nombre_archivo}",

    "tipo_archivo": "{tipo_archivo}",

    "documento": {{
        "es_documento_medico": null,
        "tipo_documento": null,
        "fecha_documento": null,
        "numero_documento": null,
        "institucion_medica": null
    }},

    "paciente": {{
        "id_paciente": null,
        "nombre_completo": null,
        "fecha_nacimiento": null,
        "edad": null,
        "sexo": null,
        "curp": null,
        "telefono": null,
        "correo": null,
        "direccion": null,
        "peso_kg": null,
        "altura_cm": null,
        "alergias": [],
        "antecedentes_medicos": [],
        "antecedentes_quirurgicos": [],
        "antecedentes_familiares": []
    }},

    "medico": {{
        "nombre_completo": null,
        "especialidad": null,
        "cedula_profesional": null,
        "institucion": null,
        "telefono": null,
        "correo": null
    }},

    "consulta": {{
        "fecha": null,
        "hora": null,
        "motivo_consulta": null,
        "sintomas": [],
        "signos": [],
        "observaciones": null
    }},

    "diagnosticos": [],

    "signos_vitales": {{
        "presion_arterial": null,
        "frecuencia_cardiaca_lpm": null,
        "frecuencia_respiratoria_rpm": null,
        "temperatura_c": null,
        "saturacion_oxigeno_porcentaje": null,
        "glucosa_mg_dl": null
    }},

    "medicamentos": [],

    "tratamiento": {{
        "descripcion": null,
        "medicamentos": [],
        "procedimientos": [],
        "terapias": [],
        "recomendaciones": [],
        "cuidados": [],
        "restricciones": [],
        "dieta": null,
        "actividad_fisica": null
    }},

    "estudios": [],

    "procedimientos": [],

    "seguimiento": {{
        "proxima_cita": null,
        "indicaciones_seguimiento": [],
        "signos_alarma": [],
        "observaciones": null
    }},

    "datos_no_legibles_o_ambiguos": [],

    "observaciones": null,

    "clasificacion_riesgo": {{
            "urgente": false,
            "motivo_urgencia": null,
            "datos_ambiguos": [],
            "datos_faltantes": []
        }},
    
        "clasificacion_documento": {{
            "categoria": "Otro"
        }}
}}


RECUERDA:

1. NO INVENTAR INFORMACIÓN.
2. USAR null SI EL DATO NO EXISTE.
3. USAR [] SI NO EXISTEN ELEMENTOS.
4. INFORMAR DATOS ILEGIBLES EN
   "datos_no_legibles_o_ambiguos".
5. CONSERVAR EXACTAMENTE EL NOMBRE DE ARCHIVO.
6. DEVOLVER ÚNICAMENTE JSON VÁLIDO.

"""

    return prompt

def limpiar_respuesta_json(texto_respuesta):
    """
    Limpia posibles bloques Markdown
    alrededor del JSON.
    """
    texto = texto_respuesta.strip()

    # Si Gemini devuelve ```json
    if texto.startswith( "```json"):

        texto = texto[len("```json"):]

    # Si devuelve solamente ```
    elif texto.startswith("```"):
        texto = texto[len("```"):]

    # Eliminar cierre Markdown.
    if texto.endswith("```"):
        texto = texto[:-len("```")]

    return texto.strip()

def validar_json_clinico(texto_respuesta,nombre_archivo):
    """
    Convierte la respuesta de Gemini
    en un diccionario y valida
    los datos básicos que pedimos se generaran
    """

    if not texto_respuesta:

        raise ValueError("Gemini no devolvió ninguna respuesta")

    #Aplicando Limpiar Markdown.
    texto_limpio = limpiar_respuesta_json(texto_respuesta)

    #Intentar convertir texto a JSON del texto limpiado:
    try:

        datos_clinicos = json.loads(texto_limpio)

    except json.JSONDecodeError as error:

        print("\nRespuesta recibida de Gemini: ")
        print(texto_respuesta)

        raise ValueError("\nGemini no devolvió JSON válido.\n" f"Error: {error}")

    #Comprobando que el JSON sea un objeto.
    if not isinstance(datos_clinicos,dict):

        raise ValueError("\nLa respuesta de Gemini no es un objeto JSON")

    #Comprobando el nombre del JSON:
    nombre_respuesta = (datos_clinicos.get("nombre_archivo"))

    if nombre_respuesta != nombre_archivo:

        raise ValueError(

            "\nEl nombre del archivo "
            "devuelto por Gemini "
            "no coincide con el generado "
            "por MediFlow.\n\n"

            f"Nombre esperado:\n"
            f"{nombre_archivo}\n\n"

            f"Nombre recibido:\n"
            f"{nombre_respuesta}"

        )


    print("\nJSON clínico validado correctamente")

    return datos_clinicos

def procesar_con_gemini(ruta_archivo,tipo_archivo,nombre_archivo):
    """
    Realizando estos procesos con Gemini:
        1. Sube archivo.
        2. Crea prompt.
        3. Envía archivo + instrucciones.
        4. Recibe respuesta.
        5. Valida JSON.
        6. Devuelve JSON clínico.
    """
    #Realiza el análisis completo con Gemini.

    #Paso1 Subir archivo:
    archivo_gemini = subir_archivo_a_gemini(ruta_archivo)

    #Paso2 Creamos las instrucciones a realiar para analizar el archivo subido:
    prompt = crear_prompt_prueba(tipo_archivo,nombre_archivo)

    #Testeamos:
    print("\nEspere El Agente Inteligente MediFlow con Gemini integrado: ")
    print("Por el Equipo50_LATAM_G10, esta analizando el archivo subido\n")

    #Paso3 Enviamos el prompt + archivo subido a Gemini
    respuesta = cliente_gemini.models.generate_content(
        model = MODELO_GEMINI,
        contents = [prompt,archivo_gemini]
    )

    #Paso 4 Obtenemos el texto de respuesta que genero Gemini:
    texto_respuesta = respuesta.text

    #Comprobamos que Gemini haya respondido
    if not texto_respuesta:

        raise ValueError("Gemini no devolvió ninguna respuesta.")

    #Paso 5 Validamos la respueta(JSON):
    datos_clinicos = (validar_json_clinico(texto_respuesta,nombre_archivo))
    #Paso6 Devolvemos el diccionario JSON
    return datos_clinicos

def generar_nombre_json_clinico(nombre_archivo):
    """
    Genera el nombre del JSON clinico
    utilizando el nombre generado del archivo original, que es el que guardamos
    """
    nombre_sin_extension = Path(nombre_archivo).stem

    nombre_json = (f"{nombre_sin_extension}" f"_Datos_Clinicos.json")

    return nombre_json
