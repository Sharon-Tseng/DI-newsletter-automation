# products.json schema

One file per edition at `runs/<YYYY-MM>/products.json`. It is the single source of truth across
the four stages: Stage 1 fills the skeleton from `products_raw.json`, Stage 2 fills `copy`,
Stage 3 fills `banner.image`, Stage 4 reads everything. Editing this file and re-running
`build_newsletter.py` is how every change is made — never hand-edit the HTML output.

```jsonc
{
  "edition": {
    "month": "2026-10",                       // used in output filenames
    "edition_no": 3,
    "title": "Data Infra What's New",
    "edition_label": { "en": "October 2026 Edition", "zh": "2026 年 10 月號" },
    "release_month": { "en": "September", "zh": "9 月" },   // "<Month> Product Updates" section title
    "next_month":    { "en": "November", "zh": "11 月" },   // for the "Coming in …" header
    "theme": { "canvas": "#F2F5EF", "card_border": "#D3E2CC", "ink_deep": "#1F3A2E" },  // optional per-edition palette
    "preheader":     { "en": "…", "zh": "…" },              // hidden email preview line
    "hero_banner": "banners/hero.jpg",         // run-relative path or URL; null → placeholder
    "intro": {                                 // paragraphs; all but the last are bold greeting lines
      "en": ["Dear colleagues,", "Welcome to the third edition …", "This month … #BuildFaster …"],
      "zh": ["各位同事好，", "歡迎閱讀第三期 …", "本月 … #BuildFaster …"]
    }
  },
  "products": [
    {
      "id": "langfuse",                        // canonical id, also the HTML comment marker
      "name": "Langfuse",
      "mascot": "langfuse_octopus",            // key in references/mascots.md, or null
      "status": "live",                        // "live" | "coming"
      "skip": false,                           // true → omitted from output (kept for the record)
      "show_header": false,                    // optional; default = no banner. Title/subtitle/audience hide when a banner exists
      "source_rows": [5, 6, 7, 8],
      "release_note": "Released in September",
      "copy": {
        "en": {
          "title": "…", "subtitle": "…",
          "audience": null,                    // string only for non-default audiences
          "layout": "numbered",                // or "grouped": tinted panel per feature.group, titles only
          "layout_opts": { "numerals": false, "descriptions": false },   // grouped only; defaults shown
          "status_label": null,                // override the NOW LIVE / COMING SOON pill text
          "features": [
            { "name": "…", "tag": "For CLI & script users",   // optional kicker: who this is for (omit when layout is grouped)
              "group": "HDFS alerts",          // required when layout is "grouped"
              "desc": "…",
              "bullets": ["…"],                // optional
              "bullets_style": "chips",        // optional: ≤5 short items render as a chip row instead of a list
              "bullets_label": "Improvements include:",   // optional small grey lead-in line above the bullets/chips
              "visual": {                      // optional; type "checks", "steps", "flow" or "before_after"
                "type": "steps", "style": "timeline",   // default; "boxes" for the older bordered cards
                "steps": [ { "label": "Detect pending work", "caption": "…" }, { "label": "…", "caption": "…" } ],
                "footnote": "Pending items include Experiments, Evals, and Exports.",   // small grey line under the cards
                "note": "Unaffected projects are never interrupted." },                 // ✓ line
              "visual_checks_example": {
                "type": "checks", "items": ["Faster reads", "Consistent with the V4 single-table model"] },
              "visual_flow_example": {
                "type": "flow", "nodes": ["di-cli reads", "V4 event aggregation"],
                "retired": "Postgres trace_sessions table", "retired_note": "no longer a dependency" },
              "visual_alt": {                  // before_after shape, for concrete value comparisons
                "type": "before_after",
                "before": { "label": "BEFORE", "items": ["SDK","API","MCP","di-cli"], "caption": "…" },
                "after":  { "label": "NOW", "badge": "Recommended", "items": ["DI-CLI","MCP","SDK","API"],
                            "highlight": "DI-CLI", "caption": "…" } },
              "example": "…", "example_label": "Try asking" }   // optional
          ]
        },
        "zh": { /* same shape */ }
      },
      "banner": {
        "headline": "Langfuse Gets Faster", "subheadline": "…", "highlight": "…",
        "audience_tags": [],                   // pills on the banner; empty when audience is default
        "pose": "…",                           // this edition's mascot action
        "prompt": "…",                         // final prompt sent to Grok
        "image": "banners/langfuse.jpg",       // null until approved
        "approved": false,
        "attempts": [ { "prompt": "…", "verdict": "user: robot too small" } ]
      },
      "buttons": [                             // 1–3; first is primary blue
        { "label": { "en": "Open Langfuse ↗", "zh": "開啟 Langfuse ↗" }, "url": "https://langfuse.shopee.io/" }
      ]
    }
  ]
}
```

Button label conventions: `Open <Product> ↗` / `開啟 <Product> ↗`, `User Guide ↗` / `使用指南 ↗`,
`Try <Agent> ↗` / `試用 <Agent> ↗`, `Give us Feedback!` / `給我們回饋！`, `<X> Community ↗` /
`<X> 社群 ↗`.
