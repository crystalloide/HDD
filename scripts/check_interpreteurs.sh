#!/bin/bash
# =============================================================================
# check_interpreteurs.sh — interpréteurs Zeppelin utiles aux TP HDD
# À exécuter DEPUIS LA MACHINE HÔTE, Zeppelin démarré :
#   bash scripts/check_interpreteurs.sh            # présence + exécution réelle (1 à 3 min)
#   bash scripts/check_interpreteurs.sh --rapide   # présence et réglages seulement
# Vérifie sh, hive, impala, hbase, spark (pyspark, sql), python, md, file, java,
# puis exécute un paragraphe de test pour chacun dans une note temporaire,
# supprimée à la fin. Le code est dans scripts/check_interpreteurs.py, monté
# dans le conteneur zeppelin (/opt/scripts).
# =============================================================================
set -u

if ! docker ps --format '{{.Names}}' | grep -qx zeppelin; then
  echo "Le conteneur zeppelin n'est pas démarré (profil zeppelin ou full)." >&2
  exit 1
fi

SANS_EXECUTION=0
[ "${1:-}" = "--rapide" ] && SANS_EXECUTION=1

# Conteneurs démarrés : un test dont le service est absent est ignoré
ACTIFS="$(docker ps --format '{{.Names}}' | tr '\n' ' ')"

exec docker exec -e ACTIFS="${ACTIFS}" -e SANS_EXECUTION="${SANS_EXECUTION}" \
  zeppelin python3 /opt/scripts/check_interpreteurs.py
