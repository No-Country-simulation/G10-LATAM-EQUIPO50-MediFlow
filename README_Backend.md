# MediFlow Backend Modular

Esta versión separa el backend original de MediFlow en diferentes archivos
según la responsabilidad de cada parte.

## Estructura

Backedn_MediFlow/
* main.py
* librerias.py
* configuracion.py
* umbrales.py
* reglas.py
* archivos.py
* gemini.py
* langgraph_mediflow.py
* almacenamiento.py
* resultados.py
* correo.py


## Función de cada archivo

### librerias.py
Contiene las librerías utilizadas por el proyecto.

### configuracion.py
Contiene las variables compartidas:
- API Key de Gemini.
- Credenciales del correo.
- Cliente de Gemini.
- Modelo de Gemini.
- Rutas de Almacen_Local.
- Extensiones permitidas.

### umbrales.py
Contiene toda la configuración de los umbrales de inconsistencia.

### reglas.py
Contiene las reglas modificables que utiliza LangGraph.

### archivos.py
Contiene la selección, validación, renombrado y guardado del archivo original.

### gemini.py
Contiene la integración con Gemini:
- Subida del archivo.
- Prompt.
- Limpieza del JSON.
- Validación del JSON.
- Procesamiento con Gemini.
- Generación del nombre del JSON clínico.

### langgraph_mediflow.py
Contiene los nodos y el grafo de clasificación.

### almacenamiento.py
Contiene la creación de carpetas de clasificación y el guardado/movimiento
del JSON final.

### resultados.py
Contiene las funciones que muestran al usuario los resultados del análisis.

### correo.py
Contiene la validación de las credenciales y el envío de alertas por correo.

### main.py
Es el punto principal de ejecución. Coordina los módulos.
