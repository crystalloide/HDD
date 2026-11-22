# -*- coding: utf-8 -*-
"""Petit générateur de notebooks Zeppelin 0.12 (.zpln) : énoncé + corrigé à partir d'une seule source.

Le code Java, Pig, HiveQL et Python des corrigés est lu dans tp/ : modifier une
source de tp/, puis relancer  python3 tools/notebooks/generer.py  pour mettre à
jour les notebooks des deux versions.
"""
import hashlib
import json
import os
import re

import markdown

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DATE = "2026-11-23 09:00:00.000"

EDITOR = {
    "md": ("markdown", "ace/mode/markdown"),
    "sh": ("sh", "ace/mode/sh"),
    "hive": ("sql", "ace/mode/sql"),
    "impala": ("sql", "ace/mode/sql"),
    "spark.sql": ("sql", "ace/mode/sql"),
    "spark.pyspark": ("python", "ace/mode/python"),
    "python": ("python", "ace/mode/python"),
    "hbase": ("text", "ace/mode/text"),
    "java": ("java", "ace/mode/java"),
    "file": ("text", "ace/mode/text"),
}


class P:
    """Paragraphe. text = version corrigé ; enonce = version énoncé (None : identique).
    only = 'enonce' | 'corrige' | None. graph = réglages de graphique (dict) ou None."""

    def __init__(self, interp, text, title=None, enonce=None, only=None, graph=None, hide_editor=None):
        self.interp = interp
        self.text = text.strip("\n")
        self.title = title
        self.enonce = enonce.strip("\n") if enonce is not None else None
        self.only = only
        self.graph = graph
        self.hide_editor = hide_editor


def md(text, title=None, enonce=None, only=None):
    return P("md", text, title=title, enonce=enonce, only=only)


def code(interp, text, title=None, enonce=None, only=None, graph=None):
    return P(interp, text, title=title, enonce=enonce, only=only, graph=graph)


def source(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as f:
        return f.read().rstrip("\n")


def heredoc(path, content, after=""):
    """Paragraphe %sh qui écrit un fichier (code Java, script Pig...)."""
    d = os.path.dirname(path)
    txt = f"mkdir -p {d}\ncat > {path} <<'EOF'\n{content}\nEOF\necho \"écrit : {path}\""
    if after:
        txt += "\n" + after
    return txt


def bar_chart(keys, values, groups=None, mode="multiBarChart"):
    def cols(names, start=0):
        return [{"name": n, "index": i, "aggr": "sum"} for i, n in names]
    return {"mode": mode, "keys": cols(keys), "values": cols(values), "groups": cols(groups or [])}


def _md_html(text):
    html = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    return '<div class="markdown-body">\n' + html + "\n</div>"


def _pid(note_id, i):
    h = int(hashlib.md5(f"{note_id}-{i}".encode()).hexdigest()[:8], 16)
    return f"20261123-0900{i:02d}_{h % 1000000000:09d}", f"paragraph_17958240{i:05d}_{h % 1000000000}"


def _paragraph(p, text, note_id, i):
    interp_line = "%" + p.interp
    full = interp_line + "\n" + text
    lang, mode = EDITOR[p.interp]
    is_md = p.interp == "md"
    pid, job = _pid(note_id, i)
    cfg = {
        "tableHide": False,
        "editorSetting": {"language": lang, "editOnDblClick": is_md, "completionKey": "TAB",
                          "completionSupport": not is_md},
        "colWidth": 12.0,
        "editorMode": mode,
        "fontSize": 9.0,
        "editorHide": is_md if p.hide_editor is None else p.hide_editor,
        "title": bool(p.title),
        "results": {},
        "enabled": True,
    }
    if p.graph:
        g = dict(p.graph)
        cfg["results"] = {"0": {"graph": {
            "mode": g["mode"], "height": 320.0, "optionOpen": False,
            "setting": {g["mode"]: {"rotate": {"degree": "-45"}, "xLabelStatus": "default"}},
            "commonSetting": {}, "keys": g["keys"], "groups": g["groups"], "values": g["values"]},
            "helium": {}}}
    para = {
        "title": p.title or "",
        "text": full,
        "user": "anonymous",
        "dateUpdated": DATE,
        "progress": 0,
        "config": cfg,
        "settings": {"params": {}, "forms": {}},
        "apps": [],
        "runtimeInfos": {},
        "progressUpdateIntervalMs": 500,
        "jobName": job,
        "id": pid,
        "dateCreated": DATE,
        "status": "READY",
    }
    if is_md:
        para["status"] = "FINISHED"
        para["results"] = {"code": "SUCCESS", "msg": [{"type": "HTML", "data": _md_html(text)}]}
        para["dateStarted"] = DATE
        para["dateFinished"] = DATE
    return para


def build(paragraphs, variant, name, note_id, folder):
    """variant : 'enonce' ou 'corrige'. Écrit zeppelin/notebook/<folder>/<name>_<id>.zpln"""
    paras = []
    i = 0
    for p in paragraphs:
        if p.only and p.only != variant:
            continue
        text = p.enonce if (variant == "enonce" and p.enonce is not None) else p.text
        i += 1
        paras.append(_paragraph(p, text, note_id, i))
    # paragraphe vide final (comme Zeppelin)
    nb = {
        "paragraphs": paras,
        "name": name,
        "id": note_id,
        "defaultInterpreterGroup": "spark",
        "version": "0.12.1",
        "noteParams": {},
        "noteForms": {},
        "angularObjects": {},
        "config": {"isZeppelinNotebookCronEnable": False, "looknfeel": "default", "personalizedMode": "false"},
        "info": {},
        "path": "/" + folder + "/" + name,
    }
    out_dir = os.path.join(REPO, "zeppelin", "notebook", folder)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{name}_{note_id}.zpln")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=2)
    return path, len(paras)


def check_ids(note_id):
    assert re.fullmatch(r"2[A-Z0-9]{8}", note_id), note_id
