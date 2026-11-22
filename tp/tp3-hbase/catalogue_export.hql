-- TP3 — Table externe Hive sur l'export du catalogue HBase
CREATE DATABASE IF NOT EXISTS catalogue;

CREATE EXTERNAL TABLE IF NOT EXISTS catalogue.produits_export (
  id        STRING,
  libelle   STRING,
  categorie STRING,
  prix      DOUBLE,
  promo     STRING,
  quantite  INT,
  entrepot  STRING
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ';'
STORED AS TEXTFILE
LOCATION '/data/catalogue/export';

SELECT id, libelle, prix, promo FROM catalogue.produits_export WHERE id IN ('P0001', 'P0007');

SELECT categorie, COUNT(*) AS nb_produits, ROUND(AVG(prix), 2) AS prix_moyen,
       SUM(quantite) AS stock_total, COUNT(NULLIF(promo, '')) AS nb_promos
FROM catalogue.produits_export
GROUP BY categorie
ORDER BY categorie;
