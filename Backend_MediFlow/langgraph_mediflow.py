#LangGraph y clasificacion del documento

#Libreriras usadas:
from librerias import *

#Configuracion compartida:
from configuracion import *

#Configuracion de reglas:
from reglas import *

def normalizar_categoria(categoria):
    """Valida la categoría entregada por Gemini: """
    categorias_permitidas = {
        "Receta Médica",
        "Informe de Estudio de Diagnóstico por Imágenes/Laboratorio",
        "Orden de Solicitud de Procedimiento",
        "Epicrisis / Informe de Alta",
        "Certificado Médico",
        "Otro" #Habia Otro
    }
    #Si el documento no esta en ninguna categoria dada regresa Otro
    if not isinstance(categoria, str):
        return "Otro"#Otro

    categoria = categoria.strip()

    if categoria in categorias_permitidas:
        return categoria

    return "Otro"#CHECAR

def asegurar_estructura_clasificacion(datos):
    """
    Crea las estructuras que LangGraph necesita si Gemini no las
    devuelve. Esto evita KeyError y permite que LangGraph complete
    la clasificación de forma determinista
    """
    if not isinstance(datos.get("clasificacion_documento"), dict):
        datos["clasificacion_documento"] = {}

    if not isinstance(datos.get("clasificacion_riesgo"), dict):
        datos["clasificacion_riesgo"] = {}

    documento = datos.get("documento", {})

    if not datos["clasificacion_documento"].get("categoria"):
        datos["clasificacion_documento"]["categoria"] = normalizar_categoria(
            documento.get("tipo_documento")
        )

    riesgo = datos["clasificacion_riesgo"]
    riesgo.setdefault("urgente", False)
    riesgo.setdefault("motivo_urgencia", None)
    riesgo.setdefault("datos_ambiguos", [])
    riesgo.setdefault("datos_faltantes", [])
    riesgo.setdefault("clasificacion_final", None)
    riesgo.setdefault("requiere_revision_humana", False)

    return datos

def nodo_clasificar_documento(estado):
    """
    Valida la categoría del documento entregada por Gemini:
    """
    datos = asegurar_estructura_clasificacion(estado["datos_clinicos"])

    categoria = datos["clasificacion_documento"].get("categoria")
    categoria = normalizar_categoria(categoria)
    datos["clasificacion_documento"]["categoria"] = categoria

    estado["datos_clinicos"] = datos

    print(f"\n[LangGraph] Categoría: {categoria}")
    return estado

def nodo_validar_coherencia_documental(estado):

    datos = estado["datos_clinicos"]

    umbrales = estado["umbrales"]

    #Obtenemos las Reglas desde el estado de LangGraph
    # LangGraph recibe las reglas desde el nodo inicial,
    
    #Posteriormente seleccionaremos automaticamente
    #las reglas de acuerdo con la categoria
    reglas = estado.get("reglas",REGLAS_DEFECTO)

    datos = asegurar_estructura_clasificacion(datos)

    categoria = datos["clasificacion_documento"].get("categoria","Otro")

    categoria = normalizar_categoria(categoria)

    #Aqui ocurre la seleccion automatica:
    #Si Gemini clasifico como:
    #Receta Médica
    #LangGraph utilizara:
    #reglas["Receta Médica"]
    #Si clasifico como Epicrisis:
    #reglas["Epicrisis / Informe de Alta"]
    #El usuario NO necesita seleccionar manualmente la categoria
    
    reglas_categoria = reglas.get(categoria,{})

    puntaje = 0

    motivos = []

    paciente = datos.get("paciente",{})

    medico = datos.get("medico",{})

    tratamiento = datos.get("tratamiento",{})

    #Aplicando Reglas para la categoria: RECETA MEDICA
    if categoria == "Receta Médica":

        if not datos.get("medicamentos"):
            puntaje += reglas_categoria.get("sin_medicamentos",0)

            motivos.append("La receta no contiene medicamentos.")

        if not tratamiento.get("medicamentos"):
            puntaje += reglas_categoria.get("sin_medicamentos_tratamiento",0)

            motivos.append("No se encontraron medicamentos en el tratamiento.")

        if not paciente.get("id_paciente"):
            puntaje += reglas_categoria.get("sin_id_paciente",0)

            motivos.append("Falta el identificador del paciente.")

        if not paciente.get("nombre_completo"):
            puntaje += reglas_categoria.get("sin_nombre_paciente",0)

            motivos.append("Falta el nombre del paciente.")

        if not medico.get("nombre_completo"):
            puntaje += reglas_categoria.get("sin_nombre_medico",0)

            motivos.append("Falta el nombre del medico.")

        recomendaciones = tratamiento.get("recomendaciones",[])

        medicamentos = tratamiento.get("medicamentos",[])

        if recomendaciones and not medicamentos:
            puntaje += reglas_categoria.get("recomendaciones_sin_medicamentos",0)

            motivos.append("Existen recomendaciones pero no se encontraron medicamentos.")


    #Aplicando Reglas para la categoria: INFORME DE ESTUDIO
    elif categoria == ("Informe de Estudio de Diagnóstico por Imágenes/Laboratorio"):
        estudios = datos.get("estudios",[])

        if not estudios:
            puntaje += reglas_categoria.get("sin_estudios",0)

            motivos.append("No se encontraron estudios.")

        else:
            estudios_sin_resultado = 0
            for estudio in estudios:
                if not estudio.get("resultado"):
                    estudios_sin_resultado += 1

            regla_por_estudio = reglas_categoria.get("estudio_sin_resultado",0)

            regla_maxima = reglas_categoria.get("maximo_estudio_sin_resultado",0)

            puntaje += min(regla_maxima,estudios_sin_resultado * regla_por_estudio)

            if estudios_sin_resultado > 0:
                motivos.append(f"{estudios_sin_resultado} estudio(s) sin resultado.")


    #Aplicando Reglas para la categoria: ORDEN DE PROCEDIMIENTO
    elif categoria == ("Orden de Solicitud de Procedimiento"):
        procedimientos = datos.get("procedimientos",[])

        if not procedimientos:
            puntaje += reglas_categoria.get("sin_procedimientos",0)

            motivos.append("No se encontraron procedimientos.")

    #Aplicando Reglas para la categoria: EPICRISIS
    elif categoria == ("Epicrisis / Informe de Alta"):
        diagnosticos = datos.get("diagnosticos",[])

        if not diagnosticos:
            puntaje += reglas_categoria.get("sin_diagnosticos",0)

            motivos.append("No se encontraron diagnosticos.")

        descripcion_tratamiento = tratamiento.get("descripcion")

        medicamentos = tratamiento.get("medicamentos",[])

        if not descripcion_tratamiento and not medicamentos:
            puntaje += reglas_categoria.get("sin_tratamiento",0)

            motivos.append("No se encontro informacion de tratamiento.")

        seguimiento = datos.get("seguimiento",[])

        if not seguimiento:
            puntaje += reglas_categoria.get("sin_seguimiento",0)

            motivos.append("No se encontraron indicaciones de seguimiento.")

    #Aplicando Reglas para la categoria: CERTIFICADO MEDICO
    elif categoria == "Certificado Médico":
        if not paciente.get("nombre_completo"):
            puntaje += reglas_categoria.get("sin_nombre_paciente",0)

            motivos.append("Falta el nombre del paciente.")

        if not medico.get("nombre_completo"):
            puntaje += reglas_categoria.get("sin_nombre_medico",0)

            motivos.append("Falta el nombre del medico.")

    #Aplicando Reglas para la categoria: DATOS AMBIGUOS
    riesgo = datos["clasificacion_riesgo"]

    ambiguos = riesgo.get("datos_ambiguos",[])
    #Cambio
    datos_ilegibles = datos.get("datos_no_legibles_o_ambiguos")

    cantidad_ambiguedades = (len(ambiguos) + len(datos_ilegibles))
    
    #Aqui esta la Regla de Ambiguedad Configurable:
    regla_ambiguedad = reglas.get("ambiguidad",REGLAS_DEFECTO["ambiguidad"])

    puntos_ambiguedad = min(regla_ambiguedad.get("maximo",20),cantidad_ambiguedades * regla_ambiguedad.get("por_dato",5))

    puntaje += puntos_ambiguedad

    if cantidad_ambiguedades > 0:

        motivos.append(f"Se detectaron " f"{cantidad_ambiguedades} dato(s) ambiguo(s).")

    #Limitando PUNTAJE A 100
    puntaje = min(puntaje,100)

    #Determinando el nivel de urgencia:
    if puntaje < umbrales["umbral_normal"]:
        nivel = "normal"

    elif puntaje < umbrales["umbral_revision"]:
        nivel = "revision"

    elif puntaje < umbrales["umbral_alerta"]:
        nivel = "revision_prioritaria"

    else:
        nivel = "alerta"

    #Guardando Validacion de coherencia de documento
    datos["validacion_coherencia"] = {

        "puntaje_incoherencia": puntaje,

        "nivel_coherencia": nivel,

        "categoria_reglas_aplicadas": categoria,

        "umbrales_utilizados": umbrales,

        "reglas_utilizadas": reglas_categoria,

        "motivos": motivos,

        "requiere_revision_humana":nivel != "normal"
    }

    #Clasificacion De estados de alerta:
    if not riesgo.get("urgente",False):
        if nivel == "alerta":
            estado["clasificacion_final"] = "alerta"

        elif nivel == "revision_prioritaria":
            estado["clasificacion_final"] = "revision_prioritaria"

        elif nivel == "revision":
            estado["clasificacion_final"] = "revision"

        else:
            estado["clasificacion_final"] = "normal"

    estado["datos_clinicos"] = datos

    return estado

def nodo_detectar_urgencia(estado):
    """
    Comprueba una urgencia explícita reportada por Gemini,
    La urgencia siempre tiene prioridad sobre la coherencia.
    """
    datos = estado["datos_clinicos"]
    riesgo = datos.get("clasificacion_riesgo", {})

    urgente = riesgo.get("urgente", False)

    if urgente is True:
        estado["clasificacion_final"] = "urgente"
        print("\n[LangGraph] Documento marcado como URGENTE!!\n")

    return estado

def nodo_detectar_ambiguedad(estado):
    """La urgencia tiene prioridad sobre la ambigüedad."""
    if estado.get("clasificacion_final") == "urgente":
        return estado

    datos = estado["datos_clinicos"]
    riesgo = datos.get("clasificacion_riesgo", {})

    ambiguos = riesgo.get("datos_ambiguos", [])
    datos_ilegibles = datos.get("datos_no_legibles_o_ambiguos", [])

    if ambiguos or datos_ilegibles:
        estado["clasificacion_final"] = "ambiguo"
        print("\n[LangGraph] Documento marcado como AMBIGUO\n")

    return estado

def nodo_detectar_datos_faltantes(estado):
    """Prioridad: urgente > ambiguo > datos faltantes > coherencia > normal."""
    if estado.get("clasificacion_final") in {"urgente", "ambiguo"}:
        return estado

    datos = estado["datos_clinicos"]
    riesgo = datos.get("clasificacion_riesgo", {})
    faltantes = riesgo.get("datos_faltantes", [])

    if faltantes:
        estado["clasificacion_final"] = "datos_faltantes"
        print("\n[LangGraph] Documento marcado como DATOS FALTANTES\n")

    return estado

def nodo_decidir_ruta(estado):
    """
    Determina la clasificación final respetando esta prioridad:

        1. urgente
        2. ambiguo
        3. datos_faltantes
        4. alerta_coherencia
        5. revision_coherencia
        6. normal

    De esta forma, una urgencia explícita nunca es reemplazada por
    una clasificación de coherencia del documento
    """
    clasificacion = estado.get("clasificacion_final")

    if not clasificacion:
        clasificacion = "normal"

    estado["clasificacion_final"] = clasificacion

    datos = asegurar_estructura_clasificacion(estado["datos_clinicos"])
    riesgo = datos["clasificacion_riesgo"]

    riesgo["clasificacion_final"] = clasificacion
    riesgo["requiere_revision_humana"] = clasificacion != "normal"

    estado["datos_clinicos"] = datos

    print(f"\n[LangGraph] Clasificación final: {clasificacion}")

    return estado

def construir_grafo_clasificacion():
    """
    Flujo actualizado:
    
    1. START,
    2. clasificar_documento,
    3. validar_coherencia_documental,
    4. detectar_urgencia,
    5. detectar_ambiguedad,
    6. detectar_datos_faltantes,
    7. decidir_ruta,
    8. END
    """

    grafo = StateGraph(dict)

    grafo.add_node("clasificar_documento", nodo_clasificar_documento)
    grafo.add_node("validar_coherencia_documental", nodo_validar_coherencia_documental)
    grafo.add_node("detectar_urgencia", nodo_detectar_urgencia)
    grafo.add_node("detectar_ambiguedad", nodo_detectar_ambiguedad)
    grafo.add_node("detectar_datos_faltantes", nodo_detectar_datos_faltantes)
    grafo.add_node("decidir_ruta", nodo_decidir_ruta)

    grafo.add_edge(START, "clasificar_documento")
    grafo.add_edge("clasificar_documento", "validar_coherencia_documental")
    grafo.add_edge("validar_coherencia_documental", "detectar_urgencia")
    grafo.add_edge("detectar_urgencia", "detectar_ambiguedad")
    grafo.add_edge("detectar_ambiguedad", "detectar_datos_faltantes")
    grafo.add_edge("detectar_datos_faltantes", "decidir_ruta")
    grafo.add_edge("decidir_ruta", END)

    return grafo.compile()

def ejecutar_langgraph(datos_clinicos,umbrales,reglas):
    estado_inicial = {

        "datos_clinicos":
            datos_clinicos,

        "clasificacion_final":
            None,

        "umbrales":
            umbrales,

        "reglas":
            reglas
    }

    grafo = construir_grafo_clasificacion()

    resultado = grafo.invoke(estado_inicial)

    return resultado
