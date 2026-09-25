# Data Infra Newsletter — skill + monthly runs

Everything needed to produce the monthly *Data Infra What's New* newsletter with Claude.

```
skill/            Source of the Claude skill (SKILL.md, references/, scripts/, assets/mascots/)
dist/             Packaged skill (.skill) — upload this to Claude to install/update
runs/<YYYY-MM>/   One folder per edition
  products.json   Single source of truth: copy (EN + 简体), banners, theme, decisions
  products_raw.json   Stage-1 extraction from the Google Sheet
  out/            Generated newsletter_<month>_en.html / _zh.html
  chatgpt_layout_review_<date>.md   Layout review log (ChatGPT rounds + team decisions)
```

## Monthly workflow (summary)
1. Stage 1 — read the `<N>月newsletter` tab of the "Data Infra What's New 🔥" sheet → `products_raw.json`
2. Stage 2 — write EN + 简体 copy per product (edit the PIC's text, never invent) → `products.json`
3. Stage 3 — banners with Grok Imagine via Claude in Chrome (mascots as protagonists, edition theme); approved images go to the `diana_email_banner` repo and their raw URLs into `products.json`
4. Stage 4 — `python skill/scripts/build_newsletter.py runs/<month>` → HTML; `render_preview.py` for review

Full rules live in `skill/SKILL.md` and `skill/references/`.

## Rebuild an edition locally
```
pip install openpyxl playwright pillow opencc-python-reimplemented
python -m playwright install chromium
python skill/scripts/check_copy.py runs/2026-10
python skill/scripts/build_newsletter.py runs/2026-10
python skill/scripts/render_preview.py runs/2026-10/out/newsletter_2026-10_en.html
```

Banner images are hosted in `Sharon-Tseng/diana_email_banner` (DI Newsletter/<Month>/).
