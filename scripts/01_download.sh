#!/usr/bin/env bash
#
# Descarga los microdatos abiertos ENIGHUR 2024-2025 del INEC y extrae solo
# los CSV que necesita el analisis. Idempotente: si el archivo ya existe y pesa
# lo esperado, no lo vuelve a bajar.
#
# Fuente oficial (CC BY 4.0):
#   https://www.ecuadorencifras.gob.ec/encuesta-nacional-de-ingresos-y-gastos-de-los-hogares-urbanos-y-rurales/
#
# Uso:  bash scripts/01_download.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA="$ROOT/data"
mkdir -p "$DATA"

BASE_URL="https://www.ecuadorencifras.gob.ec/documentos/web-inec/Estadisticas_Sociales/enighur/2024-2025"
ZIP_URL="$BASE_URL/DATOS_ABIERTOS_ENIGHUR.zip"
ZIP_FILE="$DATA/datos_abiertos.zip"

# Solo estos CSV son necesarios para el analisis (el zip completo pesa ~170 MB).
NEEDED=(
  "Bases de trabajo_csv/ENIGHUR25_HOGARES_AGREGADOS.csv"
  "Bases de trabajo_csv/ENIGHUR2025_PERSONAS_INGRESOS.csv"
  "Bases de trabajo_csv/ENIGHUR2025_INGRESOS_H.csv"
)

echo ">> Descargando microdatos ENIGHUR 2024-2025..."
if [[ -f "$ZIP_FILE" ]]; then
  echo "   Ya existe $ZIP_FILE (omito descarga). Borralo para re-bajar."
else
  curl -fL --retry 3 -o "$ZIP_FILE" "$ZIP_URL"
fi

echo ">> Verificando que sea un ZIP valido..."
if ! unzip -t "$ZIP_FILE" >/dev/null 2>&1; then
  echo "ERROR: el archivo descargado no es un ZIP valido." >&2
  exit 1
fi

echo ">> Extrayendo solo los CSV necesarios..."
cd "$DATA"
for f in "${NEEDED[@]}"; do
  unzip -o "$ZIP_FILE" "DATOS ABIERTOS ENIGHUR_2026_05/$f" >/dev/null
  echo "   OK  $f"
done

echo ">> Listo. Ahora corre:  python3 scripts/02_analysis.py"
