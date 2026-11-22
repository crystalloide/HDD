# -*- coding: utf-8 -*-
"""
Régénère les notebooks des TP (énoncés et corrigés) à partir des fichiers
tp*.py de ce dossier et des sources de tp/.

    pip install markdown          # rendu HTML des paragraphes %md
    python3 tools/notebooks/generer.py

Écrit zeppelin/notebook/HDD/{0 - Demarrage, 1 - Enonces, 2 - Corriges}/.
Les notebooks de « 3 - Complements » et « Demo ecosysteme » ne sont pas touchés.
Ensuite : reconstruire l'image Zeppelin et réinitialiser le volume des notebooks
(voir le README, section « Réinitialiser »).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zep  # noqa: E402
import tp0, tp1, tp2, tp3, tp4, tp5  # noqa: E402,E401

print(*zep.build(tp0.P, "corrige", tp0.NAME, "2HDD00DEM", "HDD/0 - Demarrage"))
for mod, num in [(tp1, 1), (tp2, 2), (tp3, 3), (tp4, 4), (tp5, 5)]:
    for variant, dossier, suffixe in [("enonce", "HDD/1 - Enonces", "ENOX"), ("corrige", "HDD/2 - Corriges", "CORX")]:
        nid = f"2HDD{num}{suffixe}"
        zep.check_ids(nid)
        print(*zep.build(mod.P, variant, mod.NAME, nid, dossier))
