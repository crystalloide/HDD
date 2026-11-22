# -*- coding: utf-8 -*-
from zep import md, code, bar_chart

NAME = "TP5 - Referentiel client partage - Spark Spark SQL et console"
Z = "/data/referentiel/clients"
HDFS = "hdfs://namenode:8020"

P = [
md("""
## TP5 — Référentiel client partagé avec Spark et Spark SQL — console de visualisation

**Objectif** : construire le même référentiel client qu'au TP4, cette fois avec **Spark** (DataFrames et Spark SQL), le partager avec Hive et Impala par le metastore, puis le visualiser et suivre les traitements dans les consoles.

| Étape | Contenu |
|---|---|
| 0. Préparer | zone du référentiel et droits (script idempotent, si le TP4 n'a pas été fait) |
| 1. Lire | fichiers bruts, schéma explicite, mode permissif |
| 2. Nettoyer | doublons exacts, lignes invalides, normalisation des villes |
| 3. Construire | une ligne par client : CA cumulé, canaux |
| 4. Partager | Parquet partitionné dans la zone du référentiel ; table externe Hive, visible d'Impala |
| 5. Interroger | Spark SQL : agrégats, fenêtres, comparaison avec le TP4 |
| 6. Visualiser | graphiques Zeppelin, Spark UI (4040), Spark History (18080), Hue |
| 7. Industrialiser | la même chaîne en batch avec `spark-submit` |

**Critères de réussite** : le référentiel Spark compte autant de clients que prévu ; la même table est visible depuis Spark, Hive et Impala avec les mêmes totaux ; un utilisateur hors groupe ne peut pas lire les fichiers ; un graphique est produit dans la console.

Prérequis : profil `full`. L'interpréteur Spark de Zeppelin agit sur HDFS sous l'identité **`root`** : ce compte de service reçoit une ACL sur la zone du référentiel, comme `hive` et `impala`. Premier paragraphe Spark : 30 à 60 s de démarrage.
""", title="Présentation du TP"),

code("sh", """
bash /opt/tp/commun/preparer_referentiel.sh
""", title="0.1 Préparer la zone du référentiel (idempotent)"),

md("""
Le script reprend les étapes « Organiser » et « Partager » du TP4 et ajoute la zone `spark` : écriture pour `root` (Spark), lecture pour `hive`, `impala` et le groupe `marketing`, avec entrées `default:` héritées.

### Étape 1 — Lire les fichiers bruts
""", title="Étape 1"),

code("spark.pyspark", f"""
from pyspark.sql import functions as F, Window
from pyspark.sql.types import StructType, StructField, StringType

BRUTE = "{HDFS}{Z}/brute"
SORTIE = "{HDFS}{Z}/spark"

# Tout en chaîne de caractères : on contrôle et on convertit nous-mêmes à l'étape 2
schema = StructType([StructField(c, StringType()) for c in
                     ["id", "nom", "ville", "ca", "segment", "canal", "date_inscription"]])
brut = (spark.read
        .option("sep", ";")
        .option("header", "false")       # l'en-tête de chaque fichier sera filtré comme une ligne invalide
        .option("mode", "PERMISSIVE")    # ligne mal formée -> colonnes nulles, pas d'arrêt
        .schema(schema)
        .csv(BRUTE))
print("lignes lues :", brut.count(), "| partitions :", brut.rdd.getNumPartitions())
brut.show(5, truncate=False)
""", title="1.1 Lecture avec un schéma explicite",
enonce=f"""
from pyspark.sql import functions as F, Window
from pyspark.sql.types import StructType, StructField, StringType

BRUTE = "{HDFS}{Z}/brute"
SORTIE = "{HDFS}{Z}/spark"

schema = StructType([StructField(c, StringType()) for c in
                     ["id", "nom", "ville", "ca", "segment", "canal", "date_inscription"]])
# TODO : lire les CSV de BRUTE avec ce schéma : séparateur « ; », sans en-tête, mode PERMISSIVE
brut = None
print("lignes lues :", brut.count(), "| partitions :", brut.rdd.getNumPartitions())
brut.show(5, truncate=False)
"""),

code("spark.pyspark", """
# Les anomalies, vues par Spark
z.show(brut.filter(~F.col("id").rlike(r"^C[0-9]{6}$") | F.col("date_inscription").isNull()
                   | (F.trim(F.col("ville")) == "") | ~F.col("ca").rlike(r"^[0-9]+(\\.[0-9]+)?$")).limit(15))
""", title="1.2 Quelques lignes anormales"),

md("""
### Étape 2 — Nettoyer et normaliser

Mêmes règles qu'au TP1 et au TP4 : doublons exacts supprimés, identifiant `C` + 6 chiffres, CA numérique positif, date `aaaa-mm-jj`, ville normalisée (accents retirés, espaces réduits, majuscules). La normalisation s'écrit avec les fonctions natives de Spark (`translate`, `regexp_replace`, `upper`) : pas d'UDF Python, donc pas d'aller-retour entre la JVM et Python.
""", title="Étape 2"),

code("spark.pyspark", """
ACCENTS  = "àâäáãåçéèêëíìîïñóòôöõúùûüýÿÀÂÄÁÃÅÇÉÈÊËÍÌÎÏÑÓÒÔÖÕÚÙÛÜÝ"
SANS_ACC = "aaaaaaceeeeiiiinooooouuuuyyAAAAAACEEEEIIIINOOOOOUUUUY"

def normalise_ville(col):
    return F.upper(F.regexp_replace(F.trim(F.translate(col, ACCENTS, SANS_ACC)), r"\\s+", " "))

sans_doublons = brut.dropDuplicates()
propre = (sans_doublons
          .filter(F.col("id").rlike(r"^C[0-9]{6}$"))
          .filter(F.col("ca").rlike(r"^[0-9]+(\\.[0-9]+)?$"))
          .filter(F.col("date_inscription").rlike(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$"))
          .withColumn("ville", normalise_ville(F.col("ville")))
          .filter(F.col("ville") != "")
          .select("id", F.trim("nom").alias("nom"), "ville",
                  F.col("ca").cast("double").alias("ca"),
                  F.lower(F.trim("segment")).alias("segment"),
                  F.lower(F.trim("canal")).alias("canal"),
                  "date_inscription")
          .cache())
print("lignes lues       :", brut.count())
print("après doublons    :", sans_doublons.count())
print("lignes valides    :", propre.count())
print("villes distinctes :", propre.select("ville").distinct().count())
""", title="2.1 Règles de nettoyage",
enonce="""
ACCENTS  = "àâäáãåçéèêëíìîïñóòôöõúùûüýÿÀÂÄÁÃÅÇÉÈÊËÍÌÎÏÑÓÒÔÖÕÚÙÛÜÝ"
SANS_ACC = "aaaaaaceeeeiiiinooooouuuuyyAAAAAACEEEEIIIINOOOOOUUUUY"

def normalise_ville(col):
    # TODO : translate (accents) -> trim -> regexp_replace(r"\\s+", " ") -> upper
    return col

sans_doublons = brut.dropDuplicates()
# TODO : filtrer (id, ca, date), normaliser la ville, écarter les villes vides,
#        sélectionner id, nom (trim), ville, ca (cast double), segment et canal (lower/trim), date_inscription
propre = sans_doublons
print("lignes lues       :", brut.count())
print("après doublons    :", sans_doublons.count())
print("lignes valides    :", propre.count())
print("villes distinctes :", propre.select("ville").distinct().count())
"""),

md("""
### Étape 3 — Construire le référentiel : une ligne par client
""", title="Étape 3"),

code("spark.pyspark", """
referentiel = (propre.groupBy("id")
               .agg(F.max("nom").alias("nom"),
                    F.max("ville").alias("ville"),
                    F.max("segment").alias("segment"),
                    F.round(F.sum("ca"), 2).alias("ca_total"),
                    F.countDistinct("canal").cast("int").alias("nb_canaux"),
                    F.concat_ws("|", F.array_sort(F.collect_set("canal"))).alias("canaux"),
                    F.min("date_inscription").alias("date_premiere_inscription"))
               .cache())
print("clients :", referentiel.count(), "| présents dans plusieurs canaux :", referentiel.filter("nb_canaux > 1").count())
z.show(referentiel.orderBy(F.desc("ca_total")).limit(10))
""", title="3.1 Agréger par client",
enonce="""
# TODO : regrouper propre par id et calculer :
#   nom, ville, segment (max), ca_total (somme arrondie à 2 décimales),
#   nb_canaux (countDistinct de canal, en int), canaux (concat_ws("|", array_sort(collect_set("canal")))),
#   date_premiere_inscription (min)
referentiel = None
print("clients :", referentiel.count(), "| présents dans plusieurs canaux :", referentiel.filter("nb_canaux > 1").count())
z.show(referentiel.orderBy(F.desc("ca_total")).limit(10))
"""),

code("spark.pyspark", """
referentiel.explain()   # plan physique : lecture CSV, filtres, HashAggregate, Exchange (shuffle)
""", title="3.2 Plan d'exécution"),

md("""
### Étape 4 — Écrire et partager

Spark écrit du **Parquet** (colonnes, compressé) partitionné par ville dans la zone `spark` du référentiel. Puis Hive déclare une table externe sur ces fichiers : le **metastore** la rend visible de Spark, Hive, Impala et Hue. Les fichiers créés par Spark héritent des ACL `default:` de la zone.
""", title="Étape 4"),

code("spark.pyspark", """
(referentiel.write.mode("overwrite")
    .partitionBy("ville")
    .parquet(SORTIE + "/clients"))
stats = (referentiel.groupBy("ville")
         .agg(F.count("*").alias("nb_clients"), F.round(F.sum("ca_total"), 2).alias("ca_total")))
stats.coalesce(1).write.mode("overwrite").parquet(SORTIE + "/stats_villes")
print("écrit dans", SORTIE)
""", title="4.1 Écrire en Parquet partitionné",
enonce="""
# TODO : écrire referentiel en Parquet dans SORTIE + "/clients", partitionné par ville, en mode overwrite
stats = (referentiel.groupBy("ville")
         .agg(F.count("*").alias("nb_clients"), F.round(F.sum("ca_total"), 2).alias("ca_total")))
# TODO : écrire stats en un seul fichier Parquet (coalesce(1)) dans SORTIE + "/stats_villes"
print("écrit dans", SORTIE)
"""),

code("sh", f"""
SU="env HADOOP_USER_NAME=hadoop"
$SU hdfs dfs -ls {Z}/spark/clients | head -6
$SU hdfs dfs -du -s -h {Z}/raffinee/clients {Z}/spark/clients 2>/dev/null
echo "--- ACL héritées par une partition écrite par Spark"
$SU hdfs dfs -getfacl "{Z}/spark/clients/ville=LYON"
""", title="4.2 Fichiers, volumes, ACL héritées"),

code("hive", f"""
CREATE DATABASE IF NOT EXISTS referentiel;
CREATE EXTERNAL TABLE IF NOT EXISTS referentiel.clients_spark (
  id                        STRING,
  nom                       STRING,
  segment                   STRING,
  ca_total                  DOUBLE,
  nb_canaux                 INT,
  canaux                    STRING,
  date_premiere_inscription STRING
)
PARTITIONED BY (ville STRING)
STORED AS PARQUET
LOCATION '{Z}/spark/clients';
MSCK REPAIR TABLE referentiel.clients_spark;
CREATE EXTERNAL TABLE IF NOT EXISTS referentiel.stats_villes_spark (ville STRING, nb_clients BIGINT, ca_total DOUBLE)
STORED AS PARQUET
LOCATION '{Z}/spark/stats_villes'
""", title="4.3 Déclarer les tables dans le metastore (Hive)",
enonce=f"""
CREATE DATABASE IF NOT EXISTS referentiel;
-- TODO : table externe referentiel.clients_spark sur {Z}/spark/clients :
--        colonnes du référentiel SANS la ville, PARTITIONED BY (ville STRING), STORED AS PARQUET
-- TODO : enregistrer les partitions écrites par Spark (MSCK REPAIR TABLE ...)
-- TODO : table externe referentiel.stats_villes_spark (ville, nb_clients BIGINT, ca_total DOUBLE),
--        Parquet, sur {Z}/spark/stats_villes
"""),

code("hive", """
SELECT COUNT(*) AS nb_clients, COUNT(DISTINCT ville) AS nb_villes, ROUND(SUM(ca_total), 2) AS ca_total
FROM referentiel.clients_spark
""", title="4.4 Hive lit les fichiers de Spark"),

code("impala", """
INVALIDATE METADATA referentiel.clients_spark;
SELECT COUNT(*) AS nb_clients, COUNT(DISTINCT ville) AS nb_villes, ROUND(SUM(ca_total), 2) AS ca_total
FROM referentiel.clients_spark
""", title="4.5 Impala aussi"),

md("""
### Étape 5 — Interroger avec Spark SQL

Spark lit la table par le metastore Hive partagé (`spark.table`, `%spark.sql`). Les requêtes ci-dessous utilisent des **fonctions de fenêtre** et comparent les référentiels des TP4 et TP5.
""", title="Étape 5"),

code("spark.sql", """
SELECT ville, segment, id, nom, ca_total, rang
FROM (
  SELECT ville, segment, id, nom, ca_total,
         ROW_NUMBER() OVER (PARTITION BY ville ORDER BY ca_total DESC) AS rang
  FROM referentiel.clients_spark
) t
WHERE rang <= 3 AND ville IN ('PARIS', 'LYON', 'MARSEILLE')
ORDER BY ville, rang
""", title="5.1 Les 3 meilleurs clients par ville (fenêtre)",
enonce="""
-- TODO : pour PARIS, LYON et MARSEILLE, les 3 clients au plus fort ca_total
--        indice : ROW_NUMBER() OVER (PARTITION BY ville ORDER BY ca_total DESC) dans une sous-requête
SELECT 1
"""),

code("spark.sql", """
SELECT segment,
       COUNT(*)                                   AS nb_clients,
       ROUND(AVG(ca_total), 2)                    AS ca_moyen,
       ROUND(100 * AVG(IF(nb_canaux > 1, 1, 0)), 1) AS pct_multi_canaux
FROM referentiel.clients_spark
GROUP BY segment
ORDER BY ca_moyen DESC
""", title="5.2 Indicateurs par segment"),

code("spark.pyspark", """
# Comparaison avec le référentiel Pig/Hive du TP4 (s'il existe)
if spark.catalog.tableExists("referentiel.clients_orc"):
    tp4 = spark.table("referentiel.clients_orc").select("id", F.col("ca_total").alias("ca_tp4"))
    tp5 = spark.table("referentiel.clients_spark").select("id", F.col("ca_total").alias("ca_tp5"))
    ecarts = tp4.join(tp5, "id", "full_outer").filter("ca_tp4 IS NULL OR ca_tp5 IS NULL OR abs(ca_tp4 - ca_tp5) > 0.01")
    print("clients TP4 :", tp4.count(), "| clients TP5 :", tp5.count(), "| écarts :", ecarts.count())
else:
    print("Table referentiel.clients_orc absente : TP4 non réalisé, comparaison ignorée.")
""", title="5.3 Pig/Hive et Spark donnent-ils le même référentiel ?"),

md("""
### Étape 6 — Visualiser et suivre

* Les résultats `%spark.sql` s'affichent en graphique (boutons au-dessus du résultat).
* **Spark UI** http://localhost:4040 : *Jobs*, *Stages* (shuffle), *Storage* (DataFrames en cache), *SQL / DataFrame* (plans).
* **Spark History** http://localhost:18080 : applications terminées (journaux d'événements dans `hdfs:///spark-logs`).
* **Hue** : éditeur *Impala*, requête sur `referentiel.clients_spark`, onglet graphique.
""", title="Étape 6"),

code("spark.sql", """
SELECT ville, nb_clients, ca_total
FROM referentiel.stats_villes_spark
ORDER BY ca_total DESC
""", title="6.1 Chiffre d'affaires par ville (barres)", graph=bar_chart([(0, "ville")], [(2, "ca_total")])),

code("spark.sql", """
SELECT canaux, COUNT(*) AS nb_clients
FROM referentiel.clients_spark
GROUP BY canaux
ORDER BY nb_clients DESC
""", title="6.2 Combinaisons de canaux (secteurs)", graph=bar_chart([(0, "canaux")], [(1, "nb_clients")], mode="pieChart")),

code("spark.sql", """
SELECT SUBSTR(date_premiere_inscription, 1, 4) AS annee, segment, COUNT(*) AS nb_clients
FROM referentiel.clients_spark
GROUP BY SUBSTR(date_premiere_inscription, 1, 4), segment
ORDER BY annee
""", title="6.3 Inscriptions par année et segment (courbes)",
     graph=bar_chart([(0, "annee")], [(2, "nb_clients")], groups=[(1, "segment")], mode="lineChart")),

md("""
### Étape 7 — Industrialiser : la même chaîne en batch

Le notebook sert à explorer ; en production, la chaîne est un programme soumis par `spark-submit` (ordonnancé par Airflow, Oozie...). `tp/tp5-spark/referentiel_spark.py` reprend les étapes 1 à 4. L'application apparaît dans le Spark Master (8080) puis dans le Spark History (18080).

> Version légère du lab (worker Spark à 2 cœurs) : l'application Spark de Zeppelin occupe déjà les 2 cœurs, le programme batch resterait en attente (*WAITING*). Arrêtez d'abord l'interpréteur : menu utilisateur > *Interpreter* > `spark` > *restart*.
""", title="Étape 7"),

code("sh", f"""
head -40 /opt/tp/tp5-spark/referentiel_spark.py | tail -25
echo "..."
spark-submit --master spark://spark-master:7077 --conf spark.cores.max=2 \\
    /opt/tp/tp5-spark/referentiel_spark.py {HDFS}{Z}/brute {HDFS}{Z}/spark/batch 2>&1 \\
  | grep -E 'SPARK_REFERENTIEL|^\\+|^\\|' | head -12
""", title="7.1 spark-submit du programme batch"),

md("""
**Questions**

1. Comparez le volume de `raffinee/clients` (texte, TP4) et de `spark/clients` (Parquet) : d'où vient l'écart ?
2. Pourquoi le `count()` de l'étape 3.1 est-il bien plus rapide la deuxième fois ?
3. Hive a dû exécuter `MSCK REPAIR TABLE` : pourquoi ? Que faudrait-il faire après une nouvelle écriture de Spark ?
""", title="Questions"),

md("""
**Réponses**

1. Parquet stocke par colonnes, encode (dictionnaire pour `segment`, `canaux`) et compresse (Snappy) : le volume est nettement plus faible que le texte. La colonne `ville` n'est même plus stockée : elle est portée par le nom du répertoire de partition.
2. `cache()` : après la première action, le DataFrame reste en mémoire des executors (onglet *Storage* de la Spark UI).
3. Les partitions écrites par Spark sont de simples répertoires : le metastore ne les connaît pas tant qu'on ne les déclare pas (`MSCK REPAIR TABLE` ou `ALTER TABLE ... ADD PARTITION`). Après réécriture : relancer `MSCK REPAIR` si de nouvelles villes apparaissent, et `REFRESH`/`INVALIDATE METADATA` côté Impala.
""", title="Réponses", only="corrige"),

md("""
### Contrôle des critères de réussite
""", title="Contrôle"),

code("spark.pyspark", f"""
import json, subprocess
attendus = json.load(open("/opt/data/hdd/attendus.json"))["referentiel"]
ok = lambda m: print("  [ OK ]", m)
ko = lambda m: print("  [ KO ]", m)
n = spark.table("referentiel.clients_spark").count()
(ok if n == attendus["nb_clients"] else ko)(f"référentiel Spark : {{n}} clients (attendu {{attendus['nb_clients']}})")
ca = spark.table("referentiel.clients_spark").agg(F.round(F.sum("ca_total"), 2)).first()[0]
(ok if abs(ca - attendus["ca_total"]) < 1 else ko)(f"CA total : {{ca}} (attendu {{attendus['ca_total']}})")
eve = subprocess.run(["hdfs", "dfs", "-ls", "{Z}/spark/clients"], env={{**__import__("os").environ, "HADOOP_USER_NAME": "eve"}},
                     capture_output=True, text=True)
(ok if eve.returncode != 0 else ko)("eve (hors groupe) ne peut pas lire les fichiers du référentiel")
print("  (Hive et Impala : comparer les paragraphes 4.4 et 4.5 ; graphique : paragraphes 6.x)")
""", title="Contrôle automatique"),
]
