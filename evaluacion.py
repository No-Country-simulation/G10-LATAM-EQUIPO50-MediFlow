#!/usr/bin/env python3
"""
evaluacion.py - Evaluacion en lote de MediFlow contra el ground truth.

Que hace:
  1. Recorre los documentos de casos/ y los pasa por Gemini + LangGraph.
  2. Compara la salida del agente contra casos/referencia/ground_truth.jsonl.
  3. Calcula metricas: clasificacion, campos extraidos, enrutamiento,
     recall de urgencias y tabla de calibracion de umbrales.

Importante:
  - El agente NUNCA ve el ground truth. Solo recibe el documento.
  - Llama a procesar_con_gemini() y ejecutar_langgraph() directamente,
    por lo que NO envia correos ni copia archivos al almacen local.
  - Guarda cache de las respuestas: si vuelves a correrlo, no repite
    las llamadas a Gemini ya hechas (ahorra cuota y tiempo).

Uso:
    python evaluacion.py                      # todos los documentos
    python evaluacion.py --split dev          # solo los 30 de desarrollo
    python evaluacion.py --limite 5           # prueba rapida con 5
    python evaluacion.py --solo-metricas      # recalcula sin llamar a Gemini
"""
import argparse
import csv
import json
import os
import re
import sys
import time
import traceback
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from dotenv import load_dotenv

# El evaluador corre siempre en local y no usa el almacenamiento en la nube.
# Si existe .env.pruebas, sus valores tienen prioridad sobre el .env de
# produccion, asi se puede medir sin tocar la configuracion real del despliegue.
RUTA_ENV_PRUEBAS = Path(__file__).parent / ".env.pruebas"
if RUTA_ENV_PRUEBAS.exists():
    load_dotenv(RUTA_ENV_PRUEBAS, override=True)

RAIZ = Path(__file__).resolve().parent
BACKEND = RAIZ / "Backend_MediFlow"
CASOS = RAIZ / "casos"
REFERENCIA = CASOS / "referencia"
SALIDA = RAIZ / "evaluacion_resultados"
CACHE = SALIDA / "cache"

# Los modulos del backend se importan entre si de forma plana
# (from configuracion import *), por eso agregamos su carpeta al path.
sys.path.insert(0, str(BACKEND))

# --------------------------------------------------------------------------
# EQUIVALENCIAS entre el vocabulario del agente y el del ground truth
# --------------------------------------------------------------------------
CATEGORIA_AGENTE_A_GT = {
    "Receta Médica": "receta_medica",
    "Informe de Estudio de Diagnóstico por Imágenes/Laboratorio": "informe_estudio",
    "Orden de Solicitud de Procedimiento": "orden_procedimiento",
    "Epicrisis / Informe de Alta": "epicrisis",
    "Certificado Médico": "certificado_medico",
    "Otro": "otro",
}
DESTINO_POR_CATEGORIA = {
    "receta_medica": "farmacia",
    "orden_procedimiento": "auditoria_autorizaciones",
    "informe_estudio": "historia_clinica_electronica",
    "epicrisis": "historia_clinica_electronica",
    "certificado_medico": "historia_clinica_electronica",
    "otro": "revision_humana",
}

# --------------------------------------------------------------------------
# NORMALIZACION: comparar texto sin que tildes o mayusculas cuenten como error
# --------------------------------------------------------------------------
def normalizar(texto):
    if texto is None:
        return ""
    texto = str(texto).strip().lower()
    texto = "".join(c for c in unicodedata.normalize("NFD", texto)
                    if unicodedata.category(c) != "Mn")
    texto = re.sub(r"\s+", " ", texto)
    return texto

def solo_digitos(texto):
    return re.sub(r"\D", "", str(texto or ""))

def nombres_coinciden(esperado, obtenido):
    """Tolerante: 'Dr. Juan Perez Gomez' vs 'Juan Pérez Gómez' cuenta como acierto."""
    a = set(normalizar(esperado).replace("dr.", "").replace("dra.", "").split())
    b = set(normalizar(obtenido).replace("dr.", "").replace("dra.", "").split())
    if not a or not b:
        return False
    comunes = len(a & b)
    return comunes >= max(2, min(len(a), len(b)) - 1)

def primera_palabra(texto):
    n = normalizar(texto)
    return n.split()[0] if n else ""

# --------------------------------------------------------------------------
# LECTURA DE LA SALIDA DEL AGENTE
# --------------------------------------------------------------------------
def campos_del_agente(datos, clasificacion_final):
    """Traduce el JSON del agente a los pocos campos que vamos a comparar."""
    paciente = datos.get("paciente") or {}
    medico = datos.get("medico") or {}
    diagnosticos = datos.get("diagnosticos") or []
    medicamentos = datos.get("medicamentos") or []
    coherencia = datos.get("validacion_coherencia") or {}
    riesgo = datos.get("clasificacion_riesgo") or {}

    # El documento del paciente puede venir en id_paciente o en curp
    documento = paciente.get("id_paciente") or paciente.get("curp")

    # El primer diagnostico con codigo es el que comparamos
    cie10 = None
    for d in diagnosticos:
        if isinstance(d, dict) and d.get("codigo"):
            cie10 = d["codigo"]
            break

    nombres_med = []
    for m in medicamentos:
        if isinstance(m, dict):
            nombres_med.append(m.get("nombre") or m.get("principio_activo") or "")
        else:
            nombres_med.append(str(m))

    categoria_agente = (datos.get("clasificacion_documento") or {}).get("categoria", "Otro")
    categoria = CATEGORIA_AGENTE_A_GT.get(categoria_agente, "otro")

    return {
        "categoria": categoria,
        "categoria_cruda": categoria_agente,
        "paciente_nombre": paciente.get("nombre_completo"),
        "paciente_documento": documento,
        "medico_nombre": medico.get("nombre_completo"),
        "matricula": medico.get("cedula_profesional"),
        "cie10": cie10,
        "medicamentos": [n for n in nombres_med if n],
        "puntaje": coherencia.get("puntaje_incoherencia"),
        "nivel": coherencia.get("nivel_coherencia"),
        "urgente": bool(riesgo.get("urgente")),
        "clasificacion_final": clasificacion_final,
        "requiere_revision": bool(riesgo.get("requiere_revision_humana")),
    }

def ruta_del_agente(campos):
    """Regla de enrutamiento: urgencia primero, luego revision, luego categoria."""
    if campos["clasificacion_final"] == "urgente" or campos["urgente"]:
        return "urgencias"
    if campos["clasificacion_final"] != "normal":
        return "revision_humana"
    return DESTINO_POR_CATEGORIA.get(campos["categoria"], "historia_clinica_electronica")

# --------------------------------------------------------------------------
# COMPARACION DE UN DOCUMENTO
# --------------------------------------------------------------------------
def comparar(verdad, campos):
    """Devuelve un dict campo -> True/False/None (None = no aplica)."""
    r = {}
    r["categoria"] = campos["categoria"] == verdad["categoria"]

    pac = verdad.get("paciente") or {}
    if pac.get("nombre"):
        r["paciente_nombre"] = nombres_coinciden(pac["nombre"], campos["paciente_nombre"])
        r["paciente_documento"] = (solo_digitos(pac.get("documento")) ==
                                   solo_digitos(campos["paciente_documento"]))
    prof = verdad.get("profesional") or {}
    if prof.get("nombre"):
        r["medico_nombre"] = nombres_coinciden(prof["nombre"], campos["medico_nombre"])
    if prof.get("matricula"):
        r["matricula"] = (solo_digitos(prof["matricula"]) == solo_digitos(campos["matricula"]))

    dx = verdad.get("diagnostico") or {}
    if dx.get("cie10"):
        r["cie10"] = normalizar(dx["cie10"]) == normalizar(campos["cie10"])

    meds_v = {primera_palabra(m["nombre"]) for m in (verdad.get("medicamentos") or [])}
    if meds_v:
        meds_a = {primera_palabra(m) for m in campos["medicamentos"]}
        r["medicamentos"] = meds_v == meds_a

    urg_v = verdad["urgencia"] == "alta"
    urg_a = ruta_del_agente(campos) == "urgencias"
    r["urgencia"] = urg_v == urg_a
    r["ruta"] = ruta_del_agente(campos) == verdad["ruta_esperada"]
    return r

# --------------------------------------------------------------------------
# PROCESAMIENTO
# --------------------------------------------------------------------------
def procesar_documento(ruta, umbrales, reglas, backend):
    """Pasa un documento por Gemini + LangGraph. Sin correos ni copias."""
    tipo = backend["validar_extension"](str(ruta))
    nombre = ruta.name
    datos = backend["procesar_con_gemini"](str(ruta), tipo, nombre)
    resultado = backend["ejecutar_langgraph"](datos, umbrales, reglas)
    return resultado["datos_clinicos"], resultado.get("clasificacion_final")

def cargar_backend():
    from archivos import validar_extension
    from gemini import procesar_con_gemini
    from langgraph_mediflow import ejecutar_langgraph
    from umbrales import cargar_configuracion_umbrales
    from reglas import cargar_configuracion_reglas
    return {
        "validar_extension": validar_extension,
        "procesar_con_gemini": procesar_con_gemini,
        "ejecutar_langgraph": ejecutar_langgraph,
        "umbrales": cargar_configuracion_umbrales(),
        "reglas": cargar_configuracion_reglas(),
    }

# --------------------------------------------------------------------------
# METRICAS
# --------------------------------------------------------------------------
def porcentaje(aciertos, total):
    return f"{100 * aciertos / total:5.1f}%  ({aciertos}/{total})" if total else "    -"

def informe(filas, umbrales_agente):
    print("\n" + "=" * 68)
    print("RESULTADOS DE LA EVALUACION")
    print("=" * 68)
    total = len(filas)
    errores = [f for f in filas if f.get("error")]
    ok = [f for f in filas if not f.get("error")]
    print(f"\nDocumentos procesados: {total}   |   fallidos: {len(errores)}")
    if not ok:
        return

    print("\n--- EXACTITUD POR CAMPO ---")
    campos = ["categoria", "paciente_nombre", "paciente_documento", "medico_nombre",
              "matricula", "cie10", "medicamentos", "urgencia", "ruta"]
    for c in campos:
        vals = [f["comparacion"].get(c) for f in ok if c in f["comparacion"]]
        print(f"{c:22} {porcentaje(sum(1 for v in vals if v), len(vals))}")

    print("\n--- RECALL DE URGENCIAS (lo mas critico) ---")
    urgentes = [f for f in ok if f["verdad"]["urgencia"] == "alta"]
    detectadas = [f for f in urgentes if f["ruta_agente"] == "urgencias"]
    print(f"Urgencias reales: {len(urgentes)}  |  detectadas: {len(detectadas)}")
    for f in urgentes:
        if f["ruta_agente"] != "urgencias":
            print(f"  ESCAPADA: {f['id']} ({f['verdad']['categoria']}, {f['verdad']['formato']}) "
                  f"-> el agente la mando a {f['ruta_agente']}")

    print("\n--- CARGA DE REVISION HUMANA ---")
    a_revision = [f for f in ok if f["ruta_agente"] == "revision_humana"]
    esperados = [f for f in ok if f["verdad"]["ruta_esperada"] == "revision_humana"]
    print(f"El agente manda a revision: {len(a_revision)}/{len(ok)} "
          f"({100*len(a_revision)/len(ok):.0f}%)  |  esperado: {len(esperados)}")

    print("\n--- POR FORMATO Y CALIDAD ---")
    for clave in ("formato", "calidad"):
        grupos = defaultdict(list)
        for f in ok:
            grupos[f["verdad"][clave]].append(f["comparacion"].get("categoria"))
        for g, vals in sorted(grupos.items()):
            print(f"{clave:8} {g:16} categoria: {porcentaje(sum(1 for v in vals if v), len(vals))}")

    print("\n--- CASOS TRAMPA ---")
    trampas = [f for f in ok if f["verdad"].get("trampa")]
    for f in trampas:
        marca = "OK " if f["comparacion"].get("ruta") else "NO "
        print(f"  {marca} {f['id']:8} {f['verdad']['trampa']:24} "
              f"esperado: {f['verdad']['ruta_esperada']:28} agente: {f['ruta_agente']}")

    print("\n--- CALIBRACION DE UMBRALES (puntaje de incoherencia) ---")
    print("umbral  a revision  errores que se escapan")
    for u in range(0, 101, 10):
        revision = [f for f in ok if (f["puntaje"] or 0) >= u]
        pasan = [f for f in ok if (f["puntaje"] or 0) < u]
        fallos = [f for f in pasan if not all(v for v in f["comparacion"].values() if v is not None)]
        print(f"{u:5}   {len(revision):6}      {len(fallos):6}")
    print(f"\nUmbrales configurados hoy: {umbrales_agente}")

    print("\n--- MATRIZ DE CONFUSION (categoria) ---")
    matriz = Counter((f["verdad"]["categoria"], f["campos"]["categoria"]) for f in ok)
    cats = sorted({c for par in matriz for c in par})
    print(f"{'real \\ agente':24}" + "".join(f"{c[:11]:>13}" for c in cats))
    for real in cats:
        print(f"{real:24}" + "".join(f"{matriz.get((real, pred), 0):>13}" for pred in cats))

# --------------------------------------------------------------------------
# PRINCIPAL
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Evaluacion en lote de MediFlow")
    ap.add_argument("--split", choices=["dev", "test", "todos"], default="todos")
    ap.add_argument("--limite", type=int, default=0, help="procesar solo N documentos")
    ap.add_argument("--pausa", type=float, default=1.0, help="segundos entre llamadas a Gemini")
    ap.add_argument("--forzar", action="store_true", help="ignorar la cache y volver a llamar a Gemini")
    ap.add_argument("--solo-metricas", action="store_true", help="usar solo la cache, sin llamar a Gemini")
    a = ap.parse_args()

    gt_path = REFERENCIA / "ground_truth.jsonl"
    if not gt_path.is_file():
        sys.exit(f"No encuentro {gt_path}. Sube primero la carpeta casos/referencia/.")

    verdades = [json.loads(l) for l in gt_path.open(encoding="utf-8")]
    if a.split != "todos":
        verdades = [v for v in verdades if v["split"] == a.split]
    if a.limite:
        verdades = verdades[:a.limite]

    SALIDA.mkdir(exist_ok=True)
    CACHE.mkdir(exist_ok=True)

    backend = None
    if not a.solo_metricas:
        backend = cargar_backend()
    umbrales = backend["umbrales"] if backend else {}
    reglas = backend["reglas"] if backend else {}

    filas = []
    for i, v in enumerate(verdades, 1):
        doc_id = v["id"]
        ruta = CASOS / "documents" / Path(v["archivo"]).name
        cache_f = CACHE / f"{doc_id}.json"
        print(f"[{i}/{len(verdades)}] {doc_id} ...", end=" ", flush=True)

        try:
            if cache_f.is_file() and not a.forzar:
                guardado = json.loads(cache_f.read_text(encoding="utf-8"))
                datos, clasificacion = guardado["datos"], guardado["clasificacion_final"]
                print("(cache)", end=" ")
            elif a.solo_metricas:
                print("sin cache, omitido")
                continue
            else:
                if not ruta.is_file():
                    raise FileNotFoundError(f"no existe {ruta}")
                datos, clasificacion = procesar_documento(ruta, umbrales, reglas, backend)
                cache_f.write_text(json.dumps(
                    {"datos": datos, "clasificacion_final": clasificacion},
                    ensure_ascii=False, indent=2), encoding="utf-8")
                time.sleep(a.pausa)

            campos = campos_del_agente(datos, clasificacion)
            filas.append({
                "id": doc_id, "verdad": v, "campos": campos,
                "comparacion": comparar(v, campos),
                "ruta_agente": ruta_del_agente(campos),
                "puntaje": campos["puntaje"], "error": None,
            })
            print(f"-> {filas[-1]['ruta_agente']}")
        except Exception as e:
            filas.append({"id": doc_id, "verdad": v, "error": str(e),
                          "comparacion": {}, "campos": {}, "ruta_agente": None, "puntaje": None})
            print(f"ERROR: {e}")
            traceback.print_exc(limit=1)

    informe(filas, umbrales)

    # detalle por documento, para revisar los fallos uno por uno
    with (SALIDA / "detalle.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "formato", "calidad", "trampa", "categoria_real", "categoria_agente",
                    "ruta_esperada", "ruta_agente", "puntaje", "campos_fallados", "error"])
        for fila in filas:
            v = fila["verdad"]
            fallados = [k for k, ok in fila["comparacion"].items() if ok is False]
            w.writerow([fila["id"], v["formato"], v["calidad"], v.get("trampa") or "",
                        v["categoria"], fila["campos"].get("categoria", ""),
                        v["ruta_esperada"], fila["ruta_agente"] or "", fila["puntaje"],
                        "|".join(fallados), fila["error"] or ""])
    print(f"\nDetalle por documento: {SALIDA / 'detalle.csv'}")

if __name__ == "__main__":
    main()