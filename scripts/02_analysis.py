#!/usr/bin/env python3
"""
Analisis ENIGHUR 2024-2025 (INEC Ecuador).

Responde tres preguntas sobre el "hogar promedio gana ~$1.135/mes":
  1. Distribucion real del ingreso del hogar (la media engana, ver mediana).
  2. Cuantos perceptores (personas que aportan ingreso) tiene un hogar.
  3. Cuantas personas ganan >= $1.200 por si solas.
Ademas reproduce el dato de "ayuda con dinero a otros hogares" (codigo 2009006).

Entrada:  data/DATOS ABIERTOS ENIGHUR_2026_05/Bases de trabajo_csv/*.csv
Salida:   results/resumen.json  (y copia en docs/data/resumen.json)

Notas metodologicas
-------------------
- Todos los promedios/porcentajes usan el factor de expansion 'Fexp'.
- Separador de columnas: ';' (HOGARES_AGREGADOS) o ',' (PERSONAS/INGRESOS_H).
- Separador decimal: coma -> se convierte a punto.
- Ingreso laboral por persona = i1703099 (neto dependiente) + i1706099 (neto
  independiente). Validado: al agregar por hogar reproduce ~96-100% de
  'ing_trab_mon' del archivo de hogares.
- "Perceptor": persona que recibe algun ingreso (marca 'perceptor' del INEC).
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "data" / "DATOS ABIERTOS ENIGHUR_2026_05" / "Bases de trabajo_csv"
F_HOG = BASE / "ENIGHUR25_HOGARES_AGREGADOS.csv"
F_PER = BASE / "ENIGHUR2025_PERSONAS_INGRESOS.csv"
F_ING = BASE / "ENIGHUR2025_INGRESOS_H.csv"


def num(s):
    """Convierte texto ENIGHUR ('1.234,56' estilo) a float; vacio -> 0.0."""
    s = (s or "").strip().replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def wpercentiles(pairs, ps):
    """Percentiles ponderados. pairs = [(valor, peso)], ps = lista de cuantiles."""
    a = sorted(pairs)
    total = sum(w for _, w in a)
    out, cum, i = {}, 0.0, 0
    for p in ps:
        target = p * total
        while i < len(a) and cum + a[i][1] < target:
            cum += a[i][1]
            i += 1
        out[p] = a[i][0] if i < len(a) else a[-1][0]
    return out


def wmean(pairs):
    tot = sum(w for _, w in pairs)
    return sum(v * w for v, w in pairs) / tot if tot else 0.0


def require(path):
    if not path.exists():
        sys.exit(
            f"ERROR: falta {path}\n"
            "Corre primero scripts/01_download.sh para descargar los microdatos."
        )


def analizar_hogares():
    require(F_HOG)
    tot, mon = [], []
    W = ge_media = ge_sm = 0.0
    deciles_pers = defaultdict(float)
    with open(F_HOG, encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh, delimiter=";"):
            w = num(row["Fexp"])
            t = num(row["ing_cor_tot"])
            m = num(row["ing_mon_cor"])
            tot.append((t, w))
            mon.append((m, w))
            W += w
            if t >= 1135:
                ge_media += w
            if t >= 470:  # salario basico unificado 2024-2025
                ge_sm += w
    media = wmean(tot)
    pc = wpercentiles(tot, [0.10, 0.25, 0.50, 0.75, 0.90])
    # % de hogares que gana MENOS que la media (la media no es lo "tipico")
    pct_bajo_media = 100 * sum(w for t, w in tot if t < media) / W
    # media excluyendo al 10% mas rico: cuanto la inflan los de arriba
    tot_sorted = sorted(tot)
    corte = 0.9 * W
    cum, sub = 0.0, []
    for t, w in tot_sorted:
        if cum >= corte:
            break
        take = min(w, corte - cum)
        sub.append((t, take))
        cum += take
    media_sin_top10 = wmean(sub)
    return {
        "hogares_muestra": len(tot),
        "hogares_expandidos": round(W),
        "media": round(media, 2),
        "mediana": round(pc[0.50], 2),
        "p10": round(pc[0.10], 2),
        "p25": round(pc[0.25], 2),
        "p75": round(pc[0.75], 2),
        "p90": round(pc[0.90], 2),
        "media_monetario": round(wmean(mon), 2),
        "pct_alcanza_media": round(100 * ge_media / W, 1),
        "pct_bajo_media": round(pct_bajo_media, 1),
        "media_sin_top10": round(media_sin_top10, 2),
        "pct_sobre_salario_basico": round(100 * ge_sm / W, 1),
    }


def analizar_quintiles():
    """Divide los hogares en 5 grupos iguales (20% c/u) por ingreso total y
    calcula, por quintil: ingreso medio/mediano, % del ingreso nacional, tamano
    del hogar, perceptores y per capita. Muestra la distorsion de la media."""
    require(F_HOG)
    rows = []
    with open(F_HOG, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            rows.append((num(r["ing_cor_tot"]), num(r["Fexp"]),
                         num(r["NUMPERS"]), num(r["gas_cor_tot"])))
    rows.sort()  # ordena por ingreso (primer campo)
    W = sum(w for _, w, _, _ in rows)
    tot_inc = sum(t * w for t, w, _, _ in rows)
    tot_gas = sum(g * w for _, w, _, g in rows)
    grupos = [[] for _ in range(5)]
    cum, qi = 0.0, 0
    for row in rows:
        grupos[min(qi, 4)].append(row)
        cum += row[1]
        if cum >= (qi + 1) * (W / 5) and qi < 4:
            qi += 1
    out = []
    for i, g in enumerate(grupos):
        Wq = sum(w for _, w, _, _ in g)
        inc = sum(t * w for t, w, _, _ in g)
        gas = sum(gc * w for _, w, _, gc in g)
        pers = sum(n * w for _, w, n, _ in g)
        med = wpercentiles([(t, w) for t, w, _, _ in g], [0.5])[0.5]
        out.append({
            "quintil": f"Q{i + 1}",
            "ingreso_medio": round(inc / Wq, 2),
            "ingreso_mediano": round(med, 2),
            "gasto_medio": round(gas / Wq, 2),
            "balance": round((inc - gas) / Wq, 2),
            "tasa_ahorro_pct": round(100 * (inc - gas) / inc, 1),
            "gasto_sobre_ingreso_pct": round(100 * gas / inc, 1),
            "pct_ingreso_nacional": round(100 * inc / tot_inc, 1),
            "pct_gasto_nacional": round(100 * gas / tot_gas, 1),
            "tam_hogar": round(pers / Wq, 2),
            "per_capita": round(inc / pers, 2),
        })
    q1, q5 = out[0]["ingreso_medio"], out[4]["ingreso_medio"]

    # Reparto de personas por quintil de HOGARES (20% de hogares != 20% de personas)
    reparto = []
    for i, g in enumerate(grupos):
        Pq = sum(n * w for _, w, n, _ in g)
        reparto.append({"quintil": f"Q{i + 1}",
                        "pct_personas": round(100 * Pq / sum(n * w for _, w, n, _ in rows), 1)})

    return {
        "grupos": out,
        "ratio_q5_q1": round(q5 / q1, 1),
        "reparto_personas": reparto,
        "nacional": {
            "ingreso_medio": round(tot_inc / W, 2),
            "gasto_medio": round(tot_gas / W, 2),
            "balance": round((tot_inc - tot_gas) / W, 2),
            "tasa_ahorro_pct": round(100 * (tot_inc - tot_gas) / tot_inc, 1),
        },
        "por_persona": _quintiles_por_persona(rows),
    }


def _quintiles_por_persona(rows):
    """Quintiles donde cada grupo = 20% de la POBLACION (no de hogares),
    ordenando por ingreso per capita y ponderando por personas (Fexp*NUMPERS).
    Es la foto mas honesta de la desigualdad: corrige que los hogares ricos
    sean mas grandes. rows = [(ing_hogar, Fexp, NUMPERS, gas_hogar)]."""
    pers = []  # (ing_pc, peso_personas, gas_pc)
    for ing, w, n, gas in rows:
        if n > 0:
            pers.append((ing / n, w * n, gas / n))
    pers.sort()
    P = sum(p for _, p, _ in pers)
    tot_inc = sum(pc * p for pc, p, _ in pers)
    grupos = [[] for _ in range(5)]
    cum, qi = 0.0, 0
    for row in pers:
        grupos[min(qi, 4)].append(row)
        cum += row[1]
        if cum >= (qi + 1) * (P / 5) and qi < 4:
            qi += 1
    out = []
    for i, g in enumerate(grupos):
        Pq = sum(p for _, p, _ in g)
        inc = sum(pc * p for pc, p, _ in g) / Pq
        gas = sum(gc * p for _, p, gc in g) / Pq
        out.append({
            "quintil": f"Q{i + 1}",
            "ingreso_per_capita": round(inc, 2),
            "gasto_per_capita": round(gas, 2),
            "tasa_ahorro_pct": round(100 * (inc - gas) / inc, 1),
            "pct_ingreso_nacional": round(100 * sum(pc * p for pc, p, _ in g) / tot_inc, 1),
        })
    return {"grupos": out,
            "ratio_q5_q1": round(out[4]["ingreso_per_capita"] / out[0]["ingreso_per_capita"], 1)}


def analizar_personas():
    require(F_PER)
    with open(F_PER, encoding="latin-1") as fh:
        reader = csv.reader(fh, delimiter=",")
        header = next(reader)
        idx = {c: i for i, c in enumerate(header)}
        i1, i2 = idx["i1703099"], idx["i1706099"]
        fx, hi, pc_i = idx["Fexp"], idx["Identif_hog"], idx["perceptor"]
        nperc = defaultdict(int)
        hw = {}
        earners = []  # (ingreso_laboral, peso) de perceptores con ingreso>0
        for row in reader:
            hw[row[hi]] = num(row[fx])
            if row[pc_i].strip() not in ("", "0", " "):
                nperc[row[hi]] += 1
                inc = num(row[i1]) + num(row[i2])
                if inc > 0:
                    earners.append((inc, num(row[fx])))
    # perceptores por hogar
    dist = defaultdict(float)
    Wh = 0.0
    suma_perc = 0.0
    for hid, w in hw.items():
        n = nperc.get(hid, 0)
        dist[min(n, 4)] += w
        Wh += w
        suma_perc += n * w
    dist_pct = {("4+" if k == 4 else str(k)): round(100 * v / Wh, 1)
                for k, v in sorted(dist.items())}
    # ingreso laboral individual
    Wec = sum(w for _, w in earners)
    pc = wpercentiles(earners, [0.25, 0.50, 0.75, 0.90, 0.95, 0.99])
    umbrales = []
    for thr in (470, 800, 1000, 1200, 2000, 3000):
        g = sum(w for v, w in earners if v >= thr)
        umbrales.append({"umbral": thr, "personas": round(g),
                         "pct": round(100 * g / Wec, 1)})
    return {
        "perceptores": {
            "promedio_por_hogar": round(suma_perc / Wh, 2),
            "distribucion_pct": dist_pct,
        },
        "ingreso_individual": {
            "perceptores_con_ingreso": round(Wec),
            "media": round(wmean(earners), 2),
            "mediana": round(pc[0.50], 2),
            "p25": round(pc[0.25], 2),
            "p75": round(pc[0.75], 2),
            "p90": round(pc[0.90], 2),
            "p95": round(pc[0.95], 2),
            "p99": round(pc[0.99], 2),
            "umbrales": umbrales,
        },
    }


def analizar_ayuda():
    require(F_ING)
    W = ayuda_total = ge = 0.0
    montos = []
    with open(F_ING, encoding="latin-1") as fh:
        for row in csv.DictReader(fh, delimiter=","):
            w = num(row["Fexp"])
            a = num(row.get("i2009006", 0))
            W += w
            ayuda_total += w * a
            if a > 0:
                ge += w
                montos.append((a, w))
    return {
        "total_mensual_usd": round(ayuda_total),
        "hogares_que_dan": round(ge),
        "pct_hogares_que_dan": round(100 * ge / W, 1),
        "promedio_entre_quienes_dan": round(ayuda_total / ge, 2),
        "mediana_entre_quienes_dan": round(wpercentiles(montos, [0.5])[0.5], 2),
    }


def main():
    print("Analizando hogares...")
    hogar = analizar_hogares()
    print("Analizando quintiles...")
    quintiles = analizar_quintiles()
    print("Analizando personas (puede tardar)...")
    personas = analizar_personas()
    print("Analizando ayuda a otros hogares...")
    ayuda = analizar_ayuda()

    resumen = {
        "meta": {
            "fuente": "ENIGHUR 2024-2025, INEC Ecuador",
            "licencia": "CC BY 4.0",
            "url": "https://www.ecuadorencifras.gob.ec/encuesta-nacional-de-ingresos-y-gastos-de-los-hogares-urbanos-y-rurales/",
            "muestra_viviendas": 41184,
            "hogares_expandidos": hogar["hogares_expandidos"],
            "personas_expandidas": 18091905,
            "salario_basico_2024_2025": 470,
        },
        "hogar": hogar,
        "quintiles": quintiles,
        "perceptores": personas["perceptores"],
        "ingreso_individual": personas["ingreso_individual"],
        "ayuda_otros_hogares": ayuda,
    }

    out = ROOT / "results" / "resumen.json"
    out.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    docs = ROOT / "docs" / "data" / "resumen.json"
    docs.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK -> {out}")
    print(f"OK -> {docs}")
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
