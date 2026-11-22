#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TP2 — Mesures d'un job MapReduce terminé, lues dans le JobHistory Server (API REST).

    python3 /opt/tp/tp2-yarn/mesurer_job.py job_1763650000000_0003 [libellé]

Affiche : file YARN, durée, nombre de maps et de reduces, nombre MAXIMAL de
maps exécutés en même temps (calculé à partir des heures de début et de fin
de chaque tâche), durée moyenne d'un map.
"""
import json
import sys
import time
import urllib.error
import urllib.request

JHS = "http://historyserver:19888/ws/v1/history/mapreduce/jobs/"


def lire(url, tentatives=20):
    """Le JHS ne connaît le job que quelques secondes après sa fin : on réessaie."""
    for i in range(tentatives):
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                return json.load(r)
        except (urllib.error.HTTPError, urllib.error.URLError):
            if i == tentatives - 1:
                raise
            time.sleep(3)


def simultanes_max(taches):
    evts = []
    for t in taches:
        evts.append((t["startTime"], 1))
        evts.append((t["finishTime"], -1))
    courant = maxi = 0
    for _, delta in sorted(evts, key=lambda e: (e[0], e[1])):
        courant += delta
        maxi = max(maxi, courant)
    return maxi


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    job_id = sys.argv[1]
    libelle = sys.argv[2] if len(sys.argv) > 2 else ""
    job = lire(JHS + job_id)["job"]
    taches = lire(JHS + job_id + "/tasks")["tasks"]["task"]
    maps = [t for t in taches if t["type"] == "MAP"]
    duree = (job["finishTime"] - job["startTime"]) / 1000.0
    print(f"MESURE {libelle}".strip())
    print(f"  job              : {job_id} ({job['state']})")
    print(f"  file YARN        : {job['queue']}")
    print(f"  durée            : {duree:.1f} s")
    print(f"  maps / reduces   : {job['mapsTotal']} / {job['reducesTotal']}")
    print(f"  maps simultanés  : {simultanes_max(maps)} au maximum")
    print(f"  durée moy. map   : {job.get('avgMapTime', 0) / 1000.0:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
