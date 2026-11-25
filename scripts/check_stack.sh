#!/bin/bash
# =============================================================================
# check_stack.sh — vérification de bout en bout des composants DÉMARRÉS
# À exécuter DEPUIS LA MACHINE HÔTE, une fois "docker compose ... up -d" terminé
# (comptez 3 à 5 minutes après le démarrage pour le profil full) :
#   bash scripts/check_stack.sh             # vérifications rapides
#   bash scripts/check_stack.sh --complet   # + un paragraphe par interpréteur Zeppelin et un vrai
#                                           #   job MapReduce soumis depuis Zeppelin (2 à 4 min)
# Chaque composant non démarré (profil non activé) est simplement ignoré.
# =============================================================================
set -u

COMPLET=0
[ "${1:-}" = "--complet" ] && COMPLET=1

OK=0; KO=0; SKIP=0
LOG="$(mktemp)"
trap 'rm -f "${LOG}"' EXIT

running () { docker ps --format '{{.Names}}' | grep -qx "$1"; }

check () {
  local label="$1"; shift
  if "$@" > "${LOG}" 2>&1; then
    printf "  [ OK ]  %s\n" "${label}"; OK=$((OK + 1))
  else
    printf "  [ KO ]  %s\n" "${label}"; KO=$((KO + 1))
    tail -n 8 "${LOG}" | sed 's/^/           | /'
  fi
}

skip () { printf "  [ -- ]  %s (non démarré)\n" "$1"; SKIP=$((SKIP + 1)); }

echo "== Atelier Hadoop / Hive (socle) =="
check "HDFS : NameNode hors safe mode" \
  bash -c "docker exec namenode hdfs dfsadmin -safemode get | grep -q 'Safe mode is OFF'"
check "YARN : NodeManager enregistré" \
  bash -c "docker exec resourcemanager yarn node -list 2>/dev/null | grep -q RUNNING"
check "Tez : tarball présent sur HDFS" \
  docker exec namenode hdfs dfs -test -f /apps/tez/tez.tar.gz
check "lab-init : données de démonstration chargées (code retour 0)" \
  bash -c "[ \"\$(docker inspect -f '{{.State.ExitCode}}' lab-init 2>/dev/null)\" = 0 ]"
check "Hive : SELECT COUNT(*) FROM sales_db.transactions = 150" \
  bash -c "docker exec hiveserver2 beeline -u 'jdbc:hive2://localhost:10000/default' --silent=true --showHeader=false --outputformat=tsv2 -e 'SELECT COUNT(*) FROM sales_db.transactions' 2>/dev/null | grep -qx 150"

check "HDFS : permissions actives, ACL activées (lab HDD)" \
  bash -c "docker exec namenode hdfs getconf -confKey dfs.permissions.enabled | grep -qx true && docker exec namenode hdfs getconf -confKey dfs.namenode.acls.enabled | grep -qx true"
check "HDFS : groupes des comptes de test (bob -> marketing)" \
  bash -c "docker exec namenode hdfs groups bob 2>/dev/null | grep -q 'marketing'"
check "HDFS : répertoires des TP /data et /demo" \
  bash -c "docker exec namenode hdfs dfs -test -d /data && docker exec namenode hdfs dfs -test -d /demo"
if running historyserver; then
  check "JobHistory Server MapReduce (port 19888)" \
    docker exec historyserver curl -fs http://localhost:19888/ws/v1/history/info
else
  printf "  [ KO ]  %s\n" "JobHistory Server : conteneur historyserver arrêté"; KO=$((KO + 1))
fi

echo ""
echo "== Spark =="
if running spark-master; then
  check "Spark : 1 worker enregistré auprès du master" \
    bash -c "docker exec spark-master curl -fs http://localhost:8080/json/ | grep -q '\"aliveworkers\" *: *1'"
  check "Spark : lecture de sales_db.transactions via le metastore Hive (spark-submit)" \
    bash -c "docker exec spark-master spark-submit /opt/scripts/spark/smoke_test.py 2>&1 | grep 'SPARK_OK' | grep -q 'transactions=150'"
else skip "Spark"; fi
if running spark-history; then
  check "Spark History Server (port 18080)" \
    docker exec spark-history curl -fs http://localhost:18080/api/v1/applications
else skip "Spark History Server"; fi

echo ""
echo "== Zeppelin =="
if running zeppelin; then
  check "Zeppelin : API REST (port 8082)" \
    docker exec zeppelin curl -fs http://localhost:8082/api/version
  check "Zeppelin : interpréteurs sh, hive, impala, hbase, spark, python, md, file, java déclarés et réglés" \
    bash "$(dirname "$0")/check_interpreteurs.sh" --rapide
  check "Zeppelin : client HDFS disponible pour %sh" \
    docker exec zeppelin hdfs dfs -ls /user/data
  check "Zeppelin : sources des TP (/opt/tp) et données HDD (/opt/data/hdd)" \
    bash -c "docker exec zeppelin test -f /opt/tp/tp1-mapreduce/src/main/java/fr/orsys/hdd/tp1/ClientsParVille.java && docker exec zeppelin test -f /opt/data/hdd/clients/crm_2026-11.csv"
  check "Zeppelin : javac (JDK 17) pour compiler les TP Java" \
    docker exec zeppelin /opt/jdk17/bin/javac -version
  check "Zeppelin : client MapReduce configuré pour YARN (mapred-site.xml)" \
    bash -c "docker exec zeppelin grep -q '<value>yarn</value>' /opt/hadoop-conf/mapred-site.xml"
  check "Zeppelin : Apache Pig installé (TP4)" \
    bash -c "docker exec zeppelin bash -c 'command -v pig && pig -version 2>&1 | grep -i \"apache pig\"'"
  if [ "${COMPLET}" = 1 ]; then
    check "Zeppelin : un paragraphe exécuté par interpréteur (scripts/check_interpreteurs.sh)" \
      bash "$(dirname "$0")/check_interpreteurs.sh"
    check "MapReduce : job de test (pi) soumis depuis Zeppelin, terminé SUCCEEDED" \
      bash -c "docker exec zeppelin bash -c 'yarn jar /opt/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-*.jar pi 2 100 2>&1' | grep -q 'Estimated value of Pi'"
  fi
else skip "Zeppelin"; fi

echo ""
echo "== HBase =="
if running hbase-master; then
  check "HBase : master actif + RegionServer en ligne" \
    bash -c "echo status | docker exec -i hbase-master hbase shell -n 2>/dev/null | grep -Eq '1 active master.*[1-9][0-9]* servers'"
  check "HBase : table de démonstration clients_hbase (20 lignes)" \
    bash -c "echo \"count 'clients_hbase'\" | docker exec -i hbase-master hbase shell -n 2>/dev/null | grep -q '20 row'"
else skip "HBase"; fi
if running hbase-thrift; then
  check "HBase Thrift (port 9090, utilisé par Hue)" \
    docker exec hbase-thrift bash -c "echo > /dev/tcp/localhost/9090"
else skip "HBase Thrift"; fi

echo ""
echo "== Impala =="
if running impalad; then
  check "Impala : SELECT COUNT(*) FROM sales_db.transactions = 150" \
    bash -c "docker exec hiveserver2 beeline -u 'jdbc:hive2://impalad:21050/default;auth=noSasl' --silent=true --showHeader=false --outputformat=tsv2 -e 'INVALIDATE METADATA sales_db.transactions; SELECT COUNT(*) FROM sales_db.transactions;' 2>/dev/null | grep -qx 150"
else skip "Impala"; fi

echo ""
echo "== Hue =="
if running hue; then
  check "Hue : serveur web (port 8888)" \
    docker exec hue curl -fs http://localhost:8888/desktop/debug/is_alive
  check "Hue : connexion hue/hue + configuration de l'interface (/api/get_config/)" \
    docker exec hue /usr/share/hue/atelier-check.sh
else skip "Hue"; fi

echo ""
echo "Résultat : ${OK} OK, ${KO} KO, ${SKIP} non démarré(s)"
[ "${KO}" -eq 0 ]
