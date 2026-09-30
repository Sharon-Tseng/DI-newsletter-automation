# DI Newsletter Automation

Produces the monthly **Data Infra What's New** newsletter (English + 简体中文 HTML) with Claude:
read the product sheet → write copy → generate mascot banners with Grok → lay out the cards.
The Claude skill in `skill/` holds every rule the team has agreed on; `runs/` keeps one folder
per edition so any month can be rebuilt or resumed.

```
CLAUDE.md                 Project memory for Claude Code — read this first in a new session
skill/                    Skill source — edit here
  SKILL.md                4-stage workflow, checkpoints, decisions already made
  references/             copy rules, mascots, banner/Grok workflow, JSON schema, example run
  scripts/                read_sheet.py · check_copy.py · build_newsletter.py · render_preview.py
                          bake_banner_text.py (renders title/tags onto a scene-only banner)
  assets/mascots/         reference images of every mascot
  assets/fonts/           Gloock · Marmelad · Bodoni Moda · Noto Sans (used by bake_banner_text.py)
dist/                     data-infra-newsletter.skill — the packaged skill you upload to Claude
runs/<YYYY-MM>/           One folder per edition
  products_raw.json       Stage 1: normalised rows from the Google Sheet
  products.json           Single source of truth: copy, banners, screenshots, theme, decisions
  images/                 feature screenshots from the sheet (local until uploaded to GitHub)
  banners/                banner specs (spec_*.json) and text-baked banner variants
  raw/                    cards delivered by colleagues as finished HTML (+ their CSS), inserted verbatim
  out/                    newsletter_<month>_en.html · newsletter_<month>_zh.html
  chatgpt_layout_review_<date>.md   layout / team review log
```

Banner images are **not** in this repo. They live in
[`Sharon-Tseng/diana_email_banner`](https://github.com/Sharon-Tseng/diana_email_banner)
under `DI Newsletter/<Month>/`, and `products.json` points at their raw URLs. One file name
per image, forever — never overwrite `X_banner.jpg` with a different picture (see
`skill/references/banner_workflow.md` → "GitHub hygiene").

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

### Before you start (5-minute checklist)

1. Open **Chrome** (the profile where the Claude extension is installed). Leave it open for the whole run —
   Claude opens its own "Claude" tab group inside it.
2. In that Chrome, make sure you are **logged in to https://grok.com/imagine** (banners) and, if you want
   layout reviews, **https://chatgpt.com** (ChatGPT). Claude cannot log in for you and will stop at any
   login page or CAPTCHA.
3. Have the mascot reference images at hand (`skill/assets/mascots/` or your own copies). During the
   banner stage Claude will ask you to upload them in Grok's "+" → Uploads panel; it cannot upload files
   from its own environment.
4. Open **Claude Desktop**, start a **new** conversation, and tick **Claude in Chrome** in the connectors
   menu of that chat (it is off by default in every new chat).
5. Know the month's **theme**, which banners **you** own this month (others come from colleagues), and
   whether any colleague is handing over a **finished card HTML** instead of sheet text.

Then paste:

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
   grouped layout when the sheet lists features under category headings. If a row offers a
   **screenshot** (可提供的截图 column), Claude asks you here whether to use it, reports its
   size/aspect in one line, places it inside the feature by shape (wide landscape → full text-column
   width; squarer → fixed width, centred) and adds a centred EN+ZH caption. Products that are not
   live yet go to the **"NEXT UP / Coming in <month>"** section after Latest Releases. Diana cards
   always end with the three fixed buttons (Open Diana · Diana Community · Give us Feedback).
   Say what to change; say "锁定" when a product is done.
3. **Banners (Grok Imagine, in your Chrome)** — for each banner you own:
   - Claude navigates to grok.com/imagine in its tab group; if Grok shows a login or Cloudflare check,
     finish it yourself and say 好了.
   - When asked, upload the mascot reference (and the hero group shot for the theme) via **"+" → Upload**;
     Claude then selects them from the Uploads panel, writes the prompt (16:9, mascot identity block,
     theme, English text only) and generates.
   - Claude shows a zoomed screenshot; you say OK or what to change; it iterates (text edits work well,
     spacing edits less so — it will redesign the whole text block rather than nudge).
   - Want Chinese text on the ZH banner? Ask Grok for a text-free copy of the approved EN banner, then
     add the Chinese headline and pills in the same style; store it as `banner.image.zh`
     (`<Product>_CN_banner.jpg`). `bake_banner_text.py` is the fallback when Grok keeps garbling a character.
   - Approved: **you** download the image from Grok and upload it to
     `diana_email_banner/DI Newsletter/<Month>/<Product>_banner.jpg`, then paste the GitHub URL back.
     (Claude's environment cannot reach assets.grok.com.)
   - The **hero** is regenerated every edition with all mascots in the month's theme,
     title "Data Infra What's New" + pill "Newsletter <Mon YYYY> Release".
   - Products without a mascot get a text-only HTML banner (no Grok).
4. **Layout** — two HTML files, rendered screenshots for review. Optional: ask Claude to send
   a card to ChatGPT for a layout-only review (text frozen); only CSS suggestions are applied.

At the end Claude gives you `newsletter_<month>_en.html`, `newsletter_<month>_zh.html`,
`products.json` and (if any) `chatgpt_layout_review_<date>.md`.

### Cards delivered by a colleague as HTML

If a teammate hands over a finished card (one `<table class="newsletter-module">` per language),
Claude does not retype it: it saves the module under `runs/<month>/raw/`, their CSS as
`raw/final_cards*.css`, sets `product.raw_module` + `edition.extra_css`, and the builder inserts
it verbatim (their content wins on overlaps; only CJK font stack / stamp text / letter-spacing are
aligned with the template). Text placed on a banner with CSS (`position:absolute`) is dropped by
Gmail and Outlook — Claude offers to bake it into the image with `bake_banner_text.py`; you decide.

## 2. Every month — save the run to this repo

```bash
git pull
mkdir -p runs/<YYYY-MM>/out
# copy the files Claude produced into it:
#   products.json, products_raw.json, images/ (feature screenshots, if any),
#   banners/ and raw/ (if any), out/newsletter_<month>_en.html, out/newsletter_<month>_zh.html,
#   chatgpt_layout_review_<date>.md (if any)
git add runs/<YYYY-MM>
git commit -m "<Mon YYYY> edition"
git push
```

Never commit HTML built with `--embed-images` (base64 screenshots make the file huge) — save
those as `*_embedded.html`, which is git-ignored. Before the **final send**, upload any local
screenshots or banners in `runs/<month>/images/` and `runs/<month>/banners/` to
`diana_email_banner/DI Newsletter/<Month>/`, switch each `src` in `products.json` to the raw URL,
and rebuild without `--embed-images` — the final HTML must contain no local paths.

If Claude changed anything in the skill during the run (it says so — e.g. a new layout rule),
also replace `dist/data-infra-newsletter.skill` and the changed files under `skill/`, then
re-upload the `.skill` to Claude so next month starts from the new rules.

## 3. Partial jobs

Open a new chat with the connector ticked, attach `runs/<month>/products.json`, and say one of:

- `只改 <Product> 的文案` — Stage 2 for that product, then rebuild
- `重生 <Product> 的 banner` — Stage 3 for that product
- `把 <month> 的 HTML 重做` — Stage 4 only (e.g. after a banner URL arrives)
- `Diana 2.8 的 PRD 在附件，照 PRD 寫卡片` — copy from a PRD instead of the sheet
- `同事給了 <Product> 的最終 HTML，直接放進去` — integrate a colleague's card as a raw module

## 4. Rebuild locally without Claude (optional)

```bash
pip install openpyxl playwright pillow opencc-python-reimplemented
python -m playwright install chromium

python skill/scripts/check_copy.py      runs/2026-10          # length + audience rules (captions count)
python skill/scripts/build_newsletter.py runs/2026-10          # → runs/2026-10/out/*.html
python skill/scripts/render_preview.py  runs/2026-10/out/newsletter_2026-10_en.html   # PNG previews
python skill/scripts/bake_banner_text.py runs/2026-10/banners/spec_cli.json          # bake text onto a banner
```

`build_newsletter.py` needs only the standard library (Python 3.9+); the other scripts need the
packages above. `check_copy.py` still counts the JSON copy of raw-module cards, so a colleague's
card can show `[OVER]` without affecting the HTML that ships.

Local screenshot paths are written relative to the HTML, so the default build stays small and
previewable. Add `--embed-images` only to send someone a self-contained preview (base64 —
never commit it). Edit `runs/<month>/products.json` and rebuild — never hand-edit the
generated HTML.

Working in Claude Code? Just say "read CLAUDE.md" — it holds the project memory (decisions,
current edition status, context-size rules like never attaching `dist/*.skill` or embedded HTML).

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
- Exactly two product sections: "LATEST RELEASES / <release month> Product Updates" (live only), then "NEXT UP / Coming in <edition month>" for every non-live product.
- Every card ends with at least one button; Diana cards always carry Open Diana · Diana Community · Give us Feedback.
- Visual components: ✓ checks · timeline steps · flow · before/after; grouped cards = filled category tag + title-only rows, no numerals.
- Feature screenshots from the sheet's 可提供的截图 column: always ask the user first, analyse size/aspect, place by shape inside the feature, centred caption underneath; preview with `--embed-images`, final send uses the GitHub raw URL.
- Colleague-built cards are inserted verbatim as `raw_module`s; banner text should be part of the image (Grok-drawn or baked) because CSS overlays vanish in Gmail/Outlook — the team may still choose the overlay knowingly.
- `banner.image` may be per language (`{"en": …, "zh": …}`) when the text is baked or drawn in each language.
- Per-edition theme via `edition.theme`; ZH has its own CJK type scale.
- "di CLI" (no hyphen) accepted on banners; Grok can't draw the hyphen.
- Hero: mascots always the protagonists, regenerated each edition for the theme.
- GitHub banner repo: one file name per image, never reuse or overwrite.

Current edition status and open items live in `CLAUDE.md` → "October 2026 status".
