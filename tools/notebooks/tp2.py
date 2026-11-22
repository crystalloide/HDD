# -*- coding: utf-8 -*-
from zep import md, code

NAME = "TP2 - Configuration de l implementation YARN"

PREPARE = """
# Construit le jar du TP1 à partir de la solution de référence (/opt/tp) :
# ce TP ne dépend pas de l'état de votre TP1.
mkdir -p /tmp/hdd/tp2 && cd /tmp/hdd/tp2
rm -rf classes && mkdir classes
/opt/jdk17/bin/javac --release 17 -encoding UTF-8 -cp "$(hadoop classpath)" -d classes \\
    $(find /opt/tp/tp1-mapreduce/src -name '*.java') && /opt/jdk17/bin/jar cf clients.jar -C classes .
ls -l clients.jar
# Données propres du TP1 (relance la collecte si besoin)
if ! hdfs dfs -test -e /data/clean/clients/_SUCCESS; then
  hdfs dfs -mkdir -p /data/raw/clients && hdfs dfs -put -f /opt/data/hdd/clients/*.csv /data/raw/clients/
  hdfs dfs -rm -r -f -skipTrash /data/clean/clients
  yarn jar clients.jar fr.orsys.hdd.tp1.CollecteClients /data/raw/clients /data/clean/clients 2>&1 | grep -E 'HDD_ETAT|COLLECTE'
fi
hdfs dfs -du -s -h /data/clean/clients
"""

# Lancement d'un job de mesure : $1 = libellé, le reste = options -D
LANCER = r"""
# Fonction de lancement réutilisée par les étapes suivantes :
#   lancer <libellé> [-D ...]   -> soumet ClientsParVille, affiche les mesures du JobHistory
cat > /tmp/hdd/tp2/lancer.sh <<'EOF'
#!/bin/bash
lib="$1"; shift
sortie="/data/out/yarn_${lib}"
hdfs dfs -rm -r -f -skipTrash "$sortie" > /dev/null
debut=$(date +%s)
yarn jar /tmp/hdd/tp2/clients.jar fr.orsys.hdd.tp1.ClientsParVille \
     -D mapreduce.input.fileinputformat.split.maxsize=131072 \
     -D hdd.map.pause.ms=4000 \
     "$@" '/data/clean/clients/part-*' "$sortie" > "/tmp/hdd/tp2/${lib}.log" 2>&1
job=$(grep -o 'HDD_JOB_ID=job_[0-9_]*' "/tmp/hdd/tp2/${lib}.log" | cut -d= -f2)
echo "durée vue du client : $(( $(date +%s) - debut )) s  —  $(grep HDD_ETAT /tmp/hdd/tp2/${lib}.log)"
if [ -n "$job" ]; then
  python3 /opt/tp/tp2-yarn/mesurer_job.py "$job" "$lib" | tee "/tmp/hdd/tp2/${lib}.mesure"
else
  tail -20 "/tmp/hdd/tp2/${lib}.log"
fi
EOF
chmod +x /tmp/hdd/tp2/lancer.sh && echo "lancer.sh prêt"
"""

OBSERVER = """
# À lancer PENDANT qu'un job tourne (Zeppelin exécute les paragraphes %sh en parallèle) :
# toutes les 5 s, mémoire et conteneurs alloués par YARN.
for i in $(seq 1 12); do
  curl -s "http://resourcemanager:8088/ws/v1/cluster/apps?states=RUNNING" | python3 -c "
import json, sys
apps = (json.load(sys.stdin).get('apps') or {}).get('app', [])
for a in apps:
    print(f\\"{a['id']}  {a['name'][:22]:22} file={a['queue']:8} conteneurs={a['runningContainers']:2}  mémoire={a['allocatedMB']:5} Mo  vcores={a['allocatedVCores']}\\")
if not apps: print('(aucune application en cours)')
"
  sleep 5
done
"""

P = [
md("""
## TP2 — Configuration de l'implémentation YARN

**Objectif** : comprendre et ajuster les ressources YARN, puis isoler des traitements dans une file dédiée.

| Étape | Contenu |
|---|---|
| 1. Observer | capacité du cluster, nœuds, files (ResourceManager, port 8088) |
| 2. Mesurer | relancer le job du TP1, noter conteneurs simultanés et durée, pour deux tailles de map |
| 3. Ajuster | changer la mémoire annoncée par le NodeManager (`yarn.nodemanager.resource.memory-mb`) |
| 4. Appliquer | recréer le NodeManager, relancer, comparer |
| 5. Partager | créer une file `dev` dans le Capacity Scheduler, `yarn rmadmin -refreshQueues` |
| 6. Vérifier | soumettre avec `-D mapreduce.job.queuename=dev`, contrôler la file et la part du cluster |

**Critères de réussite** : vous expliquez le lien entre mémoire du nœud et nombre de conteneurs ; le job s'exécute dans la file `dev` ; aucun conteneur n'est tué pour dépassement mémoire.

Certaines actions se font **depuis un terminal de l'hôte**, à la racine du dépôt (elles agissent sur les conteneurs) : elles sont signalées 🖥️.
""", title="Présentation du TP"),

code("sh", PREPARE, title="0.1 Préparer le jar et les données"),
code("sh", LANCER.strip("\n"), title="0.2 Outil de mesure"),

md("""
### Étape 1 — Observer

Ouvrez http://localhost:8088 : *Cluster Metrics* (mémoire et vcores totaux), *Nodes*, *Scheduler*. Puis comparez avec la ligne de commande et l'API REST ci-dessous.

Rappel de la configuration du lab (`hadoop/config`, `spark/hadoop-conf/mapred-site.xml`) :

| Paramètre | Valeur | Rôle |
|---|---|---|
| `yarn.nodemanager.resource.memory-mb` | 4096 (3072 en version légère) | mémoire que le nœud offre aux conteneurs |
| `yarn.nodemanager.resource.cpu-vcores` | 8 (4 en version légère) | vcores offerts |
| `yarn.scheduler.minimum-allocation-mb` / `maximum-allocation-mb` | 256 / 4096 | plus petit et plus grand conteneur accordés |
| `yarn.app.mapreduce.am.resource.mb` | 512 | ApplicationMaster MapReduce |
| `mapreduce.map.memory.mb` / `mapreduce.map.java.opts` | 512 / `-Xmx410m` | conteneur map et tas Java (≈ 80 %) |
| `yarn.scheduler.capacity.resource-calculator` | `DominantResourceCalculator` | mémoire **et** vcores sont comptés |
""", title="Étape 1"),

code("sh", """
yarn node -list -showDetails 2>/dev/null | grep -E 'Node-Id|Total-Nodes|Configured Resources|Allocated Resources|Resource Utilization'
curl -s http://resourcemanager:8088/ws/v1/cluster/metrics | python3 -c "
import json, sys; m = json.load(sys.stdin)['clusterMetrics']
print(f\\"mémoire : {m['totalMB']} Mo au total, {m['availableMB']} Mo libres | vcores : {m['totalVirtualCores']} | nœuds actifs : {m['activeNodes']} | applications en cours : {m['appsRunning']}\\")"
yarn queue -status default 2>/dev/null | grep -E 'Queue Name|State|Capacity'
""", title="1.1 Capacité du cluster"),

md("""
### Étape 2 — Mesurer

Le job `ClientsParVille` du TP1 est découpé en une vingtaine de maps (`split.maxsize` = 128 Ko) ; chaque map marque une pause de 4 s au démarrage (`hdd.map.pause.ms`), le temps d'observer les conteneurs.

1. Lancez la mesure **A** (maps de 512 Mo) ; pendant qu'elle tourne, lancez le paragraphe **2.3 Observer** et regardez http://localhost:8088.
2. Lancez la mesure **B** (maps de 1024 Mo, tas à 80 %).

Notez pour chacune : conteneurs simultanés, maps simultanés, durée.

Avant de mesurer, fermez les sessions Tez laissées ouvertes par Hue ou `%hive` : elles occupent des conteneurs (`yarn application -list`, puis `yarn application -kill <id>`).

| Mesure | Map | NodeManager | Maps simultanés | Durée |
|---|---|---|---|---|
| A | 512 Mo | 4096 Mo | … | … |
| B | 1024 Mo | 4096 Mo | … | … |
| C | 512 Mo | 2048 Mo | … | … |
""", title="Étape 2"),

code("sh", """
/tmp/hdd/tp2/lancer.sh A_map512
""", title="2.1 Mesure A : maps de 512 Mo"),

code("sh", """
/tmp/hdd/tp2/lancer.sh B_map1024 -D mapreduce.map.memory.mb=1024 -D mapreduce.map.java.opts=-Xmx820m
""", title="2.2 Mesure B : maps de 1024 Mo",
enonce="""
# TODO : relancer la mesure avec des conteneurs map de 1024 Mo et un tas Java d'environ 80 % de cette taille
#        (options -D mapreduce.map.memory.mb=... et -D mapreduce.map.java.opts=-Xmx...m)
/tmp/hdd/tp2/lancer.sh B_map1024
"""),

code("sh", OBSERVER.strip("\n"), title="2.3 Observer pendant l'exécution (à lancer pendant 2.1 ou 2.2)"),

md("""
**Questions**

1. Combien de maps tournent en même temps en A ? en B ? Retrouvez ces nombres par le calcul.
2. Quelle ressource limite le parallélisme en A : la mémoire ou les vcores ?
3. Pourquoi la durée totale augmente-t-elle en B alors que chaque map dispose de plus de mémoire ?
""", title="Questions"),

md("""
**Réponses** (NodeManager à 4096 Mo et 8 vcores, AM de 512 Mo / 1 vcore)

1. A : (4096 − 512) / 512 = 7 maps simultanés ; B : (4096 − 512) / 1024 = 3 maps simultanés (3,5 arrondi à l'inférieur).
2. En A, mémoire et vcores limitent au même niveau : 7 conteneurs de 512 Mo + l'AM = 4096 Mo, et 7 + 1 = 8 vcores. Avec le `DominantResourceCalculator`, la ressource la plus sollicitée en proportion décide.
3. Le job ne manque pas de mémoire : il a besoin de parallélisme. Des conteneurs plus gros sont moins nombreux, donc plus de « vagues » de maps. Dimensionner un conteneur au juste besoin augmente le débit du cluster.
""", title="Réponses", only="corrige"),

md("""
### Étape 3 — Ajuster la capacité du NodeManager 🖥️

La capacité annoncée par le NodeManager est lue **au démarrage** du conteneur : elle est injectée par Docker Compose (variable `NM_MEMORY_MB`, valeur par défaut 4096). Depuis un terminal de l'hôte, à la racine du dépôt :

```bash
NM_MEMORY_MB=2048 docker compose --profile full up -d nodemanager
# version légère : NM_MEMORY_MB=2048 docker compose -f docker-compose-light.yml --profile full up -d nodemanager
```

`docker compose restart` ne suffirait pas : il redémarre le même conteneur, avec l'ancienne configuration. `up -d` **recrée** le conteneur avec la nouvelle valeur. Les applications YARN en cours sur ce nœud (sessions Tez de Hue ou Zeppelin) sont interrompues.

Attendez une trentaine de secondes, puis vérifiez la nouvelle capacité.
""", title="Étape 3"),

code("sh", """
curl -s http://resourcemanager:8088/ws/v1/cluster/metrics | python3 -c "
import json, sys; m = json.load(sys.stdin)['clusterMetrics']
print(f\\"mémoire totale : {m['totalMB']} Mo | vcores : {m['totalVirtualCores']} | nœuds actifs : {m['activeNodes']}\\")"
""", title="3.1 Vérifier la nouvelle capacité"),

md("""
### Étape 4 — Appliquer et comparer

Relancez la mesure A avec le NodeManager à 2048 Mo (mesure C), puis comparez.
""", title="Étape 4"),

code("sh", """
/tmp/hdd/tp2/lancer.sh C_nm2048
""", title="4.1 Mesure C : maps de 512 Mo, NodeManager à 2048 Mo"),

code("sh", """
echo "Mesure            maps simultanés   durée"
for f in /tmp/hdd/tp2/*.mesure; do
  printf "%-18s %8s %16s\\n" "$(basename "$f" .mesure)" \\
    "$(grep 'maps simultanés' "$f" | grep -o '[0-9]*' | head -1)" \\
    "$(grep 'durée  ' "$f" | grep -o '[0-9.]* s')"
done
""", title="4.2 Tableau comparatif"),

md("""
🖥️ **Remettre la capacité d'origine** avant la suite (depuis l'hôte) :

```bash
docker compose --profile full up -d nodemanager
```

C : (2048 − 512) / 512 = 3 maps simultanés : la mémoire du nœud borne le nombre de conteneurs.

### Étape 5 — Partager : une file `dev` 🖥️

Le Capacity Scheduler répartit le cluster entre des files. Le fichier `tp/tp2-yarn/capacity-scheduler-dev.xml` reprend la configuration du lab et ajoute une file `dev` : 30 % garantis, plafonnée à 50 % ; `default` passe à 70 %.

Lisez le fichier (paragraphe suivant), puis appliquez-le **à chaud** depuis l'hôte :

```bash
bash tp/tp2-yarn/ajouter_file_dev.sh
```

Le script copie le fichier dans le conteneur `resourcemanager` puis lance `yarn rmadmin -refreshQueues` : les files sont relues sans redémarrage.
""", title="Étape 5"),

code("sh", """
grep -E '<name>|<value>' /opt/tp/tp2-yarn/capacity-scheduler-dev.xml | sed -e 's/<property><name>//' -e 's#</name><value># = #' -e 's#</value></property>##' | grep 'root\\.'
""", title="5.1 Lire la configuration des files"),

code("sh", """
mapred queue -list 2>/dev/null | grep -E 'Queue Name|Queue State|Scheduling Info'
""", title="5.2 Vérifier les files depuis Zeppelin"),

md("""
### Étape 6 — Vérifier

Soumettez le job dans la file `dev`, puis contrôlez la file utilisée (mesure, page *Scheduler* du ResourceManager). Avec 50 % du cluster au plus (2048 Mo), combien de maps simultanés attendez-vous ?
""", title="Étape 6"),

code("sh", """
/tmp/hdd/tp2/lancer.sh D_file_dev -D mapreduce.job.queuename=dev
""", title="6.1 Soumettre dans la file dev",
enonce="""
# TODO : relancer la mesure en choisissant la file « dev » (propriété mapreduce.job.queuename)
/tmp/hdd/tp2/lancer.sh D_file_dev
"""),

code("sh", """
yarn application -list -appStates FINISHED 2>/dev/null | grep -E 'clients-par-ville' | awk '{print $1, $4, $5, $6, $7}' | tail -5
""", title="6.2 Applications terminées et leur file"),

md("""
**Réponse** : la file `dev` peut monter à 50 % de 4096 Mo = 2048 Mo, AM compris : (2048 − 512) / 512 = 3 maps simultanés. Le plafond (`maximum-capacity`) protège les autres files ; `user-limit-factor = 2` permet à un utilisateur seul de dépasser la capacité garantie (30 %) jusqu'au plafond.
""", title="Réponse", only="corrige"),

md("""
### Pour aller plus loin

1. **Conteneur trop gros** : demandez des maps de 5000 Mo (`-D mapreduce.map.memory.mb=5000`). Que répond YARN ? Quelle propriété fixe cette limite ?
2. **Tas trop grand pour son conteneur** : `-D mapreduce.map.memory.mb=512 -D mapreduce.map.java.opts=-Xmx2g`. Dans ce lab, le contrôle de mémoire physique du NodeManager est désactivé (`yarn.nodemanager.pmem-check-enabled=false`) : en production, quel serait le risque ?
3. **Journaux agrégés** : `yarn logs -applicationId <id> | head` sur un job terminé.
4. **Rendre la file permanente** : bloc « TP2 » en fin de `hadoop/config`.
""", title="Bonus"),

code("sh", """
hdfs dfs -rm -r -f -skipTrash /data/out/yarn_trop_gros
timeout 120 yarn jar /tmp/hdd/tp2/clients.jar fr.orsys.hdd.tp1.ClientsParVille -D mapreduce.map.memory.mb=5000 \\
     '/data/clean/clients/part-*' /data/out/yarn_trop_gros 2>&1 | grep -iE 'capability|invalid|maximum|HDD_ETAT' | head -5
echo "--- limite du cluster :"
curl -s http://resourcemanager:8088/conf | grep -o 'yarn.scheduler.maximum-allocation-mb</name><value>[0-9]*' | sed 's#</name><value># = #'
""", title="B.1 Conteneur plus grand que le maximum autorisé"),

code("sh", """
app=$(yarn application -list -appStates FINISHED 2>/dev/null | grep clients-par-ville | tail -1 | awk '{print $1}')
echo "Journaux agrégés de $app (extrait) :"
yarn logs -applicationId "$app" 2>/dev/null | grep -E 'LogType|Container:|INFO .*(Starting|Task|completed)' | head -15
""", title="B.2 Journaux agrégés d'un job terminé"),

md("""
**Réponses**

1. Le job échoue à la soumission ou l'AM le refuse : *Invalid resource request… maximum allowed allocation*. La limite est `yarn.scheduler.maximum-allocation-mb` (4096 Mo ici).
2. La JVM peut consommer bien plus que la mémoire réservée : sur un nœud partagé, elle prive les autres conteneurs et peut faire intervenir l'OOM killer. Avec le contrôle actif, le NodeManager tue le conteneur (*running beyond physical memory limits*) : d'où la règle `-Xmx` ≈ 80 % de `memory.mb`.
""", title="Réponses bonus", only="corrige"),

md("""
### Contrôle des critères de réussite
""", title="Contrôle"),

code("sh", """
ok () { printf "  [ OK ] %s\\n" "$1"; }; ko () { printf "  [ KO ] %s\\n" "$1"; }
a=$(grep 'maps simultanés' /tmp/hdd/tp2/A_map512.mesure 2>/dev/null | grep -o '[0-9]*' | head -1)
b=$(grep 'maps simultanés' /tmp/hdd/tp2/B_map1024.mesure 2>/dev/null | grep -o '[0-9]*' | head -1)
[ -n "$a" ] && [ -n "$b" ] && [ "$b" -lt "$a" ] && ok "maps simultanés : $a (512 Mo) > $b (1024 Mo)" || ko "mesures A et B (étape 2)"
grep -q 'file YARN *: dev' /tmp/hdd/tp2/D_file_dev.mesure 2>/dev/null && ok "job exécuté dans la file dev" || ko "file dev (étapes 5 et 6)"
tues=$(curl -s "http://resourcemanager:8088/ws/v1/cluster/apps?states=FINISHED,FAILED,KILLED" | grep -o 'beyond physical memory' | wc -l)
[ "$tues" = 0 ] && ok "aucun conteneur tué pour dépassement mémoire" || ko "$tues conteneur(s) tué(s) pour dépassement mémoire"
total=$(curl -s http://resourcemanager:8088/ws/v1/cluster/metrics | python3 -c "import json,sys; print(json.load(sys.stdin)['clusterMetrics']['totalMB'])")
echo "  (capacité actuelle du nœud : $total Mo — remettre la valeur d'origine si besoin)"
""", title="Contrôle automatique"),
]
