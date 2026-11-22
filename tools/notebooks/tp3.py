# -*- coding: utf-8 -*-
from zep import md, code, source, heredoc, bar_chart

NAME = "TP3 - HBase - Gerer les modifications d un catalogue"
SRC = "tp/tp3-hbase/src/main/java/fr/orsys/hdd/tp3/"
W = "/tmp/hdd/tp3"
J = W + "/src/fr/orsys/hdd/tp3/"


def java(fichier, enonce=None, titre=None):
    corr = source(SRC + fichier)
    return code("sh", heredoc(J + fichier, corr), title=titre or fichier,
                enonce=heredoc(J + fichier, enonce) if enonce else None)


def remplacer(texte, avant, apres):
    assert avant in texte, avant[:60]
    return texte.replace(avant, apres)


CHARGE_ENONCE = remplacer(source(SRC + "ChargeCatalogue.java"), """        Put p = new Put(Bytes.toBytes(f[0]));
        p.addColumn(Catalogue.INFO, Bytes.toBytes("libelle"), ts, Bytes.toBytes(f[1]));
        p.addColumn(Catalogue.INFO, Bytes.toBytes("categorie"), ts, Bytes.toBytes(f[2]));
        p.addColumn(Catalogue.INFO, Catalogue.PRIX, ts, Bytes.toBytes(f[3]));
        p.addColumn(Catalogue.STOCK, Bytes.toBytes("quantite"), ts, Bytes.toBytes(f[4]));
        p.addColumn(Catalogue.STOCK, Bytes.toBytes("entrepot"), ts, Bytes.toBytes(f[5]));
        lot.add(p);
        if (lot.size() == tailleLot) {
          table.put(lot);                                 // un seul aller-retour par lot
          total += lot.size();
          lots++;
          lot.clear();
        }""", """        // TODO 1 : créer un Put pour la ligne f[0] (clé = identifiant produit)
        // TODO 2 : ajouter les 5 cellules, toutes à l'horodatage ts :
        //          info:libelle, info:categorie, info:prix, stock:quantite, stock:entrepot
        //          (p.addColumn(famille, colonne, ts, valeur) ; tout est en octets : Bytes.toBytes)
        // TODO 3 : ajouter le Put au lot ; quand le lot atteint tailleLot, l'envoyer
        //          en une fois (table.put(lot)), compter, puis vider le lot""")

HISTO_ENONCE = remplacer(source(SRC + "HistoriquePrix.java"), """      Get get = new Get(Bytes.toBytes(args[0]));
      get.addColumn(Catalogue.INFO, Catalogue.PRIX);
      get.readVersions(versions);
      Result r = table.get(get);""", """      // TODO : construire un Get sur la ligne args[0], limité à la colonne info:prix,
      //        demandant « versions » versions (readVersions), puis l'exécuter
      Result r = null;""")

MAJ_ENONCE = remplacer(source(SRC + "MajConditionnelle.java"), """      CheckAndMutate cam = CheckAndMutate.newBuilder(ligne)
          .ifEquals(Catalogue.INFO, Catalogue.PRIX, Bytes.toBytes(args[1]))
          .build(put);
      CheckAndMutateResult res = table.checkAndMutate(cam);""", """      // TODO : construire un CheckAndMutate sur la ligne : SI info:prix vaut args[1]
      //        ALORS appliquer le Put ; l'exécuter avec table.checkAndMutate(...)
      //        indice : CheckAndMutate.newBuilder(ligne).ifEquals(famille, colonne, valeur).build(put)
      CheckAndMutateResult res = null;""")

COMPILE = f"""cd {W}
rm -rf classes && mkdir -p classes
/opt/jdk17/bin/javac --release 17 -encoding UTF-8 -cp "$(hbase classpath 2>/dev/null)" -d classes $(find src -name '*.java') \\
  && /opt/jdk17/bin/jar cf catalogue.jar -C classes . && echo "OK : $(ls -l catalogue.jar)" """

RUN = 'java -cp "$(hbase classpath 2>/dev/null):/tmp/hdd/tp3/catalogue.jar"'
FILTRE = "2>&1 | grep -vE 'SLF4J|log4j|WARN|^\\s*$'"

P = [
md("""
## TP3 — HBase : gérer les modifications d'un catalogue de données

**Objectif** : créer un catalogue produits dans HBase et y appliquer des modifications en conservant l'historique.

| Étape | Contenu |
|---|---|
| 1. Créer | table `catalogue`, familles `info` (3 versions) et `stock`, depuis le shell |
| 2. Charger | insérer les produits fournis avec un programme Java (Put par lots) |
| 3. Modifier | changer des prix (shell et Java, modifications datées), ajouter une colonne `info:promo` à certains produits |
| 4. Historiser | relire les 3 dernières versions d'un prix (shell puis API Java) |
| 5. Sécuriser | mise à jour conditionnelle avec `checkAndMutate` |
| 6. Exposer | table externe Hive sur le catalogue, puis une requête SQL (et Impala) |

**Critères de réussite** : les trois versions d'un prix sont lisibles ; une colonne ajoutée n'existe que pour les lignes concernées ; la mise à jour conditionnelle échoue si la valeur a changé ; la requête Hive renvoie les valeurs courantes.

Prérequis : profil `full` (ou `zeppelin` + `hbase`, et `impala` pour la dernière requête). Console HBase : http://localhost:16010. Fichiers fournis : `/opt/data/hdd/catalogue/` (produits, modifications datées, promotions).
""", title="Présentation du TP"),

code("sh", """
head -4 /opt/data/hdd/catalogue/produits.csv
echo "..."; wc -l /opt/data/hdd/catalogue/*.csv
echo "--- modifications datées (les 6 premières)"
head -7 /opt/data/hdd/catalogue/modifications.csv
echo "--- promotions"
head -4 /opt/data/hdd/catalogue/promos.csv
""", title="0.1 Les fichiers du catalogue"),

md("""
### Étape 1 — Créer la table depuis le shell HBase

Une table HBase se déclare avec ses **familles de colonnes** seulement ; les colonnes elles-mêmes naissent à l'écriture. `VERSIONS => 3` : la famille `info` garde les trois dernières valeurs de chaque cellule.

L'interpréteur `%hbase` exécute le paragraphe dans `hbase shell` (quelques secondes de démarrage à chaque fois).
""", title="Étape 1"),

code("hbase", """
create 'catalogue', {NAME => 'info', VERSIONS => 3}, 'stock'
describe 'catalogue'
list
""", title="1.1 Créer et décrire la table",
enonce="""
# TODO : créer la table 'catalogue' avec deux familles :
#   info  : 3 versions conservées par cellule
#   stock : réglages par défaut
# puis la décrire (describe) et lister les tables (list)
"""),

md("""
### Étape 2 — Charger avec l'API Java : Put par lots

`ChargeCatalogue` lit `produits.csv` et envoie les lignes par **lots** de 50 `Put` : un aller-retour réseau par lot au lieu d'un par ligne. Toutes les cellules portent l'horodatage du 1er janvier 2026 (création du catalogue) : les modifications datées de l'étape 3 deviendront des versions plus récentes.

Une `Connection` est lourde (à partager), une `Table` est légère (une par usage, à fermer) : d'où le *try-with-resources*.
""", title="Étape 2"),

java("Catalogue.java", None, "2.1 Catalogue.java (constantes, fourni)"),
java("ChargeCatalogue.java", CHARGE_ENONCE, "2.2 ChargeCatalogue.java"),
java("AppliqueModifications.java", None, "2.3 AppliqueModifications.java (fourni, utilisé à l'étape 3)"),
java("HistoriquePrix.java", HISTO_ENONCE, "2.4 HistoriquePrix.java (utilisé à l'étape 4)"),
java("MajConditionnelle.java", MAJ_ENONCE, "2.5 MajConditionnelle.java (utilisé à l'étape 5)"),
java("CreerCatalogue.java", None, "2.6 CreerCatalogue.java (variante Java de l'étape 1, fournie)"),
code("sh", COMPILE, title="2.7 Compiler (classpath : hbase classpath)"),

code("sh", f"""
cd {W}
{RUN} fr.orsys.hdd.tp3.ChargeCatalogue /opt/data/hdd/catalogue/produits.csv 50 {FILTRE}
""", title="2.8 Charger le catalogue"),

code("hbase", """
count 'catalogue'
get 'catalogue', 'P0001'
scan 'catalogue', {LIMIT => 2}
""", title="2.9 Vérifier dans le shell"),

md("""
### Étape 3 — Modifier

1. Changer un prix à la main dans le shell (horodatage = maintenant).
2. Appliquer les **modifications datées** (3 vagues : avril, juillet, octobre 2026) avec `AppliqueModifications` : chaque `Put` porte l'horodatage de sa date d'effet.
3. Ajouter la colonne `info:promo` **aux seuls produits en promotion** : le shell peut lire des commandes sur son entrée standard (`hbase shell -n`).
""", title="Étape 3"),

code("hbase", """
put 'catalogue', 'P0002', 'info:prix', '9.90'
get 'catalogue', 'P0002', 'info:prix'
""", title="3.1 Modifier un prix dans le shell",
enonce="""
# TODO : fixer le prix du produit P0002 à 9.90 (commande put), puis relire la cellule (get)
"""),

code("sh", f"""
cd {W}
{RUN} fr.orsys.hdd.tp3.AppliqueModifications /opt/data/hdd/catalogue/modifications.csv {FILTRE}
""", title="3.2 Appliquer les modifications datées (Java)"),

code("sh", """
# Une commande « put » par ligne de promos.csv, envoyées en une fois au shell HBase
tail -n +2 /opt/data/hdd/catalogue/promos.csv \\
  | sed -E "s/^([^;]+);(.*)$/put 'catalogue', '\\1', 'info:promo', '\\2'/" > /tmp/hdd/tp3/promos.hbase
head -3 /tmp/hdd/tp3/promos.hbase
hbase shell -n < /tmp/hdd/tp3/promos.hbase 2>&1 | grep -cE '^Took' | xargs echo "commandes exécutées :"
""", title="3.3 Ajouter info:promo aux produits en promotion"),

code("hbase", """
scan 'catalogue', {COLUMNS => ['info:promo']}
get 'catalogue', 'P0003'
""", title="3.4 Une colonne n'existe que là où elle a été écrite"),

md("""
**À observer** : le `scan` sur `info:promo` ne renvoie que les 15 produits en promotion ; `P0003` n'a pas de cellule `promo` du tout. Une table HBase est **creuse** : une colonne absente ne coûte rien, il n'y a pas de valeur « NULL » stockée.

### Étape 4 — Historiser
""", title="Étape 4"),

code("hbase", """
get 'catalogue', 'P0001', {COLUMN => 'info:prix', VERSIONS => 3}
get 'catalogue', 'P0007', {COLUMN => 'info:prix', VERSIONS => 5}
""", title="4.1 Versions d'un prix dans le shell",
enonce="""
# TODO : afficher les 3 dernières versions de info:prix pour P0001
#        indice : get 'table', 'ligne', {COLUMN => ..., VERSIONS => ...}
# TODO : même chose pour P0007 en demandant 5 versions : combien en obtenez-vous ?
"""),

code("sh", f"""
cd {W}
{RUN} fr.orsys.hdd.tp3.HistoriquePrix P0001 3 {FILTRE}
{RUN} fr.orsys.hdd.tp3.HistoriquePrix P0007 5 {FILTRE}
""", title="4.2 Versions d'un prix avec l'API Java"),

md("""
**Questions** : P0007 a reçu 4 prix (création + 3 vagues). Pourquoi n'en lit-on que 3 ? Quand la version la plus ancienne disparaît-elle physiquement du disque ?
""", title="Questions"),

md("""
**Réponse** : `VERSIONS => 3` sur la famille `info` : à la lecture, HBase ne renvoie jamais plus de 3 versions ; la plus ancienne est supprimée physiquement lors d'une **compaction majeure** (réécriture des HFiles), visible avec `major_compact 'catalogue'`. Les horodatages ordonnent les versions : ici ce sont les dates d'effet, pas l'heure d'écriture.
""", title="Réponse", only="corrige"),

md("""
### Étape 5 — Sécuriser : mise à jour conditionnelle

Deux applications lisent le prix de P0001 (27.90) et veulent le changer. Avec un simple `Put`, la dernière écriture écrase l'autre sans le savoir. `checkAndMutate` teste et écrit **atomiquement** sur le RegionServer : le changement n'a lieu que si la valeur courante est encore celle attendue.
""", title="Étape 5"),

code("sh", f"""
cd {W}
echo "1re mise à jour, prix attendu 27.90 :"
{RUN} fr.orsys.hdd.tp3.MajConditionnelle P0001 27.90 25.90 {FILTRE}
echo "2e mise à jour, avec la même valeur attendue (devenue fausse) :"
{RUN} fr.orsys.hdd.tp3.MajConditionnelle P0001 27.90 24.90 {FILTRE}
""", title="5.1 Deux mises à jour concurrentes"),

code("hbase", """
get 'catalogue', 'P0001', {COLUMN => 'info:prix', VERSIONS => 3}
""", title="5.2 Historique après la mise à jour"),

md("""
### Étape 6 — Exposer le catalogue au SQL

Hive et Impala ne lisent pas HBase directement dans ce lab. On **exporte** les valeurs courantes (la dernière version de chaque cellule) dans un fichier sur HDFS, puis on pose une table externe Hive dessus. L'export passe par le serveur Thrift d'HBase, avec la bibliothèque Python `happybase`.

> Variante « en direct », sans copie : une table Hive `STORED BY 'org.apache.hadoop.hive.hbase.HBaseStorageHandler'` avec `"hbase.columns.mapping" = ":key,info:libelle,info:prix,..."`. Elle lit HBase à chaque requête, mais exige les jars clients HBase et la configuration ZooKeeper côté HiveServer2 et sur les nœuds YARN.
""", title="Étape 6"),

code("python", source("tp/tp3-hbase/export_catalogue.py"), title="6.1 Exporter les valeurs courantes (happybase)"),

code("hive", source("tp/tp3-hbase/catalogue_export.hql").split("SELECT id, libelle")[0].strip().rstrip(";"),
     title="6.2 Table externe Hive sur l'export",
     enonce="""
CREATE DATABASE IF NOT EXISTS catalogue;
-- TODO : table externe catalogue.produits_export sur /data/catalogue/export
--        colonnes : id, libelle, categorie, prix (DOUBLE), promo, quantite (INT), entrepot
--        fichier texte, séparateur « ; »
"""),

code("hive", """
SELECT id, libelle, prix, promo FROM catalogue.produits_export WHERE id IN ('P0001', 'P0007')
""", title="6.3 Valeurs courantes vues par Hive"),

code("hive", """
SELECT categorie, COUNT(*) AS nb_produits, ROUND(AVG(prix), 2) AS prix_moyen,
       SUM(quantite) AS stock_total, COUNT(NULLIF(promo, '')) AS nb_promos
FROM catalogue.produits_export
GROUP BY categorie
ORDER BY categorie
""", title="6.4 Synthèse par catégorie (graphique)", graph=bar_chart([(0, "categorie")], [(2, "prix_moyen")])),

code("impala", """
INVALIDATE METADATA catalogue.produits_export;
SELECT categorie, COUNT(*) AS nb_produits, ROUND(AVG(prix), 2) AS prix_moyen
FROM catalogue.produits_export GROUP BY categorie ORDER BY categorie
""", title="6.5 La même table vue par Impala"),

md("""
### Pour aller plus loin

* **Filtre côté serveur** : `scan 'catalogue', {FILTER => "SingleColumnValueFilter('info', 'categorie', =, 'binary:saisie')"}`. Le filtre s'exécute sur le RegionServer, mais il parcourt toute la table : une bonne **clé de ligne** reste le premier levier de performance.
* **Régions** : `list_regions 'catalogue'`, puis la page de la table sur http://localhost:16010.
* **Créer la table en Java** : `disable 'catalogue'`, `drop 'catalogue'`, puis `CreerCatalogue` (API à builders, valable en HBase 2.x et 3.x) et rejouer les étapes 2 à 5.
""", title="Bonus"),

code("hbase", """
scan 'catalogue', {FILTER => "SingleColumnValueFilter('info', 'categorie', =, 'binary:saisie')", COLUMNS => ['info:libelle', 'info:prix'], LIMIT => 5}
list_regions 'catalogue'
""", title="B.1 Filtre côté serveur, régions"),

md("""
### Contrôle des critères de réussite
""", title="Contrôle"),

code("python", """
import happybase, subprocess
ok = lambda m: print("  [ OK ]", m)
ko = lambda m: print("  [ KO ]", m)
conn = happybase.Connection("hbase-thrift", 9090, timeout=20000)
t = conn.table("catalogue")
versions = t.cells(b"P0001", b"info:prix", versions=5)
(ok if len(versions) == 3 else ko)(f"P0001 : {len(versions)} versions lisibles de info:prix {[v.decode() for v in versions]}")
promos = sum(1 for _ in t.scan(columns=[b"info:promo"]))
total = sum(1 for _ in t.scan(columns=[b"info:libelle"]))
(ok if 0 < promos < total else ko)(f"info:promo présente sur {promos} produits sur {total}")
courant = t.row(b"P0001", columns=[b"info:prix"]).get(b"info:prix", b"").decode()
(ok if courant == "25.90" else ko)(f"mise à jour conditionnelle : prix courant de P0001 = {courant} (25.90 attendu, la 2e mise à jour refusée)")
conn.close()
export = subprocess.run(["hdfs", "dfs", "-cat", "/data/catalogue/export/catalogue.csv"], capture_output=True, text=True).stdout
ligne = next((l for l in export.splitlines() if l.startswith("P0001;")), "")
(ok if ";25.90;" in ligne else ko)(f"export lu par Hive à jour : {ligne or 'absent (étape 6.1)'}")
""", title="Contrôle automatique"),
]
