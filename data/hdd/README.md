# Données des hand-labs HDD

Données **fictives**, générées par `scripts/generer_donnees_hdd.py` (graine fixe : le script régénère exactement les mêmes fichiers). Montées dans Zeppelin sous `/opt/data/hdd` (lecture seule).

## Clients — `clients/` (TP1, TP4, TP5)

Trois extractions du même jour, une par canal. Séparateur `;`, première ligne = en-tête :

```
id;nom;ville;ca;segment;canal;date_inscription
C000001;Céline Faure;Bordeaux;228.67;particulier;crm;2019-02-25
```

| Champ | Contenu |
|---|---|
| `id` | identifiant client `C` + 6 chiffres ; un même client peut figurer dans plusieurs canaux |
| `nom` | prénom et nom |
| `ville` | ville de résidence (24 villes), saisie libre |
| `ca` | chiffre d'affaires annuel du client **dans ce canal** (euros, point décimal) |
| `segment` | `particulier`, `professionnel`, `entreprise` |
| `canal` | `crm`, `web`, `magasin` |
| `date_inscription` | `aaaa-mm-jj` |

| Fichier | Lignes (en-tête comprise) |
|---|---|
| `crm_2026-11.csv` | 18 887 |
| `web_2026-11.csv` | 9 931 |
| `magasins_2026-11.csv` | 7 894 |

### Anomalies volontaires

| Anomalie | Volume | Traitement attendu |
|---|---|---|
| ligne d'en-tête dans chaque fichier | 3 | ignorée |
| villes saisies en majuscules, minuscules, avec espaces, sans accents | ~6 % des lignes | normalisation : sans accents, espaces réduits, majuscules (`  saint-étienne ` → `SAINT-ETIENNE`) |
| mauvais séparateur (`,`) ou champ manquant | 246 | rejet `FORMAT` |
| ville vide | 268 | rejet `VILLE_ABSENTE` |
| CA illisible (`N/A`, `12,50`, vide) ou négatif | 170 | rejet `CA_INVALIDE` |
| doublons exacts dans l'export CRM | 63 | supprimés avant consolidation |

## Valeurs de référence (`attendus.json`)

| Indicateur | Valeur |
|---|---|
| lignes valides après collecte (TP1, doublons exacts compris) | 36 025 |
| villes après normalisation | 24 |
| clients uniques du référentiel (TP4, TP5) | 24 254 |
| dont présents dans plusieurs canaux | 10 225 |
| CA total du référentiel | 57 982 586,91 € |

## Catalogue — `catalogue/` (TP3)

| Fichier | Format | Contenu |
|---|---|---|
| `produits.csv` | `id;libelle;categorie;prix;quantite;entrepot` | 120 produits (`P0001` = Clavier, 29.90, catégorie `saisie`) |
| `modifications.csv` | `id;famille;colonne;valeur;date_effet` | 65 modifications en 3 vagues (2026-04-01, 2026-07-01, 2026-10-01) ; la date d'effet devient l'horodatage HBase |
| `promos.csv` | `id;promo` | 15 produits en promotion (colonne `info:promo`) |

Cas d'école : `P0001` passe de 29.90 à 28.90 puis 27.90 (exactement 3 versions) ; `P0007` change aux 3 vagues (4 valeurs, seules les 3 plus récentes restent lisibles avec `VERSIONS => 3`).
