# DI Newsletter Automation

Produces the monthly **Data Infra What's New** newsletter (English + 简体中文 HTML) with Claude:
read the product sheet → write copy → generate mascot banners with Grok → lay out the cards.
The Claude skill in `skill/` holds every rule the team has agreed on; `runs/` keeps one folder
per edition so any month can be rebuilt or resumed.

```
skill/                    Skill source — edit here
  SKILL.md                4-stage workflow, checkpoints, decisions already made
  references/             copy rules, mascots, banner/Grok workflow, JSON schema, example run
  scripts/                read_sheet.py · check_copy.py · build_newsletter.py · render_preview.py
  assets/mascots/         reference images of every mascot
dist/                     data-infra-newsletter.skill — the packaged skill you upload to Claude
runs/<YYYY-MM>/           One folder per edition
  products_raw.json       Stage 1: normalised rows from the Google Sheet
  products.json           Single source of truth: copy, banners, theme, decisions
  out/                    newsletter_<month>_en.html · newsletter_<month>_zh.html
  chatgpt_layout_review_<date>.md   layout review log
```

Banner images are **not** in this repo. They live in
[`Sharon-Tseng/diana_email_banner`](https://github.com/Sharon-Tseng/diana_email_banner)
under `DI Newsletter/<Month>/`, and `products.json` points at their raw URLs.

---

## 0. One-time setup

| What | Why |
|---|---|
| Claude **Desktop** app (not the web) | needed for Claude to drive Chrome |
| **Claude in Chrome** extension, signed in with the same account, and the connector switched on in Settings → Connectors | Grok Imagine and ChatGPT review run in your browser |
| **Google Drive** connector | reads the "Data Infra What's New 🔥" sheet |
| Logged in to **grok.com** and **chatgpt.com** in that Chrome profile | Claude never handles your credentials |
| Upload `dist/data-infra-newsletter.skill` to Claude (Settings → Skills) | installs / updates the skill |

Sheet: `https://docs.google.com/spreadsheets/d/1JaxsrNxMsbPelxACyRnGZrBMVcjo1HffBWhsvWBFyis` — one tab per edition,
named `<N>月newsletter`. The edition made at the end of month M uses the **M+1** tab.

## 1. Every month — run it in Claude

Start a **new** conversation in Claude Desktop with the Claude in Chrome connector ticked for that chat, then:

```
用 data-infra-newsletter skill 做 <N> 月的 newsletter。
讀「<N>月newsletter」tab。這期主題是：<一句話，例如 叢林探險 / 太空 / 春節>。
這期我負責的 banner：<產品清單，例如 Langfuse、hero>；其他 banner 由同事提供。
```

Attach `runs/<previous-month>/products.json` if you want the previous edition as a reference.

Claude then walks through four checkpoints; you answer each one before it continues:

1. **Extract** — a table of products found in the tab, plus warnings (empty rows, truncated
   cells, missing entry URLs, products with no mascot, version-only rows like "Diana 2.8").
   Decide: drop / chase the PIC / wait for a PRD.
2. **Copy** — EN and 简体 copy per product, shown side by side. It edits the PIC's text, never
   invents; ≤ 300 words/chars; one main sentence + one background sentence per feature;
   grouped layout when the sheet lists features under category headings. Say what to change;
   say "锁定" when a product is done.
3. **Banners** — for each banner you own: upload the mascot reference(s) in Grok Imagine when
   asked, Claude writes the prompt, generates, shows a zoom, you give a verdict, it iterates.
   Approved image → you download → upload to `diana_email_banner/DI Newsletter/<Month>/<Product>_banner.jpg`
   → paste the GitHub URL back. The **hero** is regenerated every edition with all mascots
   in the month's theme, title "Data Infra What's New" + pill "Newsletter <Mon YYYY> Release".
4. **Layout** — two HTML files, rendered screenshots for review. Optional: ask Claude to send
   a card to ChatGPT for a layout-only review (text frozen); only CSS suggestions are applied.

At the end Claude gives you `newsletter_<month>_en.html`, `newsletter_<month>_zh.html`,
`products.json` and (if any) `chatgpt_layout_review_<date>.md`.

## 2. Every month — save the run to this repo

```bash
git pull
mkdir -p runs/<YYYY-MM>/out
# copy the files Claude produced into it:
#   products.json, products_raw.json, out/newsletter_<month>_en.html, out/newsletter_<month>_zh.html,
#   chatgpt_layout_review_<date>.md (if any)
git add runs/<YYYY-MM>
git commit -m "<Mon YYYY> edition"
git push
```

If Claude changed anything in the skill during the run (it says so — e.g. a new layout rule),
also replace `dist/data-infra-newsletter.skill` and the changed files under `skill/`, then
re-upload the `.skill` to Claude so next month starts from the new rules.

## 3. Partial jobs

Open a new chat with the connector ticked, attach `runs/<month>/products.json`, and say one of:

- `只改 <Product> 的文案` — Stage 2 for that product, then rebuild
- `重生 <Product> 的 banner` — Stage 3 for that product
- `把 <month> 的 HTML 重做` — Stage 4 only (e.g. after a banner URL arrives)
- `Diana 2.8 的 PRD 在附件，照 PRD 寫卡片` — copy from a PRD instead of the sheet

## 4. Rebuild locally without Claude (optional)

```bash
pip install openpyxl playwright pillow opencc-python-reimplemented
python -m playwright install chromium

python skill/scripts/check_copy.py      runs/2026-10          # length + audience rules
python skill/scripts/build_newsletter.py runs/2026-10          # → runs/2026-10/out/*.html
python skill/scripts/render_preview.py  runs/2026-10/out/newsletter_2026-10_en.html   # PNG previews
```

Edit `runs/<month>/products.json` and rebuild — never hand-edit the generated HTML.

## 5. Updating the skill

1. Edit files under `skill/` (rules in `references/*.md`, template in `scripts/build_newsletter.py`).
2. Re-package: the `.skill` is a zip whose top-level folder is `data-infra-newsletter/`:
   ```bash
   rm -f dist/data-infra-newsletter.skill
   cp -r skill data-infra-newsletter && zip -r dist/data-infra-newsletter.skill data-infra-newsletter -x '*.DS_Store' && rm -rf data-infra-newsletter
   ```
3. Upload `dist/data-infra-newsletter.skill` to Claude (it replaces the old version).
4. Commit `skill/` and `dist/` together so the repo and Claude stay in sync.

## Decisions baked into the skill (Oct 2026)

- Copy: edit the PIC's words, never add nouns/examples/benefits they didn't write; ≤ 300 EN words / 300 ZH chars; 简体 with mainland vocabulary.
- Reader situation as a small blue kicker above each feature; all features on a banner as pills.
- Card title/subtitle hidden when a banner exists; stamp-style status badge sits inline with feature 01.
- Section title is "<release month> Product Updates".
- Visual components: ✓ checks · timeline steps · flow · before/after; grouped cards = filled category tag + title-only rows, no numerals.
- Per-edition theme via `edition.theme`; ZH has its own CJK type scale.
- "di CLI" (no hyphen) accepted on banners; Grok can't draw the hyphen.
- Hero: mascots always the protagonists, regenerated each edition for the theme.
