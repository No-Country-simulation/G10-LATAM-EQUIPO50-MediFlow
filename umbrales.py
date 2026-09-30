#Configuracion de Umbrales de MediFlow

#Libreriras usadas:
from librerias import *

#Configuracion compartida:
from configuracion import *

#Cambio Nuevo Parte1: CONFIGURACIÓN DE UMBRALES
#Los umbrales NO representan gravedad médica,
#Representan el puntaje de INCONSISTENCIAS en el DOCUMENTO,
#Que detecta LangGraph mediante reglas de validación establecidas
#Ejemplo con los valores por defecto(Prueba por ahora):
#   0 - 19  -> NORMAL
#   20 - 59 -> REVISIÓN
#   60 -100 -> ALERTA

#El usuario podrá modificar estos valores al iniciar el programa,
#Se guardarán en un archivo JSON para no tener que escribirlos
#nuevamente en cada ejecución.

UMBRALES_DEFECTO = {
    "umbral_normal"  :  20,
    "umbral_revision":  40,
    "umbral_alerta"  :  60
}

def validar_umbrales(umbrales):
    """
    Cambio Nuevo Parte2
    Menos peso agregado significa que tiene mas inforamción el documento,
    Comprueba que los tres umbrales estén entre 0 y 100
    y que respeten el orden lógico establecido:

        NORMAL < REVISIÓN < ALERTA

    Esto evita configuraciones imposibles como:
        normal   = 60
        revision = 40
        alerta   = 20
    """
    try:
        normal      = int(umbrales["umbral_normal"])
        revision    = int(umbrales["umbral_revision"])
        alerta      = int(umbrales["umbral_alerta"])
    except (KeyError, TypeError, ValueError):
        return False

    return (0 <= normal < revision < alerta <= 100)

def guardar_configuracion_umbrales(umbrales):
    """
    Cambio Nuevo Parte3

    Guarda los umbrales elegidos por el usuario en:
        Almacen_Local/configuracion_umbral.json

    Así la configuración permanece disponible para la siguiente ejecución
    """
    if not validar_umbrales(umbrales):
        raise ValueError(
            "Los umbrales deben cumplir: "
            "0 <= NORMAL < REVISIÓN < ALERTA <= 100."
        )

    with open(Carpeta_Configuracion, "w", encoding="utf-8") as archivo:
        json.dump(umbrales, archivo, ensure_ascii=False, indent=4)

def cargar_configuracion_umbrales():
    """
    Cambio Nuevo Parte4

    Carga una configuración previamente guardada,
    Si no existe o está dañada, utiliza los valores por defecto establecidos
    """
    if not os.path.isfile(Carpeta_Configuracion):
        return UMBRALES_DEFECTO.copy()

    try:
        with open(Carpeta_Configuracion, "r", encoding="utf-8") as archivo:
            umbrales = json.load(archivo)

        if validar_umbrales(umbrales):
            return {
                "umbral_normal"  :  int(umbrales["umbral_normal"]),
                "umbral_revision":  int(umbrales["umbral_revision"]),
                "umbral_alerta"  :  int(umbrales["umbral_alerta"])
            }

    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass

    print("\nLa configuración de umbrales no es válida.")
    print("Se utilizarán los valores por defecto!!\n")
    return UMBRALES_DEFECTO.copy()

def mostrar_explicacion_umbrales(umbrales):
    """
    Cambio Nuevo Parte5

    Explicando al usuario qué significa cada rango antes de pedirle
    si desea modificarlo el rango de cada umbral
    """
    normal      =   umbrales["umbral_normal"]
    revision    =   umbrales["umbral_revision"]
    alerta      =   umbrales["umbral_alerta"]

    print("\nCONFIGURACIÓN DE UMBRALES DE COHERENCIA DEL DOCUMENTO SUBIDO: ")
    print("\nMediFlow calcula un PUNTAJE DE INCONSISTENCIA con rango de: 0 a 100")
    print("Este puntaje NO es una Calificación Médica y Tampoco mide la gravedad")
    print("de un paciente. Mide cuántas inconsistencias tiene el documento subido por el usuario,")
    print("que se detectan mediante las reglas de validación de MediFlow IA Equipo50 G-10 LATAM.")
    print("\nMientras MAYOR sea el puntaje establecido: ")
    print("Quiere decir que hay mayor cantidad/peso de inconsistencias detectadas en el documento dado")
    print("\nRANGOS ACTUALES: \n")
    print(f"0 - {normal - 1}        :   NORMAL")
    print(f"{normal} - {revision - 1}       :   REVISIÓN")
    print(f"{revision} - {alerta - 1}       :   REVISIÓN PRIORITARIA")
    print(f"{alerta} - 100      :   ALERTA")
    print("\nNOTA: tanto REVISIÓN como REVISIÓN PRIORITARIA requieren la")
    print("revisión humana; La segunda indica un puntaje más alto.")
    print("La ALERTA se alcanza cuando el puntaje es igual o mayor")
    print("que el umbral_alerta establecido.")
    print("\nEjemplo:")
    print(f"Si un documento obtiene {normal - 1} puntos Se Asigna:      NORMAL")
    print(f"Si obtiene {normal} puntos Se Asigna:                   Comienzar la zona de REVISIÓN")
    print(f"Si obtiene {alerta} puntos Se Asigna:                   ALERTA\n")

def solicitar_configuracion_umbrales():
    """
    Cambio Nuevo Parte6

    Pregunta al usuario si desea modificar los umbrales y
    Valida los valores introducidos para despues guardar estos
    """
    umbrales = cargar_configuracion_umbrales()

    mostrar_explicacion_umbrales(umbrales)

    respuesta = input("\n¿Deseas modificar estos valores? (Responde con: si o no): ").strip().lower()

    if respuesta not in {"s", "si", "sí", "Si"}:
        print("\nSe conservarán los umbrales actuales!")
        return umbrales

    while True:
        try:
            print("\nIntroduce los nuevos valores en el Rango de entre 0 y 100, por favor.")
            print("Recuerda, la prioridad establecida es: NORMAL < REVISIÓN < ALERTA \n")

            normal      =   int(input("Nuevo umbral NORMAL: ").strip())
            revision    =   int(input("Nuevo umbral REVISIÓN: ").strip())
            alerta      =   int(input("Nuevo umbral ALERTA: ").strip())

            nuevos_umbrales = {
                "umbral_normal":    normal,
                "umbral_revision":  revision,
                "umbral_alerta":    alerta
            }

            if not validar_umbrales(nuevos_umbrales):
                print("\nConfiguración inválida!!!")
                print("IMPORTANTE!: Debe cumplirse: 0 <= NORMAL < REVISIÓN < ALERTA <= 100")
                continue

            guardar_configuracion_umbrales(nuevos_umbrales)

            print("\nUmbrales actualizados correctamente!!")
            print(f"NORMAL:                 0 a {normal - 1}")
            print(f"REVISIÓN:               {normal} a {revision - 1}")
            print(f"REVISIÓN PRIORITARIA:   {revision} a {alerta - 1}")
            print(f"ALERTA:                 {alerta} a 100")

            return nuevos_umbrales

        except ValueError:
            print("\nDebes introducir únicamente números enteros.")
