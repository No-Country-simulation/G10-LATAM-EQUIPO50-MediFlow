#Envio de alertas por correo

#Libreriras usadas:
from librerias import *

#Configuracion compartida:
from configuracion import *

#Cambio Nuevo:
#Ruta donde se guardara la configuracion de los correos agregados,
#que recibiran las alertas de MediFlow.
Carpeta_Configuracion_Correos = os.path.join(Carpeta_Almacen,"configuracion_correos.json")

def cargar_correos_destino():
    """
    Carga los correos que recibiran las alertas
    desde el archivo configuracion_correos.json.

    Si el archivo no existe, utiliza el correo que
    actualmente se encuentra configurado en EMAIL_DESTINO
    dentro del archivo .env.

    De esta manera mantenemos compatibilidad con la
    configuracion anterior de MediFlow.
    """

    #Verificamos si ya existe el archivo de configuracion
    if os.path.exists(Carpeta_Configuracion_Correos):

        try:

            #Abrimos el archivo de configuracion
            with open(
                Carpeta_Configuracion_Correos,
                "r",
                encoding="utf-8"
            ) as archivo:

                configuracion = json.load(archivo)

            #Obtenemos la lista de correos
            correos = configuracion.get("correos_destino", [])

            #Verificamos que sea una lista
            if isinstance(correos, list):

                return correos

        except Exception as error:

            print("\nError al cargar la configuracion de correos:")
            print(error)


    #CAMBIO NUEVO:
    #Si el archivo todavia no existe,
    #utilizamos EMAIL_DESTINO del archivo .env
    #para crear la configuracion inicial.

    correos_iniciales = []

    if EMAIL_DESTINO:

        #Permitimos colocar varios correos separados por coma
        correos_iniciales = [
            correo.strip()
            for correo in EMAIL_DESTINO.split(",")
            if correo.strip()
        ]


    #CAMBIO NUEVO:
    #Guardamos automaticamente la configuracion inicial
    #en el nuevo archivo JSON.

    if correos_iniciales:

        guardar_correos_destino(correos_iniciales)


    return correos_iniciales

def guardar_correos_destino(correos):
    """
    Guarda la lista de correos que recibiran
    las alertas de MediFlow.
    """

    #Nos aseguramos de que exista la carpeta Almacen_Local
    os.makedirs(Carpeta_Almacen,exist_ok=True)

    #Creamos la estructura que tendra el archivo JSON
    configuracion = {"correos_destino": correos}

    #Guardamos la configuracion
    with open(Carpeta_Configuracion_Correos,"w",encoding="utf-8") as archivo:

        json.dump(configuracion,archivo,ensure_ascii=False,indent=4)


def agregar_correo_destino(correo):
    """
    Agrega un nuevo correo a la lista de destinatarios,
    Si el correo ya existe, no se vuelve a agregar.
    """
    #Quitamos espacios innecesarios
    correo = correo.strip()

    #Verificamos que se haya recibido un correo
    if not correo:
        raise ValueError("El correo no puede estar vacio.")

    #Cargamos los correos actuales
    correos = cargar_correos_destino()

    #Verificamos si el correo ya existe
    if correo in correos:
        return correos

    #Agregamos el nuevo correo
    correos.append(correo)

    #Guardamos la nueva configuracion
    guardar_correos_destino(correos)

    return correos

def eliminar_correo_destino(correo):
    """
    Elimina un correo de la lista de destinatarios.
    """

    #Quitamos espacios innecesarios
    correo = correo.strip()

    #Cargamos los correos actuales
    correos = cargar_correos_destino()


    #Verificamos si el correo existe
    if correo not in correos:

        raise ValueError("El correo indicado no se encuentra configurado.")

    #Eliminamos el correo
    correos.remove(correo)

    #Guardamos la nueva configuracion
    guardar_correos_destino(correos)


    return correos


def validar_configuracion_correo():
    """
    Verifica que las variables necesarias
    estén definidas en el archivo .env.
    """

    if not EMAIL_USUARIO:
        raise ValueError("No se encontro EMAIL_USUARIO en el archivo .env")

    if not EMAIL_PASSWORD:
        raise ValueError("No se encontro EMAIL_PASSWORD en el archivo .env")

    #Los destinatarios ahora se obtienen desde
    #configuracion_correos.json.
    correos_destino = cargar_correos_destino()

    #Verificamos que exista por lo menos
    #un destinatario configurado.
    if not correos_destino:

        raise ValueError("No se encontraron correos destinatarios configurados.")

    

def enviar_alerta_correo(nombre_paciente,nombre_medico,tipo_documento,clasificacion_final,motivo,ruta_json):
    """
    Envía un correo de alerta cuando MediFlow determina
    que el documento requiere revision humana.

    Parametros:
        nombre_paciente:
            Nombre del paciente obtenido por Gemini.

        nombre_medico:
            Nombre del medico obtenido por Gemini.

        tipo_documento:
            Tipo de documento analizado.

        clasificacion_final:
            Clasificacion final determinada por LangGraph.

        motivo:
            Motivos por los cuales el documento requiere
            revision humana.
    """

    #Primero verificamos que exista la configuracion para enviar el correo
    validar_configuracion_correo()

    #Obtenemos todos los correos configurados
    #para recibir las alertas.
    destinatarios = cargar_correos_destino()

    #Creamos el mensaje a enviar por correo
    mensaje = EmailMessage()

    #Ponemos Asunto al correo:
    mensaje["Subject"] = ("ALERTA MEDIFLOW - Requiere Revision Humana")

    #Cuenta de correo desde la cual se enviara:
    mensaje["From"] = EMAIL_USUARIO

    #Los destinatarios ahora se obtienen
    #desde configuracion_correos.json.
    mensaje["To"] = destinatarios

    #Medico o responsable del area que recibira la alerta por correo
    #Convertir la cadena en una lista de correos
    #destinatarios = [correo.strip() for correo in EMAIL_DESTINO.split(",")]

    #Agregar destinatarios
    #mensaje["To"] = destinatarios

    #Agregamos el mensaje del correo
    cuerpo = f"""ALERTA MEDIFLOW

Se ha detectado un documento clinico que requiere
REVISION HUMANA por parte del personal encargado.

Datos del Documento:

Paciente:
{nombre_paciente}

Medico:
{nombre_medico}

Tipo de Documento:
{tipo_documento}

Clasificacion Final:
{clasificacion_final}

Motivos de Revision:
{motivo}

Ruta donde se guardo el JSON Final:
{ruta_json}

Por favor, revise el documento en el sistema MediFlow.

Este mensaje fue generado automaticamente
por el sistema Inteligente de MediFlow.
"""

    mensaje.set_content(cuerpo)

    #Hacemos la conexion a los servidores del correo:
    try:

        #Testeando:
        print("\nConectando con el servidor de correo, espere")

        #Para usar Gmail se utiliza:
        #SMTP:
        #smtp.gmail.com
        #Puerto SSL:
        #465
        #SMTP_SSL crea una conexión cifrada.

        with smtplib.SMTP_SSL("smtp.gmail.com",465) as servidor:

            #Iniciamos Sesion
            servidor.login(EMAIL_USUARIO,EMAIL_PASSWORD)

            #Enviamos el mensaje creado
            servidor.send_message(mensaje)

        #Verificamos que se haya enviado el correo:
        print("\nAlerta por correo enviada Exitosamente!!!")

        #Mostramos todos los destinatarios utilizados
        #para enviar la alerta.
        print(f"Destinatarios: {', '.join(destinatarios)}")

        #Vemos a quien le mandamos el correo:
        #print(f"Destinatario: {EMAIL_DESTINO}")

        return True

    #Si no se pudo enviar manda alerta:
    except smtplib.SMTPAuthenticationError:

        print("\nError de autenticacion no se pudo enviar el correo")
        print("\nPosibles motivos")
        print("\nVerifica:")
        print("El correo de Gmail este bien configurado")
        print("La contraseña del correo que hara el envio")
        print("La verificación en dos pasos este configurada")
        print("Y que se este utilizando una contraseña de aplicacion")

        return False

    except Exception as error:

        print("\nError al enviar el correo:")
        print(error)

        return False
