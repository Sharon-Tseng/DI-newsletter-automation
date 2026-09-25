#!/usr/bin/env python3
"""Check every product's copy against the length rule and report problems.

Rule: per product, per language, everything a reader sees inside the card body —
title, subtitle, audience line, feature names, descriptions, bullets and examples —
must fit in 300 English words (en) or 300 CJK/word characters (zh). Button labels
are excluded. Also flags features with no description, and audience lines that are
just "All <product> users" (those should be dropped, not shown).

Usage: python check_copy.py <run_dir>   (exit code 1 if any product fails)
"""
import json
import os
import re
import sys

LIMIT = {"en": 300, "zh": 300}          # hard ceiling
TARGET = {"en": 250, "zh": 280}         # comfortable target; 300 is the hard limit
FEATURE_MAX = {"en": 45, "zh": 65}      # per-feature desc: one main sentence + one background sentence


def texts(copy):
    parts = [copy.get("title", ""), copy.get("subtitle", ""), copy.get("audience") or ""]
    parts += sorted({f.get("group", "") for f in copy.get("features", []) if f.get("group")})
    for f in copy.get("features", []):
        parts += [f.get("name", ""), f.get("tag", ""), f.get("desc", ""), f.get("example", "")]
        parts += f.get("bullets", []) or []
        v = f.get("visual") or {}
        for side in ("before", "after"):
            parts.append((v.get(side) or {}).get("caption", ""))
        parts += v.get("items", []) or []
        for st in v.get("steps", []) or []:
            parts += [st.get("label", ""), st.get("caption", "")]
        parts += [v.get("note", ""), v.get("footnote", "")]
    return [p for p in parts if p]


def count(lang, s):
    if lang == "en":
        return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’\-/.:~%]*", s))
    # zh: count CJK characters + latin words as one unit each, ignore punctuation/space
    cjk = re.findall(r"[\u4e00-\u9fff\u3400-\u4dbf]", s)
    latin = re.findall(r"[A-Za-z0-9][A-Za-z0-9'’\-/.:~%]*", s)
    return len(cjk) + len(latin)


def main(run_dir):
    with open(os.path.join(run_dir, "products.json"), encoding="utf-8") as f:
        data = json.load(f)
    failed = False
    generic = re.compile(r"^\s*(all|所有|全體|全部)\b", re.I)
    for p in data["products"]:
        if p.get("skip"):
            continue
        for lang in ("en", "zh"):
            copy = p.get("copy", {}).get(lang)
            if not copy:
                print(f"[MISSING] {p['id']} has no {lang} copy")
                failed = True
                continue
            n = sum(count(lang, s) for s in texts(copy))
            unit = "words" if lang == "en" else "chars"
            flag = "OK  " if n <= TARGET[lang] else ("LONG" if n <= LIMIT[lang] else "OVER")
            if n > LIMIT[lang]:
                failed = True
            print(f"[{flag}] {p['id']:<16} {lang}  {n:>3} {unit}  (target {TARGET[lang]}, max {LIMIT[lang]})")
            for f in copy.get("features", []):
                dn = count(lang, f.get("desc", ""))
                if dn > FEATURE_MAX[lang]:
                    print(f"        · feature '{f.get('name')}' desc is {dn} {unit} (>{FEATURE_MAX[lang]}) — cut to one sentence or move detail to bullets")
                if not f.get("desc") and not f.get("bullets"):
                    print(f"        · feature '{f.get('name')}' has no desc/bullets")
            aud = copy.get("audience")
            if aud and generic.match(aud):
                print(f"        · audience '{aud}' looks generic — drop it (rule: only show non-default audiences)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
