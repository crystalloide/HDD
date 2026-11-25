#!/usr/bin/env python3
# =============================================================================
# check_interpreteurs.py — contrôle des interpréteurs Zeppelin utiles aux TP HDD
# Exécuté DANS le conteneur zeppelin par scripts/check_interpreteurs.sh :
#   1. présence et réglage de chaque interpréteur (API REST de Zeppelin) ;
#   2. exécution d'un paragraphe de test par interpréteur, dans une note
#      temporaire supprimée à la fin.
# Un interpréteur dont le service n'est pas démarré (profil non activé) est
# simplement ignoré. Code retour : 0 si aucun KO, 1 sinon.
# =============================================================================
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("ZEPPELIN_URL", "http://localhost:8082").rstrip("/") + "/api"
ACTIFS = set(os.environ.get("ACTIFS", "").split())
SANS_EXECUTION = os.environ.get("SANS_EXECUTION", "0") == "1"

SPARK = ["spark-master", "spark-worker"]

# (réglage, groupe, propriété clé, valeur attendue, TP qui l'utilisent)
REGLAGES = [
    ("sh",     "sh",     None,              None,                                             "TP1 à TP5"),
    ("hive",   "jdbc",   "default.url",     "jdbc:hive2://hiveserver2:10000/default",         "TP1, TP3, TP4, TP5"),
    ("impala", "jdbc",   "default.url",     "jdbc:hive2://impalad:21050/default;auth=noSasl", "TP3, TP4, TP5"),
    ("hbase",  "hbase",  "hbase.home",      "/opt/hbase",                                     "TP3, compléments HBase"),
    ("spark",  "spark",  "spark.master",    "spark://spark-master:7077",                      "TP5"),
    ("python", "python", "zeppelin.python", "python3",                                        "TP3 (happybase)"),
    ("md",     "md",     None,              None,                                             "tous (textes)"),
    ("file",   "file",   "hdfs.url",        "http://namenode:9870/webhdfs/v1/",               "démo écosystème"),
    ("java",   "java",   None,              None,                                             "démo écosystème"),
]

# (libellé, texte du paragraphe, texte attendu dans le résultat, conteneurs requis)
TESTS = [
    ("%md",            "%md\nOK-md", "OK-md", []),
    ("%sh",            "%sh\nhdfs dfs -test -d /data && echo OK-sh", "OK-sh", ["namenode"]),
    ("%python",        "%python\nimport happybase, pandas\nprint('OK-python')", "OK-python", []),
    ("%file",          "%file\nls /", "user", ["namenode"]),
    ("%hive",          "%hive\nSELECT 'OK-hive'", "OK-hive", ["hiveserver2"]),
    ("%impala",        "%impala\nSELECT 'OK-impala'", "OK-impala", ["impalad"]),
    ("%hbase",         "%hbase\nlist", "row(s)", ["hbase-master", "hbase-regionserver"]),
    ("%java",          "%java\npublic class Controle {\n"
                       "  public static void main(String[] args) { System.out.println(\"OK-java\"); }\n}",
                       "OK-java", []),
    # Spark en dernier : le premier paragraphe démarre l'application (30 à 90 s)
    ("%spark.pyspark", "%spark.pyspark\nprint('OK-pyspark', spark.range(5).count())", "OK-pyspark 5", SPARK),
    ("%spark.sql",     "%spark.sql\nSELECT 'OK-sparksql' AS controle", "OK-sparksql", SPARK),
]

REPARATION = (
    "Réglages d'origine : recréer le conteneur Zeppelin, qui repart de\n"
    "zeppelin/conf/interpreter.json (les notebooks, dans un volume, sont conservés) :\n"
    "    docker compose --profile full up -d --force-recreate zeppelin\n"
    "    (version légère : docker compose -f docker-compose-light.yml --profile full up -d --force-recreate zeppelin)"
)


def appel(methode, chemin, corps=None, delai=60):
    donnees = json.dumps(corps).encode("utf-8") if corps is not None else None
    req = urllib.request.Request(BASE + chemin, data=donnees, method=methode,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=delai) as rep:
            return json.load(rep)
    except urllib.error.HTTPError as err:
        try:
            return json.load(err)
        except Exception:
            return {"status": "HTTP %d" % err.code, "message": str(err)}


def valeur(prop):
    if isinstance(prop, dict):
        return prop.get("value", prop.get("defaultValue"))
    return prop


def ligne(etat, libelle, detail=""):
    print("  [ %s ]  %s%s" % (etat, libelle, ("  " + detail) if detail else ""))


def resume(texte, n=6):
    lignes = [l for l in (texte or "").strip().splitlines() if l.strip()]
    return "\n".join("           | " + l[:150] for l in lignes[:n])


def controle_reglages():
    print("== Interpréteurs déclarés (Settings > Interpreter) ==")
    rep = appel("GET", "/interpreter/setting")
    if rep.get("status") != "OK":
        ligne("KO", "API REST de Zeppelin injoignable", str(rep)[:200])
        return 1, set()
    reglages = {s["name"]: s for s in rep["body"]}
    ko, presents = 0, set()
    for nom, groupe, cle, attendu, tp in REGLAGES:
        s = reglages.get(nom)
        if s is None:
            ligne("KO", "%-7s absent" % nom, "(utilisé par : %s)" % tp)
            ko += 1
            continue
        if s.get("group") != groupe:
            ligne("KO", "%-7s groupe %s au lieu de %s" % (nom, s.get("group"), groupe))
            ko += 1
            continue
        presents.add(nom)
        if cle is None:
            ligne("OK", "%-7s (%s)" % (nom, groupe), "TP : %s" % tp)
            continue
        v = valeur(s.get("properties", {}).get(cle))
        if attendu is not None and v != attendu:
            ligne("KO", "%-7s %s = %s" % (nom, cle, v), "attendu : %s" % attendu)
            ko += 1
        else:
            ligne("OK", "%-7s %s = %s" % (nom, cle, v), "TP : %s" % tp)
    autres = sorted(set(reglages) - {r[0] for r in REGLAGES})
    if autres:
        print("  Autres interpréteurs installés (non utilisés par les TP) : " + ", ".join(autres))
    return ko, presents


def controle_execution(presents):
    print("")
    print("== Exécution d'un paragraphe par interpréteur (note temporaire) ==")
    a_lancer = []
    for libelle, texte, attendu, requis in TESTS:
        reglage = libelle[1:].split(".")[0]
        manquants = [c for c in requis if c not in ACTIFS]
        if reglage not in presents:
            ligne("--", libelle, "(interpréteur absent, voir ci-dessus)")
        elif manquants:
            ligne("--", libelle, "(non démarré : %s)" % ", ".join(manquants))
        else:
            a_lancer.append((libelle, texte, attendu))
    if not a_lancer:
        return 0

    rep = appel("POST", "/notebook", {
        "notePath": "/_controle_interpreteurs_%d" % int(time.time()),
        "paragraphs": [{"title": l, "text": t} for l, t, _ in a_lancer],
    })
    if rep.get("status") != "OK":
        ligne("KO", "création de la note de test", str(rep)[:200])
        return 1
    note_id = rep["body"]
    ko = 0
    try:
        note = appel("GET", "/notebook/" + note_id)["body"]
        ids = [p["id"] for p in note["paragraphs"]]
        for (libelle, _, attendu), pid in zip(a_lancer, ids):
            debut = time.time()
            appel("POST", "/notebook/run/%s/%s" % (note_id, pid), delai=300)
            p = appel("GET", "/notebook/%s/paragraph/%s" % (note_id, pid)).get("body", {})
            res = p.get("results") or {}
            sortie = "\n".join(m.get("data", "") for m in res.get("msg", []))
            duree = "%.0f s" % (time.time() - debut)
            if res.get("code") == "SUCCESS" and attendu in sortie:
                ligne("OK", libelle, duree)
            else:
                ko += 1
                ligne("KO", libelle, "%s, statut %s" % (duree, p.get("status")))
                print(resume(sortie or p.get("errorMessage") or "(aucune sortie)"))
    finally:
        appel("DELETE", "/notebook/" + note_id)
    return ko


def main():
    ko, presents = controle_reglages()
    if not SANS_EXECUTION:
        ko += controle_execution(presents)
    print("")
    if ko:
        print("Résultat : %d KO." % ko)
        print(REPARATION)
        return 1
    if SANS_EXECUTION:
        print("Résultat : tous les interpréteurs utiles aux TP sont présents et correctement réglés.")
        return 0
    print("Résultat : tous les interpréteurs utiles aux TP sont présents et répondent.")
    if set(SPARK) <= ACTIFS:
        print("(L'application Spark « zeppelin » reste démarrée : elle est partagée avec les notebooks.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
