# Dockerfile de MediFlow
# Version de Python utilizada: 3.11.13
# Se utiliza la imagen oficial de Python 3.11-slim
FROM python:3.11-slim

#Configuracion de Python:
# Evita que Python genere archivos .pyc
# y permite visualizar los mensajes inmediatamente.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

#Carpeta de trabajo
WORKDIR /app

#Instalacion de dependencias:
# Se copia solamente requirements.txt para instalar
# las librerias necesarias para la nueva arquitectura.
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

#Copiar archivos del proyecto:
#Se copian directamente Backend_MediFlow y Frontend,
#Streamlit se comunicara directamente con el backend.
COPY Backend_MediFlow ./Backend_MediFlow
COPY Frontend ./Frontend
COPY cloud ./cloud

# Crear carpetas de almacenamiento
# Se crean las carpetas utilizadas por MediFlow
# dentro del contenedor.
RUN mkdir -p Almacen_Local/Archivos_Temporales \
    Almacen_Local/Archivos_Originales \
    Almacen_Local/Datos_Clinicos

#Puerto utilizado por Streamlit
EXPOSE 8501

#Ejecutar Streamlit,
# Cambio Nuevo:
# Streamlit es ahora la aplicacion principal.
# No se utiliza FastAPI ni Uvicorn.
CMD ["streamlit", "run", "Frontend/app_streamlit_backend_directo.py", "--server.address=0.0.0.0", "--server.port=8501"]