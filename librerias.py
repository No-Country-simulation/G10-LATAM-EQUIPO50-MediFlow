#LangGraph y generacion de JSON FINAL, Umbrales, Reglas,
#Enrutamiento, Correo listo

#Libreriras usadas:
#Permite trabajar con rutas, archivos y carpetas.
import os

#Permite copiar el archivo original.
import shutil

# Permite obtener fecha y hora para generar
from datetime import datetime

# Facilita trabajar con nombres y extensiones.
from pathlib import Path

#Parte Nueva:
#JSON:
#Nos permitira comprobar posteriormente si Gemini,devuelve JSON valido
import json

#SDK oficial de Gemini
from google import genai

#CARGAR VARIABLES DE ENTORNO DESDE EL ARCHIVO .ENV
#Esto busca el archivo .env y carga sus variables
#en la memoria del sistema. Cargando la API_KEY de Gemini:
#No olvidar
from dotenv import load_dotenv
load_dotenv()

#Parte Nueva: Envio de alertas por correo
#Librerias incluidas en Python para crear y enviar correos
import smtplib
from email.message import EmailMessage

#LangGraph:
from langgraph.graph import StateGraph, START, END
