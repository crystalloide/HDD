#!/bin/bash
# =============================================================================
# TP2 — Ajoute la file YARN « dev » à chaud (À LANCER DEPUIS L'HÔTE, à la
# racine du dépôt) :   bash tp/tp2-yarn/ajouter_file_dev.sh
#
# 1. copie capacity-scheduler-dev.xml à la place de la configuration du
#    Capacity Scheduler, DANS le conteneur resourcemanager ;
# 2. demande au ResourceManager de relire ses files : yarn rmadmin -refreshQueues
#    (aucun redémarrage, les applications en cours continuent) ;
# 3. affiche l'état des files.
#
# La modification vit dans le conteneur : elle disparaît s'il est recréé
# (« docker compose up » après un changement de configuration, « down »...).
# Pour la rendre permanente : décommenter le bloc « TP2 — file dev » de hadoop/config.
# Retour à l'état initial :  bash tp/tp2-yarn/ajouter_file_dev.sh --retirer
# =============================================================================
set -euo pipefail
CONF=/opt/hadoop/etc/hadoop/capacity-scheduler.xml

if [ "${1:-}" = "--retirer" ]; then
  # La file doit être arrêtée (STOPPED) avant de pouvoir être supprimée.
  docker exec resourcemanager bash -c "sed -i 's#<name>yarn.scheduler.capacity.root.dev.state</name><value>RUNNING#<name>yarn.scheduler.capacity.root.dev.state</name><value>STOPPED#' ${CONF}"
  docker exec resourcemanager yarn rmadmin -refreshQueues
  echo "File dev arrêtée. Recréer le conteneur pour revenir à la configuration d'origine :"
  echo "  docker compose up -d --force-recreate resourcemanager"
  exit 0
fi

docker exec resourcemanager cp "${CONF}" "${CONF}.origine" 2>/dev/null || true
docker cp "$(dirname "$0")/capacity-scheduler-dev.xml" resourcemanager:/tmp/capacity-scheduler-dev.xml
docker exec resourcemanager cp /tmp/capacity-scheduler-dev.xml "${CONF}"
docker exec resourcemanager yarn rmadmin -refreshQueues
echo ""
docker exec resourcemanager yarn queue -status default 2>/dev/null | grep -E 'Queue Name|State|Capacity'
docker exec resourcemanager yarn queue -status dev     2>/dev/null | grep -E 'Queue Name|State|Capacity'
echo ""
echo "OK - file dev disponible : -D mapreduce.job.queuename=dev"
