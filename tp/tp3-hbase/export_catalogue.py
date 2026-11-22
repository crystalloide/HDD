# -*- coding: utf-8 -*-
"""
TP3 — Exposition du catalogue HBase à Hive / Impala par export.
À exécuter dans Zeppelin (%python) : lit la table 'catalogue' par le serveur
Thrift d'HBase (happybase), écrit les valeurs COURANTES dans un fichier CSV
sur HDFS (/data/catalogue/export), sur lequel une table externe Hive est posée.

Variante « en direct » (sans copie) : table Hive STORED BY HBaseStorageHandler,
voir le notebook. Elle demande les jars clients HBase côté HiveServer2.
"""
import io
import subprocess

import happybase

COLONNES = [("info", "libelle"), ("info", "categorie"), ("info", "prix"), ("info", "promo"),
            ("stock", "quantite"), ("stock", "entrepot")]
CIBLE = "/data/catalogue/export/catalogue.csv"

conn = happybase.Connection("hbase-thrift", 9090, timeout=20000)
try:
    table = conn.table("catalogue")
    tampon = io.StringIO()
    nb = 0
    for cle, cellules in table.scan():          # une version par cellule : la plus récente
        valeurs = [cellules.get(f"{f}:{q}".encode(), b"").decode("utf-8") for f, q in COLONNES]
        tampon.write(";".join([cle.decode("utf-8")] + valeurs) + "\n")
        nb += 1
finally:
    conn.close()

subprocess.run(["hdfs", "dfs", "-mkdir", "-p", "/data/catalogue/export"], check=True)
subprocess.run(["hdfs", "dfs", "-put", "-f", "-", CIBLE],
               input=tampon.getvalue().encode("utf-8"), check=True)
print(f"{nb} produits exportés vers {CIBLE}")
