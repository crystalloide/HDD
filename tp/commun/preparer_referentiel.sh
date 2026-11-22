#!/bin/bash
# =============================================================================
# Prépare (ou remet en état) la zone HDFS du référentiel client partagé.
# Idempotent. Utilisé par le TP5 si le TP4 n'a pas été fait, et comme
# référence du corrigé des étapes « Organiser » et « Partager » du TP4.
#
#   bash /opt/tp/commun/preparer_referentiel.sh          (depuis Zeppelin, %sh)
#
# Identités (authentification « simple » : HDFS croit HADOOP_USER_NAME) :
#   hadoop     superutilisateur HDFS (compte qui fait tourner le NameNode)
#   crm_admin  propriétaire du référentiel (groupe crm)
#   hive, impala, root : comptes de service de HiveServer2, d'Impala et de
#   Zeppelin/Spark, autorisés par ACL
#   bob (groupe marketing) : lecteur autorisé ; eve : hors groupe, refusée
# Groupes : hadoop/config, propriété hadoop.user.group.static.mapping.overrides
# =============================================================================
set -euo pipefail

SU="env HADOOP_USER_NAME=hadoop"
CRM="env HADOOP_USER_NAME=crm_admin"
DONNEES="${HDD_DATA:-/opt/data/hdd}"
Z=/data/referentiel/clients

echo "== Organiser : zones brute, raffinée, ORC (Hive) et Spark"
$SU hdfs dfs -mkdir -p /data/referentiel "$Z/brute" "$Z/raffinee" "$Z/orc" "$Z/spark"
$SU hdfs dfs -chmod 755 /data/referentiel
$SU hdfs dfs -chown crm_admin:crm "$Z" "$Z/brute" "$Z/raffinee" "$Z/orc" "$Z/spark"
$SU hdfs dfs -chmod 750 "$Z" "$Z/brute" "$Z/raffinee"
$SU hdfs dfs -chmod 770 "$Z/orc" "$Z/spark"

echo "== Partager : ACL des comptes de service et du groupe marketing"
# Traverser la racine du référentiel
$SU hdfs dfs -setfacl -m user:hive:r-x,user:impala:r-x,user:root:r-x,group:marketing:r-x "$Z"
# Zone brute : lue par Spark (Zeppelin, compte root) au TP5
$SU hdfs dfs -setfacl -m user:root:r-x "$Z/brute"
# Zones exposées : lecture pour Hive, Impala, Spark (root), marketing ; entrées « default »
# héritées par tout ce qui sera créé dedans (fichiers Pig, partitions Hive...)
for d in raffinee orc spark; do
  $SU hdfs dfs -setfacl -R -m \
    user:hive:r-x,user:impala:r-x,user:root:r-x,group:marketing:r-x,default:user:hive:r-x,default:user:impala:r-x,default:user:root:r-x,default:group:marketing:r-x \
    "$Z/$d"
done
# Écriture : Hive alimente la table ORC, Spark (root) écrit sa zone
$SU hdfs dfs -setfacl -R -m user:hive:rwx,default:user:hive:rwx "$Z/orc"
$SU hdfs dfs -setfacl -R -m user:root:rwx,default:user:root:rwx "$Z/spark"

echo "== Collecter : fichiers sources dans la zone brute"
$CRM hdfs dfs -put -f "$DONNEES"/clients/*.csv "$Z/brute/"
$SU hdfs dfs -ls "$Z" "$Z/brute" || true
echo ""
$SU hdfs dfs -getfacl "$Z/raffinee"
echo "OK - zone du référentiel prête"
