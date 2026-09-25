#!/usr/bin/env python3
"""Render newsletter HTML to PNG screenshots for review in chat.

Usage:
    python render_preview.py <html_file> [--out <dir>] [--card <product_id>]

Without --card: writes full-page screenshot split into ~1600px tall slices
(preview_<lang>_0.png, _1.png, ...). With --card: screenshots only the card whose
HTML comment marker is <!-- product_id -->, useful for reviewing one product.
Requires playwright + chromium (present in the Claude sandbox).
"""
import argparse
import os
import sys

from playwright.sync_api import sync_playwright

SLICE = 1600
WIDTH = 900


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html_file")
    ap.add_argument("--out", default=None)
    ap.add_argument("--card", default=None, help="product id to crop to")
    args = ap.parse_args()

    src = os.path.abspath(args.html_file)
    out = args.out or os.path.dirname(src)
    os.makedirs(out, exist_ok=True)
    stem = os.path.splitext(os.path.basename(src))[0]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": WIDTH, "height": 1200})
        page.goto(f"file://{src}", wait_until="load", timeout=60000)
        page.wait_for_timeout(800)  # let web fonts settle
        if args.card:
            # find the table that follows the marker comment
            box = page.evaluate(
                """(pid) => {
                    const it = document.createNodeIterator(document.body, NodeFilter.SHOW_COMMENT);
                    let n; while ((n = it.nextNode())) {
                        if (n.nodeValue.trim() === pid) {
                            const tbl = n.nextElementSibling; const r = tbl.getBoundingClientRect();
                            return {x:r.left, y:r.top+window.scrollY, width:r.width, height:r.height};
                        }
                    } return null; }""",
                args.card,
            )
            if not box:
                print(f"card {args.card} not found", file=sys.stderr)
                return 1
            path = os.path.join(out, f"{stem}_{args.card}.png")
            page.screenshot(path=path, clip=box, full_page=True)
            print(path)
        else:
            h = page.evaluate("document.body.scrollHeight")
            for i, y in enumerate(range(0, h, SLICE)):
                path = os.path.join(out, f"{stem}_{i}.png")
                page.screenshot(path=path, clip={"x": 0, "y": y, "width": WIDTH, "height": min(SLICE, h - y)}, full_page=True)
                print(path)
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
