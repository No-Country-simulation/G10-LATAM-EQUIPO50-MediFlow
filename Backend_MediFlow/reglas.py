#Configuracion de Reglas de MediFlow

#Libreriras usadas:
from librerias import *

#Configuracion compartida:
from configuracion import *

#Reglas por defecto para LangGraph:
#Cada categoria tiene sus propias reglas,
#El valor representa cuantos puntos se agregan al puntaje de incoherencia,
#Cuando se encuentra esa condicion,
#LangGraph seleccionara automaticamente el bloque correcto
#Dependiendo de la categoria clasificada por Gemini

REGLAS_DEFECTO = {
    "Receta Médica": {

        "sin_medicamentos": 30,

        "sin_medicamentos_tratamiento": 20,

        "sin_id_paciente": 5,

        "sin_nombre_paciente": 10,

        "sin_nombre_medico": 5,

        "recomendaciones_sin_medicamentos": 20
    },

    "Informe de Estudio de Diagnóstico por Imágenes/Laboratorio": {

        "sin_estudios": 40,

        "estudio_sin_resultado": 10,

        "maximo_estudio_sin_resultado": 20
    },

    "Orden de Solicitud de Procedimiento": {

        "sin_procedimientos": 40
    },

    "Epicrisis / Informe de Alta": {

        "sin_diagnosticos": 20,

        "sin_tratamiento": 20,

        "sin_seguimiento": 10
    },

    "Certificado Médico": {

        "sin_nombre_paciente": 20,

        "sin_nombre_medico": 20
    },

    "ambiguidad": {

        "por_dato": 5,

        "maximo": 20
    }
}

def validar_reglas(reglas):

    if not isinstance(reglas, dict):

        return False

    categorias = [
        "Receta Médica",
        "Informe de Estudio de Diagnóstico por Imágenes/Laboratorio",
        "Orden de Solicitud de Procedimiento",
        "Epicrisis / Informe de Alta",
        "Certificado Médico",
        "ambiguidad"
    ]

    for categoria in categorias:

        if categoria not in reglas:

            return False

        if not isinstance(reglas[categoria], dict):

            return False

        for valor in reglas[categoria].values():

            if not isinstance(valor, int):

                return False

            if valor < 0 or valor > 100:

                return False

    return True

def guardar_configuracion_reglas(reglas):

    try:

        with open(Carpeta_Configuracion_Reglas,"w",encoding="utf-8") as archivo:
            json.dump(reglas,archivo,ensure_ascii=False,indent=4)

        print("\nConfiguracion de reglas guardada CORRECTAMENTE!")

    except Exception as error:

        print(f"\nNo se pudo guardar la configuracion de reglas: {error}")

def cargar_configuracion_reglas():

    if not os.path.exists(Carpeta_Configuracion_Reglas):

        return json.loads(json.dumps(REGLAS_DEFECTO,ensure_ascii=False))

    try:

        with open(Carpeta_Configuracion_Reglas,"r",encoding="utf-8") as archivo:
            reglas = json.load(archivo)

        if validar_reglas(reglas):

            return reglas

        print("\nLa configuracion guardada de reglas no es valida")

        return json.loads(json.dumps(REGLAS_DEFECTO,ensure_ascii=False))

    except Exception as error:

        print(f"\nError al cargar las reglas: {error}")

        return json.loads(json.dumps(REGLAS_DEFECTO,ensure_ascii=False))

def mostrar_explicacion_reglas(reglas):

    print("\nREGLAS ACTUALES DE LANGGRAPH")

    print("\nCada regla agrega puntos al puntaje de incoherencia del documento subido,")

    print("Entre mayor sea el valor, mayor sera el impacto de esa inconsistencia")

    print("\nLangGraph NO aplica todas las reglas al mismo tiempo,")

    print("Primero identifica la categoria y despues selecciona automaticamente las reglas correspondientes\n")

    for categoria, reglas_categoria in reglas.items():

        print(f"\n[{categoria}]")

        for nombre_regla, valor in reglas_categoria.items():

            print(f"  {nombre_regla}: +{valor} puntos")

def solicitar_configuracion_reglas():

    reglas = cargar_configuracion_reglas()

    mostrar_explicacion_reglas(reglas)

    respuesta = input("\n¿Deseas modificar las reglas de LangGraph? (Responde: si/no): ").strip().lower()

    if respuesta not in ["s", "si", "sí", "Si"]:

        print("\nSe utilizaran las reglas actuales!!")

        return reglas

    print("\nMODIFICACION DE REGLAS")

    print("\nPuedes introducir un nuevo valor")

    print("Si presionas ENTER, se conservara el valor actual ")

    print("\nEjemplo: ")

    print(
        "Una regla de +30 significa que esa inconsistencia, "
        "AGREGA 30 puntos al puntaje"
    )

    for categoria in reglas:

        print("\n" + "-" * 70)

        print(f"CATEGORIA: {categoria}")

        for nombre_regla in reglas[categoria]:

            valor_actual = reglas[categoria][nombre_regla]

            while True:

                nuevo_valor = input(f"\n{nombre_regla} " f"[actual {valor_actual}]: ").strip()

                if nuevo_valor == "":
                    break

                try:

                    nuevo_valor = int(nuevo_valor)

                    if 0 <= nuevo_valor <= 100:

                        reglas[categoria][nombre_regla] = nuevo_valor

                        break

                    print("ERROR: El valor debe estar en un rango entre 0 y 100")

                except ValueError:

                    print("ERROR: Introduce un numero entero!!!")

    if validar_reglas(reglas):

        guardar_configuracion_reglas(reglas)

        print("\nLas nuevas reglas se guardaron EXITOSAMENTE!!!")

    else:

        print("\nLa configuracion NO es valida!!!!: ")

        print("Se utilizaran las reglas por DEFECTO!!")
        reglas = json.loads(json.dumps(REGLAS_DEFECTO,ensure_ascii=False))

    mostrar_explicacion_reglas(reglas)

    return reglas
