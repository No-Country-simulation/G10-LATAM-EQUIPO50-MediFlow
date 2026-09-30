#Mostrar resultados de MediFlow

#Libreriras usadas:
from librerias import *

#Configuracion compartida:
from configuracion import *

def mostrar_resultado_final(resultado_langgraph,ruta_json):
    """
    Muestra el resultado final
    del procesamiento.
    """
    datos = resultado_langgraph["datos_clinicos"]

    categoria = datos["clasificacion_documento"]["categoria"]

    clasificacion = resultado_langgraph["clasificacion_final"]

    validacion = datos.get("validacion_coherencia",{})

    print("\nRESULTADO FINAL MEDIFLOW: ")
    print(f"\nCategoria documental: \n" f"{categoria}")
    print(f"Clasificacion final: \n" f"{clasificacion}")
    print(f"Puntaje de incoherencia: \n" f"{validacion.get('puntaje_incoherencia', 0)}")
    print(f"Nivel de coherencia: \n" f"{validacion.get('nivel_coherencia', 'normal')}")

    print(f"Reglas utilizadas: \n" f"{validacion.get('categoria_reglas_aplicadas', categoria)}")
    print(f"\nArchivo JSON: ")
    print(ruta_json)

def mostrar_niveles_evaluacion(umbrales, nivel_actual, puntaje):
    """
    Muestra al usuario todos los niveles que puede tener
    el documento según los umbrales configurados,

    IMPORTANTE:
    Estos niveles representan INCONSISTENCIAS en el DOCUMENTO,
    NO representan gravedad médica ni una confianza médica
    """

    normal      = umbrales["umbral_normal"]
    revision    = umbrales["umbral_revision"]
    alerta      = umbrales["umbral_alerta"]

    print("\nNIVELES DE EVALUACIÓN DE MEDIFLOW: ")

    print("\nEl puntaje utilizado por MediFlow va en un rango de 0 a 100,")
    print("Este puntaje representa INCONSISTENCIAS detectadas")
    print("en el documento mediante las reglas configuradas,")
    print("NO representa una calificación médica ni la gravedad")
    print("del estado de salud del paciente.\n")

    print("NIVELES CONFIGURADOS por el usuario o dejados por Default: \n")

    print(f"0 - {normal - 1} : NORMAL")

    print(f"{normal} - {revision - 1} : REVISIÓN")

    print(f"{revision} - {alerta - 1} : REVISIÓN PRIORITARIA")

    print(f"{alerta} - 100 : ALERTA")

    print(f"\nPuntaje obtenido por este documento: {puntaje}")
    print(f"\nNivel obtenido: {nivel_actual.upper()}")

def mostrar_resultado_final_completo(resultado_langgraph, ruta_json, umbrales):
    """
    Muestra al usuario el resultado final completo de MediFlow,

    Además de mostrar la ruta del JSON, informa:
        La Categoría del documento,
        La Clasificación final del documento,
        El Puntaje de inconsistenciadel documento,
        El Nivel de coherencia del documento,
        El Nivel de  Urgencia que tiene el documento,
        Los Datos ambiguos del documento,
        Los Datos faltantes del documento,
        Los Motivos de inconsistencias del documento,
        LA Ruta donde se guardó el JSON del documenti Final generado,
        Todos los niveles posibles hasta ahora se mostraran en pantalla.
    """

    datos = resultado_langgraph["datos_clinicos"]

    categoria = datos["clasificacion_documento"]["categoria"]

    clasificacion = resultado_langgraph["clasificacion_final"]

    validacion = datos.get("validacion_coherencia", {})

    puntaje = validacion.get("puntaje_incoherencia",0)

    nivel_coherencia = validacion.get("nivel_coherencia","normal")

    riesgo = datos.get("clasificacion_riesgo",{})

    motivos = validacion.get("motivos",[])

    print("\nEl Resultado Final De MEDIFLOW es: \n")
    
    print(f"\nCategoría documental:")
    print(f"  {categoria}")

    print(f"\nClasificación final:")
    print(f"  {clasificacion.upper()}")

    print(f"\nPuntaje de inconsistencia:")
    print(f"  {puntaje} / 100")

    print(f"\nNivel de coherencia:")
    print(f"  {nivel_coherencia.upper()}")

    # Información de riesgo detectada por Gemini
    print("\nInformacion de Riesgo Detectadas: \n")

    urgente = riesgo.get("urgente",False)

    if urgente:
        print("  - URGENCIA: SÍ")

        motivo_urgencia = riesgo.get("motivo_urgencia")

        if motivo_urgencia:
            print(f"    Motivo: {motivo_urgencia}")

    else:
        print("  - URGENCIA: NO")

    #Informacion sobre: Datos ambiguos
    datos_ambiguos = riesgo.get("datos_ambiguos",[])

    datos_no_legibles = datos.get("datos_no_legibles_o_ambiguos",[])

    print(f"  - Datos ambiguos: {len(datos_ambiguos)}")

    if datos_ambiguos:
        for dato in datos_ambiguos:
            print(f"      • {dato}")

    print(f"  - Datos no legibles/ambiguos: " f"{len(datos_no_legibles)}")

    if datos_no_legibles:
        for dato in datos_no_legibles:
            print(f"      • {dato}")

    #Información sobre: Datos faltantes
    datos_faltantes = riesgo.get("datos_faltantes",[])

    print(f"  - Datos faltantes: {len(datos_faltantes)}")

    if datos_faltantes:
        for dato in datos_faltantes:
            print(f"      • {dato}")

    
    #Informacion de: Motivos de inconsistencias
    print("\nMotivos de la Evaluacion Del Documento")

    if motivos:
        for motivo in motivos:
            print(f"  • {motivo}")

    else:
        print("  No se detectaron inconsistencias mediante las reglas configuradas.")

    #Mostrando todos los niveles obtenidos para clasificar el documento:
    mostrar_niveles_evaluacion(umbrales,nivel_coherencia,puntaje)

    #Obtenmos la Ruta actual del JSON Final
    print("\nJSON FINAL GENERADO: ")

    print(f"Nombre: \n")
    print(f"  {os.path.basename(ruta_json)}")

    print(f"\nUbicación actual:")
    print(f"  {ruta_json}\n")
