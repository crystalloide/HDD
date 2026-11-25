# HDD — Hand-labs de la formation ORSYS « Hadoop, développement »

Environnement Docker Compose prêt à l'emploi pour réaliser les **travaux pratiques de la formation HDD** (3 jours, 21 h) : un cluster Hadoop complet sur le poste du stagiaire, les jeux de données, le code des TP et les **notebooks Zeppelin** (énoncés et corrigés).

| TP | Programme HDD | Outils | Notebook |
|---|---|---|---|
| **TP1** | Gérer la collecte d'informations clientèles par MapReduce · Développement d'une tâche basée sur MapReduce | HDFS, MapReduce Java, YARN, JobHistory, Hive (bonus) | `TP1 - Collecte clients et taches MapReduce` |
| **TP2** | Configuration de l'implémentation YARN | YARN, Capacity Scheduler, ResourceManager, JobHistory | `TP2 - Configuration de l implementation YARN` |
| **TP3** | HBase : gérer les modifications d'un catalogue de données | HBase shell, API Java HBase, happybase, Hive, Impala | `TP3 - HBase - Gerer les modifications d un catalogue` |
| **TP4** | Pig, Hive (Java) : administrer un référentiel client partagé sur Hadoop · Utilisation de la console de visualisation | HDFS (droits, ACL, quotas, instantanés, fsck), Pig + UDF Java, PigServer, Hive, Impala, JDBC Java, Hue, Zeppelin | `TP4 - Referentiel client partage - Pig Hive Java et console` |
| **TP5** | Spark : administrer un référentiel client partagé sur Hadoop · Utilisation de la console de visualisation | Spark (DataFrames), Spark SQL, Parquet, metastore Hive, Impala, Spark UI / History, Hue, Zeppelin | `TP5 - Referentiel client partage - Spark Spark SQL et console` |

Les notebooks sont tous dans Zeppelin (http://localhost:8082), dossier **HDD** :

```
HDD/
├── 0 - Demarrage     00 - Prise en main et démonstration Hadoop (chapitre 1), Demo ecosysteme
├── 1 - Enonces       TP1 à TP5 à compléter (TODO)
├── 2 - Corriges      TP1 à TP5 complets, avec réponses aux questions
└── 3 - Complements   exercices HBase supplémentaires
```

Chaque notebook se termine par un paragraphe **« Contrôle automatique »** qui vérifie les critères de réussite du TP (`[ OK ]` / `[ KO ]`).

## Composants et versions

| Composant | Version | Rôle dans les TP |
|---|---|---|
| Hadoop (HDFS, YARN, **JobHistory**) | 3.4.2 (JDK 17) | tous ; JobHistory : TP1, TP2 |
| MapReduce (client Java) | 3.4.2 | TP1, TP2, Pig |
| Tez | 0.10.5 | moteur de Hive |
| Hive (metastore + HiveServer2) | 4.1.0 | TP1 bonus, TP3, TP4, TP5 |
| **Pig** | 0.18.0 | TP4 |
| HBase (+ ZooKeeper 3.8.4) | 2.6.7 | TP3 |
| Spark | 4.0.4 (Python 3.10) | TP5 |
| Impala | 4.5.2 | TP3, TP4, TP5 |
| Zeppelin | 0.12.1 | notebooks de tous les TP |
| Hue | 4.11.0 (PostgreSQL 15) | TP4, TP5 (console de visualisation) |

La pile est reprise du dépôt [crystalloide/BD540](https://github.com/crystalloide/BD540) : mêmes versions, mêmes correctifs de compatibilité (détaillés dans [docs/notes-techniques.md](docs/notes-techniques.md)), plus les [adaptations propres aux TP HDD](#adaptations-de-la-pile-pour-les-tp-hdd).

## Prérequis

- Docker Engine 23+ avec Compose v2 et BuildKit (ou Docker Desktop récent), machine **x86_64 / amd64** (Ubuntu conseillé).
- Machine de **4 CPU** minimum (8 conseillés) et mémoire allouée à Docker de **16 Go** minimum pour le profil `full` (24 Go conseillés). Chaque conteneur a un plafond CPU et mémoire, avec des tas Java alignés : budget détaillé en tête de `docker-compose.yml`, mesure réelle par `docker stats --no-stream`.
- Machine de 16 Go de RAM au total : `docker-compose-light.yml` (mêmes services, plafonds plus serrés, conçu pour 4 CPU / 16 à 20 Go).
- ~25 Go d'espace disque. Premier build : 15 à 30 minutes (téléchargements Docker Hub, miroirs Apache, Maven Central).
- Ports libres : `9870 9864 8088 8042 19888 10000 10002 8080 8081 18080 8082 4040 2181 16010 16030 9090 9095 21050 25000 25010 25020 8888`.

## Démarrage

```bash
cd ~
sudo rm -Rf HDD
git clone https://github.com/crystalloide/HDD
cd HDD
```
```bash
# Option n°1 : pour lancer tous les TP (recommandé)
docker compose --profile full up -d --build
```
```bash
# Option n°1 2 : pour lancer une version économe en ressources
docker compose -f docker-compose-light.yml --profile full up -d --build
```

Suivre l'initialisation, puis attendre que les services soient `healthy` (3 à 5 minutes) :

```bash
docker compose logs tez-init          # doit finir par « Tez-Init : TERMINÉ avec succès ! »
```
```bash
docker compose --profile full ps
```
```bash
bash scripts/check_stack.sh            # chaque ligne doit afficher [ OK ]
```
```bash
bash scripts/check_stack.sh --complet  # + un paragraphe par interpréteur Zeppelin et un vrai job MapReduce
```

Les services `tez-init`, `lab-init` et `hbase-init` s'arrêtent d'eux-mêmes (`Exited (0)`) : c'est normal.

Ouvrir ensuite **Zeppelin : http://localhost:8082**, notebook *HDD / 0 - Demarrage / 00 - Prise en main*.

### Profils et TP

| Commande | TP possibles |
|---|---|
| `docker compose --profile full up -d --build` | tous |
| `docker compose --profile zeppelin up -d --build` | TP1, TP2 (Zeppelin + Spark, sans HBase, Impala, Hue) |
| `docker compose --profile zeppelin --profile hbase up -d --build` | + TP3 (sauf la requête Impala) |
| `docker compose up -d --build` | socle seul : HDFS, YARN, JobHistory, Hive |

## Consoles web

| Console | URL | Profil |
|---|---|---|
| NameNode (HDFS) | http://localhost:9870 | socle |
| DataNode | http://localhost:9864 | socle |
| ResourceManager (YARN) | http://localhost:8088 | socle |
| NodeManager | http://localhost:8042 | socle |
| **JobHistory (MapReduce)** | **http://localhost:19888** | socle |
| HiveServer2 | http://localhost:10002 | socle |
| **Zeppelin** | **http://localhost:8082** | zeppelin |
| Driver Spark lancé par Zeppelin | http://localhost:4040 | zeppelin |
| Spark Master / Worker / History | http://localhost:8080 / 8081 / 18080 | spark |
| HBase Master / RegionServer / Thrift | http://localhost:16010 / 16030 / 9095 | hbase |
| Impala (impalad / statestore / catalog) | http://localhost:25000 / 25010 / 25020 | impala |
| **Hue** (`hue` / `hue`) | **http://localhost:8888** | hue |

Raccourcis dans le dossier `url/`.

## Données des TP

`data/hdd/` (monté dans Zeppelin sous `/opt/data/hdd`), généré par `scripts/generer_donnees_hdd.py` (données fictives, reproductibles) :

| Fichier | Contenu |
|---|---|
| `clients/crm_2026-11.csv`, `web_2026-11.csv`, `magasins_2026-11.csv` | 36 712 lignes clients sur 3 canaux, avec anomalies volontaires (en-têtes, villes mal saisies ou absentes, lignes mal formées, CA invalides, doublons exacts) |
| `catalogue/produits.csv`, `modifications.csv`, `promos.csv` | catalogue de 120 produits, 3 vagues de changements de prix datés, 15 promotions |
| `attendus.json` | valeurs attendues, utilisées par les contrôles automatiques |

Détail : [data/hdd/README.md](data/hdd/README.md).

## Comptes du lab

L'authentification est « simple » (sans Kerberos) : HDFS croit l'identité annoncée par le client, que les TP choisissent avec `HADOOP_USER_NAME`.

| Compte | Groupe | Rôle |
|---|---|---|
| `hadoop` | *(superutilisateur HDFS)* | administration : quotas, instantanés, `chown`, `fsck` |
| `crm_admin`, `alice` | `crm` | propriétaires du référentiel client (TP4, TP5) |
| `bob` | `marketing` | lecteur autorisé par ACL |
| `eve` | `stagiaires` | hors groupe : accès refusé |
| `root`, `hive`, `impala`, `hue` | — | comptes de service de Zeppelin/Spark, HiveServer2, Impala, Hue |
| Hue : `hue` / `hue`, `admin` / `admin` | | connexion à Hue |

## Organisation du dépôt

```
HDD/
├── docker-compose.yml, docker-compose-light.yml
├── hadoop/ hive/ hive-conf/ hbase/ impala/ hue/ spark/   images et configuration de la pile
├── zeppelin/notebook/HDD/      notebooks des TP (copiés dans l'image Zeppelin)
├── tp/                         sources des TP, montées dans Zeppelin sous /opt/tp (lecture seule)
│   ├── tp1-mapreduce/          Java MapReduce (pom.xml)
│   ├── tp2-yarn/               file « dev » du Capacity Scheduler, mesure des jobs
│   ├── tp3-hbase/              Java HBase (pom.xml), export happybase, HiveQL
│   ├── tp4-pig-hive/           Pig Latin, UDF Java, PigServer, client JDBC (pom.xml), HiveQL
│   ├── tp5-spark/              PySpark batch (spark-submit)
│   └── commun/                 préparation de la zone du référentiel
├── data/hdd/                   jeux de données des TP
├── scripts/                    check_stack.sh, génération des données, atelier moteurs Hive
├── docs/                       guide formateur, correspondance programme, notes techniques
├── tools/notebooks/            générateur des notebooks énoncés/corrigés à partir de tp/
└── url/                        raccourcis vers les consoles
```

Les notebooks compilent le code Java avec `javac` dans le conteneur Zeppelin (sans Maven ni Internet). Les `pom.xml` servent à travailler dans un IDE : voir [tp/README.md](tp/README.md).

Pour faire évoluer un TP : modifier la source dans `tp/` (ou le texte dans `tools/notebooks/tpN.py`), puis `python3 tools/notebooks/generer.py` régénère l'énoncé et le corrigé ensemble.

## Adaptations de la pile pour les TP HDD

Par rapport au dépôt BD540 :

| Élément | Adaptation | Pourquoi |
|---|---|---|
| `historyserver` (nouveau service) | JobHistory Server MapReduce, port 19888 | suivi des jobs terminés (TP1, TP2, Pig) |
| `hadoop/config` | `mapreduce.framework.name=yarn` (au lieu de `yarn-tez`) ; adresses du JobHistory ; `yarn.log.server.url` | vrais jobs MapReduce, visibles dans le JobHistory |
| `hadoop/config` | permissions HDFS **actives**, ACL actives, masque de création `000` ; groupes des comptes de test (`hadoop.user.group.static.mapping.overrides`) | le TP référentiel protège une zone par droits et ACL ; le masque `000` laisse tout le reste partagé entre moteurs, comme avant |
| `hive-conf/`, `spark/hadoop-conf/`, `impala/conf/`, `hbase/conf/` `core-site.xml` | `fs.permissions.umask-mode=000` | idem, côté clients |
| `hadoop/init-tez.sh` | `/data`, `/demo`, répertoires personnels des comptes ; `/user/hadoop` en `1777` | la racine HDFS n'est plus ouverte en écriture |
| `spark/hadoop-conf/mapred-site.xml` (nouveau), `yarn-site.xml` | client MapReduce de Zeppelin : YARN, JobHistory, conteneurs de 512 Mo | `yarn jar`, `pig`, `hadoop jar` depuis Zeppelin |
| `spark/Dockerfile` (cible zeppelin) | **Apache Pig 0.18.0** (`/opt/pig`) | TP4 |
| `docker-compose*.yml` | `nodemanager` : capacité réglable par `NM_MEMORY_MB` / `NM_VCORES` ; ports 8042 et 9864 ; montage `./tp` dans Zeppelin ; projet, images et réseau renommés `hdd-lab` | TP2 ; consoles ; sources des TP ; cohabitation avec BD540 |
| `docker-compose*.yml`, `zeppelin/conf/zeppelin-env.sh` | plafonds `cpus` / `mem_limit` sur chaque service, tas Java alignés (`HADOOP_HEAPSIZE_MAX`, `SERVICE_OPTS`, `HBASE_HEAPSIZE`...), poids CPU réduit pour `nodemanager` et `spark-worker` ; healthchecks NameNode / ResourceManager par curl au lieu d'une JVM cliente ; `ZEPPELIN_MEM` / `ZEPPELIN_INTP_MEM` du compose pris en compte | aucun service ne peut affamer les autres ; redémarrage `stop` / `up` possible sans blocage en safe mode |
| `scripts/check_stack.sh` | contrôles JobHistory, permissions, groupes, Pig, javac, sources des TP ; option `--complet` | vérification avant la session |
| `scripts/check_interpreteurs.sh` (nouveau) | présence, réglages et exécution réelle des interpréteurs Zeppelin des TP (`%sh`, `%hive`, `%impala`, `%hbase`, `%spark.pyspark`, `%spark.sql`, `%python`, `%md`, `%file`, `%java`) | vérification avant la session ; voir [docs/composants.md](docs/composants.md) |

## Réinitialiser

```bash
# Tout arrêter et repartir de zéro (HDFS, metastore, notebooks modifiés, base Hue)
docker compose --profile full --profile llap down -v
```
```bash
# Ou Réinstaller seulement les notebooks d'origine (après une mise à jour du dépôt)
docker compose --profile full rm -sf zeppelin && docker volume rm hdd-lab_zeppelin_notebook
```
```bash
# Et relancer
docker compose --profile full up -d --build zeppelin
```

> **HDFS n'est pas sur un volume Docker.** Recréer `namenode` ou `datanode` vide HDFS ; `tez-init` et `lab-init` remettent les répertoires et les données de démonstration, mais les données des TP sont perdues. Compose recrée un conteneur dès que sa configuration change : après une mise à jour de `hadoop/config` (partagé par tous les services Hadoop), un `docker compose --profile full up -d` recrée donc toute la partie Hadoop. Pour ne recréer qu'un service, ajouter `--no-deps` (exemple : `docker compose --profile full up -d --no-deps nodemanager`).

HDFS n'a pas de volume persistant : recréer le conteneur `namenode` efface les données des TP (le TP2 ne recrée que le `nodemanager`).

## Dépannage

| Symptôme | Cause probable / solution |
|---|---|
| `yarn jar` depuis Zeppelin reste en `LocalJobRunner` (`job_local...`) | `/opt/hadoop-conf/mapred-site.xml` absent : image Zeppelin ancienne. `docker compose --profile full up -d --build zeppelin` |
| Job MapReduce bloqué en `ACCEPTED` | ressources YARN prises par des sessions Tez (Hue, Zeppelin `%hive`) ou NodeManager réduit (TP2). `yarn application -list`, `yarn application -kill <id>`, ou remettre la capacité : `docker compose --profile full up -d --no-deps nodemanager` |
| `Permission denied: user=root ... inode="/"` | création d'un répertoire à la racine HDFS : utiliser `/data/...` (ouvert) ou le superutilisateur (`HADOOP_USER_NAME=hadoop`) |
| `Permission denied` sur `/data/referentiel/...` pour Hive, Impala ou Spark | ACL du compte de service manquante (TP4 étape 2) : `bash /opt/tp/commun/preparer_referentiel.sh` depuis Zeppelin remet la zone en état |
| `pig: command not found` | Pig n'a pas pu être téléchargé au build (miroirs Apache) : voir la sortie du build, puis `docker compose --profile full build --no-cache zeppelin` |
| `The DiskSpace quota ... is exceeded` | quota d'espace inférieur à un bloc (128 Mo) : voir TP4 étape 3.2 ; `HADOOP_USER_NAME=hadoop hdfs dfsadmin -clrSpaceQuota <rép>` |
| `create 'catalogue'` : `Table already exists` | TP3 relancé : `disable 'catalogue'` puis `drop 'catalogue'` dans `%hbase` |
| Impala ne voit pas une table | `INVALIDATE METADATA base.table;` |
| Programme Spark en `WAITING` (version légère) | l'application Spark de Zeppelin occupe les cœurs du worker : redémarrer l'interpréteur `spark` |
| Hue : page blanche, erreur CSRF | voir [docs/composants.md](docs/composants.md#hue--httplocalhost8888) et `docker exec hue /usr/share/hue/atelier-check.sh` |
| Autres symptômes (Impala, HBase, LLAP, Hive) | tableau de dépannage complet hérité de BD540 : [docs/notes-techniques.md](docs/notes-techniques.md) et [docs/composants.md](docs/composants.md) |

## Documentation

- [docs/guide-formateur.md](docs/guide-formateur.md) : préparation des postes, déroulé sur 3 jours, points d'attention par TP.
- [docs/correspondance-programme.md](docs/correspondance-programme.md) : programme ORSYS HDD ↔ support de cours ↔ TP et notebooks.
- [docs/composants.md](docs/composants.md) : interpréteurs Zeppelin, Spark, HBase, Impala, Hue.
- [docs/atelier-moteurs-hive.md](docs/atelier-moteurs-hive.md) : atelier MapReduce / Tez / LLAP sur Hive (démonstration du chapitre 2).
- [docs/notes-techniques.md](docs/notes-techniques.md) : choix de versions et correctifs de compatibilité.

## Licence

GPL-3.0 (voir `LICENSE`), comme le dépôt BD540 dont la pile est issue. Données de test fictives.
