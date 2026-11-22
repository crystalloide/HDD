# -*- coding: utf-8 -*-
"""
TP5 — Référentiel client partagé avec Spark (version batch, pour spark-submit).
Le notebook Zeppelin « TP5 » déroule les mêmes étapes paragraphe par paragraphe.

    spark-submit /opt/tp/tp5-spark/referentiel_spark.py \
        hdfs://namenode:8020/data/referentiel/clients/brute \
        hdfs://namenode:8020/data/referentiel/clients/spark/batch

Sorties (Parquet) :
    <sortie>/clients        1 ligne par client, partitionné par ville
    <sortie>/stats_villes   nb de clients et CA par ville
"""
import sys

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType

SCHEMA_BRUT = StructType([StructField(c, StringType()) for c in
                          ["id", "nom", "ville", "ca", "segment", "canal", "date_inscription"]])

# Même règle que la UDF Pig NormaliseVille : accents retirés, espaces réduits, majuscules.
ACCENTS = "àâäáãåçéèêëíìîïñóòôöõúùûüýÿÀÂÄÁÃÅÇÉÈÊËÍÌÎÏÑÓÒÔÖÕÚÙÛÜÝ"
SANS_ACC = "aaaaaaceeeeiiiinooooouuuuyyAAAAAACEEEEIIIINOOOOOUUUUY"


def normalise_ville(col):
    return F.upper(F.regexp_replace(F.trim(F.translate(col, ACCENTS, SANS_ACC)), r"\s+", " "))


def lire_brut(spark, chemin):
    # mode PERMISSIVE : une ligne au mauvais format donne des colonnes nulles
    # au lieu d'arrêter la lecture ; le filtre de l'étape suivante l'écarte.
    return (spark.read
            .option("sep", ";")
            .option("header", "false")
            .option("mode", "PERMISSIVE")
            .schema(SCHEMA_BRUT)
            .csv(chemin))


def nettoyer(brut):
    return (brut
            .dropDuplicates()                                           # doublons exacts
            .filter(F.col("id").rlike(r"^C[0-9]{6}$"))                  # en-têtes, mauvais séparateur
            .filter(F.col("ca").rlike(r"^[0-9]+(\.[0-9]+)?$"))          # CA numérique positif
            .filter(F.col("date_inscription").rlike(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$"))
            .withColumn("ville", normalise_ville(F.col("ville")))
            .filter(F.col("ville") != "")
            .select("id",
                    F.trim("nom").alias("nom"),
                    "ville",
                    F.col("ca").cast("double").alias("ca"),
                    F.lower(F.trim("segment")).alias("segment"),
                    F.lower(F.trim("canal")).alias("canal"),
                    "date_inscription"))


def construire_referentiel(propre):
    return (propre.groupBy("id")
            .agg(F.max("nom").alias("nom"),
                 F.max("ville").alias("ville"),
                 F.max("segment").alias("segment"),
                 F.round(F.sum("ca"), 2).alias("ca_total"),
                 F.countDistinct("canal").cast("int").alias("nb_canaux"),
                 F.concat_ws("|", F.array_sort(F.collect_set("canal"))).alias("canaux"),
                 F.min("date_inscription").alias("date_premiere_inscription")))


def stats_par_ville(referentiel):
    return (referentiel.groupBy("ville")
            .agg(F.count("*").alias("nb_clients"),
                 F.round(F.sum("ca_total"), 2).alias("ca_total"))
            .withColumn("rang", F.row_number().over(Window.orderBy(F.desc("ca_total"))).cast("int")))


def main(argv):
    if len(argv) != 3:
        print("Usage : referentiel_spark.py <entrée brute> <sortie>", file=sys.stderr)
        return 2
    entree, sortie = argv[1], argv[2].rstrip("/")
    spark = SparkSession.builder.appName("tp5-referentiel-clients").getOrCreate()
    referentiel = construire_referentiel(nettoyer(lire_brut(spark, entree))).cache()
    (referentiel.write.mode("overwrite")
     .partitionBy("ville")
     .parquet(sortie + "/clients"))
    stats = stats_par_ville(referentiel)
    stats.coalesce(1).write.mode("overwrite").parquet(sortie + "/stats_villes")
    print("SPARK_REFERENTIEL clients=%d multi_canaux=%d villes=%d" % (
        referentiel.count(),
        referentiel.filter("nb_canaux > 1").count(),
        stats.count()))
    stats.orderBy("rang").show(30, truncate=False)
    spark.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
