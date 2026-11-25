# Guide formateur — hand-labs HDD

## Avant la session

### Poste stagiaire

- VM Ubuntu (ou poste Linux) x86_64, **4 CPU / 16 Go de RAM alloués à Docker minimum** pour le profil `full` (8 CPU / 24 Go conseillés), 25 Go de disque libre ; Docker Engine 23+ et Compose v2. Un conteneur tué par manque de mémoire s'arrête avec le code 137 (`docker inspect -f '{{.State.OOMKilled}}' <conteneur>`) : relever son `mem_limit` dans le compose.
- Avec 16 Go de RAM au total (et non pour Docker seul) : utiliser `docker-compose-light.yml`.

### Préparation (la veille)

```bash
git clone https://github.com/crystalloide/HDD && cd HDD
docker compose --profile full up -d --build      # 15 à 30 min la première fois
bash scripts/check_stack.sh --complet             # tout doit être [ OK ]
                                                  # (inclut scripts/check_interpreteurs.sh : un paragraphe par interpréteur Zeppelin)
```

Puis dérouler **une fois chaque notebook corrigé** (*HDD / 2 - Corriges*, *Run all*) sur un poste de référence : c'est le meilleur test de l'environnement. Remettre ensuite les postes à zéro :

```bash
docker compose --profile full --profile llap down -v
docker compose --profile full up -d
```

Les images restent en cache : le redémarrage prend 3 à 5 minutes.

> **Important — première utilisation.** La pile Docker est celle du dépôt BD540, éprouvée. Les ajouts propres à HDD — JobHistory Server, Pig 0.18, client MapReduce de Zeppelin, permissions HDFS actives avec masque `000` — ont été conçus sur cette base et le code des TP a été testé hors cluster (jobs MapReduce en mode local, Spark local, HiveQL, compilation Java), mais l'ensemble n'a pas encore tourné sur un poste complet. Le passage des corrigés la veille est donc indispensable pour la première session.

### Images partagées (salle sans bon débit)

Construire les images une fois, puis les distribuer :

```bash
docker save $(docker images --format '{{.Repository}}:{{.Tag}}' | grep -E '^hdd-lab|apache/impala|postgres|zookeeper') | gzip > hdd-images.tgz
# sur chaque poste :  gunzip -c hdd-images.tgz | docker load
```

## Déroulé proposé sur 3 jours

| Jour | Chapitre | Lab | Durée |
|---|---|---|---|
| 1 | 1. Le big data | démonstration *00 - Prise en main* (wordcount, consoles) | 15 min |
| 1 | 2. Collecte et MapReduce (début) | **TP1** | 2 h 30 |
| 2 | 2. Collecte et MapReduce (fin) | **TP2** | 1 h 30 |
| 2 | 3. Stockage avec HBase | **TP3** | 2 h |
| 3 | 4. Stockage sur HDFS, Pig et Hive | **TP4** | 2 h 30 |
| 3 | Spark (prolongement) | **TP5** | 1 h 30 |

Distribuer les **énoncés** (*1 - Enonces*) ; les **corrigés** (*2 - Corriges*) sont dans la même instance Zeppelin : à masquer ou à supprimer des postes si nécessaire (`docker exec zeppelin rm -rf "/opt/zeppelin/notebook/HDD/2 - Corriges"` puis redémarrer Zeppelin), ou à ouvrir en fin de TP.

## Points d'attention par TP

### TP1 — Collecte et MapReduce

- Le premier essai sur les données **brutes** est volontairement faux (une centaine de « villes ») : c'est l'accroche de l'étape de collecte.
- Les stagiaires qui bloquent sur un fichier Java peuvent exécuter le paragraphe correspondant du corrigé : chaque fichier est écrit par son propre paragraphe.
- Le répertoire de sortie ne doit pas exister : les paragraphes le suppriment avant chaque lancement (`hdfs dfs -rm -r -f`).
- Valeurs attendues : 36 712 lignes lues, 36 025 valides, 3 en-têtes, 684 rejets (FORMAT 246, VILLE_ABSENTE 268, CA_INVALIDE 170), 24 villes.

### TP2 — YARN

- Deux actions se font **depuis l'hôte** (🖥️) : recréer le NodeManager avec `NM_MEMORY_MB`, puis `bash tp/tp2-yarn/ajouter_file_dev.sh`. Prévoir un terminal à côté du navigateur.
- **Remettre la capacité d'origine** après l'étape 4 (`docker compose --profile full up -d nodemanager`) : avec 2048 Mo, les sessions Tez de Hive se partagent très peu de place.
- Recréer le NodeManager interrompt les sessions Tez en cours (Hue, `%hive`) : elles se rouvrent à la requête suivante.
- Valeurs attendues (NodeManager à 4096 Mo / 8 vcores, AM 512 Mo) : 7 maps simultanés avec des maps de 512 Mo, 3 avec 1024 Mo, 3 avec un NodeManager à 2048 Mo, 3 dans la file `dev` (plafond 50 %). En version légère (3072 Mo / 4 vcores, les vcores limitent) : 3, 2, 3 et 1.
- Avant les mesures, arrêter les sessions Tez ouvertes par Hue ou `%hive`, qui occupent des conteneurs : `yarn application -list`, puis `yarn application -kill <id>` (ou attendre 5 min d'inactivité).
- La file `dev` est perdue si le ResourceManager est recréé : la rendre permanente avec le bloc commenté en fin de `hadoop/config`.

### TP3 — HBase

- Chaque paragraphe `%hbase` relance un shell HBase : quelques secondes de démarrage.
- Si la table existe déjà (TP relancé) : `disable 'catalogue'`, `drop 'catalogue'`.
- Les horodatages des modifications sont des **dates d'effet** (2026) : un `put` manuel fait aujourd'hui est donc plus récent que toutes les vagues. Après `MajConditionnelle`, P0001 vaut 25.90 et ses 3 versions lisibles sont 25.90, 27.90, 28.90.
- L'exposition à Hive passe par un **export** : le prix lu par Hive est celui du moment de l'export. Discuter la variante `HBaseStorageHandler` (lecture en direct) et ses prérequis.

### TP4 — Référentiel Pig / Hive

- Point clé pédagogique : HDFS en authentification simple croit `HADOOP_USER_NAME`. Les droits protègent des erreurs, pas des malveillants : Kerberos. Et avec `doAs=false`, tout utilisateur SQL lit le référentiel par Hive : Ranger.
- Le quota d'espace de 50 Mo (étape 3.2) fait échouer l'écriture d'un fichier de 1 Ko : HDFS réserve un bloc complet de 128 Mo.
- Pig lance plusieurs jobs MapReduce (2 à 4 min au total) : en profiter pour parcourir le JobHistory.
- Hue *Fichiers* sous le compte `hue` : accès **refusé** au référentiel (pas d'ACL pour ce compte) ; créer l'utilisateur Hue `bob` pour montrer l'accès par le groupe `marketing`.
- Si une étape d'administration a été mal faite : `bash /opt/tp/commun/preparer_referentiel.sh` remet la zone dans l'état attendu (dans un paragraphe `%sh`).
- Valeur attendue : 24 254 clients, 10 225 présents dans plusieurs canaux.

### TP5 — Spark

- Le paragraphe 0.1 prépare la zone si le TP4 n'a pas été fait ; il ajoute les ACL du compte `root` (Spark de Zeppelin).
- Version légère : le worker Spark n'a que 2 cœurs ; arrêter l'interpréteur Spark de Zeppelin avant le `spark-submit` de l'étape 7.
- Les comparaisons TP4 / TP5 (paragraphe 5.3) doivent donner 0 écart : les règles de nettoyage sont identiques dans les deux chaînes.

## Remettre un TP à zéro (paragraphe `%sh`)

```bash
# TP1 / TP2
hdfs dfs -rm -r -f -skipTrash /data/raw /data/clean /data/out ; rm -rf /tmp/hdd/tp1 /tmp/hdd/tp2
# TP4 / TP5 (superutilisateur : instantanés et quotas d'abord)
export HADOOP_USER_NAME=hadoop
hdfs dfs -deleteSnapshot /data/referentiel/clients avant_maj ; hdfs dfsadmin -disallowSnapshot /data/referentiel/clients
hdfs dfsadmin -clrSpaceQuota /data/referentiel/clients ; hdfs dfsadmin -clrQuota /data/referentiel/clients
hdfs dfs -rm -r -f -skipTrash /data/referentiel
```

```sql
-- %hive : les tables sont externes, DROP ne supprime que les définitions
DROP DATABASE IF EXISTS referentiel CASCADE;
DROP DATABASE IF EXISTS catalogue CASCADE;
DROP DATABASE IF EXISTS tp1 CASCADE;
```

```
# %hbase
disable 'catalogue'
drop 'catalogue'
```
