#Envio de alertas por correo

#Libreriras usadas:
from librerias import *

#Configuracion compartida:
from configuracion import *

def validar_configuracion_correo():
    """
    Verifica que las variables necesarias
    estén definidas en el archivo .env.
    """

    if not EMAIL_USUARIO:
        raise ValueError("No se encontro EMAIL_USUARIO en el archivo .env")

    if not EMAIL_PASSWORD:
        raise ValueError("No se encontro EMAIL_PASSWORD en el archivo .env")

    if not EMAIL_DESTINO:
        raise ValueError("No se encontro EMAIL_DESTINO en el archivo .env")

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

    #Creamos el mensaje a enviar por correo
    mensaje = EmailMessage()

    #Ponemos Asunto al correo:
    mensaje["Subject"] = ("ALERTA MEDIFLOW - Requiere Revision Humana")

    #Cuenta de correo desde la cual se enviara:
    mensaje["From"] = EMAIL_USUARIO

    #Medico o responsable del area que recibira la alerta por correo
    #Convertir la cadena en una lista de correos
    destinatarios = [
        correo.strip()
        for correo in EMAIL_DESTINO.split(",")
    ]

    #Agregar destinatarios
    mensaje["To"] = destinatarios

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

        #Vemos a quien le mandamos el correo:
        print(f"Destinatario: {EMAIL_DESTINO}")

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
