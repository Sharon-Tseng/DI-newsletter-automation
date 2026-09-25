#!/usr/bin/env python3
"""Build the Data Infra newsletter HTML (one file per language) from products.json.

Usage:
    python build_newsletter.py <run_dir> [--lang en|zh|all] [--out <dir>]

<run_dir> must contain products.json (see references/schema.md). Banner images are
resolved relative to <run_dir>; if a banner is missing a labelled placeholder is
rendered so layout can be reviewed before the Grok step is finished.

The template is a table-based email layout copied from the September 2026 edition
(840px cards, #F7F4EA canvas, Gloock headings, Marmelad body). Do not restyle in
this script per edition — change assets/design_tokens.md and here together only when
the team deliberately changes the newsletter look.
"""
import argparse
import re
import base64
import html
import json
import mimetypes
import os
import sys

# ---------------------------------------------------------------- tokens
CANVAS = "#F7F4EA"
CARD_BG = "#FFFFFF"
INK = "#172033"
INK_DEEP = "#173866"
MUTED = "#657083"
BLUE = "#2463D4"
BLUE_SHADOW = "#173F98"
BLUE_SOFT = "#5B8DEF"
BLUE_SOFT_SHADOW = "#3E6FC7"
GREEN = "#00A96B"
RED = "#EF4C3F"
RULE = "#E8EDF5"
EXAMPLE_BG = "#F5F7FA"
EXAMPLE_BORDER = "#D9E1EA"
EXAMPLE_INK = "#24344D"
CHIP_BG = "#E8F0FE"          # accent chips: tinted brand blue so highlighted items stand out
CHIP_BORDER = "#B9CFF5"
CHIP_INK = "#1F4FB8"
CARD_BORDER = "transparent"   # card outline (theme may set e.g. a soft green)
SECTION_RULE = "#E5E8EE"
CLOSING_BG = "#F3F7FF"
CLOSING_BORDER = "#CFE0FF"
NUM_COLORS = [RED, BLUE, GREEN]

SERIF = "'Gloock',Georgia,serif"
SANS = "'Marmelad',Arial,sans-serif"
SANS_ZH = "'PingFang SC','Microsoft YaHei','Noto Sans SC',Arial,sans-serif"   # CJK first: one texture for Chinese + Latin terms
MONO = "'Geist Mono','SFMono-Regular',Menlo,Consolas,monospace"

STRINGS = {
    "en": {
        "latest_kicker": "LATEST RELEASES",
        "latest_title": "{month} Product Updates",
        "next_kicker": "NEXT UP",
        "next_title": "Coming in {month}",
        "live": "NOW LIVE",
        "coming": "COMING SOON",
        "built_for": "Built for",
        "example": "Prompt Examples",
        "closing_title": "💬 We'd love to hear from you",
        "closing_body": "We hope you enjoy these new updates, and we welcome your feedback and suggestions.",
        "regards": "BEST REGARDS,",
        "team": "Data Infra Team",
        "internal": "INTERNAL USE ONLY",
        "footer": "Data Infra Monthly Newsletter · {edition}",
        "html_lang": "en",
    },
    "zh": {
        "latest_kicker": "本月上线",
        "latest_title": "{month}产品更新",
        "next_kicker": "即将推出",
        "next_title": "{month} 即将上线",
        "live": "已上线",
        "coming": "即将上线",
        "built_for": "适用对象",
        "example": "提示示例",
        "closing_title": "💬 期待你的反馈",
        "closing_body": "希望这些更新对你有帮助，也欢迎随时告诉我们你的想法与建议。",
        "regards": "祝 顺心",
        "team": "Data Infra 团队",
        "internal": "仅供内部使用",
        "footer": "Data Infra 每月月报 · {edition}",
        "html_lang": "zh-Hans",
    },
}


def esc(s):
    return html.escape(s or "", quote=True)


def t(lang, key, **kw):
    return STRINGS[lang][key].format(**kw)


def font(lang):
    return SANS_ZH if lang == "zh" else SANS


def title_font(lang):
    """Feature/card titles: Gloock for EN; a single CJK sans for ZH (serif+sans clash otherwise)."""
    return SANS_ZH if lang == "zh" else SERIF


# ZH-specific type sizes (ChatGPT layout review, 2026-09-25): tighter tracking, smaller body,
# heavier sans titles. EN keeps the September values.
def T(lang, key):
    zh = {"h2": "font-size:24px;line-height:34px;font-weight:600;letter-spacing:0;",
          "h1": "font-size:32px;line-height:42px;font-weight:600;letter-spacing:0;",
          "kicker": "font-size:12px;line-height:18px;font-weight:500;letter-spacing:0;",
          "body": "font-size:15px;line-height:26px;letter-spacing:0;",
          "step_h": "font-size:14px;line-height:20px;font-weight:600;letter-spacing:0;",
          "step_p": "font-size:13px;line-height:20px;letter-spacing:0;",
          "chip": "font-size:13px;line-height:18px;font-weight:500;letter-spacing:0;",
          "check": "font-size:14px;line-height:20px;letter-spacing:0;"}
    en = {"h2": "font-size:23px;line-height:29px;font-weight:400;",
          "h1": "font-size:36px;line-height:43px;font-weight:400;",
          "kicker": "font-size:11px;line-height:15px;letter-spacing:.8px;text-transform:uppercase;",
          "body": "font-size:16px;line-height:25px;",
          "step_h": "font-size:14px;line-height:19px;font-weight:700;",
          "step_p": "font-size:13px;line-height:19px;",
          "chip": "font-size:13px;line-height:18px;font-weight:700;",
          "check": "font-size:14px;line-height:20px;"}
    return (zh if lang == "zh" else en)[key]


def nowrap_latin(text, lang):
    """ZH only: keep Latin/technical tokens (SDK/API, V4, trace_sessions) on one line."""
    if lang != "zh":
        return esc(text)
    parts = re.split(r"([A-Za-z0-9_][A-Za-z0-9_./\-]*)", text)
    return "".join(f'<span style="white-space:nowrap;">{esc(pt)}</span>' if i % 2 else esc(pt) for i, pt in enumerate(parts))


def resolve_img(run_dir, ref, embed):
    """Return a src value for an image reference (URL, or run-relative path)."""
    if not ref:
        return None
    if ref.startswith("http://") or ref.startswith("https://"):
        return ref
    path = ref if os.path.isabs(ref) else os.path.join(run_dir, ref)
    if not os.path.exists(path):
        return None
    if not embed:
        return ref
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"


# ---------------------------------------------------------------- pieces
def banner_block(product, lang, run_dir, embed):
    b = product.get("banner") or {}
    src = resolve_img(run_dir, b.get("image"), embed)
    if src:
        return (
            f'<tr><td style="padding:0;background:{CARD_BG};">'
            f'<img src="{esc(src)}" width="840" alt="{esc(product["name"])} hero banner" '
            f'style="display:block;width:840px;max-width:100%;height:auto;border:0;"></td></tr>'
        )
    head = esc(b.get("headline") or product["name"])
    sub = esc(b.get("subheadline") or "")
    if b.get("text_only"):
        # Designed HTML banner for products without a mascot (team decision): solid light
        # panel, headline + subheadline, optional highlight pill. Email-safe, no image.
        hl = b.get("highlight")
        pill_html = (
            f'<span style="display:inline-block;margin-top:16px;padding:7px 14px;border-radius:999px;background:{BLUE};color:#FFFFFF;'
            f'font-family:{SANS};font-size:13px;line-height:16px;letter-spacing:.3px;">{esc(hl)}</span>' if hl else ""
        )
        return (
            f'<tr><td style="padding:0;background:#EAF1FF;border-bottom:1px solid #D6E3FA;">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;border-collapse:collapse;">'
            f'<tr><td valign="middle" style="padding:52px 44px 48px;">'
            f'<p style="margin:0 0 10px;font-family:{SANS};font-size:12px;line-height:16px;letter-spacing:1.5px;text-transform:uppercase;color:{BLUE};">{esc(product["name"])}</p>'
            f'<p style="margin:0;font-family:{SERIF};font-size:38px;line-height:44px;color:{INK_DEEP};">{head}</p>'
            f'<p style="margin:10px 0 0;font-family:{SANS};font-size:17px;line-height:25px;color:{MUTED};max-width:560px;">{sub}</p>'
            f'{pill_html}'
            f'</td></tr></table></td></tr>'
        )
    # Placeholder so the card can be reviewed before Grok output is approved.
    return (
        f'<tr><td style="padding:0;background:#E9EEF7;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;height:280px;border-collapse:collapse;">'
        f'<tr><td valign="middle" style="padding:40px 44px;font-family:{SANS};">'
        f'<p style="margin:0 0 6px;font-size:12px;letter-spacing:1.5px;color:{BLUE};">BANNER PLACEHOLDER · pending Grok</p>'
        f'<p style="margin:0;font-family:{SERIF};font-size:34px;line-height:40px;color:{INK_DEEP};">{head}</p>'
        f'<p style="margin:8px 0 0;font-size:17px;line-height:24px;color:{MUTED};">{sub}</p>'
        f'</td></tr></table></td></tr>'
    )


def pill(text, bg):
    """Small filled pill (kept for misc uses)."""
    return (
        f'<span style="display:inline-block;padding:8px 14px;border-radius:999px;background:{bg};color:#FFFFFF;'
        f'font-family:{SANS};font-size:14px;line-height:18px;letter-spacing:.4px;white-space:nowrap;">{esc(text)}</span>'
    )


def stamp(text, color, lang="en"):
    """Status badge as a rubber-stamp: double outline, tracked caps, slight tilt (team request,
    Oct 2026 — echoes the September 'HOT AND FRESH' stamp). The tilt is progressive
    enhancement; Outlook ignores transform and shows an upright stamp, which still reads."""
    is_zh = lang == "zh"
    return (
        f'<span style="display:inline-block;padding:9px 18px;border:4px double {color};border-radius:8px;color:{color};'
        f'font-family:{font(lang)};font-size:{"20px" if is_zh else "19px"};line-height:24px;font-weight:700;'
        f'letter-spacing:{"5px" if is_zh else "3px"};text-transform:uppercase;white-space:nowrap;'
        f'transform:rotate(-6deg);-webkit-transform:rotate(-6deg);">{esc(text)}</span>'
    )


def feature_rows(features, lang, stamp_html=""):
    rows = []
    n = len(features)
    for i, f in enumerate(features):
        num = f"{i+1:02d}"
        color = NUM_COLORS[i % len(NUM_COLORS)]
        first, last = i == 0, i == n - 1
        num_pad = ("1px" if first else "24px") + " 13px " + ("0" if last else "24px") + " 0"
        body_pad = ("0" if first else "24px") + " 0 " + ("0" if last else "24px")
        border = "" if last else f"border-bottom:1px solid {RULE};"
        inner = ""
        if f.get("tag"):
            inner += (
                f'<p style="margin:0 0 5px;font-family:{font(lang)};{T(lang,"kicker")}color:{BLUE};">{esc(f["tag"])}</p>'
            )
        inner += (
            f'<h2 style="margin:0 0 6px;font-family:{title_font(lang)};{T(lang,"h2")}color:{INK};">{nowrap_latin(f["name"], lang)}</h2>'
        )
        if f.get("desc"):
            inner += f'<p style="margin:0;font-family:{font(lang)};{T(lang,"body")}color:{MUTED};">{esc(f["desc"])}</p>'
        if f.get("bullets") and f.get("bullets_label"):
            inner += (
                f'<p style="margin:12px 0 0;font-family:{font(lang)};font-size:13px;line-height:18px;color:{MUTED};">{esc(f["bullets_label"])}</p>'
            )
        if f.get("bullets") and f.get("bullets_style") == "chips":
            # inline-block spans so the row wraps instead of widening the card
            chips = "".join(
                f'<span style="display:inline-block;margin:0 8px 8px 0;padding:8px 12px;border-radius:8px;background:{CHIP_BG};'
                f'border:1px solid {CHIP_BORDER};color:{CHIP_INK};font-family:{font(lang)};{T(lang,"chip")}white-space:nowrap;">{esc(b)}</span>'
                for b in f["bullets"]
            )
            inner += f'<div style="margin-top:{"8px" if f.get("bullets_label") else "12px"};line-height:0;">{chips}</div>'
        elif f.get("bullets"):
            items = "".join(
                f'<li style="margin:0 0 4px;">{esc(b)}</li>' for b in f["bullets"]
            )
            inner += (
                f'<ul style="margin:8px 0 0;padding:0 0 0 20px;font-family:{font(lang)};font-size:15px;line-height:23px;color:{MUTED};">{items}</ul>'
            )
        if f.get("visual") and f["visual"].get("type") == "before_after":
            inner += before_after_block(f["visual"], lang)
        if f.get("visual") and f["visual"].get("type") == "flow":
            inner += flow_block(f["visual"], lang)
        if f.get("visual") and f["visual"].get("type") == "checks":
            inner += checks_block(f["visual"], lang)
        if f.get("visual") and f["visual"].get("type") == "steps":
            inner += steps_block(f["visual"], lang)
        if f.get("example"):
            label = f.get("example_label") or t(lang, "example")
            inner += (
                f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" '
                f'style="width:100%;border-collapse:separate;margin-top:14px;background:{EXAMPLE_BG};border:1px solid {EXAMPLE_BORDER};border-radius:10px;">'
                f'<tr><td style="padding:11px 13px 12px;">'
                f'<p style="margin:0 0 4px;font-family:{font(lang)};font-size:14px;line-height:20px;color:{BLUE};">{esc(label)}</p>'
                f'<p style="margin:0;font-family:{MONO};font-size:14px;line-height:22px;color:{EXAMPLE_INK};word-break:break-word;">{esc(f["example"])}</p>'
                f'</td></tr></table>'
            )
        if first and stamp_html:
            inner = (
                f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;border-collapse:collapse;"><tr>'
                f'<td valign="top">{inner}</td><td width="170" align="right" valign="top" style="width:170px;padding:0 8px 0 12px;">{stamp_html}</td></tr></table>'
            )
        rows.append(
            f'<tr><td valign="top" width="52" style="width:52px;min-width:52px;padding:{num_pad};font-family:{SERIF};font-size:29px;line-height:32px;color:{color};">{num}</td>'
            f'<td valign="top" style="padding:{body_pad};{border}">{inner}</td></tr>'
        )
    return "".join(rows)


def before_after_block(v, lang):
    """Two-panel 'Before → Now' schematic built from tables so it renders in email clients."""
    def panel(side, tone):
        chips = []
        for it in side.get("items", []):
            hl = it == side.get("highlight")
            if hl:
                chips.append(
                    f'<td style="padding:0 6px 6px 0;"><span style="display:inline-block;padding:6px 12px;border-radius:8px;background:{BLUE};color:#FFFFFF;'
                    f'font-family:{MONO};font-size:13px;line-height:16px;font-weight:700;">{esc(it)}</span></td>'
                )
            else:
                chips.append(
                    f'<td style="padding:0 6px 6px 0;"><span style="display:inline-block;padding:6px 12px;border-radius:8px;background:#FFFFFF;border:1px solid {EXAMPLE_BORDER};'
                    f'color:{"#9AA5B8" if tone == "after" else EXAMPLE_INK};font-family:{MONO};font-size:13px;line-height:16px;">{esc(it)}</span></td>'
                )
        badge = ""
        if side.get("badge"):
            badge = (f'<span style="display:inline-block;margin-left:8px;padding:2px 8px;border-radius:999px;background:{GREEN};color:#FFFFFF;'
                     f'font-family:{font(lang)};font-size:11px;line-height:14px;">{esc(side["badge"])}</span>')
        label_color = "#9AA5B8" if tone == "before" else BLUE
        return (
            f'<p style="margin:0 0 8px;font-family:{font(lang)};font-size:12px;line-height:16px;letter-spacing:1px;color:{label_color};">{esc(side.get("label",""))}{badge}</p>'
            f'<table role="presentation" cellspacing="0" cellpadding="0" border="0" style="border-collapse:collapse;"><tr>{"".join(chips)}</tr></table>'
            f'<p style="margin:6px 0 0;font-family:{font(lang)};font-size:13px;line-height:19px;color:{MUTED};">{esc(side.get("caption",""))}</p>'
        )
    return (
        f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" '
        f'style="width:100%;border-collapse:separate;margin-top:14px;background:{EXAMPLE_BG};border:1px solid {EXAMPLE_BORDER};border-radius:10px;">'
        f'<tr>'
        f'<td valign="top" width="46%" style="padding:14px 12px 14px 16px;">{panel(v["before"], "before")}</td>'
        f'<td valign="middle" align="center" width="8%" style="padding:0;font-family:{SERIF};font-size:26px;color:{BLUE};">→</td>'
        f'<td valign="top" width="46%" style="padding:14px 16px 14px 12px;">{panel(v["after"], "after")}</td>'
        f'</tr></table>'
    )


def flow_block(v, lang):
    """One-row data-flow strip: [node] → [node] → [node], with an optional struck-out
    'no longer used' note. Compact (≈60px) — for showing what changed under the hood."""
    cells = []
    for i, node in enumerate(v.get("nodes", [])):
        if i:
            cells.append(f'<td style="padding:0 8px;font-family:{SERIF};font-size:20px;color:{BLUE};">→</td>')
        last = i == len(v["nodes"]) - 1
        bg = BLUE if last else "#FFFFFF"
        color = "#FFFFFF" if last else EXAMPLE_INK
        border = "" if last else f"border:1px solid {EXAMPLE_BORDER};"
        cells.append(
            f'<td><span style="display:inline-block;padding:6px 12px;border-radius:8px;background:{bg};{border}'
            f'color:{color};font-family:{MONO};font-size:13px;line-height:16px;white-space:nowrap;">{esc(node)}</span></td>'
        )
    note = ""
    if v.get("retired"):
        note = (
            f'<p style="margin:8px 0 0;font-family:{font(lang)};font-size:13px;line-height:18px;color:#9AA5B8;">'
            f'<span style="color:{RED};">✕</span> <s style="font-family:{MONO};">{esc(v["retired"])}</s>'
            f'{(" — " + esc(v["retired_note"])) if v.get("retired_note") else ""}</p>'
        )
    return (
        f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" '
        f'style="width:100%;border-collapse:separate;margin-top:12px;background:{EXAMPLE_BG};border:1px solid {EXAMPLE_BORDER};border-radius:10px;">'
        f'<tr><td style="padding:12px 14px;">'
        f'<table role="presentation" cellspacing="0" cellpadding="0" border="0" style="border-collapse:collapse;"><tr>{"".join(cells)}</tr></table>'
        f'{note}</td></tr></table>'
    )


def check_icon(size=16):
    return (f'<span style="display:inline-block;width:{size}px;height:{size}px;border-radius:999px;background:{GREEN};color:#FFFFFF;'
            f'font-family:{SANS};font-size:11px;line-height:{size}px;text-align:center;">\u2713</span>')


def checks_block(v, lang):
    """One-row strip of \u2713 outcomes: the benefits the PIC listed, pulled out of the sentence."""
    cells = []
    for i, it in enumerate(v.get("items", [])):
        gap = "0" if i == len(v["items"]) - 1 else ("20px" if lang == "zh" else "22px")
        icon_gap = "8px" if lang == "zh" else "7px"
        cells.append(
            f'<td valign="middle" style="padding:0 {icon_gap} 0 0;">{check_icon(16)}</td>'
            f'<td valign="middle" style="padding:0 {gap} 0 0;font-family:{font(lang)};{T(lang,"check")}color:{INK};white-space:nowrap;">{esc(it)}</td>'
        )
    return (
        f'<table role="presentation" cellspacing="0" cellpadding="0" border="0" style="border-collapse:collapse;margin-top:10px;">'
        f'<tr>{"".join(cells)}</tr></table>'
    )


def steps_block(v, lang):
    """Process flow. Default style "timeline" (ChatGPT review, Oct 2026): four equal text
    columns, numbered markers joined by a thin rail, label + caption under each marker, no
    boxes — so a long caption in one step never leaves dead space in the others.
    style "boxes" keeps the older bordered-card version."""
    if v.get("style") == "boxes":
        return steps_boxes_block(v, lang)
    steps = v.get("steps", [])
    n = len(steps)
    rail_cells, text_cells = [], []
    for i, st in enumerate(steps):
        last = i == n - 1
        num_bg = GREEN if last else BLUE
        marker = (
            f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;border-collapse:collapse;"><tr>'
            f'<td width="24" height="24" align="center" valign="middle" bgcolor="{num_bg}" style="width:24px;height:24px;border-radius:12px;background:{num_bg};'
            f'color:#FFFFFF;font-family:{SANS};font-size:12px;line-height:24px;">{i+1}</td>'
        )
        if not last:
            marker += f'<td valign="top" style="padding:11px 0 0 8px;"><div style="height:2px;background:{EXAMPLE_BORDER};font-size:0;line-height:0;">&nbsp;</div></td>'
        else:
            marker += '<td style="font-size:0;line-height:0;">&nbsp;</td>'
        marker += '</tr></table>'
        rail_cells.append(f'<td valign="top" style="padding:0 {0 if last else 8}px 0 0;">{marker}</td>')
        text_cells.append(
            f'<td valign="top" style="padding:10px 14px 0 0;">'
            f'<p style="margin:0 0 3px;font-family:{font(lang)};{T(lang,"step_h")}color:{INK};">{nowrap_latin(st.get("label",""), lang)}</p>'
            f'<p style="margin:0;font-family:{font(lang)};{T(lang,"step_p")}color:{MUTED};">{nowrap_latin(st.get("caption",""), lang)}</p>'
            f'</td>'
        )
    note = ""
    if v.get("footnote"):
        note += f'<p style="margin:14px 0 0;font-family:{font(lang)};font-size:12px;line-height:18px;color:{MUTED};">{esc(v["footnote"])}</p>'
    if v.get("note"):
        note += (
            f'<table role="presentation" cellspacing="0" cellpadding="0" border="0" style="border-collapse:collapse;margin-top:{"5px" if v.get("footnote") else "12px"};">'
            f'<tr><td valign="middle" style="padding:0 7px 0 0;">{check_icon(16)}</td>'
            f'<td valign="middle" style="font-family:{font(lang)};{T(lang,"check")}color:{INK};">{esc(v["note"])}</td></tr></table>'
        )
    return (
        f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;border-collapse:collapse;table-layout:fixed;margin-top:14px;">'
        f'<tr>{"".join(rail_cells)}</tr>'
        f'<tr>{"".join(text_cells)}</tr>'
        f'</table>{note}'
    )


def steps_boxes_block(v, lang):
    """Older bordered-card flow, kept for products that explicitly want boxes."""
    steps = v.get("steps", [])
    cells = []
    for i, st in enumerate(steps):
        if i:
            cells.append(f'<td valign="middle" width="{12 if lang == "zh" else 18}" style="width:{12 if lang == "zh" else 18}px;padding:0;text-align:center;font-family:{SANS};font-size:16px;color:#9AA5B8;">\u2192</td>')
        last = i == len(steps) - 1
        num_bg = GREEN if last else BLUE
        cells.append(
            f'<td valign="top" style="padding:12px 10px;background:#FFFFFF;border:1px solid {EXAMPLE_BORDER};border-radius:8px;">'
            f'<span style="display:inline-block;width:22px;height:22px;border-radius:999px;background:{num_bg};color:#FFFFFF;font-family:{SANS};font-size:12px;line-height:22px;text-align:center;">{i+1}</span>'
            f'<p style="margin:7px 0 3px;font-family:{font(lang)};{T(lang,"step_h")}color:{INK};">{nowrap_latin(st.get("label",""), lang)}</p>'
            f'<p style="margin:0;font-family:{font(lang)};{T(lang,"step_p")}color:{MUTED};">{nowrap_latin(st.get("caption",""), lang)}</p></td>'
        )
    note = ""
    if v.get("footnote"):
        note += f'<p style="margin:8px 0 0;font-family:{font(lang)};font-size:12px;line-height:18px;color:{MUTED};">{esc(v["footnote"])}</p>'
    if v.get("note"):
        note += (
            f'<table role="presentation" cellspacing="0" cellpadding="0" border="0" style="border-collapse:collapse;margin-top:{"5px" if v.get("footnote") else "8px"};">'
            f'<tr><td valign="middle" style="padding:0 7px 0 0;">{check_icon(16)}</td>'
            f'<td valign="middle" style="font-family:{font(lang)};{T(lang,"check")}color:{INK};">{esc(v["note"])}</td></tr></table>'
        )
    return (
        f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed;margin-top:12px;">'
        f'<tr>{"".join(cells)}</tr></table>{note}'
    )


def grouped_features(features, lang, stamp_html="", layout_opts=None):
    layout_opts = layout_opts or {}
    """Grouped layout v2 (ChatGPT review round 5, Oct 2026): one softly tinted rounded panel
    per category with a circular count badge + category name; groups with 2+ items become a
    row of white mini-cards (each with its own 01/02 numeral), a single-item group becomes a
    wide accented row. Numerals run continuously across groups so the card still echoes the
    other cards' 01/02/03 language."""
    groups = []
    for f in features:
        g = f.get("group") or ""
        if g not in [x[0] for x in groups]:
            groups.append((g, []))
        dict(groups)[g].append(f)
    accents = [BLUE, GREEN, RED]
    zh = lang == "zh"
    head_t = "font-size:13px;line-height:19px;font-weight:600;letter-spacing:0;" if zh else "font-size:13px;line-height:18px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;"
    mini_title_t = "font-size:16px;line-height:23px;font-weight:600;letter-spacing:0;" if zh else "font-size:17px;line-height:22px;font-weight:400;"
    mini_desc_t = "font-size:13px;line-height:20px;letter-spacing:0;" if zh else "font-size:13px;line-height:19px;"
    wide_title_t = "font-size:18px;line-height:26px;font-weight:600;letter-spacing:0;" if zh else "font-size:19px;line-height:25px;font-weight:400;"
    wide_desc_t = "font-size:14px;line-height:23px;letter-spacing:0;" if zh else "font-size:15px;line-height:22px;"
    out, counter = [], 0

    def header(accent, count, name, right_html=""):
        # Category shown as a filled tag (white text on the accent colour). No count digit —
        # a number in a circle read as another numeral next to 01/02/03 (team feedback).
        tag = (
            f'<span style="display:inline-block;padding:6px 12px;border-radius:6px;background:{accent};color:#FFFFFF;'
            f'font-family:{font(lang)};{head_t}">{esc(name)}</span>'
        )
        return (
            f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;border-collapse:collapse;"><tr>'
            f'<td valign="middle">{tag}</td>'
            + (f'<td align="right" valign="top">{right_html}</td>' if right_html else "") +
            f'</tr></table>'
        )

    row_title_t = "font-size:17px;line-height:26px;font-weight:600;letter-spacing:0;" if zh else "font-size:20px;line-height:27px;font-weight:400;"
    row_desc_t = "font-size:13px;line-height:20px;letter-spacing:0;" if zh else "font-size:14px;line-height:21px;"
    show_numerals = layout_opts.get("numerals", False)   # grouped cards: off by default (team, Oct 2026)

    def item_row(f, n, accent, first, last):
        # Title-first rows (team, round 8): no numerals, no description column — the category
        # tag + title carry the message. Marker = small accent-coloured check disc.
        pt = "2px" if first else "9px"
        pb = "0" if last else "9px"
        lead = (
            f'<td width="52" valign="top" style="width:52px;padding:{pt} 10px {pb} 0;font-family:{SERIF};font-size:27px;line-height:32px;color:{NUM_COLORS[(n-1) % len(NUM_COLORS)]};">{n:02d}</td>'
            if show_numerals else
            f'<td width="26" valign="top" style="width:26px;padding:{"6px" if first else "13px"} 8px {pb} 2px;">'
            f'<span style="display:inline-block;width:18px;height:18px;border-radius:999px;background:{accent};color:#FFFFFF;font-family:{SANS};font-size:11px;line-height:18px;text-align:center;">\u2713</span></td>'
        )
        title = f'<td valign="top" style="padding:{pt} 0 {pb} 0;font-family:{title_font(lang)};{row_title_t}color:{INK};">{nowrap_latin(f["name"], lang)}</td>'
        desc = ""
        if f.get("desc") and layout_opts.get("descriptions", False):
            desc = f'<td width="300" valign="top" style="width:300px;padding:{"5px" if first else "12px"} 0 {pb} 16px;font-family:{font(lang)};{row_desc_t}color:{MUTED};">{esc(f["desc"])}</td>'
        return f'<tr>{lead}{title}{desc}</tr>'

    for gi, (gname, items) in enumerate(groups):
        accent = accents[gi % len(accents)]
        top = "0" if gi == 0 else "14px"
        rows = []
        for i, f in enumerate(items):
            counter += 1
            rows.append(item_row(f, counter, accent, i == 0, i == len(items) - 1))
        body = (
            f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;border-collapse:collapse;margin-top:10px;">'
            f'{"".join(rows)}</table>'
        )
        accent_bar = f'<td width="4" bgcolor="{accent}" style="width:4px;background:{accent};font-size:0;line-height:0;">&nbsp;</td>'
        panel = (
            f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="{EXAMPLE_BG}" '
            f'style="width:100%;border-collapse:separate;border-spacing:0;background:{EXAMPLE_BG};border:1px solid {EXAMPLE_BORDER};border-radius:12px;overflow:hidden;">'
            f'<tr>{accent_bar}<td style="padding:14px 16px 16px 15px;">'
            f'{header(accent, len(items), gname, stamp_html if gi == 0 else "")}{body}'
            f'</td></tr></table>'
        )
        out.append(f'<tr><td style="padding:{top} 0 0;">{panel}</td></tr>')
    return "".join(out)


def buttons_block(buttons, lang):
    if not buttons:
        return ""
    cells = []
    for i, b in enumerate(buttons):
        label = b["label"][lang] if isinstance(b["label"], dict) else b["label"]
        primary = i == 0
        bg = BLUE if primary else BLUE_SOFT
        sh = BLUE_SHADOW if primary else BLUE_SOFT_SHADOW
        cells.append(
            f'<td style="padding:0 8px;">'
            f'<a class="button" href="{esc(b["url"])}" target="_blank" rel="noreferrer" '
            f'style="display:inline-block;height:48px;box-sizing:border-box;padding:14px 29px;border-radius:999px;background:{bg};box-shadow:0 4px 0 {sh};'
            f'color:#FFFFFF;font-family:{font(lang)};font-size:17px;line-height:20px;text-align:center;text-decoration:none;white-space:nowrap;">{esc(label)}</a></td>'
        )
    return (
        f'<table role="presentation" align="center" cellspacing="0" cellpadding="0" border="0" style="margin:34px auto 0;border-collapse:collapse;">'
        f'<tr>{"".join(cells)}</tr></table>'
    )


def header_block(copy, lang, show_header, audience_html, status_text, status_bg):
    if show_header:
        return (
            f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;border-collapse:collapse;"><tr>'
            f'<td valign="middle" style="padding:0 16px 0 0;">'
            f'<h1 style="margin:0;font-family:{title_font(lang)};{T(lang,"h1")}color:{INK};">{esc(copy["title"])}</h1>'
            f'<p style="margin:10px 0 0;font-family:{font(lang)};font-size:16px;line-height:24px;color:{MUTED};">{esc(copy.get("subtitle",""))}</p>'
            f'{audience_html}</td>'
            f'<td width="190" align="right" valign="top" style="width:190px;padding:6px 8px 0 0;">{stamp(status_text, status_bg, lang)}</td>'
            f'</tr></table>'
        )
    # banner carries the title: no header row — the stamp is placed inline with the first
    # feature / first group panel (team: too much whitespace above 01 otherwise)
    return ""


def product_card(product, lang, run_dir, embed):
    copy = product["copy"][lang]
    status = product.get("status", "live")
    status_text = copy.get("status_label") or t(lang, status)
    status_bg = "#0B8F5C" if status == "live" else BLUE
    b = product.get("banner") or {}
    has_banner = bool(resolve_img(run_dir, b.get("image"), False)) or bool(b.get("text_only"))
    # Rule (team, Oct 2026): when the banner already carries the headline, subtitle and
    # audience pills, don't repeat them as text in the card — keep only the status pill.
    show_header = product.get("show_header", not has_banner)
    audience = copy.get("audience")
    audience_html = ""
    if audience and show_header:
        audience_html = (
            f'<p style="margin:8px 0 0;font-family:{font(lang)};font-size:15px;line-height:22px;color:{BLUE};">'
            f'{esc(t(lang, "built_for"))}: {esc(audience)}</p>'
        )
    return f"""
<tr><td align="center" valign="top" style="padding:0 0 20px;background:{CANVAS};">
<!-- {esc(product['id'])} -->
<table class="newsletter-module" role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;border-collapse:collapse;background:{CANVAS};">
<tr><td align="center" style="padding:24px 14px;">
<table class="shell" role="presentation" width="840" cellspacing="0" cellpadding="0" border="0" style="width:840px;max-width:100%;border-collapse:separate;background:{CARD_BG};border:1px solid {CARD_BORDER};border-radius:23px;overflow:hidden;box-shadow:0 10px 28px rgba(16,45,92,.10);">
{banner_block(product, lang, run_dir, embed)}
<tr><td class="card-pad" style="padding:{'42px' if show_header else '28px'} 44px 40px;font-family:{font(lang)};background:{CARD_BG};">
  {header_block(copy, lang, show_header, audience_html, status_text, status_bg)}
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;border-collapse:collapse;margin-top:{'23px' if show_header else '0'};">
    {grouped_features(copy['features'], lang, '' if show_header else stamp(status_text, status_bg, lang), copy.get('layout_opts')) if copy.get('layout') == 'grouped' else feature_rows(copy['features'], lang, '' if show_header else stamp(status_text, status_bg, lang))}
  </table>
  {buttons_block(product.get('buttons'), lang)}
</td></tr>
</table>
</td></tr></table>
</td></tr>"""


def section_header(kicker, title, lang="en"):
    return f"""
<tr><td align="center" valign="top" style="padding:0 14px 16px;background:{CANVAS};">
<table class="shell" role="presentation" width="840" cellpadding="0" cellspacing="0" border="0" style="width:840px;max-width:100%;border-collapse:collapse;background:{CANVAS};border-top:1px solid {SECTION_RULE};border-bottom:1px solid {SECTION_RULE};">
<tr><td style="padding:34px 44px 32px;">
<p style="margin:0 0 12px;font-family:{SANS};font-size:17px;line-height:22px;color:{BLUE};letter-spacing:1px;">{esc(kicker)}</p>
<h2 style="margin:0;font-family:{title_font(lang)};font-size:{'38px' if lang == 'zh' else '42px'};line-height:50px;font-weight:{600 if lang == 'zh' else 400};letter-spacing:0;color:{INK_DEEP};">{esc(title)}</h2>
</td></tr></table></td></tr>"""


def hero_block(edition, lang, run_dir, embed):
    src = resolve_img(run_dir, edition.get("hero_banner"), embed)
    if src:
        img = (
            f'<tr><td style="padding:0;"><img src="{esc(src)}" width="840" alt="{esc(edition.get("title", "Data Infra What\'s New"))}" '
            f'style="display:block;width:840px;max-width:100%;height:auto;border:0;"></td></tr>'
        )
    else:
        img = (
            f'<tr><td style="padding:48px 44px;background:#E9EEF7;font-family:{SERIF};font-size:40px;line-height:46px;color:{INK_DEEP};">'
            f'{esc(edition.get("title", "Data Infra What\'s New"))}'
            f'<p style="margin:8px 0 0;font-family:{SANS};font-size:13px;letter-spacing:1.5px;color:{BLUE};">HERO BANNER PLACEHOLDER · pending Grok</p></td></tr>'
        )
    intro = edition["intro"][lang]
    paras = []
    for i, p in enumerate(intro):
        strong = i < len(intro) - 1  # greeting lines bold, body paragraph regular
        style = f"margin:0 0 {'4px' if i == 0 else '12px'};color:{INK};" if strong else "margin:0;"
        text = f"<strong>{esc(p)}</strong>" if strong else highlight_tags(p)
        paras.append(f'<p style="{style}">{text}</p>')
    return f"""
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;border-collapse:collapse;background:{CANVAS};">
<tr><td align="center" valign="top" style="padding:24px 14px 32px;background:{CANVAS};">
<table class="hero-welcome-card" role="presentation" width="840" cellpadding="0" cellspacing="0" border="0" style="width:840px;max-width:100%;border-collapse:separate;border-spacing:0;border:1px solid {CARD_BORDER};border-radius:22px;background:{CARD_BG};box-shadow:0 8px 24px rgba(33,91,170,.10);overflow:hidden;">
{img}
<tr><td style="padding:36px 44px 38px;background:{CARD_BG};font-family:{font(lang)};font-size:{'16px' if lang == 'zh' else '18px'};line-height:28px;letter-spacing:0;color:{MUTED};text-align:left;">
{''.join(paras)}
</td></tr></table></td></tr></table>"""


def highlight_tags(text):
    """Render #Hashtags in the intro paragraph in brand blue, everything else escaped."""
    # Hashtags may be followed by ASCII or full-width punctuation (：，。) with no space in ZH.
    return re.sub(r"(#[A-Za-z0-9_]+)", lambda m: f'<strong style="color:{BLUE};">{m.group(1)}</strong>', esc(text))


def closing_block(edition, lang):
    edition_label = edition["edition_label"][lang]
    return f"""
<table class="newsletter-module-closing" role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;border-collapse:collapse;background:{CANVAS};">
<tr><td align="center" valign="top" style="padding:0 14px 32px;background:{CANVAS};">
<table class="shell" role="presentation" width="840" cellpadding="0" cellspacing="0" border="0" style="width:840px;max-width:100%;border-collapse:separate;border-spacing:0;background:{CLOSING_BG};border:1px solid {CLOSING_BORDER};border-radius:24px;box-shadow:0 10px 28px rgba(16,45,92,.12);overflow:hidden;">
<tr><td style="padding:42px 44px 38px;font-family:{font(lang)};background:{CLOSING_BG};color:{INK_DEEP};">
<p style="margin:0 0 24px;font-size:29px;line-height:36px;font-weight:700;color:{INK_DEEP};">{esc(t(lang,'closing_title'))}</p>
<p style="margin:0;max-width:650px;font-size:19px;line-height:29px;color:{MUTED};">{esc(t(lang,'closing_body'))}</p>
<p style="margin:44px 0 7px;font-size:16px;line-height:21px;font-weight:700;letter-spacing:1.5px;color:{BLUE};">{esc(t(lang,'regards'))}</p>
<p style="margin:0;font-size:28px;line-height:34px;font-weight:700;color:{INK_DEEP};">{esc(t(lang,'team'))}</p>
<div style="height:1px;margin:42px 0 0;background:#D9E6F7;line-height:1px;font-size:1px;">&nbsp;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;border-collapse:collapse;margin-top:26px;">
<tr><td valign="top" style="font-size:16px;line-height:22px;font-weight:700;letter-spacing:1.5px;color:{BLUE};">{esc(t(lang,'internal'))}</td>
<td align="right" valign="top" style="font-size:16px;line-height:22px;color:{MUTED};">{esc(t(lang,'footer',edition=edition_label))}</td></tr>
</table></td></tr></table></td></tr></table>"""


def apply_theme(theme):
    """Per-edition palette override (edition.theme in products.json). Only the keys given change."""
    global CANVAS, CARD_BG, INK, INK_DEEP, MUTED, BLUE, RULE, CARD_BORDER, SECTION_RULE, CLOSING_BG, CLOSING_BORDER, CHIP_BG, CHIP_BORDER, CHIP_INK
    for k, v in (theme or {}).items():
        if k.upper() in globals():
            globals()[k.upper()] = v


def build(data, lang, run_dir, embed):
    edition = data["edition"]
    apply_theme(edition.get("theme"))
    products = [p for p in data["products"] if not p.get("skip")]
    live = [p for p in products if p.get("status", "live") == "live"]
    coming = [p for p in products if p.get("status") == "coming"]
    preview = edition.get("preheader", {}).get(lang, "")

    body = [hero_block(edition, lang, run_dir, embed)]
    body.append(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;border-collapse:collapse;background:{CANVAS};">')
    if live:
        body.append(section_header(t(lang, "latest_kicker"), t(lang, "latest_title", month=edition.get("release_month", {}).get(lang, "")).replace("  ", " "), lang))
        body.extend(product_card(p, lang, run_dir, embed) for p in live)
    if coming:
        body.append(section_header(t(lang, "next_kicker"), t(lang, "next_title", month=edition["next_month"][lang]), lang))
        body.extend(product_card(p, lang, run_dir, embed) for p in coming)
    body.append("</table>")
    body.append(closing_block(edition, lang))

    return f"""<!DOCTYPE html>
<html lang="{t(lang,'html_lang')}" xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="x-apple-disable-message-reformatting">
<title>{esc(edition.get('title','Data Infra What\'s New'))} · {esc(edition['edition_label'][lang])}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Gloock&family=Marmelad&family=Noto+Sans+SC:wght@400;700&display=swap');
html,body{{margin:0;padding:0;background:{CANVAS};}}
img{{border:0;outline:none;text-decoration:none;}}
@media only screen and (max-width:840px){{ .shell,.hero-welcome-card{{width:100% !important;max-width:100% !important;}} .card-pad{{padding:28px 20px 28px !important;}} }}
</style>
</head>
<body style="margin:0;padding:0;background:{CANVAS};-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{esc(preview)}</div>
{''.join(body)}
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--lang", default="all", choices=["en", "zh", "all"])
    ap.add_argument("--out", default=None, help="output dir (default: <run_dir>/out)")
    ap.add_argument("--embed-images", action="store_true", help="inline local images as base64 (for preview / self-contained file)")
    args = ap.parse_args()

    run_dir = os.path.abspath(args.run_dir)
    with open(os.path.join(run_dir, "products.json"), encoding="utf-8") as f:
        data = json.load(f)
    out_dir = args.out or os.path.join(run_dir, "out")
    os.makedirs(out_dir, exist_ok=True)
    month = data["edition"]["month"]
    langs = ["en", "zh"] if args.lang == "all" else [args.lang]
    for lang in langs:
        path = os.path.join(out_dir, f"newsletter_{month}_{lang}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(build(data, lang, run_dir, args.embed_images))
        print(path)


if __name__ == "__main__":
    sys.exit(main())
