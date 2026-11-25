# Sources des TP

Montées en **lecture seule** dans le conteneur Zeppelin sous `/opt/tp`. Les notebooks recopient le code dans `/tmp/hdd/tpN` (où les stagiaires le modifient), compilent avec `/opt/jdk17/bin/javac` et exécutent sur le cluster. Les fichiers de ce dossier sont les **solutions de référence**.

| Dossier | Contenu | Utilisé par |
|---|---|---|
| `tp1-mapreduce/` | `CollecteClients` + `CollecteMapper` (job map seul, compteurs, `MultipleOutputs`), `ClientsParVille` + `ClientsMapper` + `ClientsReducer` (support de cours), `CaParVille`, `Villes`, `Resultats` | TP1, TP2 |
| `tp2-yarn/` | `capacity-scheduler-dev.xml`, `ajouter_file_dev.sh` (à lancer depuis l'hôte), `mesurer_job.py` (API REST du JobHistory) | TP2 |
| `tp3-hbase/` | `ChargeCatalogue` (Put par lots), `AppliqueModifications` (versions datées), `HistoriquePrix`, `MajConditionnelle` (`checkAndMutate`), `CreerCatalogue` ; `creer_catalogue.hbase`, `export_catalogue.py` (happybase), `catalogue_export.hql` | TP3 |
| `tp4-pig-hive/` | `referentiel_clients.pig`, UDF `NormaliseVille`, `ReferentielPigServer` (Pig embarqué), `ReferentielJdbc` (client JDBC Hive/Impala) ; `referentiel.hql` | TP4 |
| `tp5-spark/` | `referentiel_spark.py` (même chaîne en batch, `spark-submit`) | TP5 |
| `commun/` | `preparer_referentiel.sh` : zone `/data/referentiel/clients`, propriétaires, droits et ACL (idempotent) | TP5 (et corrigé TP4) |

## Construire avec Maven (IDE, poste du formateur)

Les `pom.xml` déclarent les dépendances du cluster en `provided` (Hadoop 3.4.2, HBase 2.6.7, Pig 0.18.0), Java 17 :

```bash
cd ~/HDD/tp/tp1-mapreduce && mvn -q package     # target/clients.jar
cd ~/HDD/tp/tp3-hbase     && mvn -q package     # target/catalogue.jar
cd ~/HDD/tp/tp4-pig-hive  && mvn -q package     # target/referentiel-pig.jar
```

Pour exécuter un jar construit sur l'hôte : `docker cp target/clients.jar zeppelin:/tmp/` puis, dans Zeppelin (`%sh`) :

```bash
yarn jar /tmp/clients.jar fr.orsys.hdd.tp1.ClientsParVille '/data/clean/clients/part-*' /data/out/villes
```

## Sans Zeppelin

Tout ce que font les notebooks se lance aussi en ligne de commande dans le conteneur : `docker exec -it zeppelin bash` donne les mêmes outils (`hdfs`, `yarn`, `hadoop`, `pig`, `hbase`, `spark-submit`, `/opt/jdk17/bin/javac`).
