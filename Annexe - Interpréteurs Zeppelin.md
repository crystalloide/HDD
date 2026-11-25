Tous les interpréteurs dont les notebooks des TP ont besoin sont déjà configurés dans zeppelin/conf/interpreter.json, sauf %md, que Zeppelin crée seul au démarrage. 

Le script fourni fait la vérification en conditions réelles.

Interpréteur	Réglage	Utilisé par
%hive	HiveServer2, jdbc:hive2://hiveserver2:10000/default	TP1, TP3, TP4, TP5
%hbase	shell HBase 2.6.7, /opt/hbase	TP3, exercices HBase
%spark.pyspark, %spark.sql	spark://spark-master:7077, catalogue Hive partagé	TP5
%impala	jdbc:hive2://impalad:21050/default;auth=noSasl	TP3, TP4, TP5
%sh	clients hdfs, yarn, pig, hbase, javac	tous les TP
%python	Python 3 avec happybase	TP3
%md	créé automatiquement par Zeppelin	tous
%file, %java	WebHDFS, JDK 17	démo

Points à connaître :
- %md n'est pas dans interpreter.json : Zeppelin crée au démarrage chaque interpréteur installé qui n'y figure pas. C'est ce mécanisme qui fait aussi fonctionner %md dans BD540.
- Pas d'interpréteur Pig : il n'existe plus dans Zeppelin 0.12. Le TP4 passe déjà par %sh (pig -x mapreduce).
- %hbase a une limite de 60 secondes par paragraphe, fixée dans le code de Zeppelin et non réglable. Chaque paragraphe lance un hbase shell complet. Les paragraphes HBase des TP sont courts (1 à 9 commandes) et les chargements passent par Java, donc ça tient.

#### Nouveau script de vérification, à lancer depuis l'hôte une fois la pile démarrée :


```bash
cd ~/HDD
```
bash scripts/check_interpreteurs.sh            # présence, réglages et un paragraphe exécuté par interpréteur (1 à 3 min)
```
```bash
bash scripts/check_interpreteurs.sh --rapide   # présence et réglages seulement


Ce qu'il fait : il vérifie que chaque interpréteur existe et a le bon réglage, puis exécute un paragraphe de test pour chacun, par exemple SELECT 'OK-hive', list en HBase ou spark.range(5).count(). Il passe par une note temporaire, supprimée à la fin.
Profils non démarrés : les interpréteurs dont le service ne tourne pas (HBase ou Impala, par exemple) sont ignorés.

Si un interpréteur a été supprimé ou modifié dans Zeppelin, le script affiche la commande qui le rétablit : 

```bash
docker compose --profile full up -d --force-recreate zeppelin
```

Elle remet les réglages d'origine et conserve les notebooks.