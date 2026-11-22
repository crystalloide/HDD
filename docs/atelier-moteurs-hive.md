# Atelier d'origine : moteurs Hive MapReduce / Tez / LLAP

> Repris du dépôt [crystalloide/BD540](https://github.com/crystalloide/BD540) : toujours utilisable dans ce lab (démonstration du chapitre 2, comparaison des moteurs).


## Étape 1 — Chargement des données sur HDFS

```bash
docker exec namenode bash /opt/scripts/01_prepare_hdfs.sh
```

(`data/clients.csv` est déjà fourni — 20 clients de test — mais vous pouvez
le remplacer par le vôtre avant de lancer le script.)

## Étape 2 — Création de la table Hive externe

```bash
docker exec -it hiveserver2 beeline -u 'jdbc:hive2://localhost:10000/default' -f /opt/scripts/02_create_table.hql
```

## Étape 3 — Requête et temps de traitement

```bash
docker exec -it hiveserver2 beeline -u 'jdbc:hive2://localhost:10000/default' -f /opt/scripts/03_query_villes.hql
```

## Étape 4 — Comparaison des moteurs

Manuellement en session Beeline :

```bash
docker exec -it hiveserver2 beeline -u 'jdbc:hive2://localhost:10000/default'
```
```sql
SET hive.execution.engine=mr;
SELECT ville, COUNT(*) AS nb_clients FROM clients GROUP BY ville;

SET hive.execution.engine=tez;
SELECT ville, COUNT(*) AS nb_clients FROM clients GROUP BY ville;
```

```sql
!quit
```
Ou automatiquement, depuis l'hôte, avec chronométrage :

```bash
bash scripts/benchmark_engines.sh
```

Si les profils `impala` et/ou `spark` sont démarrés, le script ajoute en bonus
la même requête exécutée par **Impala** (démons toujours actifs, sans YARN) et
par **Spark SQL**.

Pendant chaque mesure, un point d'étape s'affiche toutes les 20 s. Le script
signale aussi, avant de commencer, les applications YARN déjà actives : ce
sont souvent des sessions Tez laissées ouvertes par Hue, Zeppelin ou un
beeline, qui occupent le cluster et faussent les temps. Pour partir d'un
cluster libre :

```bash
docker exec resourcemanager yarn application -list                    # applications actives
docker exec resourcemanager yarn application -kill <Application-Id>   # en arrêter une
```

Une session Tez inactive s'arrête d'elle-même au bout de 5 minutes.

Sur un jeu de données aussi petit, l'essentiel de l'écart vient du
**démarrage** du moteur (allocation de conteneurs YARN, JVM) : MapReduce
lance un ApplicationMaster puis des tâches map/reduce séquentielles,
pendant que Tez réutilise un DAG et évite les écritures disque
intermédiaires. C'est exactement l'écart que l'atelier vous fait observer
(de l'ordre de 30 à 60 s en MapReduce contre 5 à 10 s en Tez — les valeurs
réelles dépendent de la machine).

## Étape 5 — Analyse

Éléments de restitution attendus (cf. corrigé de l'atelier) : MapReduce
lent mais robuste pour du batch planifié ; Tez plus rapide grâce à son DAG
et à l'absence d'écritures intermédiaires ; LLAP quasi instantané mais plus
complexe à opérer en production.

## Bonus LLAP (optionnel)

L'énoncé indique LLAP comme optionnel (« si disponible ») — c'est aussi le
moteur le plus lourd à faire tourner correctement. Ce dépôt fournit un
profil dédié, repris de l'environnement Docker **officiel du projet Apache
Hive** (Zookeeper + AM Tez autonome + daemon LLAP), plutôt qu'une
intégration LLAP-sur-YARN maison — cette dernière demande normalement
Slider ou le service YARN natif, largement hors du cadre d'un lab. Le prix
à payer : ce mode tourne **sans YARN**, avec un HiveServer2 dédié sur un
port séparé.

```bash
docker compose --profile llap up -d
```
## Version LLAP économe en ressources : 

```bash
docker compose -f docker-compose-light.yml --profile llap up -d
```

Puis, dans une session sur le **second** HiveServer2 (port `10001`, table
`clients` partagée via le même metastore) :

```bash
docker exec -it hiveserver2-llap beeline -u 'jdbc:hive2://localhost:10000/default'
```
```sql
SET hive.execution.engine=tez;
SET hive.llap.execution.mode=all;
SELECT ville, COUNT(*) AS nb_clients FROM clients GROUP BY ville;
```

`scripts/benchmark_engines.sh` détecte automatiquement `hiveserver2-llap`
s'il tourne et ajoute la mesure LLAP à la comparaison.

**En cas de problème avec LLAP :** retirer simplement `--profile llap` : l'atelier reste complet avec MapReduce et Tez, qui sont le cœur du sujet.

Le conteneur `zookeeper` est partagé avec le profil `hbase` : démarrer les deux
profils ensemble ne crée qu'un seul ZooKeeper.

