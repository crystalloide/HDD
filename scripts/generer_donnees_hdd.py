#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère les jeux de données des hand-labs HDD (données fictives, reproductibles).

    python3 scripts/generer_donnees_hdd.py            # écrit dans data/hdd/

Sorties :
  data/hdd/clients/crm_2026-11.csv        export du CRM (avec doublons exacts)
  data/hdd/clients/web_2026-11.csv        inscriptions du site web
  data/hdd/clients/magasins_2026-11.csv   cartes de fidélité des magasins
  data/hdd/catalogue/produits.csv         catalogue initial (TP HBase)
  data/hdd/catalogue/modifications.csv    changements de prix datés (3 vagues)
  data/hdd/catalogue/promos.csv           promotions (colonne info:promo)
  data/hdd/attendus.json                  valeurs attendues (contrôles des TP)

Format des fichiers clients (séparateur « ; », 1re ligne = en-tête) :
  id;nom;ville;ca;segment;canal;date_inscription
Un même client (même id) peut apparaître dans plusieurs canaux, avec le CA
réalisé dans ce canal. Anomalies volontaires : en-têtes, villes mal saisies
(casse, espaces, accents), villes absentes, lignes mal formées, CA invalides,
doublons exacts dans l'export CRM.
"""
import json
import os
import random
import sys
import unicodedata
from datetime import date, timedelta

SEED = 2026
RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "hdd")

VILLES = [  # (nom officiel, poids)
    ("Paris", 22), ("Lyon", 12), ("Marseille", 10), ("Toulouse", 8), ("Nice", 6),
    ("Nantes", 6), ("Strasbourg", 5), ("Montpellier", 5), ("Bordeaux", 6), ("Lille", 6),
    ("Rennes", 4), ("Reims", 3), ("Saint-Étienne", 3), ("Le Havre", 2), ("Toulon", 2),
    ("Grenoble", 3), ("Dijon", 2), ("Angers", 2), ("Nîmes", 2), ("Clermont-Ferrand", 2),
    ("Orléans", 2), ("Besançon", 1), ("Évry-Courcouronnes", 1), ("Aix-en-Provence", 2),
]
PRENOMS = ("Marie Jean Pierre Sophie Camille Lucas Léa Hugo Chloé Louis Emma Nathan Manon Thomas "
           "Julie Nicolas Sarah Antoine Laura Julien Clara Maxime Inès Paul Alice Arthur Zoé Gabriel "
           "Lucie Théo Anaïs Romain Céline Baptiste Elodie Mathieu Pauline Quentin Margaux Victor").split()
NOMS = ("Martin Bernard Dubois Thomas Robert Richard Petit Durand Leroy Moreau Simon Laurent Lefebvre "
        "Michel Garcia David Bertrand Roux Vincent Fournier Morel Girard André Lefèvre Mercier Dupont "
        "Lambert Bonnet François Martinez Legrand Garnier Faure Rousseau Blanc Guérin Muller Henry "
        "Roussel Nicolas Perrin Morin Mathieu Clément Gauthier Dumont Lopez Fontaine Chevalier Robin").split()
SEGMENTS = [("particulier", 70), ("professionnel", 22), ("entreprise", 8)]
ENTETE = "id;nom;ville;ca;segment;canal;date_inscription"


def sans_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def normalise_ville(s):
    """Même règle que la UDF Pig NormaliseVille et le mapper de collecte."""
    return " ".join(sans_accents(s).strip().upper().split())


def choix_pondere(rng, couples):
    total = sum(p for _, p in couples)
    r = rng.uniform(0, total)
    for valeur, poids in couples:
        r -= poids
        if r <= 0:
            return valeur
    return couples[-1][0]


def variante_ville(rng, ville):
    """Saisie « humaine » d'une ville : casse, espaces, accents perdus."""
    choix = rng.random()
    if choix < 0.30:
        return ville.upper()
    if choix < 0.55:
        return ville.lower()
    if choix < 0.80:
        return "  " + ville + " "
    return sans_accents(ville) if sans_accents(ville) != ville else ville.upper()


def generer_clients(rng, nb_clients=30000):
    clients = []
    debut = date(2018, 1, 1)
    for i in range(1, nb_clients + 1):
        segment = choix_pondere(rng, SEGMENTS)
        clients.append({
            "id": f"C{i:06d}",
            "nom": f"{rng.choice(PRENOMS)} {rng.choice(NOMS)}",
            "ville": choix_pondere(rng, VILLES),
            "segment": segment,
            "date": debut + timedelta(days=rng.randrange(0, 365 * 8 + 300)),
        })
    return clients


def ca_canal(rng, segment, canal):
    base = {"particulier": 380.0, "professionnel": 2400.0, "entreprise": 9800.0}[segment]
    coef = {"crm": 1.0, "web": 0.55, "magasin": 0.75}[canal]
    return round(max(5.0, rng.lognormvariate(0, 0.65) * base * coef), 2)


def ligne(c, canal, ca, ville=None):
    return ";".join([c["id"], c["nom"], ville if ville is not None else c["ville"],
                     f"{ca:.2f}", c["segment"], canal, c["date"].isoformat()])


def ecrire_source(rng, clients, canal, proportion, nom_fichier, stats, doublons_exacts=0.0):
    lignes, valides = [ENTETE], []
    for c in clients:
        if rng.random() >= proportion:
            continue
        ca = ca_canal(rng, c["segment"], canal)
        r = rng.random()
        if r < 0.004:                       # ligne mal formée (mauvais séparateur)
            lignes.append(ligne(c, canal, ca).replace(";", ","))
            stats["rejets"]["FORMAT"] += 1
            continue
        if r < 0.007:                       # champ manquant
            lignes.append(";".join(ligne(c, canal, ca).split(";")[:6]))
            stats["rejets"]["FORMAT"] += 1
            continue
        if r < 0.015:                       # ville absente
            lignes.append(ligne(c, canal, ca, ville=""))
            stats["rejets"]["VILLE_ABSENTE"] += 1
            continue
        if r < 0.019:                       # CA illisible
            l = ligne(c, canal, ca).split(";")
            l[3] = rng.choice(["N/A", "-15.00", "12,50", ""])
            lignes.append(";".join(l))
            stats["rejets"]["CA_INVALIDE"] += 1
            continue
        ville = variante_ville(rng, c["ville"]) if rng.random() < 0.06 else c["ville"]
        l = ligne(c, canal, ca, ville=ville)
        lignes.append(l)
        valides.append((c, canal, ca))
        if rng.random() < doublons_exacts:  # même ligne exportée deux fois
            lignes.append(l)
            valides.append((c, canal, ca))
            stats["doublons_exacts"] += 1
    chemin = os.path.join(RACINE, "clients", nom_fichier)
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lignes) + "\n")
    stats["lignes_fichiers"][nom_fichier] = len(lignes)
    return valides


def generer_catalogue(rng):
    familles = {
        "saisie": ["Clavier", "Souris", "Pavé numérique", "Clavier sans fil", "Souris ergonomique"],
        "affichage": ["Écran 24 pouces", "Écran 27 pouces", "Écran incurvé 34 pouces", "Support d'écran"],
        "stockage": ["Disque SSD 1 To", "Disque SSD 2 To", "Disque dur 4 To", "Clé USB 128 Go"],
        "reseau": ["Routeur Wi-Fi 6", "Switch 8 ports", "Câble RJ45 5 m", "Répéteur Wi-Fi"],
        "audio": ["Casque audio", "Micro USB", "Enceinte Bluetooth", "Casque sans fil"],
        "impression": ["Imprimante laser", "Cartouche noire", "Ramette A4", "Scanner à plat"],
    }
    prix_base = {"saisie": 35, "affichage": 220, "stockage": 110, "reseau": 70, "audio": 85, "impression": 140}
    entrepots = ["Lyon", "Paris-Nord", "Marseille", "Lille"]
    produits = [{"id": "P0001", "libelle": "Clavier", "categorie": "saisie", "prix": 29.90,
                 "quantite": 120, "entrepot": "Lyon"}]
    cats = list(familles)
    for i in range(2, 121):
        cat = cats[(i - 2) % len(cats)]
        lib = familles[cat][(i // len(cats)) % len(familles[cat])]
        prix = round(prix_base[cat] * rng.uniform(0.5, 1.8), 1) - 0.1
        produits.append({"id": f"P{i:04d}", "libelle": lib, "categorie": cat, "prix": round(prix, 2),
                         "quantite": rng.randrange(0, 400), "entrepot": rng.choice(entrepots)})
    os.makedirs(os.path.join(RACINE, "catalogue"), exist_ok=True)
    with open(os.path.join(RACINE, "catalogue", "produits.csv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("id;libelle;categorie;prix;quantite;entrepot\n")
        for p in produits:
            f.write(f"{p['id']};{p['libelle']};{p['categorie']};{p['prix']:.2f};{p['quantite']};{p['entrepot']}\n")

    # Trois vagues de changements de prix (date d'effet = horodatage HBase).
    # P0001 : 29.90 -> 28.90 -> 27.90 (exactement 3 versions).
    # P0007 : modifié aux 3 vagues -> 4 valeurs, seules les 3 plus récentes restent lisibles.
    vagues = ["2026-04-01", "2026-07-01", "2026-10-01"]
    modifs = [("P0001", "info", "prix", "28.90", vagues[0]), ("P0001", "info", "prix", "27.90", vagues[1])]
    courant = {p["id"]: p["prix"] for p in produits}
    courant["P0001"] = 27.90
    for v_idx, jour in enumerate(vagues):
        cibles = {"P0007"} | set(rng.sample([p["id"] for p in produits[2:]], 14))
        for pid in sorted(cibles):
            nouveau = round(courant[pid] * rng.uniform(0.85, 1.12), 1) - 0.1
            courant[pid] = round(nouveau, 2)
            modifs.append((pid, "info", "prix", f"{courant[pid]:.2f}", jour))
        # quelques mouvements de stock à la même date
        for pid in sorted(rng.sample([p["id"] for p in produits], 6)):
            modifs.append((pid, "stock", "quantite", str(rng.randrange(0, 400)), jour))
    modifs.sort(key=lambda m: (m[4], m[0], m[2]))
    with open(os.path.join(RACINE, "catalogue", "modifications.csv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("id;famille;colonne;valeur;date_effet\n")
        for m in modifs:
            f.write(";".join(m) + "\n")

    promos = sorted(rng.sample([p["id"] for p in produits if p["id"] != "P0001"], 15))
    with open(os.path.join(RACINE, "catalogue", "promos.csv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("id;promo\n")
        for pid in promos:
            f.write(f"{pid};-{rng.choice([10, 15, 20, 25, 30])}%\n")

    versions_p0007 = [m[3] for m in modifs if m[0] == "P0007" and m[2] == "prix"]
    return {"nb_produits": len(produits), "nb_modifications": len(modifs), "nb_promos": len(promos),
            "prix_courant_P0001": "27.90", "prix_courant_P0007": versions_p0007[-1],
            "prix_actuels": {k: f"{v:.2f}" for k, v in courant.items()}}


def main():
    rng = random.Random(SEED)
    os.makedirs(os.path.join(RACINE, "clients"), exist_ok=True)
    clients = generer_clients(rng)
    stats = {"rejets": {"FORMAT": 0, "VILLE_ABSENTE": 0, "CA_INVALIDE": 0},
             "doublons_exacts": 0, "lignes_fichiers": {}}
    valides = []
    valides += ecrire_source(rng, clients, "crm", 0.62, "crm_2026-11.csv", stats, doublons_exacts=0.004)
    valides += ecrire_source(rng, clients, "web", 0.33, "web_2026-11.csv", stats)
    valides += ecrire_source(rng, clients, "magasin", 0.26, "magasins_2026-11.csv", stats)

    # Valeurs attendues après collecte (lignes valides, doublons exacts compris)
    par_ville = {}
    for c, _, _ in valides:
        v = normalise_ville(c["ville"])
        par_ville[v] = par_ville.get(v, 0) + 1
    # Référentiel : 1 ligne par client (doublons exacts retirés, CA sommé sur les canaux)
    uniques = {}
    vus = set()
    for c, canal, ca in valides:
        cle = (c["id"], canal, ca)
        if cle in vus:
            continue
        vus.add(cle)
        u = uniques.setdefault(c["id"], {"ville": normalise_ville(c["ville"]), "ca": 0.0, "canaux": set()})
        u["ca"] += ca
        u["canaux"].add(canal)
    ref_ville = {}
    for u in uniques.values():
        r = ref_ville.setdefault(u["ville"], {"nb_clients": 0, "ca_total": 0.0})
        r["nb_clients"] += 1
        r["ca_total"] += u["ca"]
    attendus = {
        "lignes_par_fichier": stats["lignes_fichiers"],
        "entetes": 3,
        "rejets_par_motif": stats["rejets"],
        "lignes_valides_collecte": len(valides),
        "doublons_exacts_crm": stats["doublons_exacts"],
        "clients_par_ville_collecte": dict(sorted(par_ville.items())),
        "referentiel": {
            "nb_clients": len(uniques),
            "multi_canaux": sum(1 for u in uniques.values() if len(u["canaux"]) > 1),
            "ca_total": round(sum(u["ca"] for u in uniques.values()), 2),
            "par_ville": {k: {"nb_clients": v["nb_clients"], "ca_total": round(v["ca_total"], 2)}
                          for k, v in sorted(ref_ville.items())},
        },
        "catalogue": generer_catalogue(rng),
    }
    with open(os.path.join(RACINE, "attendus.json"), "w", encoding="utf-8") as f:
        json.dump(attendus, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: attendus[k] for k in ("lignes_par_fichier", "rejets_par_motif",
                                                 "lignes_valides_collecte", "doublons_exacts_crm")},
                     ensure_ascii=False, indent=2))
    print("référentiel :", attendus["referentiel"]["nb_clients"], "clients,",
          attendus["referentiel"]["multi_canaux"], "multi-canaux")
    return 0


if __name__ == "__main__":
    sys.exit(main())
