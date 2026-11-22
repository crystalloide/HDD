# Notes techniques de la pile (héritées du dépôt BD540)

> Ce document reprend les notes techniques du dépôt [crystalloide/BD540](https://github.com/crystalloide/BD540), dont la pile Docker de ce lab est issue. Les adaptations propres aux hand-labs HDD sont décrites dans le [README](../README.md#adaptations-de-la-pile-pour-les-tp-hdd).


- **`/tmp` lui-même doit être ouvert en écriture (`1777`), pas seulement
  ses sous-dossiers.** Le moteur MapReduce classique
  (`hive.execution.engine=mr`) crée son répertoire de staging directement
  sous `/tmp` (`/tmp/hadoop-yarn/staging/hive/.staging`) au premier job
  soumis ; `/tmp` était resté à sa permission HDFS par défaut (`755`,
  propriétaire `hadoop`), ce qui bloquait l'utilisateur `hive`
  (`Permission denied: user=hive, access=WRITE, inode="/tmp"`). Corrigé en
  ouvrant `/tmp` lui-même dans `init-tez.sh` — même famille de bug que
  `/user/hive` plus haut : chmoder les sous-dossiers qu'on crée ne suffit
  pas si le dossier parent, lui, reste fermé.
- **`/opt/tez/lib/` embarque aussi `commons-collections-3.2.2.jar`.** Du
  code interne à `hive-exec-4.1.0.jar` (`Operator.initializeChildren`)
  utilise encore l'ancienne bibliothèque `commons-collections`
  (`org.apache.commons.collections.CollectionUtils`, pas
  `commons-collections4`), que Hadoop 3.4.x n'embarque plus par défaut —
  chaque tâche Tez qui initialise un opérateur plantait avec
  `NoClassDefFoundError` sans ce jar. Il est placé dans `/opt/tez/lib/`
  car ce chemin fait déjà partie de `yarn.application.classpath`
  (`hadoop/config`, dupliqué dans `hive-conf/yarn-site.xml`), donc
  disponible pour l'AM et toutes les tâches sans configuration par job. Si
  une erreur `NoClassDefFoundError` similaire réapparaît pour une autre
  classe, la même recette s'applique : trouver le jar Maven correspondant
  et le déposer au même endroit.
- **Les conteneurs Hadoop tournent en JDK 17, pas en JDK 8 (par défaut de
  l'image `apache/hadoop:3.4.2`).** Deux problèmes distincts avec l'image
  officielle `apache/hive` (4.1.0) : (1) elle ajoute automatiquement des
  options JVM `--add-opens=...` en soumettant un job Tez, qu'un JDK 8 ne
  reconnaît pas ("Unrecognized option") ; (2) `hive-exec-4.1.0.jar` est
  compilé pour cibler le bytecode Java 17 (class file version 61) — un
  JDK 11, qui accepte pourtant la syntaxe `--add-opens` (JDK9+), ne peut
  toujours pas charger ces classes (`UnsupportedClassVersionError`). Les
  deux se règlent en passant Hadoop sur JDK 17. Bug connu et non réglable
  côté configuration Hive/Tez, voir
  [HIVE-29015](https://issues.apache.org/jira/browse/HIVE-29015), où le
  rapporteur confirme avoir testé exactement cette combinaison (Hadoop
  3.4.1 sous JDK 17) avec succès.
  **Installé par téléchargement direct d'une archive Eclipse Temurin
  (Adoptium), pas via `yum`** : cette image est basée sur CentOS 7, dont
  les dépôts `os`/`updates` pour ce point de version précis (7.6.1810) ont
  disparu des miroirs publics depuis la fin de vie de CentOS 7 (juin
  2024) — `yum install` y échoue désormais quasiment à chaque fois. Voir
  `hadoop/Dockerfile`.
- **`/user/hive` doit être accessible en écriture à l'utilisateur `hive`.**
  Au premier lancement d'une session Tez, Hive met en cache un jar de
  session sous `/user/<utilisateur>` sur HDFS — ici `/user/hive`, qui
  n'appartenait qu'à `hadoop` (celui qui exécute `init-tez.sh`), pas à
  `hive` (celui qui fait tourner HiveServer2) :
  `Permission denied: user=hive, access=WRITE`. Corrigé dans
  `hadoop/init-tez.sh`, qui ouvre `/user/hive` en écriture pour tout le
  monde (`chmod -R 1777`).
  Ce répertoire est **volontairement laissé sur HDFS**, pas redirigé vers
  un chemin local (`hive.user.install.directory`) comme le fait le
  quickstart officiel Apache Hive — une piste explorée puis abandonnée ici,
  documentée directement dans `hive-conf/hive-site.xml` : ce raccourci ne
  fonctionne que pour un Hive en mode local/mono-processus (leur
  quickstart par défaut), pas pour un vrai cluster YARN multi-conteneurs
  comme celui-ci, où le NodeManager qui "localise" ce jar pour lancer l'AM
  Tez est un conteneur différent de `hiveserver2` et ne voit donc aucun
  chemin local à ce dernier.
- **`hive/Dockerfile` ajoute `findutils` par-dessus `apache/hive:4.1.0`.**
  Cette image officielle (base `eclipse-temurin ubi9-minimal`) n'installe
  pas `find`, alors que son propre `entrypoint.sh` s'en sert pour appliquer
  `HIVE_CUSTOM_CONF_DIR` — le mécanisme qui pointe Hive vers notre cluster
  HDFS/YARN/Tez. Sans ce correctif, `find` échoue silencieusement (le
  script continue sans erreur bloquante) et **toute** la configuration de
  `hive-conf/` est ignorée : Hive tombe alors sur ses réglages par défaut,
  déconnectés du cluster. `metastore`, `hiveserver2`, `tezam`, `llapdaemon`
  et `hiveserver2-llap` utilisent tous cette image corrigée.
- **Pas de volume nommé pour le Derby du metastore.** Un volume Docker
  nommé fraîchement créé appartient à `root` par défaut, alors que le
  processus Hive tourne avec un utilisateur non-root (`hive`, uid 1000) :
  Derby ne peut alors plus créer sa base au premier démarrage
  (`Failed to create database`). Comme la persistance entre sessions
  n'est de toute façon pas nécessaire pour cet atelier (on repart d'un état
  propre à chaque fois avec `docker compose down -v`), le plus sûr est de
  ne pas monter de volume ici : la base Derby vit dans la couche writable
  du conteneur `metastore`, avec les bonnes permissions héritées de l'image.
- **Hive 4.1.0** a été choisi (plutôt que 4.0.x ou 4.2.x) car c'est la
  version dont le couple Hadoop/Tez annoncé par le projet Apache Hive
  (Hadoop 3.4.1 / Tez 0.10.5) colle le mieux à la version du cluster
  (Hadoop 3.4.2 / Tez 0.10.5) — Tez identique, Hadoop quasi identique.
- **`hive-conf/mapred-site.xml` met `mapreduce.framework.name=yarn`**
  (classique), volontairement différent du `yarn-tez` utilisé sur les
  conteneurs Hadoop bruts (`hadoop/config`, hérité du dépôt de référence
  pour lancer un `hadoop jar ... wordcount` directement accéléré par Tez).
  Si Hive héritait de `yarn-tez`, `SET hive.execution.engine=mr;` serait
  silencieusement réexécuté par Tez, et l'atelier ne pourrait plus montrer
  d'écart entre les deux moteurs.
- Le métastore utilise Derby **embarqué**, mais dans son propre conteneur
  dédié : `hiveserver2` (et `hiveserver2-llap`) s'y connectent uniquement
  en Thrift, jamais en direct — ce qui évite la limitation Derby
  « un seul processus à la fois » tout en gardant l'environnement simple
  (pas de Postgres à faire tourner ni de driver JDBC à télécharger).

## Pourquoi ces versions pour les composants ajoutés

- **Spark 4.0.4 et non Spark 3.x : le metastore Hive 4.1.0 a supprimé l'appel
  Thrift `get_table`.** Le client Hive 2.3 intégré à tous les Spark 3.x (et à
  Spark 4 par défaut) l'utilise encore. Avec ce metastore, toute lecture du
  catalogue échoue sur `Invalid method name: 'get_table'`. Ce n'est pas une
  hypothèse : la comparaison des fichiers `hive_metastore.thrift` de Hive 2.3 et
  4.1.0 montre la suppression de `get_table`, de `get_table_objects_by_name` et
  des API d'index.

  Spark 4.0 sait charger un **client metastore Hive 4.0** dans un class loader
  isolé (SPARK-45265). On embarque donc les jars de Hive 4.0.1, copiés depuis
  l'image officielle `apache/hive:4.0.1`, et on les active dans
  `spark/conf/spark-defaults.conf` :
  `spark.sql.hive.metastore.version=4.0.1`,
  `spark.sql.hive.metastore.jars=path`. Tous les appels Thrift du client 4.0.1
  existent dans le metastore 4.1.0 (vérifié sur les fichiers `.thrift` : aucune
  méthode retirée entre les deux).

  Spark 4.1 supporterait directement un client 4.1.0, mais Zeppelin 0.12.1 ne
  supporte pas encore Spark 4.1 : Spark 4.0.4 est la dernière version compatible
  avec les deux.

- **Zeppelin 0.12.1** supporte officiellement Spark 4.0 (ZEPPELIN-6086 ; testé
  par sa CI en Scala 2.13 sur JDK 17). L'image Zeppelin est construite *sur*
  l'image Spark : même Spark, même Python (3.10) côté driver (Zeppelin) et côté
  executors (worker), ce qu'exige PySpark.

  Deux JDK cohabitent, aiguillés par `zeppelin/conf/zeppelin-env.sh` :
  - le **serveur** tourne en JDK 11, seul JDK validé par le projet pour le
    serveur ;
  - les **interpréteurs** tournent en JDK 17, indispensable pour Spark 4 et pour
    le pilote JDBC Hive 4.1.0, compilé pour Java 17.

  `USE_HADOOP=false` empêche `bin/zeppelin.sh` d'ajouter tout
  `hadoop classpath` au classpath du serveur.

- **`%sh` dans Zeppelin.** L'interpréteur shell a été **retiré des binaires
  officiels** de Zeppelin depuis la 0.11.1 (« [HOTFIX] Disable shell
  interpreter »). Le TP l'utilise : il est réinstallé depuis Maven Central
  (`org.apache.zeppelin:zeppelin-shell:0.12.1`) pendant le build. Seul `%sh` est
  déclaré : `%sh.terminal` dépend de pty4j, hébergé hors de Maven Central.
  Comme pour tout notebook, `%sh` exécute des commandes dans le conteneur : ne
  publiez pas le port 8082 en dehors du poste du stagiaire.

- **`%hive` / `%impala`** utilisent le pilote `hive-jdbc-4.1.0-standalone`, de
  la même version que HiveServer2. Impala parle le même protocole
  HiveServer2 (`auth=noSasl`).

- **HBase 2.6.7.** La branche 2.6 est la première où JDK 17 est officiellement
  supporté (2.5.x : support préliminaire), et elle supporte Hadoop 3.4 depuis la
  2.6.2. Choix de configuration :
  - WAL `filesystem` plutôt qu'`asyncfs`, qui accède par réflexion aux classes
    internes du client HDFS ;
  - `dfs.replication=1`, car il n'y a qu'un DataNode ;
  - serveur Thrift **v1** en transport *buffered*, le seul format supporté par
    Hue.

  ZooKeeper est le même conteneur que celui du bonus LLAP. Sa liste de
  commandes « 4 lettres » autorisées est seulement élargie (`srvr`, `stat`,
  `mntr`) pour l'UI HBase.

- **Impala 4.5.2** (images officielles `apache/impala`). Deux contraintes
  viennent de ces images :
  - les noms de service `statestored` et `catalogd` sont codés en dur dans
    leur `ENTRYPOINT` ;
  - `catalogd` démarre avec `-hms_event_polling_interval_s=1`. Au démarrage, il
    vérifie que le metastore a `hive.metastore.dml.events=true` et **refuse de
    démarrer** sinon. Ce réglage a été ajouté à `hive-conf/hive-site.xml`, avec
    le `DbNotificationListener`, déjà présent dans l'image Hive 4.1.0, qui
    produit les événements. Bénéfice : synchronisation automatique Hive/Spark →
    Impala.

  Le client metastore d'Impala (CDP Hive 3.1.3000) utilise `get_table_req`, pas
  `get_table` : il est compatible avec le metastore 4.1.0. Deux différences
  avec le client Hive 4 imposent toutefois des réglages :
  - **Nom du réseau Docker.** Le client CDP remplace l'hôte de
    `hive.metastore.uris` par son nom canonique, obtenu par DNS inverse. Le DNS
    de Docker répond `<conteneur>.<réseau>`. Avec le réseau par défaut
    `hdd-lab_default`, le résultat (`metastore.hdd-lab_default`)
    contient un `_`, interdit dans une URI Java : catalogd boucle sur
    `URISyntaxException` puis s'arrête. Le réseau est donc nommé
    explicitement `hdd-lab-net`, à la fin de `docker-compose.yml`.
    Le client Hive 4 de HiveServer2 et de Spark n'est pas concerné : il garde
    l'URI telle quelle.
  - **Format des événements.** Hive 4 écrit par défaut ses événements en gzip
    (`GzipJSONMessageEncoder`), alors qu'Impala choisit son décodeur d'après sa
    propre configuration. Les deux côtés sont alignés sur `JSONMessageEncoder`
    (`hive-conf/hive-site.xml` et `impala/conf/hive-site.xml`). Sans cet
    alignement, catalogd démarre, mais la synchronisation automatique passe en
    erreur au premier `CREATE TABLE`.
  - **Type d'accès des tables (IMPALA-10792).** Le metastore Hive 4 calcule
    pour chaque table un « type d'accès » (lecture, écriture...) d'après les
    capacités que déclare le client. La version CDP d'Impala, celle des images
    officielles, se fie entièrement à ce champ. Or il arrive vide face au
    metastore Apache Hive 4. Toute requête est alors refusée :
    `AnalysisException: Operations not supported. Table x access type is: NONE`.
    La seule solution proposée en amont est de recompiler Impala contre
    Apache Hive (`USE_APACHE_HIVE=true`). L'image `impalad` de l'atelier
    (`impala/Dockerfile`) reprend donc l'image officielle et ne corrige que deux
    méthodes de `MetastoreShim`, dans le jar `impala-frontend`. Si le
    metastore ne fournit pas le type d'accès, il est calculé comme le fait le
    transformateur de Hive 4 (`MetastoreDefaultTransformer`) pour les
    capacités d'Impala. C'est ce que fait déjà la variante « Apache Hive »
    d'Impala. Résultat : tables externes et gérées en lecture/écriture, vues
    en lecture seule. Un type d'accès fourni par le metastore reste toujours
    prioritaire. Le build exécute un auto-test contre les vraies classes de
    l'image et vérifie le bytecode produit. Sources : `impala/patch/`.

  Limite connue : les statistiques de colonnes `TIMESTAMP` calculées par Hive 4
  ne sont pas relues par Impala 4.5.2 (IMPALA-15361, corrigé après la 4.5.2).
  Cela n'affecte que l'optimiseur, pas les résultats.

- **Hue 4.11.0**, dernière version publiée de Hue (les autres tags de l'image
  sont des builds quotidiens). Points de configuration :
  - `hue/hive-conf/hive-site.xml` reflète le HiveServer2 de l'atelier
    (`doAs=false`, authentification `NONE`) : Hue ne demande pas
    d'impersonation ;
  - `hive.metastore.uris` en est volontairement absent : Hue passe uniquement
    par HiveServer2. Son client Thrift direct du metastore est antérieur à
    Hive 4 ;
  - l'explorateur de fichiers utilise WebHDFS avec l'utilisateur proxy `hue`,
    autorisé dans `hadoop/config` (`hadoop.proxyuser.hue.*`) ;
  - **compte `hue` / `hue` administrateur.** `hue` est l'utilisateur interne
    que Hue crée lui-même (id 1100713), désactivé et sans mot de passe, et qui
    possède les exemples. Pour cette raison, l'écran « Create your account »
    refuse ce nom. `hue/atelier_hue_user.py` l'active au démarrage, avec les
    droits administrateur et le mot de passe `hue`. Hue retrouve cet
    utilisateur par son id et ne réinitialise jamais ces attributs. Un compte
    de secours `admin` est créé en plus : tant qu'il n'existe aucun autre
    utilisateur, Hue reste en mode « première connexion » et refuse toute
    connexion normale ;
  - **cookies propres à l'atelier** (`hue_atelier_sessionid`,
    `hue_atelier_csrftoken`). Un cookie est lié au nom d'hôte, pas au port :
    tout autre Hue ou application Django ouvert sur `localhost` (par exemple le
    Hue 4.6 du projet Big-Data-Cluster, lui aussi sur le port 8888) écrit les
    mêmes cookies `sessionid` et `csrftoken`. Or Hue 4.11 recopie la valeur
    brute du cookie CSRF dans la page (`window.CSRF_TOKEN`). Après une
    réécriture par une autre application, chaque action se termine par
    « 403 CSRF error ». Le cookie de session se renomme dans `hue/z-hue.ini`.
    Le nom du cookie CSRF est codé en dur : `hue/Dockerfile` le remplace dans
    les sources de Hue, et le build échoue s'il en reste une occurrence.

- **[Lab HDD : remplacé]** Le lab HDD **réactive** le contrôle (`dfs.permissions.enabled=true`) avec un masque de création `000` dans tous les clients : voir le README, section « Adaptations ». Note d'origine, BD540 : **Contrôle des permissions HDFS désactivé** (`dfs.permissions.enabled=false`
  dans `hadoop/config`). Chaque moteur écrit sous une identité différente :
  `hive`, `root` (Zeppelin, Spark, HBase), `impala`, l'utilisateur Hue. Sans ce
  réglage, une table créée par un moteur ne pourrait pas être alimentée ou
  supprimée par un autre, ce qui casserait l'intérêt pédagogique d'un catalogue
  partagé. Les `chmod` de `init-tez.sh` sont conservés.

- **Journaux Hive sans avertissement Log4j.** Les configurations Log4j
  fournies par Hive 4.1.0 déclarent `packages = org.apache.hadoop.hive.ql.log`.
  Log4j 2.24, embarqué par l'image, signale cette option comme dépréciée à
  chaque démarrage de JVM (« The use of package scanning to locate Log4j
  plugins is deprecated »). On en voit plusieurs par service : schematool, le
  service, puis la réinitialisation des journaux. Ces fichiers n'utilisent que
  des composants standard de Log4j. Des copies sans cette ligne sont placées
  dans `hive-conf/` et remplacent celles de l'image via `HIVE_CUSTOM_CONF_DIR`.
  Pour `lab-init`, dont le script remplace l'entrypoint de l'image, les liens
  sont créés par `scripts/lab-init.sh`.
  Les lignes `SLF4J: Class path contains multiple SLF4J bindings` sont un autre
  avertissement, lui aussi sans conséquence : Hadoop et Hive embarquent chacun
  une liaison SLF4J, et SLF4J choisit celle de Hive. Il n'est pas supprimé :
  il faudrait pour cela retirer un jar de l'image, ce qui couperait les
  messages des commandes `hdfs`. `benchmark_engines.sh` le masque.

- **Téléchargements Apache robustes.** `downloads.apache.org` et `dlcdn` ne
  conservent que la dernière version de chaque projet. Tous les téléchargements
  (Tez, HBase, Zeppelin) se replient automatiquement sur `archive.apache.org`.
  Le build reste ainsi reproductible après la sortie d'une version plus récente.

## Modifications apportées aux fichiers du projet d'origine

Les versions ne changent pas. Les seules retouches du socle sont additives :

| Fichier | Modification |
|---|---|
| `hadoop/config` | utilisateur proxy `hue` ; `dfs.permissions.enabled=false` ; WebHDFS explicitement activé ; part YARN des ApplicationMasters portée de 0.5 à 0.8 (les sessions Tez de Hue et Zeppelin ne bloquent plus le job MapReduce du benchmark) |
| `hadoop/init-tez.sh` | création de `/spark-logs`, `/user/data` (TP N1) et `/hbase` |
| `hadoop/Dockerfile` | repli sur `archive.apache.org` pour Tez 0.10.5 |
| `hive-conf/hive-site.xml` | `hive.metastore.dml.events` + `DbNotificationListener` + événements en JSON non compressé (Impala) |
| `hive-conf/core-site.xml` | utilisateur proxy `hue` (filet de sécurité) |
| `hive-conf/*-log4j2.properties` (nouveaux) | copies des configurations Log4j de Hive 4.1.0 (`hive`, `beeline`, `metastore`, `hive-exec`) sans la ligne `packages` : plus d'avertissement « package scanning » dans les journaux |
| `docker-compose.yml` | `zookeeper` partagé (profils `llap`, `hbase`, `full`) + nouveaux services + réseau nommé `hdd-lab-net` (sans `_`) |
| `scripts/benchmark_engines.sh` | mesures Impala et Spark SQL en bonus, si ces services tournent ; avertissements SLF4J/Log4j de beeline masqués ; applications YARN déjà actives signalées ; point d'étape toutes les 20 s (non compté dans les temps) |

Nouveaux fichiers : `spark/`, `zeppelin/`, `hbase/`, `impala/`, `hue/`,
`notebooks/TP_N1.ipynb`, `data/transactions.csv`,
`scripts/00_demo_sales_db.hql`, `scripts/lab-init.sh`,
`scripts/check_stack.sh`, `scripts/spark/*.py`, `url/*.url`, `.dockerignore`.
