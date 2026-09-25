---
name: data-infra-newsletter
description: "Produce the monthly Data Infra What's New newsletter end to end: read the month's tab of the 'Data Infra What's New 🔥' Google Sheet, write bilingual (EN + 简体中文) marketing copy per product, generate mascot hero banners with Grok Imagine through Claude in Chrome, and lay everything out as two HTML newsletters (one English, one Chinese) in the fixed Data Infra card style. Use this skill whenever the user mentions the Data Infra newsletter, monthly product updates email, 'What's New' sheet, newsletter cards, product hero banners, or asks to write / redo / update copy or banners for Diana, Langfuse, DataHub Agent, DI CLI, Data Studio, Scheduler Agent, DGC Agent or RAM in a newsletter context — even for a single stage (e.g. 'just rewrite the Langfuse card', 'regenerate the CLI banner', 'rebuild the October HTML')."
---

# Data Infra Newsletter

A four-stage pipeline with a human checkpoint after every stage. The user is the editor;
you are three people in turn — data wrangler, bilingual product marketer, then designer /
banner producer. Talk to the user in the Chinese they write (they have used 繁體); the newsletter ZH edition itself is Simplified Chinese with mainland vocabulary.

All state for an edition lives in `runs/<YYYY-MM>/` (create under the working directory or
wherever the user keeps previous runs):

```
runs/2026-10/
├── sheet_export.xlsx      # Stage 1 raw export
├── products_raw.json      # Stage 1 normalised rows + review notes
├── products.json          # single source of truth from Stage 2 on (references/schema.md)
├── banners/               # Stage 3 approved images
└── out/                   # Stage 4 newsletter_<month>_en.html / _zh.html + preview PNGs
```

Because state is a file, a run can stop after any checkpoint and resume next session:
check which files exist before asking the user where they are.

## Which month?

The sheet has one tab per edition named `<N>月newsletter` (case varies). The edition produced
at the end of month M is the **M+1 tab** (it lists what shipped in M and what ships in M+1).
Late September → `10月newsletter`. Confirm the tab name with the user once per run.

## Stage 1 — Extract (data wrangler)

1. Fetch the sheet with the Google Drive connector: `download_file_content` with
   `fileId = 1JaxsrNxMsbPelxACyRnGZrBMVcjo1HffBWhsvWBFyis` and
   `exportMimeType = application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.
   The result is large and lands in a tool-result JSON file — that is fine, `read_sheet.py`
   decodes it. (`read_file_content` truncates long cells; don't rely on it for copy.)
2. `python scripts/read_sheet.py <tool_result.json> "<tab>" runs/<YYYY-MM>` → `products_raw.json`.
   It forward-fills merged cells so multi-row products become one product with N features,
   skips rows marked `/`, classifies status from the 上线范围和状态 column, and prints NOTES.
3. **Checkpoint 1.** Show the user a compact table: product · status · #features · entry URL
   · mascot, followed by the NOTES verbatim (truncated cells, missing URLs, products with no
   details, products with no mascot). Ask what to do with each flagged item. Do not start
   writing copy for a product that has only a version number and no feature text — ask
   whether to chase the PIC, pull from Diana release notes, or drop it this month.

## Stage 2 — Copywrite (product marketer)

Read `references/copy_guidelines.md` first; it holds the structure, the bilingual rules and
the audience rule. Then:

1. Create `products.json` from `products_raw.json` (schema in `references/schema.md`). Fill
   `edition` (labels, intro, preheader, next_month) and, per product, `copy.en`, `copy.zh`,
   `buttons` and the text fields of `banner` (headline, subheadline, highlight,
   audience_tags, pose). Leave `banner.image = null`.
2. `python scripts/check_copy.py runs/<YYYY-MM>` — fix anything OVER before showing the user.
3. **Checkpoint 2.** Present copy one product at a time, EN and ZH side by side, in plain
   prose/lists (not the JSON). Ask for changes; edit `products.json`; re-run the checker.
   Lock a product only when the user says so — record `copy.locked = true` and stop touching
   it unless asked. Also show the proposed banner headline/subheadline here, since they are
   copy too.

## Stage 3 — Banners (visual producer + Claude in Chrome)

Read `references/banner_workflow.md` and `references/mascots.md`. For each product with a
mascot (and the edition hero): compose the prompt from the template + the mascot's identity
block, generate on grok.com/imagine through the Chrome connector, screenshot, and **wait for
the user's verdict** before downloading or moving on. Before starting, ask which banners the
user actually owns this month — in Oct 2026 Langfuse and the edition HERO were theirs;
DataHub was produced by a colleague (`banner.owner = "external"`), so the skill only wires
in the URL they hand over. The hero is regenerated every edition with the mascots as
protagonists in that month's theme (see banner_workflow.md → Edition hero banner). Products without a mascot get a text-only HTML banner (`banner.text_only`).
The approved image goes to the `Sharon-Tseng/diana_email_banner` GitHub repo and its raw URL
into `banner.image`; `assets.grok.com` is not reachable from here. Regenerate with the user's feedback
folded into the prompt; log every attempt in `banner.attempts`. Products without a mascot:
ask the user for a reference image or approval to use a text-only banner.

If the Chrome connector is not available in the session, produce the prompts, write them to
`runs/<YYYY-MM>/banner_prompts.md`, and ask the user to run them in Grok and drop the images
back; then continue.

## Stage 4 — Layout (designer)

The structure is fixed — `scripts/build_newsletter.py` is the template (840 px cards, Gloock
headings, Marmelad body, numbered 01/02/03 features, pill buttons at the card foot). The
palette is per edition via `edition.theme` (Oct 2026: low-saturation jungle green canvas
#F2F5EF, green card outlines, blue accents kept); ask for the month's theme before Stage 4.
Rules the builder applies automatically (see references/copy_guidelines.md):
- Section title is "<release_month> Product Updates", never "Latest".
- When a product has a banner (image or text-only), the card's title, subtitle and audience
  line are hidden — the banner already says them; only the stamp-style status badge stays.
- Highlight chips are tinted brand blue, bold, and wrap instead of widening the card; an
  optional `bullets_label` ("Improvements include:") sits above them in small grey text.
- Visual components: `checks`, `steps` (timeline by default, with footnote + ✓ note), `flow`, `before_after`.
- Cards whose sheet row lists features under category headings use `layout: "grouped"`
  (header band per category, no numerals) instead of the 01/02/03 list.
- The ZH edition uses its own CJK type scale (one sans stack, tighter tracking, smaller body);
  EN keeps the September values. See "Simplified-Chinese typography" in copy_guidelines.
Do not restyle beyond these knobs without telling the user.

1. `python scripts/build_newsletter.py runs/<YYYY-MM>` → `out/newsletter_<month>_en.html`
   and `_zh.html`. Add `--embed-images` when the user will open the file locally; without it
   banner paths stay relative, which is what they want when images are hosted (GitHub raw).
2. `python scripts/render_preview.py out/newsletter_<month>_en.html` (and zh) and show the
   PNGs. Missing banners render as labelled placeholders so layout review can happen before
   Stage 3 is complete.
3. **Checkpoint 3.** Take layout feedback (order of cards, which features get examples,
   button labels, intro wording). Every fix goes into `products.json` → rebuild → re-render.
   Never hand-edit the generated HTML.
4. Deliver both HTML files with `present_files`. If the previous edition's banners were hosted
   on the `Sharon-Tseng/diana_email_banner` GitHub repo, remind the user to upload this
   month's `banners/` there and swap `banner.image` to the raw URLs before the final build.

## Partial requests

"只改 Langfuse 文案" → open the existing `products.json`, run Stage 2 for that product only,
rebuild. "重生 CLI banner" → Stage 3 for that product only. "把 10 月的 HTML 重做" → Stage 4
only. Always re-run `check_copy.py` after any copy edit.

## Decisions already made (Oct 2026) — reuse unless the user changes them

- Copy: edit the PIC's text, never invent nouns, examples, chip labels or benefits; one main
  sentence + one background sentence; ≤ 300 words/chars hard limit, ~250/280 target.
- Reader situation goes in a small uppercase blue kicker above the feature title.
- Banner text style the team approved: hand-lettered cream headline with soft green shadow,
  frosted semi-transparent pills with forest-green text, ALL features as pills.
- "di CLI" (no hyphen) is accepted on banners.
- Diana 2.8 copy will come from a PRD; RAM has no mascot → text-only banner.
- A ChatGPT layout review is welcome but only CSS changes are taken, text frozen.

## Things that are not negotiable

- Length: ≤ 300 EN words / ≤ 300 ZH chars per product card. The checker is the referee.
- Mascot identity features never change; poses do. Reject drifted images.
- Banner text is English in both language editions.
- Every card ends with at least one button (entry link or guide/demo).
- Human verdict before any banner download and before any product copy is locked.
