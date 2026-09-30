#Archivo Principal de MediFlow

#Libreriras usadas:
#En este archivo se importan las funciones de cada modulo
#para mantener el flujo principal separado y mas facil de leer.

from configuracion import *
from umbrales import *
from reglas import *
from archivos import *
from gemini import *
from langgraph_mediflow import *
from almacenamiento import *
from resultados import *
from correo import *

def main():
    """
    Ejecuta toda la Fase de trabajo del backend hasta ahora,
    Flujo de trabajo actual:
        Paso1 Creacion de carpetas
        Paso2 El usuario Seleciona Archivo a subir
        Paso3 Valida la extension del archivo para ver si es permitida o no
        Paso4 Generacion del nombre del archivo subido para evitar dañar el archivo original
        Paso5 Copiamos el archivo nuevo creado
        Paso6 Testeamos Resultados Obtenidos
        PAso7 Integracion de Gemini
        Paso8 Envio de Archivo y Respuesta de interpretacion con GEmini
        Paso9 Gemini(Extraccion de texto para devolver JSON del archivo subido, 
        paso10 LandGraph CLasificacion y Genración de JSON Final
        Paso11 Umbrales, Reglas y Ennrutamiento de manera Modificables Realizado
        Paso12 Enviar Alertas por correo cuando sea distinto de Normal el documento

        Pasos Futuros:
        Frontend
        OCI
    """

    print("\nMEDIFLOW Equipo50 G-10 LATAM")
    print("Seleccion y Guardado de Archivo usando input")
    try:

        #Paso1
        crear_carpetas_base()

        #Paso2: configuración de umbrales al iniciar.
        # Se pregunta al usuario ANTES de analizar el documento para que
        # LangGraph utilice los valores elegidos durante toda la ejecución.
        umbrales = solicitar_configuracion_umbrales()

        #Paso3 CONFIGURAR REGLAS DE LANGGRAPH
        # El usuario decide si desea modificar los pesos.
        #Si responde NO:
        #se utilizan las reglas guardadas.
        
        #Si responde SI:
        #puede modificar los valores.
        
        #Posteriormente LangGraph seleccionara
        #automaticamente las reglas segun la categoria.        
        reglas = (solicitar_configuracion_reglas())

        #Paso4 Seleccion de Archivo
        ruta_archivo = seleccionar_archivo()

        #Validando Extensiones:
        validar_extension(ruta_archivo)
        print("Extension Valida")

        #Paso6 Guardamos Archivo Original para no modificarlo:
        ruta_guardada,nombre_generado = (guardar_archivo_original(ruta_archivo))

        #Paso5 Tipo de Archivo
        tipo_archivo = validar_extension(ruta_archivo)

        #Paso6  Testeando
        mostrar_informacion(ruta_archivo,tipo_archivo,ruta_guardada,nombre_generado)

        #Paso7 obteniendo MIne type archivo para gemini:
        mine_type = obtener_mime_type(ruta_archivo)
        print(f"\nMine Type: {mine_type}")

        print("\nAnalizando con Gemini el Documento")
        #Paso8 Obtencion de Datos Clinicos con Gemini:
        datos_clinicos = (procesar_con_gemini(ruta_archivo,tipo_archivo,nombre_generado))
        
        #Paso9 Mostramos la REspuesta de Gemini(JSON):
        print("\nTesteando El JSON Generado por Gemini: ")
        print(json.dumps(datos_clinicos,indent=4,ensure_ascii=False))

        #Paso10 Ejecutamos LAndGraph:
        print("Estamos Ejecutando LandgGraph!!!")
        resultado_langgraph = (ejecutar_langgraph(datos_clinicos, umbrales,reglas))

        #Paso11 Obtencion de Datos Clinico Finales
        datos_clinicos_finales = (resultado_langgraph["datos_clinicos"])

        #Paso12 Clasificacion Final:
        clasificacion_final = (resultado_langgraph["clasificacion_final"])

        #Obtencion de categoria:
        categoria = (datos_clinicos_finales["clasificacion_documento"]["categoria"])

        #Paso13 Guardamos el archivo JSON FINAL:
        ruta_json = guardar_json_clasificado(datos_clinicos_finales,nombre_generado,clasificacion_final,categoria)
                

        #Envio de correo:
        #Cambio Nuevo: Revision Humana Y Envio De Alerta Por Correo
        #Obtenemos la informacion de riesgo generada por LangGraph:
        riesgo = datos_clinicos_finales.get("clasificacion_riesgo",{})

        #Obtenemos si el documento necesita revision humana:
        requiere_revision_humana = riesgo.get("requiere_revision_humana",False)

        #Solo se enviara el correo cuando LangGraph determine
        #que el documento requiere revision humana.
        if requiere_revision_humana:
            print("\nEl documento requiere REVISION HUMANA.")

            #Obtenemos los datos del paciente:
            paciente = datos_clinicos_finales.get("paciente",{})

            nombre_paciente = paciente.get("nombre_completo","No identificado")

            #Obtenemos los datos del medico:
            medico = datos_clinicos_finales.get("medico",{})

            nombre_medico = medico.get("nombre_completo","No identificado")

            #Obtenemos el tipo de documento:
            tipo_documento = (datos_clinicos_finales.get("documento",{}).get("tipo_documento"))

            if not tipo_documento: 
                tipo_documento = categoria if "categoria" in locals() else "No identificado"

            #Obtenemos los motivos detectados por la validacion
            #de coherencia de LangGraph:
            validacion = datos_clinicos_finales.get("validacion_coherencia",{})

            motivos_revision = validacion.get("motivos",[])

            #Obtenemos el motivo de urgencia detectado por Gemini:
            motivo_urgencia = riesgo.get("motivo_urgencia")

            if motivo_urgencia:
                motivos_revision.append(f"Motivo de urgencia: {motivo_urgencia}")

            #Obtenemos los datos ambiguos:
            datos_ambiguos = riesgo.get("datos_ambiguos",[])

            if datos_ambiguos:
                motivos_revision.append("Datos ambiguos detectados: "+ ", ".join(str(dato) for dato in datos_ambiguos))

            #Obtenemos los datos faltantes:
            datos_faltantes = riesgo.get("datos_faltantes",[])

            if datos_faltantes:
                motivos_revision.append("Datos faltantes detectados: "+ ", ".join(str(dato) for dato in datos_faltantes))

            #Si por alguna razon no existe un motivo,
            #se coloca uno general para informar al responsable:
            if not motivos_revision:
                motivos_revision.append("El documento fue clasificado por LangGraph como un documento que requiere revision humana.")

            #Convertimos todos los motivos en un solo texto
            #para poder enviarlos dentro del correo:
            motivo_correo = "\n".join(f"- {motivo}"
                                      for motivo in motivos_revision)

            #Enviamos el correo de alerta:
            enviar_alerta_correo(
            nombre_paciente = nombre_paciente,
            nombre_medico = nombre_medico,
            tipo_documento = tipo_documento,
            clasificacion_final = clasificacion_final,
            motivo = motivo_correo,
            ruta_json = ruta_json
            )
        else:
            #Si el documento es NORMAL,
            #NO se envia ningun correo.
            print("\nEl documento NO requiere revision humana.")
            print("No se enviara alerta por correo.")
        #
        
        #paso14 Resumen Final:
        #mostrar_resultado_final(resultado_langgraph, ruta_json)

        #print(f"\nArchivo original:" f"\n{ruta_guardada}")
        #print(f"\nJSON clínico:" f"\n{ruta_json}")

        #PARTE FINAL BIEN:
        mostrar_resultado_final_completo(resultado_langgraph,ruta_json,umbrales)

        #Decision Final del Usuario:
        ruta_json_final = gestionar_json_final(ruta_json)
        if ruta_json_final:
            print("\nProceso MediFlow Finalizado Exitosamente!!")
            print("\nJSON clínico final disponible en: ")
            print(ruta_json_final)
        else:
            print("\nPROCESO MEDIFLOW FINALIZADO Borrado Exitosamente")
            print("El JSON clínico final fue eliminado por decisión del usuario!!!\n")
        
        print("\nEl archivo original permanece en Archivos_Originales\n")

        ##
        #Fase de subir un archivo con Gemini y mande un respuesta terminado
        print("\nIntegracion de Gemini, LandGraph y generacion de JSON Final: Guardado correctamente!\n")
        

    except Exception as error:

        print("\nERROR")
        print(f"{error}")

# Ejecutar Codigo:
if __name__ == "__main__":

    main()
