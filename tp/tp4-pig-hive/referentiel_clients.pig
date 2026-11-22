-- =============================================================================
-- TP4 — Référentiel client unique, en Pig Latin (exécuté en MapReduce sur YARN)
--
--   pig -x mapreduce \
--       -param BRUTE=/data/referentiel/clients/brute \
--       -param SORTIE_REF=/data/referentiel/clients/raffinee/clients \
--       -param SORTIE_STATS=/data/referentiel/clients/raffinee/stats_villes \
--       -param UDF_JAR=/tmp/hdd/tp4/udfs.jar \
--       -f referentiel_clients.pig
--
-- Entrée  : fichiers bruts id;nom;ville;ca;segment;canal;date_inscription
--           (un client peut figurer dans plusieurs canaux)
-- Sorties : référentiel (1 ligne par client) et statistiques par ville.
-- Les deux STORE sont exécutés ensemble (« multi-query ») : les données ne
-- sont lues qu'une fois.
-- =============================================================================

REGISTER '$UDF_JAR';
DEFINE NormaliseVille fr.orsys.hdd.tp4.NormaliseVille();

brut = LOAD '$BRUTE' USING PigStorage(';')
       AS (id:chararray, nom:chararray, ville:chararray, ca:chararray,
           segment:chararray, canal:chararray, date_inscription:chararray);

-- 1. Doublons exacts (même ligne exportée deux fois par le CRM) : supprimés
uniques = DISTINCT brut;

-- 2. Lignes exploitables : identifiant valide (élimine aussi les en-têtes et
--    les lignes au mauvais séparateur), ville renseignée, CA numérique positif,
--    date présente (élimine les lignes tronquées)
valides = FILTER uniques BY id MATCHES 'C[0-9]{6}'
                        AND NormaliseVille(ville) IS NOT NULL
                        AND ca MATCHES '[0-9]+(\\.[0-9]+)?'
                        AND date_inscription MATCHES '[0-9]{4}-[0-9]{2}-[0-9]{2}';

norm = FOREACH valides GENERATE
           id,
           TRIM(nom)             AS nom,
           NormaliseVille(ville) AS ville,
           (double) ca           AS ca,
           LOWER(TRIM(segment))  AS segment,
           LOWER(TRIM(canal))    AS canal,
           date_inscription;

-- 3. Un client = une ligne : CA cumulé sur ses canaux, liste des canaux
par_client = GROUP norm BY id;
referentiel = FOREACH par_client {
    canaux = DISTINCT norm.canal;
    GENERATE group                      AS id,
             MAX(norm.nom)              AS nom,
             MAX(norm.ville)            AS ville,
             MAX(norm.segment)          AS segment,
             ROUND_TO(SUM(norm.ca), 2)  AS ca_total,
             COUNT(canaux)              AS nb_canaux,
             BagToString(canaux, '|')   AS canaux,
             MIN(norm.date_inscription) AS date_premiere_inscription;
};

-- 4. Statistiques par ville, pour la console de visualisation
par_ville = GROUP referentiel BY ville;
stats_villes = FOREACH par_ville GENERATE
                   group                                  AS ville,
                   COUNT(referentiel)                     AS nb_clients,
                   ROUND_TO(SUM(referentiel.ca_total), 2) AS ca_total;

STORE referentiel  INTO '$SORTIE_REF'   USING PigStorage(';');
STORE stats_villes INTO '$SORTIE_STATS' USING PigStorage(';');
