"""
validacion_clinica.py - Capa de validacion deterministica para MediFlow.

Por que existe:
  Hoy la unica fuente de verdad es Gemini. Si el modelo no detecta algo,
  el sistema no lo detecta. Esta capa revisa, con reglas y catalogos, lo
  que el modelo extrajo: fechas, codigos CIE-10, dosis, valores criticos
  de laboratorio, formato de matricula y documentos con doble proposito.

  No llama a ninguna API: es codigo determinista, auditable y gratis.

Como se usa dentro de LangGraph (nodo nuevo, despues de validar coherencia):

    from validacion_clinica import nodo_validacion_clinica, decidir_destino
    grafo.add_node("validacion_clinica", nodo_validacion_clinica)

Como se prueba SIN gastar cuota de Gemini (usa los JSON ya cacheados):

    python validacion_clinica.py --cache evaluacion_resultados/cache \
                                 --ground-truth casos/referencia/ground_truth.jsonl
"""
import argparse
import datetime as dt
import json
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CATALOGOS = RAIZ / "casos" / "referencia" / "catalogos"

# PESOS DE CADA CONFLICTO (configurables, igual que las reglas existentes)
PESOS_DEFECTO = {
    "fecha_emision_futura": 40,
    "receta_vencida": 30,
    "cie10_inexistente": 30,
    "cie10_no_corresponde_diagnostico": 35,
    "dosis_fuera_de_rango": 60,
    "medicamento_sin_posologia": 15,
    "matricula_ausente": 40,
    "matricula_formato_invalido": 20,
    "documento_multiple": 35,
    "paciente_sin_identificacion": 25,
}
# Conflictos que por si solos obligan revision humana, sin importar el umbral
CONFLICTOS_CRITICOS = {"dosis_fuera_de_rango", "matricula_ausente",
                       "cie10_no_corresponde_diagnostico", "documento_multiple"}

# UTILIDADES
def normalizar(t):
    if t is None:
        return ""
    t = str(t).strip().lower()
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", t)

def a_fecha(texto):
    """Acepta 08/09/2026, 2026-09-08, 8-9-2026. Devuelve date o None."""
    if not texto:
        return None
    texto = str(texto).strip()
    for patron in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return dt.datetime.strptime(texto, patron).date()
        except ValueError:
            continue
    return None

def a_miligramos(texto):
    """'500 mg' -> 500.0 | '1 g' -> 1000.0 | '100 mcg' -> 0.1"""
    if not texto:
        return None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(mcg|mg|g|ug)", normalizar(texto))
    if not m:
        return None
    valor = float(m.group(1).replace(",", "."))
    return {"mcg": valor / 1000, "ug": valor / 1000, "mg": valor, "g": valor * 1000}[m.group(2)]

def horas_entre_tomas(*textos):
    """Busca 'cada 8 horas', 'c/12 h', 'cada 24h', 'diaria' en varios campos."""
    for t in textos:
        n = normalizar(t)
        if not n:
            continue
        m = re.search(r"(?:cada|c/)\s*(\d+)\s*(?:h|hora)", n)
        if m:
            return int(m.group(1))
        if "diari" in n or "al dia" in n or "24 h" in n:
            return 24
    return None

def unidades_por_toma(*textos):
    """'Tomar 2 tabletas cada 8 horas' -> 2"""
    for t in textos:
        n = normalizar(t)
        m = re.search(r"(\d+)\s*(?:tableta|capsula|comprimido|ampolla|jeringa|inhalacion|gota|sobre|dosis)", n)
        if m:
            return int(m.group(1))
    return None

def numero(texto):
    if texto is None:
        return None
    m = re.search(r"-?\d+(?:[.,]\d+)?", str(texto))
    return float(m.group(0).replace(",", ".")) if m else None

def cargar_catalogos(ruta=CATALOGOS):
    ruta = Path(ruta)
    def leer(nombre, defecto):
        f = ruta / nombre
        return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else defecto
    return {
        "cie10": leer("cie10_subconjunto.json", {}),
        "medicamentos": leer("medicamentos.json", {}),
        "parametros": leer("reglas_y_parametros.json", {}),
    }

# --------------------------------------------------------------------------
# VALIDACIONES
# --------------------------------------------------------------------------
def validar_fechas(datos, categoria, parametros, hoy):
    c = []
    fecha = a_fecha((datos.get("documento") or {}).get("fecha_documento"))
    if not fecha:
        return c
    if fecha > hoy:
        c.append(("fecha_emision_futura",
                  f"La fecha del documento ({fecha:%d/%m/%Y}) es posterior a hoy ({hoy:%d/%m/%Y})."))
    vigencia = parametros.get("vigencia_receta_dias", 30)
    if categoria == "Receta Médica" and (hoy - fecha).days > vigencia:
        c.append(("receta_vencida",
                  f"La receta tiene {(hoy - fecha).days} dias; la vigencia es de {vigencia}."))
    return c

def validar_cie10(datos, cat_cie10):
    c = []
    if not cat_cie10:
        return c
    for dx in datos.get("diagnosticos") or []:
        if not isinstance(dx, dict):
            continue
        codigo = (dx.get("codigo") or "").strip().upper()
        m = re.search(r"[A-Z]\d{2}(?:\.\d{1,2})?", codigo)
        codigo = m.group(0) if m else codigo
        nombre = dx.get("nombre") or ""
        if not codigo:
            continue
        entrada = cat_cie10.get(codigo)
        if entrada is None:
            c.append(("cie10_inexistente", f"El codigo {codigo} no existe en el catalogo CIE-10."))
            continue
        if not nombre:
            continue
        # Correspondencia: palabras significativas compartidas entre el texto y el catalogo
        descripcion = entrada["descripcion"] if isinstance(entrada, dict) else str(entrada)
        pal_doc = {p for p in normalizar(nombre).split() if len(p) > 4}
        pal_cat = {p for p in normalizar(descripcion).split() if len(p) > 4}
        if pal_doc and pal_cat and not (pal_doc & pal_cat):
            c.append(("cie10_no_corresponde_diagnostico",
                      f"El codigo {codigo} ({descripcion}) no corresponde al diagnostico escrito: '{nombre}'."))
    return c

def validar_medicamentos(datos, cat_medicamentos):
    c = []
    for med in datos.get("medicamentos") or []:
        if not isinstance(med, dict):
            continue
        nombre = med.get("nombre") or med.get("principio_activo") or ""
        if not nombre:
            continue
        clave = next((k for k in cat_medicamentos
                      if normalizar(k).split()[0] == normalizar(nombre).split()[0]), None)
        horas = horas_entre_tomas(med.get("frecuencia"), med.get("dosis"), med.get("indicaciones"))
        unidades = unidades_por_toma(med.get("dosis"), med.get("cantidad")) or numero(med.get("unidad_dosis")) or 1
        mg_unidad = a_miligramos(med.get("concentracion") or med.get("presentacion"))
        if clave and mg_unidad is None:
            mg_unidad = cat_medicamentos[clave].get("mg_por_unidad")
        if not horas or mg_unidad is None:
            c.append(("medicamento_sin_posologia",
                      f"No se pudo verificar la dosis de {nombre} (falta concentracion o frecuencia)."))
            continue
        diaria = mg_unidad * unidades * 24 / horas
        maximo = (cat_medicamentos.get(clave) or {}).get("dosis_maxima_diaria_mg")
        if maximo and diaria > maximo * 1.01:
            c.append(("dosis_fuera_de_rango",
                      f"{nombre}: {diaria:.0f} mg/dia supera el maximo de {maximo:.0f} mg/dia."))
    return c

def validar_valores_criticos(datos, parametros):
    """Un valor critico de laboratorio obliga urgencia, aunque Gemini no la marque."""
    criticos, hallazgos = parametros.get("valores_criticos", {}), []
    for estudio in datos.get("estudios") or []:
        if not isinstance(estudio, dict):
            continue
        
        # si el estudio viene marcado como ALTO o BAJO y el valor 
        # supera el doble del límite superior del rango de referencia, es hallazgo crítico.
        nombre = normalizar(f"{estudio.get('nombre')} {estudio.get('tipo')} " f"{estudio.get('interpretacion') or estudio.get('interpretación') or ''}")
        valor = numero(estudio.get("resultado"))
        referencia = estudio.get("rango_referencia") or estudio.get("rango_de_referencia")
        
        if valor is None:
            continue
        for analito, limites in criticos.items():
            if normalizar(analito) not in nombre:
                continue
            mayor, menor = limites.get("mayor_que"), limites.get("menor_que")
            if (mayor is not None and valor > mayor) or (menor is not None and valor < menor):
                hallazgos.append(f"{estudio.get('nombre')} = {valor} {estudio.get('unidades') or ''} "
                                 f"(rango critico).")
    return hallazgos

def validar_identidades(datos, categoria, parametros):
    c = []
    medico = datos.get("medico") or {}
    matricula = medico.get("cedula_profesional") or medico.get("matricula")
    patron = parametros.get("regex_matricula", r"^RM \d{5}-\d{2}$")
    # Se aceptan tambien los formatos de matricula argentinos del enunciado
    patron_amplio = f"({patron})|(^(MN|MP)\\s*\\d{{4,6}}$)"
    if not matricula:
        c.append(("matricula_ausente", "El documento no indica la matricula o registro del profesional."))
    elif not re.match(patron_amplio, str(matricula).strip(), re.IGNORECASE):
        c.append(("matricula_formato_invalido",
                  f"La matricula '{matricula}' no cumple el formato esperado."))
    paciente = datos.get("paciente") or {}
    if categoria != "Otro" and not (paciente.get("id_paciente") or paciente.get("curp")):
        c.append(("paciente_sin_identificacion", "No se identifico el documento del paciente."))
    return c

def validar_documento_multiple(datos, categoria):
    """Una receta que ademas solicita estudios tiene dos destinos: no es automatizable."""
    if categoria != "Receta Médica":
        return []
    solicitudes = [e for e in (datos.get("estudios") or [])
                   if isinstance(e, dict) and not e.get("resultado")]
    solicitudes += (datos.get("tratamiento") or {}).get("procedimientos") or []
    if solicitudes and datos.get("medicamentos"):
        return [("documento_multiple",
                 "El documento contiene prescripcion y solicitud de estudios: requiere doble enrutamiento.")]
    return []

# API PRINCIPAL
def validar_clinicamente(datos, catalogos=None, pesos=None, hoy=None):
    catalogos = catalogos or cargar_catalogos()
    pesos = pesos or PESOS_DEFECTO
    parametros = catalogos["parametros"]
    hoy = hoy or dt.date.today()
    categoria = (datos.get("clasificacion_documento") or {}).get("categoria", "Otro")

    conflictos = []
    conflictos += validar_fechas(datos, categoria, parametros, hoy)
    conflictos += validar_cie10(datos, catalogos["cie10"])
    conflictos += validar_medicamentos(datos, catalogos["medicamentos"])
    conflictos += validar_identidades(datos, categoria, parametros)
    conflictos += validar_documento_multiple(datos, categoria)

    hallazgos_criticos = validar_valores_criticos(datos, parametros)

    puntaje = min(100, sum(pesos.get(tipo, 10) for tipo, _ in conflictos))
    criticos = [t for t, _ in conflictos if t in CONFLICTOS_CRITICOS]

    return {
        "conflictos": [{"tipo": t, "detalle": d} for t, d in conflictos],
        "puntaje_clinico": puntaje,
        "conflictos_criticos": criticos,
        "hallazgos_criticos": hallazgos_criticos,
        "urgencia_por_hallazgo_critico": bool(hallazgos_criticos),
        "requiere_revision_humana": bool(criticos) or puntaje >= 30,
    }

def nodo_validacion_clinica(estado):
    """Nodo para LangGraph. Va DESPUES de validar_coherencia_documental."""
    datos = estado["datos_clinicos"]
    resultado = validar_clinicamente(datos, estado.get("catalogos"), estado.get("pesos_clinicos"))
    datos["validacion_clinica"] = resultado

    # Un hallazgo critico de laboratorio obliga urgencia aunque Gemini no la marque
    if resultado["urgencia_por_hallazgo_critico"]:
        estado["clasificacion_final"] = "urgente"
        riesgo = datos.setdefault("clasificacion_riesgo", {})
        riesgo["urgente"] = True
        riesgo["motivo_urgencia"] = "; ".join(resultado["hallazgos_criticos"])
    elif resultado["requiere_revision_humana"] and estado.get("clasificacion_final") != "urgente":
        estado["clasificacion_final"] = "revision_clinica"

    estado["datos_clinicos"] = datos
    return estado

def decidir_destino(datos, clasificacion_final):
    """Traduce la clasificacion a una de las cinco colas que pide el enunciado."""
    destinos = {
        "Receta Médica": "farmacia_hospitalaria",
        "Orden de Solicitud de Procedimiento": "auditoria_autorizaciones",
        "Informe de Estudio de Diagnóstico por Imágenes/Laboratorio": "historia_clinica_electronica",
        "Epicrisis / Informe de Alta": "historia_clinica_electronica",
        "Certificado Médico": "historia_clinica_electronica",
        "Otro": "revision_humana",
    }
    categoria = (datos.get("clasificacion_documento") or {}).get("categoria", "Otro")
    if clasificacion_final == "urgente":
        return "urgencias_medicas"
    if clasificacion_final != "normal":
        return "revision_humana"
    return destinos.get(categoria, "historia_clinica_electronica")

# Prueba ofline sobre la carpeta CACHE (no gasta cuota de Gemini)
def main():
    ap = argparse.ArgumentParser(description="Prueba la validacion clinica sobre los JSON ya cacheados")
    ap.add_argument("--cache", default="evaluacion_resultados/cache")
    ap.add_argument("--ground-truth", default="casos/referencia/ground_truth.jsonl")
    ap.add_argument("--catalogos", default=str(CATALOGOS))
    ap.add_argument("--hoy", default=None, help="fecha de referencia AAAA-MM-DD")
    a = ap.parse_args()

    catalogos = cargar_catalogos(a.catalogos)
    hoy = dt.date.fromisoformat(a.hoy) if a.hoy else dt.date.today()
    verdades = {}
    gt = Path(a.ground_truth)
    if gt.is_file():
        verdades = {json.loads(l)["id"]: json.loads(l) for l in gt.open(encoding="utf-8")}

    archivos = sorted(Path(a.cache).glob("*.json"))
    if not archivos:
        print(f"No hay JSON cacheados en {a.cache}. Corre antes evaluacion.py.")
        return

    antes = despues = total = 0
    for f in archivos:
        guardado = json.loads(f.read_text(encoding="utf-8"))
        datos, clasificacion = guardado["datos"], guardado.get("clasificacion_final")
        doc_id = f.stem
        ruta_antigua = decidir_destino(datos, clasificacion)

        estado = {"datos_clinicos": datos, "clasificacion_final": clasificacion, "catalogos": catalogos}
        # usamos la fecha de referencia indicada
        datos["validacion_clinica"] = validar_clinicamente(datos, catalogos, hoy=hoy)
        v = datos["validacion_clinica"]
        nueva_clasificacion = clasificacion
        if v["urgencia_por_hallazgo_critico"]:
            nueva_clasificacion = "urgente"
        elif v["requiere_revision_humana"] and clasificacion != "urgente":
            nueva_clasificacion = "revision_clinica"
        ruta_nueva = decidir_destino(datos, nueva_clasificacion)

        esperada = (verdades.get(doc_id) or {}).get("ruta_esperada")
        equivalencias = {"urgencias_medicas": "urgencias", "farmacia_hospitalaria": "farmacia"}
        norm = lambda r: equivalencias.get(r, r)

        print(f"\n{doc_id}  puntaje clinico: {v['puntaje_clinico']}")
        for c in v["conflictos"]:
            print(f"   - {c['tipo']}: {c['detalle']}")
        for h in v["hallazgos_criticos"]:
            print(f"   ! VALOR CRITICO: {h}")
        print(f"   ruta antes: {norm(ruta_antigua):28} ahora: {norm(ruta_nueva):28} esperada: {esperada}")

        if esperada:
            total += 1
            antes += norm(ruta_antigua) == esperada
            despues += norm(ruta_nueva) == esperada

    if total:
        print(f"\n{'=' * 60}\nENRUTAMIENTO CORRECTO")
        print(f"  antes de la validacion clinica: {antes}/{total} ({100*antes/total:.0f}%)")
        print(f"  despues:                        {despues}/{total} ({100*despues/total:.0f}%)")

if __name__ == "__main__":
    main()