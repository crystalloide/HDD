# Utilisation des composants (Zeppelin, Spark, HBase, Impala, Hue)

> Repris du dépôt [crystalloide/BD540](https://github.com/crystalloide/BD540). Volume des notebooks : `hdd-lab_zeppelin_notebook`.


Toutes les commandes ci-dessous se lancent depuis l'hôte. Les composants
partagent :

- le HDFS `hdfs://namenode:8020` ;
- le metastore Hive `thrift://metastore:9083` ;
- la base de démonstration **`sales_db.transactions`** (150 ventes,
  `data/transactions.csv`), créée au démarrage par le service `lab-init`. Sa
  colonne `customer_id` correspond à `id_client` de la table `clients` de
  l'atelier.

## Zeppelin — http://localhost:8082

Profil `zeppelin` (Spark est démarré avec lui). Notebooks
préinstallés :

| Notebook | Contenu |
|---|---|
| **HDD / 0 - Demarrage / 00 - Prise en main** | vérification du cluster, démonstration wordcount du chapitre 1 |
| **HDD / 1 - Enonces**, **HDD / 2 - Corriges** | les 5 TP de la formation HDD (voir le README) |
| **HDD / 0 - Demarrage / Demo ecosysteme** | la même table interrogée par HDFS, Hive, Spark, Impala et HBase : vérification de bout en bout |



Tous les interpréteurs de Zeppelin 0.12.1 sont installés (*Interpreter* dans
le menu utilisateur), plus `%sh`. Ceux qui ont un sens dans l'atelier sont
préconfigurés (`zeppelin/conf/interpreter.json`) et prêts à l'emploi :

| Interpréteur | Cible |
|---|---|
| `%spark`, `%spark.pyspark`, `%spark.sql` | Spark 4.0.4, `spark://spark-master:7077`, catalogue Hive partagé (1 Go de driver, 2 executors de 1 cœur / 1 Go) |
| `%spark.ipyspark` | PySpark dans un noyau IPython (complétion, affichage riche) |
| `%spark-submit` | `spark-submit` vers le cluster Spark (arguments dans le paragraphe) |
| `%hive` | HiveServer2 : `jdbc:hive2://hiveserver2:10000/default` (pilote JDBC Hive 4.1.0) |
| `%impala` | Impala : `jdbc:hive2://impalad:21050/default;auth=noSasl` |
| `%hbase` | shell HBase 2.6.7 (`list`, `scan 'clients_hbase'`...) relié au ZooKeeper de l'atelier, profil `hbase` |
| `%file` | navigation HDFS via WebHDFS (`ls`, `cd`, `pwd`) |
| `%sh` | shell du conteneur, avec les clients `hdfs`, `yarn` (Hadoop 3.4.2), `hbase`, `spark-submit`, `pyspark` |
| `%python` | Python 3.10, avec `happybase` (client HBase via Thrift) et `pandas` |
| `%python.ipython` | Python dans un noyau IPython |
| `%python.sql` | SQL sur des DataFrames pandas (pandasql) |
| `%jupyter` | noyau Jupyter générique, par exemple `%jupyter(kernel=python3)` |
| `%java` | classe Java avec `main`, compilée et exécutée (JDK 17) |
| `%groovy` | Groovy |
| `%md`, `%angular` | Markdown, affichage HTML/AngularJS |

Les autres interpréteurs sont installés, mais il leur faut un service absent
de l'atelier, à renseigner dans leur réglage : `%cassandra`,
`%elasticsearch`, `%mongodb`, `%neo4j`, `%influxdb`, `%bigquery`, `%alluxio`,
`%sparql` (point d'accès SPARQL), `%livy` (serveur Livy), `%flink` /
`%flink-cmd` (distribution Flink), `%jdbc` (réglage générique, PostgreSQL
local par défaut). R n'est pas installé : `%r`, `%ir` et `%spark.r` ne
s'exécutent pas.

Le notebook *HDD / 0 - Demarrage / Demo ecosysteme* contient un exemple `%hbase`,
`%file`, `%java` et `%python.ipython`. `%python` et `%spark.pyspark` restent
en mode Python classique, comme dans le TP. Le mode IPython s'utilise
explicitement avec `%python.ipython` et `%spark.ipyspark`. Les paquets Python
de la pile IPython sont figés sur des versions compatibles avec Zeppelin
0.12.1 (voir `spark/Dockerfile`).

Le premier paragraphe Spark démarre l'application Spark, ce qui prend 30 à
60 s. Elle reste ensuite active (visible sur http://localhost:8080) jusqu'au
redémarrage de l'interpréteur.

Les notebooks sont conservés dans le volume Docker `zeppelin_notebook`. Un
`docker compose down -v` le réinitialise avec les notebooks d'origine. Pour
ne réinitialiser que ce volume, par exemple après une mise à jour des
notebooks livrés :
`docker compose --profile zeppelin rm -sf zeppelin && docker volume rm hdd-lab_zeppelin_notebook`,
puis `docker compose --profile zeppelin up -d`.

## Spark — http://localhost:8080

Profil `spark`. Le cluster standalone compte 1 master et 1 worker de 4 cœurs et
3 Go. Chaque application prend au plus 2 cœurs, pour que Zeppelin et une
démonstration en ligne de commande puissent tourner ensemble.

```bash
# Shell PySpark interactif sur le cluster, avec le catalogue Hive partagé
docker exec -it spark-master pyspark
>>> spark.sql("SELECT city, SUM(amount) FROM sales_db.transactions GROUP BY city").show()

# Job batch
docker exec spark-master spark-submit /opt/scripts/spark/smoke_test.py
```

Les applications terminées restent consultables dans le Spark History Server
(http://localhost:18080). Leurs journaux d'événements sont dans
`hdfs:///spark-logs`.

> Les scripts de vérification et les notebooks passent par `pyspark` et
> `spark-submit`. Préférez ces points d'entrée à la CLI `spark-sql`, qui
> s'appuie en partie sur le Hive 2.3 intégré à Spark alors que le catalogue est
> servi ici par un client metastore Hive 4.0.1 isolé (voir
> [Notes techniques](#pourquoi-ces-versions-pour-les-composants-ajoutés)).

## HBase — http://localhost:16010

Profil `hbase`. Le service one-shot `hbase-init` crée la table de démonstration
`clients_hbase`, avec 20 lignes et les familles `infos` et `stats`.

```bash
docker exec -it hbase-master hbase shell
hbase:001:0> list
hbase:002:0> scan 'clients_hbase', {LIMIT => 3}
hbase:003:0> get 'clients_hbase', 'C001'
```

Deux autres accès sont disponibles :

- Hue, menu **HBase** ;
- Zeppelin, `%python` avec `happybase` (serveur Thrift `hbase-thrift:9090`).
  Voir le notebook *Demo ecosysteme*.

## Impala — http://localhost:25000

Profil `impala`. Impala lit les tables du metastore Hive et les fichiers HDFS,
sans passer par YARN. Les bases et tables créées par Hive, Spark ou Hue
apparaissent automatiquement dans Impala en quelques secondes : `catalogd`
suit les événements du metastore.

Après un ajout de fichiers directement dans HDFS, rechargez la table :

```sql
INVALIDATE METADATA sales_db.transactions;   -- ou REFRESH sales_db.transactions;
```

Trois clients sont possibles :

- Hue, éditeur **Impala** ;
- Zeppelin, `%impala` ;
- beeline, depuis le conteneur HiveServer2 :

```bash
docker exec -it hiveserver2 beeline -u 'jdbc:hive2://impalad:21050/default;auth=noSasl'
```

`scripts/benchmark_engines.sh` ajoute automatiquement une mesure Impala et une
mesure Spark SQL à la comparaison MapReduce / Tez quand ces services tournent.

## Hue — http://localhost:8888

Profil `hue`. Connexion avec **`hue` / `hue`**, compte administrateur avec
accès complet (éditeurs, fichiers HDFS, tables, jobs, HBase, gestion des
utilisateurs). Un compte de secours **`admin` / `admin`** existe aussi : sa
présence évite l'écran « Create your account ». Les deux sont prêts dès le
premier démarrage. Mots de passe : variables `HUE_USER_PASSWORD` et
`HUE_ADMIN_PASSWORD` du service `hue` dans `docker-compose.yml`. Elles ne
s'appliquent qu'à la création ; un mot de passe changé ensuite dans Hue est
conservé.

Vérification de bout en bout côté serveur : connexion `hue` / `hue`, puis
chargement de la configuration de l'interface.

```bash
docker exec hue /usr/share/hue/atelier-check.sh
```

Si ce test affiche `OK` mais que la page reste blanche, le problème vient du
navigateur. Il conserve en cache des données d'un autre Hue servi auparavant
à la même adresse (par exemple celui du projet Big-Data-Cluster). Ouvrez Hue
dans une fenêtre de navigation privée, ou effacez les données du site
`localhost:8888` (F12 → *Application* → *Storage* → *Clear site data*), ou
utilisez http://127.0.0.1:8888 (autre origine, donc ni cache ni stockage
partagés).

| Menu Hue | Branché sur |
|---|---|
| Éditeur **Hive** | HiveServer2 (`hiveserver2:10000`) |
| Éditeur **Impala** | `impalad:21050` |
| **Fichiers** | HDFS via WebHDFS (`namenode:9870`) |
| **Tables** | metastore, via HiveServer2 |
| **Jobs** | YARN ResourceManager |
| **HBase** | `hbase-thrift:9090` |

Les comptes, l'historique et les requêtes sauvegardées de Hue sont stockés dans
le PostgreSQL `hue-db`, sur le volume `hue_db_data`.

