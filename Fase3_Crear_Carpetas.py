import os


#Ruta donde se guardara nuestro archivo de forma actual:
Carpeta_Base = os.path.dirname(os.path.abspath(__file__))

#Procedemos a ponerle nombre a las carpetas que se crearan para identificar los archivos de forma ordenada
#Carpeta donde se guardarán las demas carpetas para tener un orden
Carpeta_Almacenamiento = os.path.join(Carpeta_Base,"Almacen_Local")

#Carpeta para guardar los archivos originales seleccionados
Carpeta_Archivos_Originales = os.path.join(Carpeta_Base,"Archivos_Originales") 

#Carpeta para guardar las imagenes procesadas en caso que el archivo seleccionado sea una imagen
Carpeta_Imagenes_Procesadas = os.path.join(Carpeta_Base,"Imagenes_Procesadas")

#Carpeta para guardar el archivo json de los documentos subidos por el usuario
Carpeta_Datos_Clinicos = os.path.join(Carpeta_Base,"Datos_Clinicos")

#Creacion de Carpetas:
def crear_carpetas():
    os.makedirs(Carpeta_Almacenamiento,exist_ok = True)

    os.makedirs(Carpeta_Archivos_Originales, exist_ok = True)

    os.makedirs(Carpeta_Imagenes_Procesadas, exist_ok = True)

    os.makedirs(Carpeta_Datos_Clinicos, exist_ok = True)




def main():

    print("\nMediflow_Equipo_50_Latam_G-10_Parte3")
    print("Creacion de Carpetas")

    #Llamando la funcion crear carpetas:
    crear_carpetas()

    #Verificando que se crearon
    print("\nCarpetas Creadas Correctamente o Verificadas Correctamente")

    print("\nCarpeta De Archivos Originales")
    #Ruta donde esta guardada la carpeta creada
    print(os.path.abspath(Carpeta_Archivos_Originales))

    print("\nCarpeta De Imagenes Procesadas")
    #Ruta donde esta guardada la carpeta creada
    print(os.path.abspath(Carpeta_Imagenes_Procesadas))

    print("\nCarpeta De Datos Clinicos")
    #Ruta donde esta guardada la carpeta creada
    print(os.path.abspath(Carpeta_Datos_Clinicos))

if __name__ == "__main__":
    main()

