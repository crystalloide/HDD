# -*- coding: utf-8 -*-
from zep import md, code, source, heredoc

NAME = "TP1 - Collecte clients et taches MapReduce"
SRC = "tp/tp1-mapreduce/src/main/java/fr/orsys/hdd/tp1/"
W = "/tmp/hdd/tp1"
J = W + "/src/fr/orsys/hdd/tp1/"


def java(fichier, enonce=None, titre=None, apres=""):
    corr = source(SRC + fichier)
    return code("sh", heredoc(J + fichier, corr, apres), title=titre or fichier,
                enonce=heredoc(J + fichier, enonce, apres) if enonce else None)


MAPPER_ENONCE = '''package fr.orsys.hdd.tp1;

import java.io.IOException;

import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;

/**
 * Map : (position, "id;nom;ville;...") -> (ville, 1)
 * La pause optionnelle (hdd.map.pause.ms) servira au TP YARN : ne pas la retirer.
 */
public class ClientsMapper extends Mapper<LongWritable, Text, Text, IntWritable> {

  private static final IntWritable UN = new IntWritable(1);
  private final Text ville = new Text();

  @Override
  protected void setup(Context ctx) throws InterruptedException {
    long pause = ctx.getConfiguration().getLong("hdd.map.pause.ms", 0L);
    if (pause > 0) {
      Thread.sleep(pause);
    }
  }

  @Override
  protected void map(LongWritable off, Text ligne, Context ctx)
      throws IOException, InterruptedException {
    // TODO 1 : découper la ligne sur « ; » (la ville est le 3e champ)
    // TODO 2 : si la ligne a au moins 3 champs, émettre (ville, 1) avec ctx.write(...)
  }
}'''

REDUCER_ENONCE = '''package fr.orsys.hdd.tp1;

import java.io.IOException;

import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Reducer;

/**
 * Reduce : (ville, [1, 1, ...]) -> (ville, total)
 */
public class ClientsReducer extends Reducer<Text, IntWritable, Text, IntWritable> {

  private final IntWritable resultat = new IntWritable();

  @Override
  protected void reduce(Text ville, Iterable<IntWritable> vals, Context ctx)
      throws IOException, InterruptedException {
    // TODO : additionner les valeurs, puis émettre (ville, total)
  }
}'''

DRIVER_ENONCE = source(SRC + "ClientsParVille.java").replace(
    """    job.setMapperClass(ClientsMapper.class);
    if (getConf().getBoolean("hdd.combiner", false)) {
      job.setCombinerClass(ClientsReducer.class);
    }
    job.setReducerClass(ClientsReducer.class);
    job.setOutputKeyClass(Text.class);
    job.setOutputValueClass(IntWritable.class);""",
    """    // TODO 1 : déclarer la classe du mapper et celle du reducer
    // TODO 2 : (étape 5) si la propriété hdd.combiner vaut true, déclarer ClientsReducer comme combiner
    //          indice : getConf().getBoolean("hdd.combiner", false)
    // TODO 3 : déclarer les types de la clé et de la valeur en sortie (Text, IntWritable)""")

COLLECTE_ENONCE = source(SRC + "CollecteMapper.java")
_debut = COLLECTE_ENONCE.index('    String[] f = ligne.split(";", -1);')
_fin = COLLECTE_ENONCE.index('    sortie.set(String.join(";", id,')
COLLECTE_ENONCE = COLLECTE_ENONCE[:_debut] + '''    String[] f = ligne.split(";", -1);          // -1 : garde les champs vides en fin de ligne
    // Règles de collecte, dans cet ordre (une règle non respectée => rejeter(MOTIF, ligne, context); return;)
    //  1. exactement 7 champs, sinon motif "FORMAT"
    //  2. en-tête (1er champ = "id") : incrémenter Collecte.ENTETES puis return (ce n'est pas un rejet)
    //  3. identifiant au format C + 6 chiffres (pattern ID), sinon "ID_INVALIDE"
    //  4. ville normalisée non vide (Villes.normalise), sinon "VILLE_ABSENTE"
    //  5. CA lisible (Double.parseDouble) et positif, sinon "CA_INVALIDE"
    //  6. date au format aaaa-mm-jj (pattern DATE), sinon "DATE_INVALIDE"
    // TODO : écrire ces contrôles et calculer id, ville, ca, date
    String id = "";       // TODO
    String ville = "";    // TODO
    double ca = 0;        // TODO
    String date = "";     // TODO

''' + COLLECTE_ENONCE[_fin:]

CA_ENONCE = '''package fr.orsys.hdd.tp1;

import java.io.IOException;

import org.apache.hadoop.conf.Configured;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.util.Tool;
import org.apache.hadoop.util.ToolRunner;

/**
 * Exercice : chiffre d'affaires par ville, à partir des données collectées
 * (id;nom;ville;ca;segment;canal;date).
 */
public class CaParVille extends Configured implements Tool {

  // TODO 1 : mapper CaMapper extends Mapper<LongWritable, Text, Text, DoubleWritable>
  //          émet (ville, ca) ; une ligne au CA illisible incrémente un compteur et est ignorée
  public static class CaMapper extends Mapper<LongWritable, Text, Text, DoubleWritable> {
  }

  // TODO 2 : reducer SommeReducer extends Reducer<Text, DoubleWritable, Text, DoubleWritable>
  //          émet (ville, somme arrondie au centime) ; il servira aussi de combiner : pourquoi est-ce correct ?
  public static class SommeReducer extends Reducer<Text, DoubleWritable, Text, DoubleWritable> {
  }

  @Override
  public int run(String[] args) throws Exception {
    getConf().setIfUnset("mapreduce.output.textoutputformat.separator", ";");
    Job job = Job.getInstance(getConf(), "ca-par-ville");
    job.setJarByClass(CaParVille.class);
    // TODO 3 : mapper, combiner, reducer, types de sortie, chemins d'entrée et de sortie (args[0], args[1])
    boolean ok = job.waitForCompletion(true);
    Resultats.afficher(job);
    return ok ? 0 : 1;
  }

  public static void main(String[] args) throws Exception {
    System.exit(ToolRunner.run(new CaParVille(), args));
  }
}'''

COMPILE = f"""cd {W}
rm -rf classes && mkdir -p classes
/opt/jdk17/bin/javac --release 17 -encoding UTF-8 -cp "$(hadoop classpath)" -d classes $(find src -name '*.java') \\
  && /opt/jdk17/bin/jar cf clients.jar -C classes . \\
  && echo "OK : $(ls -l clients.jar)" && /opt/jdk17/bin/jar tf clients.jar | grep class"""

P = [
md("""
## TP1 — Collecte d'informations clientèles et tâches MapReduce

**Objectif** : collecter des fichiers clients dans HDFS, les contrôler et les normaliser avec un job MapReduce, puis produire le nombre de clients et le chiffre d'affaires par ville.

Programme HDD : *gérer la collecte d'informations clientèles par MapReduce* et *développer une tâche basée sur MapReduce*. Durée indicative : 2 h 30.

| Étape | Contenu |
|---|---|
| 1. Collecter | déposer les fichiers des 3 canaux (CRM, web, magasins) dans `/data/raw/clients` |
| 2. Développer | `ClientsMapper`, `ClientsReducer`, driver `ClientsParVille` (API `org.apache.hadoop.mapreduce`) |
| 3. Contrôler la collecte | job « map seul » `CollecteClients` : règles qualité, compteurs, fichiers de rejets |
| 4. Exécuter et contrôler | clients par ville sur les données propres ; `_SUCCESS`, `part-r-*`, compteurs |
| 5. Optimiser | combiner, 2 reducers : comparer les compteurs |
| 6. Développer une tâche | `CaParVille` : chiffre d'affaires par ville |

**Critères de réussite** : le job se termine à l'état SUCCEEDED dans YARN ; les totaux par ville correspondent aux fichiers source ; le compteur *Reduce input records* baisse avec le combiner ; deux fichiers `part-r-*` avec 2 reducers.

Prérequis : profil `zeppelin` (ou `full`). On compile avec `javac` dans le conteneur Zeppelin : c'est l'équivalent de `mvn package` (le `pom.xml` est fourni dans `tp/tp1-mapreduce` pour travailler dans un IDE).
""", title="Présentation du TP"),

md("""
### Étape 1 — Collecter

Les trois fichiers du jour viennent de trois canaux. Format : `id;nom;ville;ca;segment;canal;date_inscription`, avec une ligne d'en-tête. Un même client peut figurer dans plusieurs canaux.

**À faire** : examiner les fichiers, puis les déposer dans `/data/raw/clients` sur HDFS et vérifier leurs blocs.
""", title="Étape 1"),

code("sh", """
ls -l /opt/data/hdd/clients/
wc -l /opt/data/hdd/clients/*.csv
echo "--- début du fichier CRM"
head -4 /opt/data/hdd/clients/crm_2026-11.csv
echo "--- quelques saisies de villes à normaliser"
cut -d';' -f3 /opt/data/hdd/clients/*.csv | grep -iE '^ |paris$|saint' | sort | uniq -c | sort -rn | head -8
""", title="1.1 Examiner les fichiers sources"),

code("sh", """
hdfs dfs -mkdir -p /data/raw/clients
hdfs dfs -put -f /opt/data/hdd/clients/*.csv /data/raw/clients/
hdfs dfs -ls -h /data/raw/clients
echo "--- blocs et réplication (fsck : superutilisateur)"
HADOOP_USER_NAME=hadoop hdfs fsck /data/raw/clients -files -blocks | grep -E 'csv|blk_|Total blocks|replication'
""", title="1.2 Déposer dans HDFS",
enonce="""
# TODO : créer /data/raw/clients sur HDFS (hdfs dfs -mkdir -p ...)
# TODO : y déposer les 3 fichiers de /opt/data/hdd/clients (hdfs dfs -put -f ...)
# TODO : lister le répertoire avec les tailles lisibles (-ls -h)

# Blocs et réplication (fsck est réservé au superutilisateur « hadoop »)
HADOOP_USER_NAME=hadoop hdfs fsck /data/raw/clients -files -blocks | grep -E 'csv|blk_|Total blocks|replication'
"""),

md("""
### Étape 2 — Développer le job « clients par ville »

Le code est celui du support (chapitre 2) : le mapper émet `(ville, 1)` pour chaque ligne, le reducer additionne. Le driver utilise `ToolRunner` : les options `-D propriété=valeur` de la ligne de commande sont lues sans recompiler.

Chaque paragraphe écrit un fichier source dans `/tmp/hdd/tp1/src`. Exécutez-les tous, puis compilez.
""", title="Étape 2"),

java("ClientsMapper.java", MAPPER_ENONCE, "2.1 ClientsMapper.java"),
java("ClientsReducer.java", REDUCER_ENONCE, "2.2 ClientsReducer.java"),
java("ClientsParVille.java", DRIVER_ENONCE, "2.3 ClientsParVille.java (driver)"),
java("Resultats.java", None, "2.4 Resultats.java (affichage des compteurs, fourni)"),
java("Villes.java", None, "2.5 Villes.java (normalisation des villes, fournie)"),
code("sh", COMPILE, title="2.6 Compiler et empaqueter (clients.jar)"),

code("sh", """
hdfs dfs -rm -r -f -skipTrash /data/out/villes_brut
yarn jar /tmp/hdd/tp1/clients.jar fr.orsys.hdd.tp1.ClientsParVille \\
     /data/raw/clients /data/out/villes_brut 2>&1 | tee /tmp/hdd/tp1/run_brut.log | grep -E 'Submitted application|map [0-9]+% reduce|HDD_|ERROR|Exception'
echo "--- nombre de « villes » trouvées : $(hdfs dfs -cat /data/out/villes_brut/part-r-* | wc -l)"
hdfs dfs -cat /data/out/villes_brut/part-r-* | head -12
""", title="2.7 Premier essai sur les données brutes"),

md("""
**Que constatez-vous ?** Une centaine de « villes » au lieu de 24 : la ligne d'en-tête compte comme une ville (`ville`), les villes vides forment un groupe, `Paris`, `PARIS` et ` paris ` sont trois clés différentes, les lignes au mauvais séparateur passent entières…

Le calcul est juste, ce sont les données qui ne le sont pas. D'où l'étape de **collecte** : contrôler et normaliser chaque ligne avant de calculer.
""", title="Analyse"),

md("""
### Étape 3 — Contrôler la collecte : un job « map seul »

`CollecteMapper` vérifie chaque ligne (règles ci-dessous), normalise la ville et le CA, et écrit :

* les lignes valides dans `part-m-*` ;
* les lignes écartées dans `rejets-m-*` (avec `MultipleOutputs`), précédées de leur motif et du fichier d'origine.

Il n'y a **pas de reducer** (`setNumReduceTasks(0)`) : aucune agrégation n'est nécessaire, chaque map écrit directement sa sortie. Les **compteurs** (`context.getCounter`) dressent le bilan qualité de la collecte.

| Règle | Motif de rejet |
|---|---|
| exactement 7 champs | `FORMAT` |
| ligne d'en-tête (`id;...`) | non rejetée : comptée dans `ENTETES` |
| identifiant `C` + 6 chiffres | `ID_INVALIDE` |
| ville renseignée (après normalisation) | `VILLE_ABSENTE` |
| CA numérique et positif | `CA_INVALIDE` |
| date `aaaa-mm-jj` | `DATE_INVALIDE` |
""", title="Étape 3"),

java("CollecteMapper.java", COLLECTE_ENONCE, "3.1 CollecteMapper.java"),
java("CollecteClients.java", None, "3.2 CollecteClients.java (driver, fourni)"),
code("sh", COMPILE, title="3.3 Recompiler"),

code("sh", """
hdfs dfs -rm -r -f -skipTrash /data/clean/clients
yarn jar /tmp/hdd/tp1/clients.jar fr.orsys.hdd.tp1.CollecteClients \\
     /data/raw/clients /data/clean/clients 2>&1 | tee /tmp/hdd/tp1/run_collecte.log | grep -E 'Submitted application|HDD_|COLLECTE|ERROR|Exception'
echo "--- compteurs « Rejets par motif »"
grep -A8 'Rejets par motif' /tmp/hdd/tp1/run_collecte.log | grep -E '^\\s+[A-Z_]+='
hdfs dfs -ls /data/clean/clients
""", title="3.4 Exécuter la collecte",
enonce="""
hdfs dfs -rm -r -f -skipTrash /data/clean/clients
# TODO : lancer fr.orsys.hdd.tp1.CollecteClients avec yarn jar, de /data/raw/clients vers /data/clean/clients
#        (garder la sortie dans un journal : 2>&1 | tee /tmp/hdd/tp1/run_collecte.log | grep -E 'HDD_|COLLECTE')
echo "--- compteurs « Rejets par motif »"
grep -A8 'Rejets par motif' /tmp/hdd/tp1/run_collecte.log | grep -E '^\\s+[A-Z_]+='
hdfs dfs -ls /data/clean/clients
"""),

code("sh", """
echo "--- lignes valides (extrait)"
hdfs dfs -cat /data/clean/clients/part-m-00000 | head -3
echo "--- rejets par motif et par fichier"
hdfs dfs -cat '/data/clean/clients/rejets-m-*' | cut -d';' -f1,2 | sort | uniq -c
echo "--- exemples"
hdfs dfs -cat '/data/clean/clients/rejets-m-*' | awk -F';' '!vu[$1]++' | head -5
""", title="3.5 Examiner les lignes valides et les rejets"),

md("""
**À noter** : `lignes lues = valides + rejets + en-têtes`. Ouvrez le job dans le **JobHistory** (http://localhost:19888, lien *Counters*) : les compteurs du groupe *Rejets par motif* y figurent.

### Étape 4 — Exécuter et contrôler

On relance `ClientsParVille` sur les données propres. Le répertoire `/data/clean/clients` contient aussi les rejets : le motif `part-*` ne retient que les lignes valides.
""", title="Étape 4"),

code("sh", """
hdfs dfs -rm -r -f -skipTrash /data/out/villes
yarn jar /tmp/hdd/tp1/clients.jar fr.orsys.hdd.tp1.ClientsParVille \\
     '/data/clean/clients/part-*' /data/out/villes 2>&1 | tee /tmp/hdd/tp1/run_villes_1r.log | grep -E 'Submitted application|HDD_|ERROR|Exception'
hdfs dfs -ls /data/out/villes
hdfs dfs -cat /data/out/villes/part-r-* | sort -t';' -k2,2nr | head -10
""", title="4.1 Clients par ville (1 reducer, sans combiner)",
enonce="""
hdfs dfs -rm -r -f -skipTrash /data/out/villes
# TODO : lancer ClientsParVille sur '/data/clean/clients/part-*' vers /data/out/villes
#        journal : 2>&1 | tee /tmp/hdd/tp1/run_villes_1r.log | grep -E 'Submitted application|HDD_'
hdfs dfs -ls /data/out/villes
hdfs dfs -cat /data/out/villes/part-r-* | sort -t';' -k2,2nr | head -10
"""),

code("sh", """
# Contrôle indépendant : le même comptage par awk, directement sur les lignes valides
hdfs dfs -cat '/data/clean/clients/part-*' | awk -F';' '{n[$3]++} END {for (v in n) print v ";" n[v]}' | sort > /tmp/hdd/tp1/attendu.txt
hdfs dfs -cat /data/out/villes/part-r-* | sort > /tmp/hdd/tp1/obtenu.txt
if diff -q /tmp/hdd/tp1/attendu.txt /tmp/hdd/tp1/obtenu.txt > /dev/null; then
  echo "IDENTIQUE : $(wc -l < /tmp/hdd/tp1/obtenu.txt) villes, $(awk -F';' '{s+=$2} END {print s}' /tmp/hdd/tp1/obtenu.txt) lignes clients"
else
  echo "DIFFÉRENT :"; diff /tmp/hdd/tp1/attendu.txt /tmp/hdd/tp1/obtenu.txt | head
fi
""", title="4.2 Contrôler les totaux"),

md("""
### Étape 5 — Optimiser : combiner et 2 reducers

* **Combiner** : un reducer local, exécuté à la sortie de chaque map, avant le shuffle. Ici `ClientsReducer` convient, car l'addition est associative et commutative.
* **2 reducers** : le partitionneur par défaut (`hash(clé) mod 2`) répartit les villes entre deux fichiers `part-r-00000` et `part-r-00001`.

Les deux options se passent en ligne de commande grâce à `ToolRunner` : `-D hdd.combiner=true -D mapreduce.job.reduces=2`. L'option `split.maxsize` découpe les fichiers en morceaux de 256 Ko : on obtient une dizaine de maps, donc un combiner plus visible.
""", title="Étape 5"),

code("sh", """
for essai in "sans:false" "avec:true"; do
  nom=${essai%%:*}; combiner=${essai##*:}
  hdfs dfs -rm -r -f -skipTrash /data/out/villes_$nom
  yarn jar /tmp/hdd/tp1/clients.jar fr.orsys.hdd.tp1.ClientsParVille \\
       -D hdd.combiner=$combiner -D mapreduce.job.reduces=2 \\
       -D mapreduce.input.fileinputformat.split.maxsize=262144 \\
       '/data/clean/clients/part-*' /data/out/villes_$nom > /tmp/hdd/tp1/run_villes_$nom.log 2>&1
  echo "combiner $nom : $(grep -E 'HDD_ETAT|HDD_COMPTEURS' /tmp/hdd/tp1/run_villes_$nom.log | tr '\\n' ' ')"
done
echo "--- fichiers produits avec 2 reducers"
hdfs dfs -ls /data/out/villes_avec
hdfs dfs -cat /data/out/villes_avec/part-r-00000 | head -3
""", title="5.1 Comparer sans / avec combiner (2 reducers)",
enonce="""
for essai in "sans:false" "avec:true"; do
  nom=${essai%%:*}; combiner=${essai##*:}
  hdfs dfs -rm -r -f -skipTrash /data/out/villes_$nom
  # TODO : relancer ClientsParVille avec les options
  #        -D hdd.combiner=$combiner  -D mapreduce.job.reduces=2
  #        -D mapreduce.input.fileinputformat.split.maxsize=262144
  #        de '/data/clean/clients/part-*' vers /data/out/villes_$nom
  #        > /tmp/hdd/tp1/run_villes_$nom.log 2>&1
  echo "combiner $nom : $(grep -E 'HDD_ETAT|HDD_COMPTEURS' /tmp/hdd/tp1/run_villes_$nom.log | tr '\\n' ' ')"
done
hdfs dfs -ls /data/out/villes_avec
"""),

md("""
**Questions**

1. Combien d'enregistrements entrent dans les reducers sans combiner ? avec combiner ? Pourquoi un tel écart ?
2. Le combiner change-t-il le résultat final ? Comparez `/data/out/villes_sans` et `/data/out/villes_avec`.
3. Comment les villes sont-elles réparties entre les deux fichiers `part-r-*` ? Pourrait-on choisir cette répartition ?
4. Dans le JobHistory, comparez la quantité d'octets échangés pendant le shuffle (*Reduce shuffle bytes*).
""", title="Questions"),

md("""
**Réponses**

1. Sans combiner, chaque ligne produit une paire `(ville, 1)` qui traverse le réseau : environ 36 000 entrées pour les reducers. Avec combiner, chaque map n'envoie qu'une paire par ville présente dans son morceau : quelques centaines au plus.
2. Non : la somme de sommes partielles est la somme totale (opération associative et commutative). Un combiner ne doit jamais changer le résultat ; pour une moyenne, il faudrait transporter (somme, nombre).
3. Par `HashPartitioner` : `hash(ville) mod 2`. Un `Partitioner` personnalisé permet un autre découpage (par région, par initiale...).
4. Les octets de shuffle chutent dans les mêmes proportions : c'est le bénéfice principal du combiner sur un vrai cluster.
""", title="Réponses", only="corrige"),

md("""
### Étape 6 — Développer une tâche : chiffre d'affaires par ville

**À faire** : écrire `CaParVille` (mapper, reducer servant aussi de combiner, driver), sur le modèle de `ClientsParVille`, avec des `DoubleWritable`. Contrôlez le résultat par awk.
""", title="Étape 6"),

java("CaParVille.java", CA_ENONCE, "6.1 CaParVille.java"),
code("sh", COMPILE, title="6.2 Recompiler"),
code("sh", """
hdfs dfs -rm -r -f -skipTrash /data/out/ca_villes
yarn jar /tmp/hdd/tp1/clients.jar fr.orsys.hdd.tp1.CaParVille \\
     '/data/clean/clients/part-*' /data/out/ca_villes 2>&1 | tee /tmp/hdd/tp1/run_ca.log | grep -E 'HDD_|ERROR|Exception'
echo "--- top 5 (MapReduce)"
hdfs dfs -cat /data/out/ca_villes/part-r-* | sort -t';' -k2,2gr | head -5
echo "--- contrôle awk"
hdfs dfs -cat '/data/clean/clients/part-*' | awk -F';' '{s[$3]+=$4} END {for (v in s) printf "%s;%.2f\\n", v, s[v]}' | sort -t';' -k2,2gr | head -5
""", title="6.3 Exécuter et contrôler"),

md("""
### Pour aller plus loin : le même calcul en une ligne de SQL

Une table Hive externe posée sur les fichiers produits par MapReduce rend leur résultat interrogeable en SQL. Et la requête équivalente, sur les données propres, est exécutée par Hive… sous forme de DAG Tez sur YARN.
""", title="Bonus"),

code("hive", """
CREATE DATABASE IF NOT EXISTS tp1;
CREATE EXTERNAL TABLE IF NOT EXISTS tp1.ca_villes (ville STRING, ca_total DOUBLE)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ';' LOCATION '/data/out/ca_villes';
CREATE EXTERNAL TABLE IF NOT EXISTS tp1.clients_propres (
  id STRING, nom STRING, ville STRING, ca DOUBLE, segment STRING, canal STRING, date_inscription STRING)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ';' LOCATION '/data/clean/clients'
TBLPROPERTIES ('comment' = 'contient aussi les rejets-m-* : voir la requête');
""", title="B.1 Tables Hive externes sur les résultats"),

code("hive", """
-- rejets-m-* : 1er champ = motif, ce n'est pas un identifiant client => filtrés
SELECT p.ville, ROUND(SUM(p.ca), 2) AS ca_sql, MAX(m.ca_total) AS ca_mapreduce
FROM tp1.clients_propres p JOIN tp1.ca_villes m ON p.ville = m.ville
WHERE p.id RLIKE '^C[0-9]{6}$'
GROUP BY p.ville
ORDER BY ca_sql DESC
LIMIT 10
""", title="B.2 SQL contre MapReduce"),

md("""
### Contrôle des critères de réussite
""", title="Contrôle"),

code("sh", """
ok () { printf "  [ OK ] %s\\n" "$1"; }; ko () { printf "  [ KO ] %s\\n" "$1"; }
grep -q 'HDD_ETAT=SUCCEEDED' /tmp/hdd/tp1/run_villes_1r.log 2>/dev/null && ok "job clients-par-ville SUCCEEDED" || ko "job clients-par-ville (étape 4.1)"
diff -q /tmp/hdd/tp1/attendu.txt /tmp/hdd/tp1/obtenu.txt >/dev/null 2>&1 && ok "totaux par ville = fichiers source" || ko "totaux par ville (étape 4.2)"
attendu=$(python3 -c "import json; print(len(json.load(open('/opt/data/hdd/attendus.json'))['clients_par_ville_collecte']))")
[ "$(wc -l < /tmp/hdd/tp1/obtenu.txt 2>/dev/null)" = "$attendu" ] && ok "$attendu villes après normalisation" || ko "nombre de villes ($attendu attendues)"
sans=$(grep -o 'reduce_in=[0-9]*' /tmp/hdd/tp1/run_villes_sans.log 2>/dev/null | cut -d= -f2)
avec=$(grep -o 'reduce_in=[0-9]*' /tmp/hdd/tp1/run_villes_avec.log 2>/dev/null | cut -d= -f2)
[ -n "$sans" ] && [ -n "$avec" ] && [ "$avec" -lt "$sans" ] && ok "Reduce input records : $sans -> $avec avec combiner" || ko "comparaison combiner (étape 5.1)"
[ "$(hdfs dfs -ls /data/out/villes_avec 2>/dev/null | grep -c part-r-)" = 2 ] && ok "2 fichiers part-r-* avec 2 reducers" || ko "2 reducers (étape 5.1)"
grep -q 'HDD_ETAT=SUCCEEDED' /tmp/hdd/tp1/run_ca.log 2>/dev/null && ok "tâche CaParVille SUCCEEDED" || ko "tâche CaParVille (étape 6)"
""", title="Contrôle automatique"),
]
