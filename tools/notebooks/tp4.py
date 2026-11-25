# -*- coding: utf-8 -*-
from zep import md, code, source, heredoc, bar_chart

NAME = "TP4 - Referentiel client partage - Pig Hive Java et console"
SRC = "tp/tp4-pig-hive/src/main/java/fr/orsys/hdd/tp4/"
W = "/tmp/hdd/tp4"
J = W + "/src/fr/orsys/hdd/tp4/"
Z = "/data/referentiel/clients"


def java(fichier, enonce=None, titre=None):
    corr = source(SRC + fichier)
    return code("sh", heredoc(J + fichier, corr), title=titre or fichier,
                enonce=heredoc(J + fichier, enonce) if enonce else None)


UDF_ENONCE = source(SRC + "NormaliseVille.java")
_a = UDF_ENONCE.index("    String v = Normalizer")
_b = UDF_ENONCE.index("    return v.isEmpty() ? null : v;")
UDF_ENONCE = UDF_ENONCE[:_a] + """    // TODO : à partir de in.get(0).toString() :
    //   1. retirer les accents : Normalizer.normalize(s, Normalizer.Form.NFD) puis supprimer les \\\\p{M}
    //   2. retirer les espaces en tête et en fin, réduire les espaces multiples à un seul
    //   3. passer en majuscules (Locale.ROOT)
    String v = "";
""" + UDF_ENONCE[_b:]

PIG = source("tp/tp4-pig-hive/referentiel_clients.pig")
PIG_ENONCE = PIG
for avant, apres in [
    ("""valides = FILTER uniques BY id MATCHES 'C[0-9]{6}'
                        AND NormaliseVille(ville) IS NOT NULL
                        AND ca MATCHES '[0-9]+(\\\\.[0-9]+)?'
                        AND date_inscription MATCHES '[0-9]{4}-[0-9]{2}-[0-9]{2}';""",
     """-- TODO : garder les lignes dont l'id est au format C + 6 chiffres (MATCHES), la ville
--        normalisée non nulle, le CA numérique positif et la date au format aaaa-mm-jj
valides = FILTER uniques BY id MATCHES 'C[0-9]{6}';"""),
    ("""referentiel = FOREACH par_client {
    canaux = DISTINCT norm.canal;
    GENERATE group                      AS id,
             MAX(norm.nom)              AS nom,
             MAX(norm.ville)            AS ville,
             MAX(norm.segment)          AS segment,
             ROUND_TO(SUM(norm.ca), 2)  AS ca_total,
             COUNT(canaux)              AS nb_canaux,
             BagToString(canaux, '|')   AS canaux,
             MIN(norm.date_inscription) AS date_premiere_inscription;
};""",
     """-- TODO : pour chaque client (FOREACH imbriqué), produire dans cet ordre :
--   id, nom, ville, segment (une valeur du groupe : MAX), ca_total (SUM arrondie : ROUND_TO),
--   nb_canaux (COUNT des canaux distincts), canaux (BagToString(..., '|')),
--   date_premiere_inscription (MIN)
referentiel = FOREACH par_client {
    canaux = DISTINCT norm.canal;
    GENERATE group AS id;
};"""),
]:
    assert avant in PIG_ENONCE, avant[:50]
    PIG_ENONCE = PIG_ENONCE.replace(avant, apres)

HQL = source("tp/tp4-pig-hive/referentiel.hql")


def bloc_hql(debut, fin=None):
    i = HQL.index(debut)
    j = HQL.index(fin) if fin else len(HQL)
    return HQL[i:j].strip()


CLASSPATH_PIG = 'PIG_JAR=$(ls $PIG_HOME/pig-*-core-h3.jar $PIG_HOME/pig-*.jar 2>/dev/null | grep -v -- -withouthadoop | head -1)'

P = [
md("""
## TP4 — Référentiel client partagé sur Hadoop, avec Pig, Hive (et Java) — console de visualisation

**Objectif** : mettre à disposition de plusieurs équipes un **référentiel client** dans HDFS, le construire avec Pig, l'interroger avec Hive et Impala, puis le visualiser.

| Étape | Contenu |
|---|---|
| 1. Organiser | `/data/referentiel/clients` : zones brute, raffinée et ORC ; dépôt des fichiers |
| 2. Partager | propriétaire et groupe, droits `750`, ACL de lecture pour un second groupe et pour les moteurs |
| 3. Protéger | quota d'espace, instantané avant modification, test de restauration |
| 4. Contrôler | `hdfs fsck`, facteur de réplication, console du NameNode (9870) |
| 5. Transformer | script Pig Latin + UDF Java (Pig appelle Java), Pig embarqué (Java pilote Pig) |
| 6. Interroger | table externe Hive, table ORC partitionnée ; Impala ; client Java JDBC |
| 7. Visualiser | graphiques dans Zeppelin et dans Hue, consoles YARN et JobHistory |

**Critères de réussite** : un utilisateur hors groupe ne peut pas lire le référentiel ; un fichier supprimé est restauré depuis l'instantané ; la même table est visible depuis Hive et Impala ; un graphique est produit dans la console.

Prérequis : profil `full` (Hue et Impala). Comptes : voir le notebook *00*. Les commandes d'administration sont passées sous l'identité adéquate avec `HADOOP_USER_NAME` (authentification « simple ») : `hadoop` = superutilisateur, `crm_admin` = propriétaire du référentiel.
""", title="Présentation du TP"),

md("""
### Étape 1 — Organiser

Le référentiel appartient à l'équipe CRM (compte `crm_admin`, groupe `crm`). Trois zones :

* `brute` : les fichiers tels que collectés ;
* `raffinee` : le référentiel produit par Pig (1 ligne par client) et ses statistiques ;
* `orc` : la table optimisée écrite par Hive.

Seul le superutilisateur peut créer sous `/data/referentiel` puis donner la propriété à `crm_admin`.
""", title="Étape 1"),

code("sh", f"""
SU="env HADOOP_USER_NAME=hadoop"; CRM="env HADOOP_USER_NAME=crm_admin"
$SU hdfs dfs -mkdir -p {Z}/brute {Z}/raffinee {Z}/orc
$SU hdfs dfs -chmod 755 /data/referentiel
$SU hdfs dfs -chown -R crm_admin:crm {Z}
$CRM hdfs dfs -put -f /opt/data/hdd/clients/*.csv {Z}/brute/
$CRM hdfs dfs -ls -R {Z}
""", title="1.1 Créer les zones et déposer les fichiers",
enonce=f"""
SU="env HADOOP_USER_NAME=hadoop"; CRM="env HADOOP_USER_NAME=crm_admin"
# TODO (superutilisateur) : créer {Z}/brute, {Z}/raffinee et {Z}/orc
# TODO (superutilisateur) : /data/referentiel en 755 ; {Z} et ses sous-répertoires à crm_admin, groupe crm (chown -R)
# TODO (crm_admin) : déposer /opt/data/hdd/clients/*.csv dans {Z}/brute
$CRM hdfs dfs -ls -R {Z}
"""),

md("""
### Étape 2 — Partager

1. Restreindre : `750` sur le référentiel et les zones brute et raffinée (`770` sur `orc`, où Hive écrira) : propriétaire en lecture-écriture, groupe `crm` en lecture, **personne d'autre**.
2. Constater : `bob` (groupe `marketing`) et `eve` (hors groupe) sont refusés.
3. Ouvrir par **ACL** : lecture pour le groupe `marketing` ; lecture pour les comptes de service `hive` et `impala` (Hive et Impala lisent les fichiers sous leur propre identité) ; écriture pour `hive` dans `orc`. Les entrées `default:` sont **héritées** par tout ce qui sera créé ensuite dans le répertoire.
4. Vérifier : `bob` lit, `eve` est toujours refusée.
""", title="Étape 2"),

code("sh", f"""
CRM="env HADOOP_USER_NAME=crm_admin"
$CRM hdfs dfs -chmod 750 {Z} {Z}/brute {Z}/raffinee
$CRM hdfs dfs -chmod 770 {Z}/orc
$CRM hdfs dfs -ls {Z}
for u in alice bob eve; do
  printf "%-6s : " $u; HADOOP_USER_NAME=$u hdfs dfs -ls {Z}/brute > /dev/null 2>/tmp/hdd_err && echo "lecture autorisée" || grep -o 'Permission denied.*' /tmp/hdd_err | cut -c1-90
done
""", title="2.1 Restreindre et constater",
enonce=f"""
CRM="env HADOOP_USER_NAME=crm_admin"
# TODO (crm_admin) : 750 sur {Z}, {Z}/brute et {Z}/raffinee ; 770 sur {Z}/orc
$CRM hdfs dfs -ls {Z}
for u in alice bob eve; do
  printf "%-6s : " $u; HADOOP_USER_NAME=$u hdfs dfs -ls {Z}/brute > /dev/null 2>/tmp/hdd_err && echo "lecture autorisée" || grep -o 'Permission denied.*' /tmp/hdd_err | cut -c1-90
done
"""),

code("sh", f"""
CRM="env HADOOP_USER_NAME=crm_admin"
# Traverser la racine du référentiel
$CRM hdfs dfs -setfacl -m group:marketing:r-x,user:hive:r-x,user:impala:r-x {Z}
$CRM hdfs dfs -setfacl -m group:marketing:r-x {Z}/brute
# Zones exposées : lecture + entrées « default » héritées par les fichiers à venir
for d in raffinee orc; do
  $CRM hdfs dfs -setfacl -m group:marketing:r-x,user:hive:r-x,user:impala:r-x,default:group:marketing:r-x,default:user:hive:r-x,default:user:impala:r-x {Z}/$d
done
# Hive écrit la table ORC
$CRM hdfs dfs -setfacl -m user:hive:rwx,default:user:hive:rwx {Z}/orc
$CRM hdfs dfs -getfacl {Z}/raffinee
$CRM hdfs dfs -ls {Z}     # le « + » après les droits signale une ACL
""", title="2.2 Ouvrir par ACL",
enonce=f"""
CRM="env HADOOP_USER_NAME=crm_admin"
# TODO : ACL sur {Z} : lecture/traversée (r-x) pour le groupe marketing et les utilisateurs hive et impala
# TODO : ACL sur {Z}/brute : r-x pour le groupe marketing
# TODO : ACL sur {Z}/raffinee et {Z}/orc : mêmes entrées + leurs versions « default: » (héritées)
# TODO : ACL sur {Z}/orc : rwx (et default:rwx) pour l'utilisateur hive
#   syntaxe : hdfs dfs -setfacl -m group:marketing:r-x,user:hive:r-x,default:user:hive:r-x <chemin>
$CRM hdfs dfs -getfacl {Z}/raffinee
$CRM hdfs dfs -ls {Z}
"""),

code("sh", f"""
for u in alice bob eve; do
  printf "%-6s : " $u; HADOOP_USER_NAME=$u hdfs dfs -ls {Z}/brute > /dev/null 2>/tmp/hdd_err && echo "lecture autorisée" || grep -o 'Permission denied.*' /tmp/hdd_err | cut -c1-90
done
echo "--- et en écriture ?"
HADOOP_USER_NAME=bob hdfs dfs -touchz {Z}/brute/essai_bob 2>&1 | grep -o 'Permission denied.*' | cut -c1-90
""", title="2.3 Vérifier"),

md("""
**À retenir** : en authentification simple, n'importe qui peut se déclarer `crm_admin` avec `HADOOP_USER_NAME`. Les droits HDFS protègent contre les erreurs, pas contre la malveillance : en production, **Kerberos** authentifie les utilisateurs. Autre limite : Hive et Impala lisent sous leur propre identité (`doAs=false` ici), donc tout utilisateur SQL voit le référentiel ; le contrôle d'accès par table et par colonne relève alors d'**Apache Ranger**.

### Étape 3 — Protéger : quota et instantané
""", title="Étape 3"),

code("sh", f"""
SU="env HADOOP_USER_NAME=hadoop"
$SU hdfs dfsadmin -setSpaceQuota 1g {Z}
$SU hdfs dfsadmin -setQuota 10000 {Z}
$SU hdfs dfs -count -q -h -v {Z}
""", title="3.1 Quotas d'espace et de noms",
enonce=f"""
SU="env HADOOP_USER_NAME=hadoop"
# TODO (superutilisateur) : quota d'espace de 1 Go sur {Z} (hdfs dfsadmin -setSpaceQuota ...)
# TODO (superutilisateur) : quota de 10 000 noms (fichiers + répertoires) (hdfs dfsadmin -setQuota ...)
$SU hdfs dfs -count -q -h -v {Z}
"""),

code("sh", """
# Piège classique : un quota d'espace se vérifie BLOC par bloc. Pour écrire,
# HDFS réserve un bloc entier (128 Mo x réplication), même pour un petit fichier.
SU="env HADOOP_USER_NAME=hadoop"
$SU hdfs dfs -mkdir -p /data/referentiel/bac_a_sable && $SU hdfs dfs -chmod 777 /data/referentiel/bac_a_sable
$SU hdfs dfsadmin -setSpaceQuota 50m /data/referentiel/bac_a_sable
echo "un fichier de 1 Ko" > /tmp/hdd_petit.txt
hdfs dfs -put -f /tmp/hdd_petit.txt /data/referentiel/bac_a_sable/ 2>&1 | grep -iE 'quota' | head -2 | cut -c1-200
$SU hdfs dfs -rm -r -f -skipTrash /data/referentiel/bac_a_sable > /dev/null
""", title="3.2 Le piège du quota d'espace"),

code("sh", f"""
SU="env HADOOP_USER_NAME=hadoop"; CRM="env HADOOP_USER_NAME=crm_admin"
$SU hdfs dfsadmin -allowSnapshot {Z}
$CRM hdfs dfs -deleteSnapshot {Z} avant_maj 2>/dev/null
$CRM hdfs dfs -createSnapshot {Z} avant_maj
$CRM hdfs dfs -ls {Z}/.snapshot
echo "--- incident : suppression d'un fichier source"
$CRM hdfs dfs -rm -skipTrash {Z}/brute/web_2026-11.csv
$CRM hdfs dfs -ls {Z}/brute
""", title="3.3 Instantané avant modification, puis incident",
enonce=f"""
SU="env HADOOP_USER_NAME=hadoop"; CRM="env HADOOP_USER_NAME=crm_admin"
# TODO (superutilisateur) : autoriser les instantanés sur {Z} (hdfs dfsadmin -allowSnapshot ...)
$CRM hdfs dfs -deleteSnapshot {Z} avant_maj 2>/dev/null
# TODO (crm_admin) : créer l'instantané « avant_maj » de {Z} (hdfs dfs -createSnapshot ...)
$CRM hdfs dfs -ls {Z}/.snapshot
echo "--- incident : suppression d'un fichier source"
$CRM hdfs dfs -rm -skipTrash {Z}/brute/web_2026-11.csv
$CRM hdfs dfs -ls {Z}/brute
"""),

code("sh", f"""
CRM="env HADOOP_USER_NAME=crm_admin"
$CRM hdfs snapshotDiff {Z} avant_maj .
$CRM hdfs dfs -cp -p {Z}/.snapshot/avant_maj/brute/web_2026-11.csv {Z}/brute/
$CRM hdfs dfs -ls {Z}/brute
""", title="3.4 Restaurer depuis l'instantané",
enonce=f"""
CRM="env HADOOP_USER_NAME=crm_admin"
# Différence entre l'instantané et l'état courant (« . ») :
$CRM hdfs snapshotDiff {Z} avant_maj .
# TODO (crm_admin) : restaurer web_2026-11.csv en le copiant depuis {Z}/.snapshot/avant_maj/brute/ (hdfs dfs -cp -p ...)
$CRM hdfs dfs -ls {Z}/brute
"""),

md("""
**À observer** : un instantané ne copie rien au moment de sa création (il fige la liste des blocs) ; la suppression d'un fichier ne libère pas ses blocs tant qu'un instantané y fait référence. `.snapshot` est un répertoire en lecture seule, visible aussi dans la console http://localhost:9870 (*Utilities > Browse*, et *Snapshot* dans le menu).

### Étape 4 — Contrôler
""", title="Étape 4"),

code("sh", f"""
SU="env HADOOP_USER_NAME=hadoop"
$SU hdfs fsck {Z} -files -blocks -locations | grep -E 'csv|blk_|Status|Total|replicated'
""", title="4.1 fsck du référentiel"),

code("sh", f"""
SU="env HADOOP_USER_NAME=hadoop"
# Facteur de réplication 3 demandé... sur un cluster d'un seul DataNode
$SU hdfs dfs -setrep 3 {Z}/brute/crm_2026-11.csv
$SU hdfs fsck {Z}/brute -files | grep -E 'Under-replicated|Under replicated|Status' | head -4
# Retour à 1 (seule valeur satisfaisable ici)
$SU hdfs dfs -setrep 1 {Z}/brute/crm_2026-11.csv
""", title="4.2 Facteur de réplication"),

md("""
**À observer** : avec `-setrep 3`, `fsck` signale des blocs **sous-répliqués** (une seule copie possible sur un seul DataNode) ; le NameNode tenterait de créer les copies manquantes si d'autres DataNodes existaient. Retrouvez ces informations dans la console du NameNode (http://localhost:9870, *Overview* et *Datanodes*).

### Étape 5 — Transformer avec Pig (Pig appelle Java)

Le script Pig Latin construit le référentiel : suppression des doublons exacts, filtrage des lignes invalides, **normalisation des villes par une UDF Java**, regroupement par client (CA cumulé sur ses canaux), statistiques par ville. Pig compile le script en jobs **MapReduce** soumis à YARN, sous l'identité `crm_admin`.
""", title="Étape 5"),

java("NormaliseVille.java", UDF_ENONCE, "5.1 UDF NormaliseVille.java"),
code("sh", f"""
cd {W}
{CLASSPATH_PIG}
echo "Pig : $PIG_JAR"
rm -rf classes && mkdir -p classes
/opt/jdk17/bin/javac --release 17 -encoding UTF-8 -cp "$PIG_JAR:$(hadoop classpath)" -d classes src/fr/orsys/hdd/tp4/NormaliseVille.java \\
  && /opt/jdk17/bin/jar cf udfs.jar -C classes . && echo "OK : $(ls -l udfs.jar)"
""", title="5.2 Compiler l'UDF (udfs.jar)"),

code("sh", heredoc(W + "/referentiel_clients.pig", PIG), title="5.3 Le script Pig Latin",
     enonce=heredoc(W + "/referentiel_clients.pig", PIG_ENONCE)),

code("sh", f"""
cd {W}
CRM="env HADOOP_USER_NAME=crm_admin"
$CRM hdfs dfs -rm -r -f -skipTrash {Z}/raffinee/clients {Z}/raffinee/stats_villes
$CRM pig -x mapreduce \\
    -param BRUTE={Z}/brute \\
    -param SORTIE_REF={Z}/raffinee/clients \\
    -param SORTIE_STATS={Z}/raffinee/stats_villes \\
    -param UDF_JAR={W}/udfs.jar \\
    -f {W}/referentiel_clients.pig 2>&1 | tee {W}/pig.log | grep -E 'Success|Failed|Input\\(s\\)|Output\\(s\\)|records|HadoopJobId|ERROR' | head -20
$CRM hdfs dfs -ls {Z}/raffinee/clients {Z}/raffinee/stats_villes
""", title="5.4 Exécuter le script (MapReduce sur YARN)"),

code("sh", f"""
CRM="env HADOOP_USER_NAME=crm_admin"
echo "clients dans le référentiel : $($CRM hdfs dfs -cat {Z}/raffinee/clients/part-* | wc -l)"
$CRM hdfs dfs -cat {Z}/raffinee/clients/part-* 2>&1 | head -3
echo "--- statistiques par ville"
$CRM hdfs dfs -cat {Z}/raffinee/stats_villes/part-* | sort -t';' -k3,3gr | head -5
echo "--- héritage des ACL par défaut sur un fichier créé par Pig"
$CRM hdfs dfs -getfacl {Z}/raffinee/clients/part-r-00000 2>/dev/null | head -12 || $CRM hdfs dfs -ls {Z}/raffinee/clients
""", title="5.5 Vérifier le référentiel produit"),

md("""
**Questions** : combien de jobs MapReduce Pig a-t-il lancés (console http://localhost:19888) ? Pourquoi les deux `STORE` ne lisent-ils les fichiers qu'une fois ? Combien de clients uniques compte le référentiel, et combien de lignes valides avaient les fichiers bruts ?

### Java pilote Pig : Pig embarqué

`ReferentielPigServer` enchaîne des instructions Pig Latin depuis un programme Java (`PigServer`) : CA moyen par segment des clients présents dans plusieurs canaux.
""", title="Pig embarqué"),

java("ReferentielPigServer.java", None, "5.6 ReferentielPigServer.java (fourni)"),
java("ReferentielJdbc.java", None, "5.7 ReferentielJdbc.java (client JDBC, utilisé à l'étape 6)"),
code("sh", f"""
cd {W}
{CLASSPATH_PIG}
HIVE_JDBC=/opt/zeppelin/interpreter/jdbc/hive-jdbc-4.1.0-standalone.jar
rm -rf classes && mkdir -p classes
/opt/jdk17/bin/javac --release 17 -encoding UTF-8 -cp "$PIG_JAR:$(hadoop classpath)" -d classes $(find src -name '*.java') \\
  && /opt/jdk17/bin/jar cf referentiel-pig.jar -C classes . && echo "OK : $(ls -l referentiel-pig.jar)"
CRM="env HADOOP_USER_NAME=crm_admin"
$CRM env HADOOP_CLASSPATH="$PIG_JAR:$PIG_HOME/lib/*:$PIG_HOME/lib/h3/*" hadoop jar referentiel-pig.jar fr.orsys.hdd.tp4.ReferentielPigServer \\
    {Z}/raffinee/clients {Z}/raffinee/segments 2>&1 | grep -E 'PIG_STATUT|^  \\(|ERROR' | head -12
""", title="5.8 Compiler et exécuter Pig embarqué"),

md("""
### Étape 6 — Interroger avec Hive, puis Impala

Les tables sont **externes** : les données restent dans la zone du référentiel, sous la protection de ses droits ; `DROP TABLE` ne supprime que la définition. Hive lit les fichiers sous l'identité `hive` : c'est l'ACL posée à l'étape 2 qui l'y autorise.
""", title="Étape 6"),

code("hive", bloc_hql("CREATE DATABASE", "-- 2. Table optimisée"), title="6.1 Tables externes sur la sortie Pig",
     enonce="""
CREATE DATABASE IF NOT EXISTS referentiel COMMENT 'Référentiel client partagé (TP HDD)';
-- TODO : table externe referentiel.clients sur /data/referentiel/clients/raffinee/clients
--        colonnes : id, nom, ville, segment, ca_total DOUBLE, nb_canaux INT, canaux, date_premiere_inscription
--        format texte, séparateur « ; » (ROW FORMAT DELIMITED FIELDS TERMINATED BY ';')
-- TODO : table externe referentiel.stats_villes (ville, nb_clients BIGINT, ca_total DOUBLE)
--        sur /data/referentiel/clients/raffinee/stats_villes
"""),

code("hive", """
SELECT COUNT(*) AS nb_clients, ROUND(SUM(ca_total), 2) AS ca_total, SUM(IF(nb_canaux > 1, 1, 0)) AS multi_canaux
FROM referentiel.clients
""", title="6.2 Premiers contrôles"),

code("hive", bloc_hql("-- 2. Table optimisée", "-- 4. Requêtes"), title="6.3 Table ORC partitionnée par ville",
     enonce="""
-- TODO : table externe referentiel.clients_orc, même schéma SANS la ville,
--        PARTITIONED BY (ville STRING), STORED AS ORC,
--        LOCATION '/data/referentiel/clients/orc'
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
-- TODO : INSERT OVERWRITE TABLE referentiel.clients_orc PARTITION (ville)
--        SELECT ... , ville FROM referentiel.clients   (la colonne de partition en DERNIER)
"""),

code("hive", """
SHOW PARTITIONS referentiel.clients_orc
""", title="6.4 Partitions créées"),

code("hive", """
EXPLAIN
SELECT segment, COUNT(*) AS nb_clients, ROUND(AVG(ca_total), 2) AS ca_moyen
FROM referentiel.clients_orc
WHERE ville = 'LYON'
GROUP BY segment
""", title="6.5 Plan d'exécution (élagage de partitions, DAG Tez)"),

code("impala", """
INVALIDATE METADATA referentiel.clients_orc;
SELECT ville, COUNT(*) AS nb_clients, ROUND(SUM(ca_total), 2) AS ca_total
FROM referentiel.clients_orc
GROUP BY ville ORDER BY ca_total DESC LIMIT 10
""", title="6.6 La même table vue par Impala"),

code("sh", f"""
cd {W}
HIVE_JDBC=/opt/zeppelin/interpreter/jdbc/hive-jdbc-4.1.0-standalone.jar
for cible in "jdbc:hive2://hiveserver2:10000/default hive" "jdbc:hive2://impalad:21050/default;auth=noSasl impala"; do
  set -- $cible
  /opt/jdk17/bin/java -cp "$HIVE_JDBC:referentiel-pig.jar" fr.orsys.hdd.tp4.ReferentielJdbc "$1" "$2" 2>/dev/null | tee "{W}/jdbc_$2.txt"
  echo
done
""", title="6.7 Client Java JDBC : HiveServer2 puis Impala"),

md("""
**Questions** : comparez les durées Hive et Impala de la même requête. D'où vient l'écart ? Dans quel cas Hive reste-t-il le bon choix ?

### Étape 7 — Visualiser : la console

**Dans Zeppelin** : le résultat d'une requête s'affiche en tableau ou en graphique (barres, secteurs, lignes) avec les boutons au-dessus du résultat ; *settings* choisit les colonnes des axes.

**Dans Hue** (http://localhost:8888, `hue` / `hue`) :

1. *Éditeur > Hive* (ou *Impala*) : exécuter la requête du paragraphe 7.1 ;
2. sous le résultat, onglet **graphique** : barres, X = `ville`, Y = `ca_total` ; enregistrer la requête (*Save*) ;
3. *Fichiers* : naviguer jusqu'à `/data/referentiel/clients` — Hue agit sous l'identité de l'utilisateur connecté (`hue`) : **refusé**, faute d'ACL pour ce compte. C'est la sécurité HDFS vue de la console ;
4. *Admin > Users* : créer l'utilisateur `bob`, se reconnecter avec lui : le référentiel devient lisible (groupe `marketing`) ;
5. *Jobs* : les jobs MapReduce de Pig et les sessions Tez de Hive.

**Consoles d'exploitation** : http://localhost:8088 (applications YARN), http://localhost:19888 (jobs Pig terminés, compteurs), http://localhost:9870 (instantanés, quotas, blocs).
""", title="Étape 7"),

code("hive", """
SELECT ville, nb_clients, ca_total
FROM referentiel.stats_villes
ORDER BY ca_total DESC
""", title="7.1 Chiffre d'affaires par ville (graphique)", graph=bar_chart([(0, "ville")], [(2, "ca_total")])),

code("hive", """
SELECT segment, COUNT(*) AS nb_clients
FROM referentiel.clients_orc
GROUP BY segment
""", title="7.2 Répartition par segment (secteurs)", graph=bar_chart([(0, "segment")], [(1, "nb_clients")], mode="pieChart")),

code("hive", """
SELECT SUBSTR(date_premiere_inscription, 1, 4) AS annee, nb_canaux, COUNT(*) AS nb_clients
FROM referentiel.clients_orc
GROUP BY SUBSTR(date_premiere_inscription, 1, 4), nb_canaux
ORDER BY annee, nb_canaux
""", title="7.3 Inscriptions par année et nombre de canaux", graph=bar_chart([(0, "annee")], [(2, "nb_clients")], groups=[(1, "nb_canaux")])),

md("""
### Contrôle des critères de réussite
""", title="Contrôle"),

code("sh", f"""
ok () {{ printf "  [ OK ] %s\\n" "$1"; }}; ko () {{ printf "  [ KO ] %s\\n" "$1"; }}
HADOOP_USER_NAME=eve hdfs dfs -ls {Z}/raffinee > /dev/null 2>&1 && ko "eve (hors groupe) lit le référentiel !" || ok "eve (hors groupe) ne peut pas lire le référentiel"
HADOOP_USER_NAME=bob hdfs dfs -ls {Z}/raffinee > /dev/null 2>&1 && ok "bob (marketing) lit le référentiel grâce à l'ACL" || ko "bob ne lit pas le référentiel (étape 2.2)"
HADOOP_USER_NAME=crm_admin hdfs dfs -test -e {Z}/.snapshot/avant_maj/brute/web_2026-11.csv && HADOOP_USER_NAME=crm_admin hdfs dfs -test -e {Z}/brute/web_2026-11.csv \\
  && ok "fichier supprimé restauré depuis l'instantané avant_maj" || ko "instantané et restauration (étape 3)"
attendu=$(python3 -c "import json; print(json.load(open('/opt/data/hdd/attendus.json'))['referentiel']['nb_clients'])")
n=$(HADOOP_USER_NAME=crm_admin hdfs dfs -cat {Z}/raffinee/clients/part-* 2>/dev/null | wc -l)
[ "$n" = "$attendu" ] && ok "référentiel Pig : $n clients (attendu $attendu)" || ko "référentiel Pig : $n clients (attendu $attendu)"
h=$(sed -n '2,11p' {W}/jdbc_hive.txt 2>/dev/null | awk '{{print $1,$2}}'); i=$(sed -n '2,11p' {W}/jdbc_impala.txt 2>/dev/null | awk '{{print $1,$2}}')
[ -n "$h" ] && [ "$h" = "$i" ] && ok "même table, mêmes résultats depuis Hive et Impala" || ko "comparaison Hive / Impala (étape 6.7)"
echo "  (graphique : à constater dans Zeppelin, paragraphes 7.x, ou dans Hue)"
""", title="Contrôle automatique"),
]
