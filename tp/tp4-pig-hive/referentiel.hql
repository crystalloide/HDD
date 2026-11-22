-- =============================================================================
-- TP4 — Exposition du référentiel dans Hive (puis Impala, Hue, Spark)
-- Les tables sont EXTERNES : les données restent dans la zone du référentiel
-- sur HDFS, sous la protection de ses droits et ACL ; DROP TABLE ne supprime
-- que la définition.
-- =============================================================================

CREATE DATABASE IF NOT EXISTS referentiel
COMMENT 'Référentiel client partagé (TP HDD)';

-- 1. Table externe posée sur la sortie Pig (texte « ; »)
CREATE EXTERNAL TABLE IF NOT EXISTS referentiel.clients (
  id                        STRING,
  nom                       STRING,
  ville                     STRING,
  segment                   STRING,
  ca_total                  DOUBLE,
  nb_canaux                 INT,
  canaux                    STRING,
  date_premiere_inscription STRING
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ';'
STORED AS TEXTFILE
LOCATION '/data/referentiel/clients/raffinee/clients';

CREATE EXTERNAL TABLE IF NOT EXISTS referentiel.stats_villes (
  ville      STRING,
  nb_clients BIGINT,
  ca_total   DOUBLE
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ';'
STORED AS TEXTFILE
LOCATION '/data/referentiel/clients/raffinee/stats_villes';

-- 2. Table optimisée : ORC, partitionnée par ville
CREATE EXTERNAL TABLE IF NOT EXISTS referentiel.clients_orc (
  id                        STRING,
  nom                       STRING,
  segment                   STRING,
  ca_total                  DOUBLE,
  nb_canaux                 INT,
  canaux                    STRING,
  date_premiere_inscription STRING
)
PARTITIONED BY (ville STRING)
STORED AS ORC
LOCATION '/data/referentiel/clients/orc';

-- 3. Chargement (partitions dynamiques : une partition par ville)
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
INSERT OVERWRITE TABLE referentiel.clients_orc PARTITION (ville)
SELECT id, nom, segment, ca_total, nb_canaux, canaux, date_premiere_inscription, ville
FROM referentiel.clients;

-- 4. Requêtes
SHOW PARTITIONS referentiel.clients_orc;

SELECT ville, COUNT(*) AS nb_clients, ROUND(SUM(ca_total), 2) AS ca_total
FROM referentiel.clients_orc
GROUP BY ville
ORDER BY ca_total DESC
LIMIT 10;

SELECT segment, nb_canaux, COUNT(*) AS nb_clients, ROUND(AVG(ca_total), 2) AS ca_moyen
FROM referentiel.clients_orc
GROUP BY segment, nb_canaux
ORDER BY segment, nb_canaux;
