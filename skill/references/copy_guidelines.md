# Copy guidelines (Stage 2)

You are writing as a marketer who understands both the engineering and the business side.
Readers are (a) engineers already using the product who should adopt the new feature and
(b) business colleagues curious about the AI products. Both must get, in one glance,
**what problem it solves and in what situation they would use it**. Feature lists that only
say what shipped ("Added X API") fail this test.

## Edit, don't rewrite — the PIC's text is the source of truth

The 解决的用户问题 / 场景 column is written by the engineer who built the feature. It is usually
already precise; what it lacks is (a) a direct address to the reader and (b) trimming. So the
job is editing, not re-authoring. The team's feedback after the first run was exactly this:
"內容已經很精簡，只是減少一點廢字，然後更 tailored to 我們的 target audience".

Do:
- Keep the PIC's nouns, numbers, product terms and ordering (trace_sessions table, ~1820 ms →
  ~205 ms, "centre modal then top banner"). Never round, soften or paraphrase a number.
- Name the reader's situation in the feature's `tag` ("For CLI & script users", "Projects with
  many prompts", "仍在用 v3 SDK / v1 API"), rendered as a small blue pill under the feature
  name. This is how "tailored to the target audience" shows up without adding a clause to
  every sentence. Omit the tag when the feature applies to everyone.
- Cut connective filler and marketing adjectives ("smoother", "seamless", "powerful",
  "designed to help teams", "更順手", "全面"). Cut restatements of the product name.
- Turn a list inside a sentence into `bullets` (4 community features → 4 bullets).
- Titles are plain: "<Product>: <Month> Updates" or "<Product>: <the one thing>". No
  slogans like "Faster, Cleaner, V4-Ready".

Don't:
- Invent a pain story the PIC didn't describe. If the sheet has only feature names (no scenario
  text), write one factual line per feature that states what the user can now do, mark the
  product in `notes` as "scenario inferred", and raise it at Checkpoint 2.
- Re-order the PIC's arguments to build a narrative; keep their sequence unless a number
  clearly belongs first.

## Two independent versions, not a translation

Each product gets an `en` and a `zh` version. Write EN first from the sheet, then write ZH
from the *same facts* — not by translating the EN sentences. Chinese readers expect shorter
clauses, fewer adjectives and verbs up front; a literal translation reads padded and hits the
character limit fast. Product names, feature names that are proper nouns (di-cli, CCIN,
Kafka-to-Hive), and UI labels stay in English inside the ZH copy.

ZH uses **Simplified Chinese with mainland vocabulary** (team decision, Oct 2026) — the same
register the PICs write in the sheet: 数据 (not 资料), 项目 (not 专案), 用户 (not 使用者),
文件 (not 档案), 调用 (not 呼叫), 反馈 (not 回馈), 示例 (not 范例), 设置 (not 设定), 检测 (not
侦测), 渠道 (not 通道), 私信 (not 私讯), 社区版 (not 社群版), 通过 (not 透过), 存储 (not 储存).
Do not write Traditional-flavoured Simplified (e.g. 「一开即现」「串接」): if the sentence
would sound odd in a Shopee/Sea internal Seatalk post, rephrase. `html lang="zh-Hans"`, font
stack Noto Sans SC / PingFang SC / Microsoft YaHei.

## Never add what the PIC didn't write

This is the rule the team cared most about after the first run ("他原本又沒有說 SDK, API, MCP
這些方法，請不要加沒有的東西"). Everything in the card — every noun in a sentence, every chip
label in a schematic, every prompt example, every claimed benefit — must be traceable to the
sheet row. If the PIC says "one of several access methods" without naming them, the schematic
shows `di-cli` + `other access methods`, not a guessed list. If there is no prompt example in
the sheet, the card has no example box. If a benefit is not stated, do not infer one; restate
the feature plainly and raise "ask PIC for scenario text" at the checkpoint.

## Length rule — enough background, not padding

Hard limit: **≤ 300 EN words / ≤ 300 ZH chars per card**. The layout should not look like a
wall of text, but the team also asked for "一些 background" — so the shape per feature is:
one main sentence (what changed) + one background sentence (why it was a problem / how it
behaves), each in the PIC's words. Lists become `bullets`; before/after changes become a
`visual`; the reader's situation goes in `tag`. `scripts/check_copy.py` reports OK / LONG /
OVER (target 250 / 280, per-feature desc ≤ 45 words / ≤ 65 字) — run it before every
checkpoint, and when a card is OVER, cut captions and subtitle first, never the background
sentence.

## Card structure

```
title        product + version or the single biggest benefit ("Langfuse: Faster, Cleaner, V4-Ready")
subtitle     one sentence: who, what changes for them, this month
audience     ONLY when the sheet names a specific group; see rule below
features[]   01..06, each:
  name       short noun phrase, benefit-oriented where possible
  tag        optional: who this item is for, 2–8 words; rendered as a small blue uppercase
             kicker ABOVE the feature name (same device as the original's "PLATFORM · DIANA")
  bullets_label optional small grey lead-in above bullets/chips, e.g. "Improvements include:"
  bullets_style "chips" when the bullets are ≤ 5 short nouns (feature names, flow names) — a
             chip row reads as a set, a bulleted list reads as a to-do
  desc       ONE sentence: what changed, with the PIC's number
  visual     optional, one row tall. Only when it shows something the sentence can't:
             `checks` — the outcomes the PIC listed after the dash ("— faster reads, consistent
             with the V4 single-table model") pulled out of the sentence as ✓ items; the sentence
             then ends at the fact. This is the team's preferred shape for "main sentence + benefits".
             `steps` — a behaviour the PIC describes as a sequence (detect → modal → banner →
             disappears). Default rendering is a horizontal TIMELINE (numbered markers on a
             thin rail, text under each marker, no boxes) — boxed cards left dead space under
             the shorter steps and the team rejected them; `"style": "boxes"` still exists. Keep each card to a 2–3-word verb label
             ("Detect pending work", "Show reminder") and a ≤ 8-word caption; move any
             enumeration (Experiments / Evals / Exports) to `footnote`, and the guarantee
             ("unaffected projects are never interrupted") to the ✓ `note`. The feature then
             has no `desc` at all — the flow *is* the content.
             `flow` — what changed under the hood ([di-cli reads] → [V4 event aggregation],
             with the retired dependency struck out). `before_after` — only when both states
             are concrete values the reader compares (numbers, versions). A visual that merely
             re-draws the sentence ("was one of several → now recommended") is worse than no
             visual: the team's words were "有講跟沒講一樣，而且很佔空間". Labels must be
             terms from the sheet row, never invented components.
  bullets    optional 2–4 short items when the feature is really a list (alert channels, task types)
  example    optional literal prompt/command a user can copy — great for agent products
```

Pattern: `tag` = reader's situation; `desc` = one sentence with the PIC's number.
Example (edited from the sheet, not rewritten):
name "Prompts list ~9× faster" · tag "Projects with many prompts" ·
desc "Distinct-prompt count cut from ~1820 ms to ~205 ms; the list opens instantly."

## Audience rule

Show the audience line only when the sheet's 目标用户 names a specific group (FP teams, data
mart / marketplace teams, users still on the legacy SDK). Do **not** show it when it is empty,
"All <product> users", "全體用戶", or otherwise the product's whole user base — those readers
are the default, and the line just adds words. When one feature out of several has a specific
audience (e.g. the V4 migration alert only concerns legacy-SDK projects), put that
qualifier inside the feature's own description rather than in the card audience line.

## Status

`live` → the sheet says Released / 已上线 / 全量; `coming` → Expected / 即将 / 🔜. Cards in
`coming` go under the "Coming in <next month>" section. If the sheet says a product will be
promoted next month instead (下個月再宣傳), skip it entirely this edition. When the status
cell is empty and the feature text exists, ask the user rather than guessing.

## When the source is a PRD instead of the sheet

Some products (Diana 2.8 is the first) arrive as a PRD rather than sheet rows. Treat the PRD
the same way as PIC text: extract only what is described as shipping in this edition's
window (ignore roadmap / future phases / open questions), keep the PRD's feature names and
numbers, and apply every rule above — no invented benefits, no examples that aren't in the
PRD. Record the PRD file name and section headings in `products.json → source_rows` (as
strings) so the card can be traced back. If the PRD doesn't say which items ship this month,
ask before writing.

## Using 現有可提供文案

If the PIC already supplied copy, treat it as the primary source for facts and tone, but still
enforce the structure and limits above — existing copy is usually a Seatalk announcement, not a
card. Keep any figures (9×, 1820 ms → 205 ms, up to 100 items) exactly.

## Things to flag at the checkpoint instead of inventing

- A feature with a name but no problem/scenario text.
- Problem text that ends mid-sentence (the sheet cell was truncated).
- Missing product entry URL or guide link — every card needs at least one button.
- A product whose 更新功能名称 is just a version number (e.g. "Diana 2.8") with no details.
- Numbers that look inconsistent between features or with last month's edition.

## Layout review loop (optional, Stage 4)

The team likes a second opinion on layout from ChatGPT before locking the HTML. Workflow that
worked: render the draft card and one reference card in the user's Chrome (inject the HTML with
the javascript tool on a blank page such as example.com — `file_upload` may refuse sandbox
paths), screenshot each, `upload_image` them into chatgpt.com, and send a prompt that freezes
the text ("do not change, shorten, reword, reorder, add or remove any text") and asks for
numbered changes with exact CSS values. Apply only suggestions that keep the September
reference's fixed values (numerals 29/32px, feature titles 23/29px, body 16/25px); log the
review in `runs/<month>/chatgpt_layout_review_<date>.md`.

## Card header vs banner (rule from Oct 2026)

When a product has a real hero banner (an approved image, or the text-only HTML banner), the
banner already shows the headline, the feature pills and any "Designed for" tags. Do **not**
repeat them: the builder hides the card's `title`, `subtitle` and audience line automatically
and keeps only the status badge (NOW LIVE / COMING SOON), right-aligned on a slim row above the
features. The badge is a rubber-stamp (19–20px caps, 4px double outline, wide tracking, −6° tilt; upright in
Outlook), placed INLINE with the first feature (right-hand cell of row 01) or inside the first group
panel's header row, not on its own row — a separate stamp row left too much whitespace above
01 (team feedback, twice) — the team asked for something bigger and stamp-like in both languages, echoing the
September "HOT AND FRESH" stamp. Green #0B8F5C for live, blue for coming. Still write `title`/`subtitle` in `products.json` — they are used for the placeholder
before the banner exists and for the preheader — but expect them to disappear once the banner
is wired in. Override with `"show_header": true` on a product if its banner has no text.

Section header: "LATEST RELEASES / <Month> Product Updates" where <Month> is the month the
features shipped (`edition.release_month`, e.g. "September" for the edition sent at the end
of September). Not "Latest".

Highlight chips (`bullets_style: "chips"`) render in tinted brand blue with bold text so the
listed items read as the highlights of the feature; they wrap onto a second row rather than
widening the card.

## Simplified-Chinese typography (rule from the Oct 2026 ChatGPT review)

The builder applies a separate type scale when `lang == "zh"` (`T(lang, key)` in
`build_newsletter.py`). Do not reuse the English values for Chinese:
- One CJK sans stack for titles, body, kickers, chips and buttons: PingFang SC → Microsoft
  YaHei → Noto Sans SC → Arial. Gloock stays only on the 01/02/03 numerals. Mixing the Latin
  serif with CJK sans in one title was the single biggest reason the ZH card looked "丑".
- Sizes: feature title 24/34 w600; card h1 32/42 w600; section title 38/50 w600; kicker 12/18
  w500 (never uppercase or letter-spaced for Chinese); body 15/26; intro 16/28; step heading
  14/20 w600, caption 13/20; chips 13/18 w500; checks 14/20. `letter-spacing: 0` everywhere.
- Latin/technical tokens inside Chinese (SDK/API, V4, trace_sessions, di-cli) are wrapped in
  `white-space:nowrap` so they never split across lines; Chinese text wraps naturally.
- Keep full-width Chinese punctuation; leave a normal space either side of Latin terms.

## Grouped cards — when the sheet lists features under category headings (rule from Oct 2026)

Some PICs write the 更新功能名称 cell as categories with sub-lists, e.g. RAM:
"For HDFS alert: 1… 2… 3… / For all alert type: 1…". Those are **not** four peer features, and
the flat 01/02/03/04 list misrepresents them (the team's words: 「已经区分成 HDFS Alerts 和 All
Alert Types 了，排版上不适合列点一二三四」). Do this instead:
- Set `copy.layout = "grouped"` and give every feature a `group` (the category name exactly as
  the PIC wrote it, translated for ZH). Drop `tag` — the group header replaces it.
- The builder renders one softly tinted rounded panel per group with a 4px accent bar; the
  category name is a filled tag (white on the accent colour — no count digit). Inside, items
  are TITLE-ONLY rows with a small accent-coloured ✓ disc: no numerals, no description
  column (team decision, Oct 2026 — when the sheet gives feature names only, the tag + title
  is the whole message; keep any description text in `desc_source` for the record).
  `layout_opts: {"numerals": true, "descriptions": true}` re-enables either if a future
  grouped card really needs them. Rejected on the way here (don't go back): thin header
  bands + hairlines ("有点丑"); circular count badges ("看起来很像编码"); bordered white
  mini-cards ("方框好丑"); numeral | title | description rows (descriptions judged
  unnecessary, numerals unnecessary for grouped cards).
- Keep the PIC's item order inside each group; group order = order in the sheet.
- Numbered layout remains the default for cards whose items are genuinely peers.

## Column alignment (rule from Oct 2026)

Every block in the newsletter — hero card, section headers, product cards, closing card —
uses the same outer cell padding (`0 14px`) and the same `.shell` 840px table with
`max-width:100%`, so their left/right edges line up at every viewport, including narrow
mail clients where everything collapses to 100% − 28px. Verified with Playwright at 1300,
900 and 700px; keep it that way when adding new block types.
