# CLAUDE.md — DI Newsletter Automation

Project memory for Claude Code. Read this first; it captures what the team decided in the
Sep 25–30, 2026 build sessions so work continues without re-deriving anything.

## What this repo is

A Claude **skill** (`skill/`) plus per-edition **runs** (`runs/<YYYY-MM>/`) that produce the
monthly *Data Infra What's New* internal newsletter as two table-based HTML emails
(English + 简体中文). Pipeline: Google Sheet → bilingual copy → Grok mascot banners → HTML.
The human (Sharon) is the editor; Claude stops at a checkpoint after every stage.

```
skill/SKILL.md                 workflow, checkpoints, decisions — the entry point
skill/references/
  copy_guidelines.md           copy rules, typography, layouts, screenshots, review loop
  banner_workflow.md           Grok Imagine via Claude in Chrome, hero banner, lessons
  mascots.md                   identity blocks per mascot (never change features, poses may)
  schema.md                    products.json schema
  example_products_2026-10.json  the real October run as a worked example
skill/scripts/
  read_sheet.py                Stage 1: xlsx export → products_raw.json (+ warnings)
  check_copy.py                length/audience/caption checks (target 250/280, hard 300)
  build_newsletter.py          THE TEMPLATE: products.json → out/newsletter_<m>_{en,zh}.html
  render_preview.py            Playwright screenshots for review (--card <id> crops one card)
skill/assets/mascots/          reference images
dist/data-infra-newsletter.skill   packaged skill to upload to Claude (zip, top folder data-infra-newsletter/)
runs/2026-10/                  products.json, products_raw.json, out/, images/, review log
```

Banner/screenshot images are hosted in `Sharon-Tseng/diana_email_banner` (`DI Newsletter/<Month>/`);
`products.json` references their raw URLs. Nothing binary except mascots lives here.

## Architecture decisions (and why)

- **Skill in Claude Desktop, not a self-hosted LangGraph service.** All integrations already
  exist there (Google Drive connector, Claude in Chrome for Grok/ChatGPT, chat = human-in-the-loop).
  The "graph" is the 4 stages + JSON state file; a run can stop after any checkpoint and resume.
- **`products.json` is the single source of truth.** Every change = edit JSON → rebuild.
  Never hand-edit generated HTML.
- **Template is code** (`build_newsletter.py`), copied from the Sept 2026 edition: 840px cards,
  Gloock numerals/EN titles, Marmelad EN body, 01/02/03 features, pill buttons. Palette is per
  edition via `edition.theme` (Oct: low-saturation jungle green `#F2F5EF`, green card outlines).
- **Two independent language editions**, same layout, EN text on banners for both.
- **Grok cannot be called by API** and `assets.grok.com` is blocked from the sandbox: images
  are generated in the user's Chrome, downloaded by the user, uploaded to GitHub, and wired in by URL.

## Rules the team fixed (do not relitigate)

Copy
- Edit the PIC's sheet text; **never invent** nouns, examples, chip labels, or benefits
  (rejected: guessed "SDK / API / MCP" chips, invented prompt examples).
- ≤ 300 EN words / 300 ZH chars per card (hard); target 250/280. One main sentence + one
  background sentence per feature; lists → chips; sequences → steps; benefits → ✓ checks.
- Reader situation goes in a small blue uppercase kicker above the feature title (EN);
  ZH kicker 12/18 w500, no uppercase/tracking.
- ZH = **Simplified with mainland vocabulary** (数据/项目/用户/调用/反馈/示例/设置/检测/渠道/私信/社区版).
- Source can be a **PRD** (Diana 2.8) — same no-invention rule.

Layout
- Section title: "<release_month> Product Updates" (never "Latest").
- With a banner present, card title/subtitle/audience are hidden; a **stamp-style** status badge
  (double outline, tracked caps, −6° tilt) sits inline right of feature 01 / first group header.
- Visual components: `checks` (✓ row), `steps` (timeline: markers on a rail, no boxes),
  `flow`, `before_after`, `bullets_style: chips` (tinted blue, bold, wrap), `bullets_label`.
- **Grouped cards** (`layout: grouped`, feature.group): tinted panel + 4px accent bar per
  category, category as filled tag, title-only rows with ✓ discs, no numerals, no descriptions
  (rejected on the way: header bands+hairlines, count badges, bordered mini-cards, numeral|title|desc rows).
- ZH type scale is separate (one CJK sans stack; titles 24/34 w600; body 15/26; letter-spacing 0;
  Latin tokens wrapped `white-space:nowrap`). Only numerals keep Gloock.
- **Screenshots** from the sheet's 可提供的截图 column: ask the user → analyse size/aspect →
  place by shape (landscape ≥1.6 full text-column width; else fixed width, centred) →
  **centred caption** underneath. Preview with `--embed-images`; final = GitHub URL.
- All blocks (hero, section headers, cards, closing) share `0 14px` outer padding + 840px `.shell`.

Banners
- Mascots' identity features never change; poses/props/scene do. Octopus stays flat cartoon in
  product banners; the 3D group shot is only for the hero the team supplied.
- Approved text treatment: hand-lettered cream headline (#F6F1E4) with soft dark-green shadow,
  frosted semi-transparent pills with forest-green text, **all** features as pills.
- Hero every edition: all mascots as protagonists in the theme, title "Data Infra What's New" +
  pill "Newsletter <Mon YYYY> Release".
- 16:9 (widest Grok offers). Grok won't draw the hyphen in "di-cli" → "di CLI" accepted.
- Products without a mascot (RAM) → text-only HTML banner.

Review loop
- ChatGPT layout reviews are welcome; only CSS/structure suggestions are applied, text frozen,
  September reference values (numerals 29/32, EN titles 23/29) not overridden. Log each round in
  `runs/<m>/chatgpt_layout_review_<date>.md`.

## October 2026 status (as of 2026-09-30)

Done
- Theme: jungle. Hero banner live (GitHub `October/Hero Banner.jpg`).
- Langfuse card: 4 features, ✓ row, timeline steps, chips with "Improvements include:",
  MCP & CLI screenshot with centred caption; banner live (GitHub `October/CLI_banner.jpg` — **misnamed**, it is the Langfuse banner; ask Sharon to rename → then update URL).
- DataHub Agent card: copy done; banner from a colleague — placeholder until URL arrives.
- RAM card: grouped title-only layout; text-only banner.
- Diana 2.8: skipped, waiting for PRD.
- Both HTML editions build cleanly; ZH Langfuse is at 299/300 chars (at the limit).

Pending / next steps
1. Receive DataHub Agent banner URL → set `products[datahub_agent].banner.image` → rebuild.
2. Receive Diana 2.8 PRD → write EN/ZH copy from it (`skip=false`, `source_rows` = PRD sections) → rebuild.
3. Upload `runs/2026-10/images/langfuse_mcp_cli_page.jpg` to `diana_email_banner/October/`,
   switch `image.src` to the raw URL, rebuild for the final send (HTML then has no local paths).
4. Rename `CLI_banner.jpg` → `Langfuse_banner.jpg` on GitHub and update the URL.
5. Final review of both HTML files in a real mail client (Outlook + Gmail), then send.
6. Commit `runs/2026-10/` and, if anything under `skill/` changed, re-package `dist/` and
   re-upload the `.skill` to Claude.

## Context-size hygiene (learned the hard way, 2026-09-30)

- Do **not** attach or `@`-read `dist/*.skill`, zip files, `skill/assets/mascots/*`, or any
  HTML built with `--embed-images` — a single base64 screenshot is ~250k tokens and the first
  Claude Code session died with "prompt is too long (~7.5M tokens)".
- Default build writes small HTML (~30 KB) that references `../images/<file>` relatively; that
  is what gets committed. `--embed-images` is only for sending a self-contained preview to
  someone; save it as `*_embedded.html` (git-ignored).
- To brief a new session: "read CLAUDE.md" is enough. If you must share a run, attach
  `runs/<m>/products.json` (≈15 KB), not the HTML.

## How to work in this repo (Claude Code)

- Rebuild: `python skill/scripts/check_copy.py runs/2026-10 && python skill/scripts/build_newsletter.py runs/2026-10 [--embed-images]`
- Preview: `python skill/scripts/render_preview.py runs/2026-10/out/newsletter_2026-10_en.html [--card langfuse]`
  (needs `pip install playwright pillow openpyxl opencc-python-reimplemented && python -m playwright install chromium`).
- Package skill after editing `skill/`: `cp -r skill data-infra-newsletter && zip -r dist/data-infra-newsletter.skill data-infra-newsletter -x '*.DS_Store' && rm -rf data-infra-newsletter`.
- When adding a layout feature: add the renderer in `build_newsletter.py`, document it in
  `references/copy_guidelines.md` + `schema.md`, mention it in `SKILL.md`, and refresh
  `references/example_products_2026-10.json` from `runs/2026-10/products.json`.
- Verify alignment at 1300 / 900 / 700px with Playwright before committing template changes.
- Keep the 300-word/char rule, the no-invention rule, and the ZH type scale — they are the
  three things the team pushed back on hardest.

## People / sources

- Sheet: `Data Infra What's New 🔥` (fileId `1JaxsrNxMsbPelxACyRnGZrBMVcjo1HffBWhsvWBFyis`), tab `<N>月newsletter` (edition made at end of month M uses tab M+1).
- PICs named in the sheet: Langfuse — Teng Ma / Jiayin Cai; DataHub Agent — Nguyen Minh Phi; RAM — Fu Kai Sheng / Zhang Qingyu; Diana — Shi Raven.
- Banner repo: `Sharon-Tseng/diana_email_banner`. Code repo: `Sharon-Tseng/DI-newsletter-automation`.
