# Correspondance programme ORSYS HDD ↔ support de cours ↔ hand-labs

Formation **HDD « Hadoop, développement »** — cours pratique, 3 jours (21 h), 30 % cours / 70 % travaux pratiques.
Numéros de diapositives : support `Support_HDD_Hadoop_developpement_-_ORSYS_-_v1.0.pptx`.

| Chapitre du programme | Diapositives | Travaux pratiques du programme | Hand-lab | Notebook Zeppelin |
|---|---|---|---|---|
| 1. Le big data | 8 à 25 | Démonstration : usage d'Hadoop (diapo 24) | démonstration formateur | `0 - Demarrage / 00 - Prise en main et demonstration Hadoop` |
| 2. Collecte de données et application de MapReduce | 26 à 47 | Gérer la collecte d'informations clientèles par MapReduce · Développement d'une tâche basée sur MapReduce (diapo 45) | **TP1** | `TP1 - Collecte clients et taches MapReduce` |
| | | Configuration de l'implémentation YARN (diapo 46) | **TP2** | `TP2 - Configuration de l implementation YARN` |
| 3. Le stockage des données avec HBase | 48 à 65 | Gérer les modifications d'un catalogue de données (diapo 64) | **TP3** | `TP3 - HBase - Gerer les modifications d un catalogue` |
| 4. Le stockage des données sur HDFS (dont Pig, Hive) | 66 à 87 | Administrer un référentiel client partagé sur Hadoop · Utilisation de la console de visualisation (diapo 87) | **TP4** (Pig, Hive, Java) | `TP4 - Referentiel client partage - Pig Hive Java et console` |
| *(prolongement)* Spark | 37, 85 | Même TP, avec Spark et Spark SQL | **TP5** | `TP5 - Referentiel client partage - Spark Spark SQL et console` |

## Étapes des TP ↔ diapositives

| TP | Étape | Notions du support | Diapositives |
|---|---|---|---|
| TP1 | Collecter | commandes HDFS, blocs | 74, 75 |
| TP1 | Développer | Mapper, Reducer, driver | 33, 34 |
| TP1 | Contrôler la collecte | types de données, flux, job map seul, compteurs | 27, 28, 32 |
| TP1 | Optimiser | Combiner, Partitioner | 35 |
| TP1 | Bonus SQL | tables externes Hive | 84 |
| TP2 | Observer, mesurer, ajuster | architecture et configuration YARN, emboîtement des mémoires | 38, 39, 40 |
| TP2 | Partager, vérifier | Capacity Scheduler, files | 41 |
| TP3 | Créer, écrire, lire | modèle de données, shell HBase | 52, 57 |
| TP3 | Charger, historiser, sécuriser | API Java HBase, versions, `checkAndMutate` | 58, 59, 60 |
| TP3 | Exposer | HBase et Hive, HCatalog | 62, 63 |
| TP4 | Organiser, partager, protéger, contrôler | droits, ACL, quotas, instantanés, `fsck`, réplication | 73, 75, 76, 78 |
| TP4 | Transformer | Pig Latin, UDF (Pig appelle Java), PigServer (Java pilote Pig) | 79, 80, 81 |
| TP4 | Interroger | Hive : tables, partitions, ORC ; Impala | 82, 83, 84, 85 |
| TP4 | Visualiser | consoles Hue et Zeppelin | 86 |
| TP5 | Construire, partager | Spark, Parquet, metastore partagé | 21, 29, 37, 85 |

Le TP5 prolonge le chapitre 4 avec Spark, en cohérence avec la consigne des hand-labs (notebooks Zeppelin, Hue, Hive, Impala, Spark, Spark SQL). Selon le rythme du groupe, il peut être proposé en autonomie ou en démonstration.
