# ChatGPT layout review — 2026-09-25
Conversation: https://chatgpt.com/c/6ab62438-2704-839e-b486-46d2c0eeca87
Inputs: draft Langfuse card (Oct 2026) vs reference DataHub Agent card (Sep 2026). Text frozen.

Applied to build_newsletter.py:
1. Audience overline 12/16px → 11/15px, letter-spacing .8px, margin 0 0 5px.
2. ✓ row: 16px icon, 7px icon gap, 22px item gap, 14/20px text, separate cells, 10px above.
3. Step cards: badge (22px) on its own row above heading; padding 12px 10px; radius 8px; copy 13/19px.
4. Footnote 12/18px, 8px above; ✓ note 14/20px, 5px above, 16px icon.
5. Chips: padding 8px 11px, 14/20px, 8px gaps.

Not applied (would break consistency with the September reference):
6. Numerals 36/40px — reference uses 29/32px.
7. Feature titles 26/32px — reference uses 23/29px. Descriptions already 16/25px.

## Round 2 — Simplified Chinese Langfuse card (same conversation)
Findings: Latin serif (Gloock) + CJK sans clash in titles; visible tracking; kicker looked like
monospace; body slightly large for Chinese; awkward wraps in step cards.

Applied (ZH only, via T(lang,…) in build_newsletter.py):
- Font stack for everything except numerals: 'PingFang SC','Microsoft YaHei','Noto Sans SC',Arial.
- Feature titles 24/34 weight 600; card h1 32/42 600; section title 38/50 600; letter-spacing 0.
- Kicker 12/18 weight 500, no uppercase, letter-spacing 0.
- Body 15/26; intro 16/28.
- Step cards: heading 14/20 600, caption 13/20; arrow columns 12px.
- Checks 14/20, icon gap 8px, item gap 20px.
- Chips 13/18 weight 500 (EN keeps 700).
- Latin/technical tokens wrapped in white-space:nowrap inside ZH titles and step text.
Not applied: fixed card heights (email clients handle it poorly).

## Round 3 — step-flow component (dead space in cards 2–4)
ChatGPT ranked: (1) horizontal timeline without cards — recommended; (2) vertical list with left
rail; (3) compact 2×2 grid. Applied option 1 as the default `steps` style: four equal text
columns, 24px numbered markers joined by a 2px rail, label + caption beneath each marker,
footnote + ✓ note below. Component height ≈ 150px. Old bordered version kept as
`"style": "boxes"`.

## Round 4 — RAM card: items belong to two categories
Problem: flat 01–04 list hid that items 1–3 are HDFS-alert changes and item 4 applies to all
alert types; the per-row kicker repeated "HDFS ALERTS" three times.
ChatGPT ranked: (1) group header bands + compact sub-items, numerals dropped — recommended;
(2) two unequal columns; (3) tinted bands over the existing rows.
Applied option 1 as `copy.layout = "grouped"` with `feature.group`: blue-tinted band for the
first group, green-tinted for the second (red third), 3px left accent, items as title + one-line
description, no numerals. ZH header 13/18 w600 letter-spacing 0.

## Round 5 — grouped RAM card v1 judged plain
ChatGPT ranked: (1) two soft tinted panels, circular count badge + category name, HDFS items as
a 3-column mini-card grid with their own numerals, single all-alert item as a wide row with a
green 4px accent — recommended; (2) two-column split; (3) stacked panels with rows.
Applied option 1 as grouped v2 (numerals kept and continuous across groups: 01–03 in the grid,
04 in the wide row). ZH: header 13/19 w600, mini-card title 16/23, desc 13/20, letter-spacing 0.

## Round 6 (team, no ChatGPT) — grouped v2 tweaks
- Count badges ("3", "1") read as numbering → category name now a filled accent tag, no digit.
- Stamp moved inline (right cell of feature 01 / first group header) → no separate row, no
  dead space above the first item. Card top padding 28px.

## Round 7 — grouped v2 mini-boxes judged ugly
ChatGPT ranked: (1) three open editorial rows (numeral | title | description) inside the panel,
same 52/270/rest columns as the 04 row, no boxes/fills/dividers — recommended; (2) borderless
columns with vertical rules; (3) numeral beside stacked title/description.
Applied option 1 as grouped v3: every group panel = filled category tag + open rows; accent bar
on every panel; numerals 27/32 Gloock continuous across groups. EN title 19/25, desc 14/21;
ZH title 16/23 w600, desc 13/20.

## Round 8 (team) — grouped v3 → v4
- Descriptions removed (kept in products.json as `desc_source`), titles only, 20/27 Gloock (ZH 17/26 w600).
- Numerals dropped for grouped cards (`layout_opts.numerals=false` default); marker = 18px accent check disc.
- Panels keep the filled category tag + 4px accent bar. Final RAM: 41 EN words / 79 ZH chars.
