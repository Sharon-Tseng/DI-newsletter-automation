#!/usr/bin/env python3
"""Bake banner text into the image so it survives every mail client.

Colleague-built cards overlay title/subtitle/tags on scene-only banners with CSS
position:absolute — Gmail/Outlook strip that and the words vanish. This script renders the
same elements with PIL at the CSS sizes (scaled from the 840px display width to the image's
pixel width) and writes a new JPG; the HTML then just shows the image.

Usage:
    python bake_banner_text.py spec.json
spec.json:
{
  "src": "banners/ram_banner.jpg", "out": "banners/ram_banner_text.jpg",
  "display_width": 840,
  "copy_width_pct": 0.66, "padding": [24, 32],        # CSS .hero-copy width + padding (px @840)
  "elements": [                                        # top→bottom, vertically centred as a block
    {"type": "title", "text": "RAM", "size": 48, "color": "#103C77", "font": "gloock", "tracking": -1.1},
    {"type": "subtitle", "text": "HDFS Alert Improvements", "size": 26, "color": "#153B42", "font": "marmelad", "bold": true, "gap_before": 9},
    {"type": "tags", "items": ["HDFS alert", "Seatalk Bot Messages"], "size": 16, "color": "#164A94",
     "bg": [255,255,255,242], "border": [29,79,153,71], "pad": [7,10], "radius": 7, "gap": 7, "gap_before": 13},
    {"type": "cards", "items": ["…"], "cols": 2, "size": 14, "color": "#1F513C", "min_height": 56, "pad": [8,11], "gap": 8},
    {"type": "stamp", "text": "NOW LIVE", "size": 14, "color": "#0B8F5C", "inline_with_title": true}
  ]
}
Fonts: skill/assets/fonts/Gloock-Regular.ttf, Marmelad-Regular.ttf (Marmelad has no bold —
"bold" is faked with a stroke).
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = {
    "gloock": os.path.join(HERE, "..", "assets", "fonts", "Gloock-Regular.ttf"),
    "marmelad": os.path.join(HERE, "..", "assets", "fonts", "Marmelad-Regular.ttf"),
}


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def font(name, px):
    return ImageFont.truetype(FONTS[name], int(round(px)))


def text_w(draw, s, f, tracking=0):
    return draw.textlength(s, font=f) + tracking * max(len(s) - 1, 0)


def draw_text(draw, xy, s, f, fill, tracking=0, stroke=0):
    x, y = xy
    if tracking:
        for ch in s:
            draw.text((x, y), ch, font=f, fill=fill, stroke_width=stroke, stroke_fill=fill)
            x += draw.textlength(ch, font=f) + tracking
    else:
        draw.text((x, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=fill)


def wrap(draw, s, f, max_w):
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=f) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def main(spec_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(spec_path))
    im = Image.open(os.path.join(base, spec["src"])).convert("RGBA")
    W, H = im.size
    S = W / spec.get("display_width", 840)           # CSS px → image px
    pad_y, pad_x = [p * S for p in spec.get("padding", [24, 32])]
    copy_w = W * spec.get("copy_width_pct", 0.68) - 2 * pad_x
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    # ---- measure pass: build a list of (height, render_fn)
    blocks = []
    stamp = None
    for el in spec["elements"]:
        t = el["type"]
        if t == "stamp":
            stamp = el
            continue
        gap = el.get("gap_before", 0) * S
        if t in ("title", "subtitle"):
            f = font(el.get("font", "gloock" if t == "title" else "marmelad"), el["size"] * S)
            tracking = el.get("tracking", 0) * S
            lh = el.get("line_height", el["size"] * (1.08 if t == "title" else 1.2)) * S
            lines = wrap(d, el["text"], f, copy_w) if el.get("wrap", True) else [el["text"]]
            stroke = int(round(0.6 * S)) if el.get("bold") else 0
            h = lh * len(lines)

            def render(y, el=el, f=f, lines=lines, lh=lh, tracking=tracking, stroke=stroke):
                fill = hex_rgb(el["color"])
                for i, ln in enumerate(lines):
                    draw_text(d, (pad_x, y + i * lh), ln, f, fill, tracking, stroke)
                    if i == 0 and el.get("_stamp"):
                        st = el["_stamp"]
                        sf = font("marmelad", st["size"] * S)
                        tw = text_w(d, st["text"], sf, st.get("tracking", 2) * S)
                        bw = tw + 2 * st.get("pad_x", 10) * S
                        bh = st["size"] * S * 1.3 + 2 * st.get("pad_y", 6) * S
                        x0 = pad_x + text_w(d, ln, f, tracking) + 16 * S
                        y0 = y + (lh - bh) / 2
                        col = hex_rgb(st["color"])
                        d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=6 * S, fill=(255, 255, 255, 178), outline=col, width=int(3 * S))
                        d.rounded_rectangle([x0 + 4 * S, y0 + 4 * S, x0 + bw - 4 * S, y0 + bh - 4 * S], radius=4 * S, outline=col, width=int(1.2 * S))
                        draw_text(d, (x0 + st.get("pad_x", 10) * S, y0 + (bh - st["size"] * S * 1.15) / 2), st["text"], sf, col, st.get("tracking", 2) * S, int(round(0.5 * S)))
            blocks.append((gap, h, render))
        elif t == "tags":
            f = font("marmelad", el["size"] * S)
            px, py = [p * S for p in el.get("pad", [7, 10])][::-1] if False else (el.get("pad", [7, 10])[1] * S, el.get("pad", [7, 10])[0] * S)
            gapx = el.get("gap", 7) * S
            th = el["size"] * S * 1.25 + 2 * py
            # flow into rows within copy_w
            rows, cur, cur_w = [], [], 0
            for it in el["items"]:
                w = text_w(d, it, f) + 2 * px
                if cur and cur_w + gapx + w > copy_w:
                    rows.append(cur); cur, cur_w = [], 0
                cur.append((it, w)); cur_w += (gapx if len(cur) > 1 else 0) + w
            if cur:
                rows.append(cur)
            h = th * len(rows) + gapx * (len(rows) - 1)

            def render(y, el=el, f=f, rows=rows, th=th, px=px, py=py, gapx=gapx):
                col = hex_rgb(el["color"])
                for r in rows:
                    x = pad_x
                    for it, w in r:
                        d.rounded_rectangle([x, y, x + w, y + th], radius=el.get("radius", 7) * S,
                                            fill=tuple(el.get("bg", [255, 255, 255, 242])), outline=tuple(el.get("border", [29, 79, 153, 71])), width=max(1, int(S)))
                        draw_text(d, (x + px, y + py - 0.05 * el["size"] * S), it, f, col, 0, int(round(0.5 * S)))
                        x += w + gapx
                    y += th + gapx
            blocks.append((gap, h, render))
        elif t == "cards":
            f = font("marmelad", el["size"] * S)
            cols = el.get("cols", 2)
            gapx = el.get("gap", 8) * S
            cw = (copy_w - gapx * (cols - 1)) / cols
            px, py = el.get("pad", [8, 11])[1] * S, el.get("pad", [8, 11])[0] * S
            lh = el["size"] * S * 1.35
            cells = []
            for it in el["items"]:
                lines = wrap(d, it, f, cw - 2 * px)
                cells.append((lines, max(el.get("min_height", 56) * S, lh * len(lines) + 2 * py)))
            rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
            row_h = [max(c[1] for c in r) for r in rows]
            h = sum(row_h) + gapx * (len(rows) - 1)

            def render(y, el=el, f=f, rows=rows, row_h=row_h, cw=cw, px=px, py=py, gapx=gapx, lh=lh):
                col = hex_rgb(el["color"])
                for r, rh in zip(rows, row_h):
                    x = pad_x
                    for lines, _ in r:
                        d.rounded_rectangle([x, y, x + cw, y + rh], radius=7 * S, fill=(255, 255, 255, 242), outline=(29, 79, 153, 71), width=max(1, int(S)))
                        ty = y + (rh - lh * len(lines)) / 2
                        for i, ln in enumerate(lines):
                            draw_text(d, (x + px, ty + i * lh), ln, f, col, 0, int(round(0.5 * S)))
                        x += cw + gapx
                    y += rh + gapx
            blocks.append((gap, h, render))
    if stamp and stamp.get("inline_with_title"):
        for el in spec["elements"]:
            if el["type"] == "title":
                el["_stamp"] = stamp
                break

    total = sum(g + h for g, h in [(b[0], b[1]) for b in blocks])
    y = (H - total) / 2 + spec.get("y_offset", 0) * S
    for gap, h, render in blocks:
        y += gap
        render(y)
        y += h

    out = Image.alpha_composite(im, overlay).convert("RGB")
    out_path = os.path.join(base, spec["out"])
    out.save(out_path, quality=90, optimize=True)
    print(out_path, out.size)


if __name__ == "__main__":
    main(sys.argv[1])
