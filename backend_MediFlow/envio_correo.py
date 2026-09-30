#Codigo para enviar alertas por correo

#Librerias
#Permite cargar las variables almacenadas en el archivo .env
from dotenv import load_dotenv

#Permite acceder a las variables de entorno
import os

#Librerías incluidas en Python para crear y enviar correos
import smtplib
from email.message import EmailMessage

#Cargamos las  Variables del archivo .env
#Y busca automaticamente el archivo .env
#Y carga sus variables en el entorno de Python:
load_dotenv()

#Obtencion de las Crendenciales:
EMAIL_USUARIO  = os.getenv("EMAIL_USUARIO")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_DESTINO  = os.getenv("EMAIL_DESTINO")

#Funcion para asegurarse qu elas credenciales existen:
def validar_configuracion_correo():
    """
    Verifica que las variables necesarias
    estén definidas en el archivo .env.
    """

    if not EMAIL_USUARIO:
        raise ValueError("No se encontro Email_Usuario en el archivo .env")

    if not EMAIL_PASSWORD:
        raise ValueError("No se encontró Email_Password en el archivo .env")

    if not EMAIL_DESTINO:
        raise ValueError("No se encontró Email_Destino en el archivo .env")



#Funcion Para Enviar el Correo
def enviar_alerta_correo(paciente_id,tipo_documento,nivel_urgencia,motivo):
    """
    Envía un correo de alerta cuando el Asistenete Inteligente
    detecta que un documento requiere atencion Humana

    Parametros:
        paciente_id:
            Identificador del paciente

        tipo_documento:
            Tipo de documento analizado

        nivel_urgencia:
            Nivel detectado por el sistema

        motivo:
            Motivo de la alerta
    """
    #Primero verificamos que exista la configuracion para enviar el correo
    #A la dependencia encargada de revisar los documentos
    #En caso que sea necesario
    validar_configuracion_correo()

    #Creamos el mensaje a enviar por correo
    mensaje = EmailMessage()

    #Ponemos Asunto al correo:
    mensaje["Subject"] = ("ALERTA MEDIFLOW - Documento urgente!!!")

    #Cuenta de correo desde la cual se enviara:
    mensaje["From"] = EMAIL_USUARIO


    #Medico o responsable del area que recibira la alerta por correo
    # Convertir la cadena en una lista de correos
    destinatarios = [correo.strip()for correo in EMAIL_DESTINO.split(",")]

    # Agregar destinatarios
    mensaje["To"] = destinatarios

    #mensaje["To"] = EMAIL_DESTINO

    #Agregamos el mensaje del correo
    cuerpo = f"""ALERTA MEDIFLOW
Se ha detectado un documento clinico que requiere
atencion inmediata y prioritaria por el personal del area del hospital,

Datos del Documento:
Paciente:
{paciente_id}

Tipo de Documento:
{tipo_documento}

Nivel de Urgencia:
{nivel_urgencia}

Motivo:
{motivo}

Por favor, revise el documento en el sistema MediFlow

Este mensaje fue generado automaticamente
por el sistema Inteligente de MediFlow.
"""
    mensaje.set_content(cuerpo)


    #Hacemos la conexion a los serbidores del correo:
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

        print("Error de autenticacion no se pudo enviar el correo")
        print("\nPosibles motivos")
        print("\nVerifica:")
        print("El correo de Gmail este bien usuario y destino")
        print("La contraseña del correo que hara el envio")
        print("\nQue la verificación en dos pasos, este configurada en la cuenta\n")


        return False


    except Exception as error:

        print("\nError al enviar el correo:")
        print(error)


        return False

#Probando envio de correo:
if __name__ == "__main__":

    print("\nPrueba de Envio de Correo del Asistente Inteligente MediFlow,")
    print("Equipo50_G-10_LATAM")

    #Datos simulados:
    #Ya que Posteriormente estos datos vendran
    #directamente del JSON generado por Gemini
    #Por ahora solo es una prueba para integrarlo a Futuro

    paciente_id = "Paciente_001"

    tipo_documento = "Laboratorio"

    nivel_urgencia = "URGENTE!!!"

    motivo = ("El analisis del documento por medio de la IA MediFlow; Indica un resultado que requiere revisión prioritaria por una persona")

    # Enviar correo
    enviar_alerta_correo(
        paciente_id    = paciente_id,
        tipo_documento = tipo_documento,
        nivel_urgencia = nivel_urgencia,
        motivo         = motivo
    )

