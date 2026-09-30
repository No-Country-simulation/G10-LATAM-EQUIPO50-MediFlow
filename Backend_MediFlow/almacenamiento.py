#Guardado y manejo del JSON Final

#Libreriras usadas:
from librerias import *

#Configuracion compartida:
from configuracion import *

#Funcion para generar el nombre del JSON clinico:
#Esta funcion se encuentra en gemini.py y se utiliza aqui
#para generar el nombre del JSON Final.
from gemini import generar_nombre_json_clinico

def convertir_categoria_a_nombre_carpeta(categoria):

    """
    Convierte la categoría documento
    en un nombre adecuado para una carpeta
    """
    categorias = {

        "Receta Médica":"Receta_Medica",

        "Informe de Estudio de Diagnóstico por Imágenes/Laboratorio":"Informe_Estudio_Diagnostico",

        "Orden de Solicitud de Procedimiento":"Orden_Solicitud_Procedimiento",

        "Epicrisis / Informe de Alta":"Epicrisis_Informe_Alta",

        "Certificado Médico":"Certificado_Medico",

        "Otro":"Otro Tipo de Documento"
    }

    return categorias.get(categoria,"Otro")

def crear_carpeta_clasificacion(clasificacion,categoria):

    """
    Crea la carpeta final donde se almacenará
    el JSON Final, Ejemplo:

    NORMAL:Datos_Clinicos/Normal/Receta_Medica/

    ALERTA:Datos_Clinicos/Alertas/Urgente/Receta_Medica/
    """

    categoria_carpeta = (convertir_categoria_a_nombre_carpeta(categoria))

    if clasificacion == "normal":
        carpeta = os.path.join(Carpeta_Datos_Clinicos,"Normal",categoria_carpeta)
    
    else:
        carpeta = os.path.join(Carpeta_Datos_Clinicos,"Alertas",clasificacion.capitalize(),categoria_carpeta)

    os.makedirs(carpeta,exist_ok=True)

    return carpeta #Regresa la ruta de la carpeta creada

def guardar_json_clasificado(datos_clinicos,nombre_archivo,clasificacion,categoria):
    """
    Guarda el JSON final dependiendo
    de la clasificación de LangGraph.
    """
    carpeta = crear_carpeta_clasificacion(clasificacion,categoria)

    ruta_json = os.path.join(carpeta,generar_nombre_json_clinico(nombre_archivo))

    with open(ruta_json,"w",encoding="utf-8") as archivo:
        json.dump(datos_clinicos,archivo,ensure_ascii=False,indent=4)

    print("\nJSON clasificado guardado en: ")
    print(ruta_json)

    return ruta_json

def gestionar_json_final(ruta_json):
    """
    Permite al usuario decidir qué hacer con el JSON final:

        1.- Conservarlo donde MediFlow lo guardó.
        2.- Guardarlo en otra ubicación.
        3.- Eliminarlo.

    El archivo original subido por el usuario NO se elimina,
    Esta función solamente administra el JSON clínico final.
    """

    while True:
        print("\n¿QUÉ DESEAS HACER CON EL JSON FINAL?")

        print("\n1 - Conservarlo donde MediFlow lo guardó")
        print("2 - Guardarlo en otra ubicación")
        print("3 - Eliminar el JSON final")

        opcion = input("\nSelecciona una opción: (1 /2 /3): ").strip()

        #Opcion 1
        if opcion == "1":

            print("\nHas Escogido Conservar el JSON FINAL.")
            print("\nEl Agente MediFlow mantendrá el archivo en: ")
            print(f"{ruta_json}")

            return ruta_json

        #Opcion 2
        elif opcion == "2":
            print("\nIntroduce la carpeta donde deseas guardar el JSON Final generado")
            print("También puedes arrastrar la carpeta desde el Finder hasta la Terminal.")

            nueva_carpeta = input("\nNueva ubicación: ").strip()
            if not nueva_carpeta:

                print("\nNo se introdujo ninguna ubicación.")
                continue

            # Eliminar comillas que pueda agregar la mac pedos con el macOS
            nueva_carpeta = nueva_carpeta.strip("'\"")

            # Expandir ~
            nueva_carpeta = os.path.expanduser(nueva_carpeta)

            # Convertir a ruta absoluta
            nueva_carpeta = os.path.abspath(nueva_carpeta)

            # Comprobar que la carpeta exista
            if not os.path.isdir(nueva_carpeta):
                respuesta = input("\nLa carpeta no existe. ¿Deseas crearla? (Responde: si/no): ").strip().lower()

                if respuesta in {"s", "si", "sí", "Si", "Sí"}:
                    try:

                        os.makedirs(nueva_carpeta,exist_ok=True)

                        print("\nCarpeta creada correctamente.")

                    except OSError as error:

                        print(f"\nNo fue posible crear " f"la carpeta: {error}")
                        continue

                else:

                    print("\nNo se modificará la ubicación.")
                    continue

            # Nombre original del JSON
            nombre_json = os.path.basename(ruta_json)

            nueva_ruta = os.path.join(nueva_carpeta,nombre_json)

            # Si ya existe por que somos pendejos, preguntar
            if os.path.exists(nueva_ruta):

                respuesta = input("\nYa existe un archivo con ese nombre ¿Deseas reemplazarlo? (Responde: si/no): ").strip().lower()

                if respuesta not in {"s","si","sí", "Si", "Sí"}:
                    print("\nOperación cancelada!!!")
                    continue

                try:
                    os.remove(nueva_ruta)

                except OSError as error:
                    print(f"\nNo fue posible reemplazar " f"el archivo: {error}")
                    continue

            try:

                # Mover el JSON desde la ubicación
                # automática hasta la nueva ubicación.
                shutil.move(ruta_json,nueva_ruta)

                print("\nJSON Final Guardado en la Nueva Ubicacion: ")
                print(f"{nueva_ruta}")

                return nueva_ruta

            except OSError as error:

                print(f"\nNo fue posible mover " f"el JSON: {error}")
                continue

        #Opcion 3
        elif opcion == "3":
            respuesta = input("\n¿ESTÁS SEGURO de eliminar el JSON final? " "(Responde: si/no): ").strip().lower()

            if respuesta in {"s","si","sí","Si","Sí"}:

                try:

                    os.remove(ruta_json)
                    print("\nJSON Final ELIMINADO CORRECTAMENTE!!!")
                    print("Prohibido Llorar!!!")

                    print("\nNota Mega Importante:")
                    print("El archivo original subido por el usuario permanece en Archivos_Originales, Ponte Verga!")

                    return None

                except OSError as error:

                    print(f"\nNo fue posible eliminar " f"el JSON: {error}")
                    return ruta_json

            else:
                print("\nEl JSON NO será eliminado.")
                return ruta_json

        #Para los chistosos!!!! Por no Decir Pendejos!
        else:

            print("\nOpción no válida!!!")
            print("Debes seleccionar 1, 2 o 3!!!")
            print("Que la verga NO LEES LAS INSTRUCCIONES??!!")
