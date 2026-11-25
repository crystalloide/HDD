# -*- coding: utf-8 -*-
from zep import md, code

NAME = "00 - Prise en main et demonstration Hadoop"

P = [
md("""
## Prise en main de l'environnement des hand-labs — formation HDD « Hadoop, développement »

Tout le cluster tourne sur votre poste, un conteneur Docker par rôle. Ce notebook vérifie l'environnement puis rejoue la **démonstration du chapitre 1** : déposer un fichier dans HDFS, lancer un job MapReduce sur YARN, suivre son exécution dans les consoles.

| Console | Adresse (depuis votre navigateur) | Rôle |
|---|---|---|
| NameNode (HDFS) | http://localhost:9870 | état du système de fichiers, *Utilities > Browse the file system* |
| DataNode | http://localhost:9864 | blocs stockés sur le nœud |
| ResourceManager (YARN) | http://localhost:8088 | applications en cours, files, conteneurs |
| NodeManager | http://localhost:8042 | conteneurs du nœud |
| JobHistory (MapReduce) | http://localhost:19888 | jobs terminés : compteurs, tâches, journaux |
| Zeppelin | http://localhost:8082 | ces notebooks |
| Hue | http://localhost:8888 (`hue` / `hue`) | éditeurs Hive et Impala, fichiers, HBase |
| Spark Master / History | http://localhost:8080 / http://localhost:18080 | applications Spark |
| HBase Master | http://localhost:16010 | tables, régions |
| Impala | http://localhost:25000 | requêtes Impala |

Les notebooks des TP sont dans **HDD / 1 - Enonces** (à compléter) et **HDD / 2 - Corriges**.
Les sources des TP sont montées en lecture seule dans `/opt/tp`, les données dans `/opt/data/hdd`. On travaille dans `/tmp/hdd` (conteneur Zeppelin).
""", title="À lire avant de commencer"),

code("sh", """
# Qui suis-je pour HDFS ? Zeppelin tourne sous « root » : c'est l'identité
# présentée au NameNode (authentification « simple », sans Kerberos).
whoami
hdfs dfs -ls /
echo "--- répertoires personnels"
hdfs dfs -ls /user
""", title="1. HDFS répond"),

code("sh", """
# Rapport du cluster : réservé au superutilisateur HDFS (le compte « hadoop »
# qui fait tourner le NameNode). En authentification simple, HDFS croit la
# variable HADOOP_USER_NAME : c'est pratique en TP, et c'est exactement
# pourquoi un cluster de production active Kerberos.
HADOOP_USER_NAME=hadoop hdfs dfsadmin -report | head -25
""", title="2. Capacité HDFS (superutilisateur)"),

code("sh", """
yarn node -list -showDetails 2>/dev/null | head -20
echo "--- files du Capacity Scheduler"
mapred queue -list 2>/dev/null | grep -E 'Queue Name|Queue State|Scheduling Info' | head -12
echo "--- métriques du cluster (API REST du ResourceManager)"
curl -s http://resourcemanager:8088/ws/v1/cluster/metrics | python3 -c "import json,sys; m=json.load(sys.stdin)['clusterMetrics']; print('mémoire YARN :', m['totalMB'], 'Mo | vcores :', m['totalVirtualCores'], '| nœuds actifs :', m['activeNodes'])"
""", title="3. YARN : nœuds, files, capacité"),

md("""
### Démonstration du chapitre 1 : usage d'Hadoop

1. déposer un fichier dans HDFS (NameNode, port 9870) ;
2. lancer l'exemple **wordcount** livré avec Hadoop : un vrai job MapReduce soumis à YARN (port 8088) ;
3. lire le résultat, puis retrouver le job terminé dans le **JobHistory** (port 19888) : compteurs, tâches map et reduce, journaux.

Pendant l'exécution, ouvrez http://localhost:8088 : l'application passe par les états ACCEPTED puis RUNNING, avec un conteneur pour l'ApplicationMaster et un par tâche.
""", title="Démonstration"),

code("sh", """
hdfs dfs -mkdir -p /demo/in
hdfs dfs -put -f /opt/hadoop/LICENSE.txt /demo/in/
hdfs dfs -ls /demo/in
""", title="4. Déposer un fichier dans HDFS"),

code("sh", """
# Journal complet dans /tmp/hdd/wordcount.log ; on n'affiche que les lignes utiles.
mkdir -p /tmp/hdd
hdfs dfs -rm -r -f -skipTrash /demo/out
yarn jar /opt/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-*.jar \\
     wordcount /demo/in /demo/out > /tmp/hdd/wordcount.log 2>&1
code=$?
grep -E 'Submitted application|Running job|map [0-9]+% reduce|completed successfully|failed|Map input records|Reduce output records|ERROR|Exception' /tmp/hdd/wordcount.log
echo "--- code retour du job : ${code}"
if [ "${code}" -ne 0 ]; then
  echo "--- fin du journal (/tmp/hdd/wordcount.log)"
  tail -25 /tmp/hdd/wordcount.log
fi
exit "${code}"
""", title="5. Lancer wordcount sur YARN"),

code("sh", """
hdfs dfs -ls /demo/out
echo "--- les 15 mots les plus fréquents"
hdfs dfs -cat /demo/out/part-r-00000 | sort -t$'\\t' -k2,2nr | head -15
""", title="6. Lire le résultat"),

code("sh", """
# Les jobs terminés sont connus du JobHistory Server (http://localhost:19888)
curl -s "http://historyserver:19888/ws/v1/history/mapreduce/jobs" | python3 -c "
import json, sys, datetime
jobs = (json.load(sys.stdin).get('jobs') or {}).get('job', [])
for j in sorted(jobs, key=lambda j: j['startTime'])[-5:]:
    debut = datetime.datetime.fromtimestamp(j['startTime'] / 1000).strftime('%H:%M:%S')
    print(f\\"{j['id']}  {j['name'][:28]:28}  {j['user']:10} {j['queue']:8} {j['state']:10} début {debut}  maps={j['mapsTotal']} reduces={j['reducesTotal']}\\")
"
""", title="7. Le job dans le JobHistory"),

md("""
### Comptes et groupes du lab

L'authentification est « simple » : HDFS croit l'identité annoncée par le client. Les comptes de test et leurs groupes sont déclarés dans `hadoop/config` (propriété `hadoop.user.group.static.mapping.overrides`) :

| Compte | Groupe | Rôle dans les TP |
|---|---|---|
| `hadoop` | *(superutilisateur)* | administration HDFS : quotas, instantanés, `chown` |
| `crm_admin`, `alice` | `crm` | propriétaires du référentiel client (TP4, TP5) |
| `bob` | `marketing` | lecteur autorisé par ACL |
| `eve` | `stagiaires` | hors groupe : doit être refusée |
| `root`, `hive`, `impala`, `hue` | — | comptes de service de Zeppelin/Spark, HiveServer2, Impala, Hue |

Les permissions HDFS sont **actives**, avec un masque de création `000` : tout ce qui est créé sans restriction explicite reste ouvert aux autres moteurs, seuls les répertoires protégés volontairement le sont.
""", title="Comptes"),

code("sh", """
hdfs groups crm_admin alice bob eve root
""", title="8. Groupes vus par le NameNode"),

md("""
### Et ensuite ?

* Vérification complète de l'écosystème (Hive, Spark, Impala, HBase sur la même table) : notebook **HDD / 0 - Demarrage / Demo ecosysteme**.
* Depuis l'hôte : `bash scripts/check_stack.sh --complet`.
* Les TP : **TP1** collecte et MapReduce, **TP2** YARN, **TP3** HBase, **TP4** référentiel avec Pig et Hive, **TP5** référentiel avec Spark.
""", title="Suite"),
]
