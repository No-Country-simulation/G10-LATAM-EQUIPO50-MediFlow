
#Archivo Principal de FastAPI para MediFlow

#Librerias usadas:
#Permite crear la aplicacion y los endpoints de FastAPI.
from fastapi import FastAPI, UploadFile, File, HTTPException

#Permite trabajar con rutas y extensiones de archivos.
from pathlib import Path

#Permite copiar archivos.
import shutil


#Creamos la aplicacion FastAPI de MediFlow.
app = FastAPI(
    title="MediFlow API",
    description="API para el procesamiento de documentos clinicos de MediFlow.",
    version="1.0.0"
)


#Endpoint principal para comprobar que FastAPI
#y MediFlow estan funcionando.
@app.get("/")
def inicio():

    return {
        "mensaje": "MediFlow API funcionando correctamente.",
        "estado": "activo"
    }


#Endpoint para comprobar el estado de la API.
@app.get("/estado")
def estado():

    return {
        "proyecto": "MediFlow",
        "estado": "activo"
    }


#Endpoint para recibir un archivo desde FastAPI.
@app.post("/procesar")
async def procesar_archivo(
    archivo: UploadFile = File(...)
):

    #Obtenemos el nombre del archivo recibido.
    nombre_archivo = archivo.filename

    #Comprobamos que se haya recibido un archivo.
    if not nombre_archivo:

        raise HTTPException(
            status_code=400,
            detail="No se recibio ningun archivo."
        )


    #Obtenemos la extension del archivo.
    extension = Path(nombre_archivo).suffix.lower()


    #Extensiones permitidas por MediFlow.
    extensiones_permitidas = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tiff",
        ".webp",
        ".pdf",
        ".json"
    }


    #Comprobamos que la extension sea permitida.
    if extension not in extensiones_permitidas:

        raise HTTPException(
            status_code=400,
            detail="El formato del archivo no es compatible con MediFlow."
        )


    #Obtenemos la carpeta principal del proyecto.
    #app_fastapi.py se encuentra dentro de Frontend,
    #por lo que debemos subir un nivel para llegar
    #a la carpeta principal de MediFlow.
    carpeta_base = Path(__file__).resolve().parent.parent


    #La carpeta Almacen_Local se encuentra fuera
    #de Backend_MediFlow y Frontend.
    carpeta_almacen = (carpeta_base/ "Almacen_Local")


    #Carpeta temporal para los archivos recibidos
    #mediante FastAPI.
    carpeta_temporal = (carpeta_almacen/ "Archivos_Temporales")


    #Creamos la carpeta si no existe.
    carpeta_temporal.mkdir(parents=True,exist_ok=True)


    #Creamos la ruta completa donde se guardara
    #el archivo recibido.
    ruta_archivo = (carpeta_temporal/ nombre_archivo)


    #Guardamos el archivo recibido por FastAPI.
    try:

        with open(ruta_archivo,"wb") as archivo_destino:

            shutil.copyfileobj(archivo.file,archivo_destino)

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"No fue posible guardar el archivo: {error}"
        )


    #Devolvemos informacion para comprobar
    #que FastAPI recibio correctamente el archivo.
    return {
        "mensaje": "Archivo recibido correctamente.",
        "nombre_archivo": nombre_archivo,
        "extension": extension,
        "ruta_archivo": str(ruta_archivo),
        "estado": "recibido"
    }
