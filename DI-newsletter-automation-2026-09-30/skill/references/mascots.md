# Mascot library

Reference images live in `assets/mascots/`. Every banner prompt must paste the product's
**identity block** verbatim and attach the reference image in Grok. Pose, expression,
props and background may change per edition; nothing in the identity block may.

The rule the team gave: 吉祥物的主觀特徵都不可以有任何變動，動作可以改變.
When Grok drifts (different hair colour, no glasses, changed outfit colour, extra
accessories), reject the image and regenerate — do not "accept because it's close".

| Product | Mascot key | File |
|---|---|---|
| Diana | `diana_dgc_girl` | `diana_dgc_girl.png` |
| DGC Agent (Data Governance Center) | `diana_dgc_girl` | `diana_dgc_girl.png` |
| Data Studio / Studio Agent | `datastudio` | `datastudio.png` |
| Langfuse | `langfuse_octopus` | `langfuse_octopus.jpg` |
| Data Hub / DataHub Agent | `datahub_robot` | `datahub_robot.png` |
| DI CLI | `cli_boy` | `cli_boy.png` |
| Scheduler Agent, RAM, OneBI | — | **no mascot yet** — ask the user for a reference image before Stage 3; use a mascot-free banner only if they say so |

## Identity blocks (paste verbatim into prompts)

### diana_dgc_girl — Diana / DGC Agent
```
A friendly 3D-rendered Pixar-style young woman with a short, chin-length bob of vivid royal-blue hair,
round thin-rimmed silver glasses, large warm brown eyes, light skin with soft pink cheeks, and a gentle
smile. She wears a plain light-blue long-sleeve crew-neck top. Soft studio lighting, smooth clean
render, same character design as the reference image. Keep hair colour, glasses, eyes and outfit
exactly as in the reference.
```
Notes: Diana = knowledge/assistant persona, so props that fit are documents, chat bubbles, a
tablet, floating knowledge cards. For DGC Agent she is the same character; props shift to
governance imagery (shield, checklist, lineage graph, magnifier over data assets).

### datastudio — Data Studio / Studio Agent
```
The same 3D Pixar-style young woman as Diana (short royal-blue bob, round thin silver glasses, warm
brown eyes, light-blue long-sleeve top) now wearing a glossy yellow hard hat and dark-navy denim
overalls with white work gloves, holding a magnifying glass over a small data table. Keep face,
hair, glasses and colours identical to the reference image.
```
Notes: she is the "engineer" variant of the Diana character. Do not remove the hard hat or
overalls — that is what distinguishes Data Studio from Diana.

### langfuse_octopus — Langfuse
```
A flat-vector cartoon octopus with a dark charcoal-navy body, big round white eyes with black pupils
and confident slanted brows, small smiling mouth. Its eight tentacles are dark on top with the
undersides alternating vivid red and cobalt blue, and they hold developer-tool props: a magnifying
glass, a terminal window, a metrics card, a code snippet card, a latency badge, small colourful cubes.
Clean flat illustration style with a white or very light background, same character as the
reference image.
```
Notes: props are what makes it "observability" — keep at least a trace/metrics card and a
terminal. Never change the red/blue tentacle undersides or make the body a different colour.

### datahub_robot — Data Hub / DataHub Agent
```
A heroic chunky mecha-style robot in glossy white and bright orange armour with dark gunmetal joints,
glowing amber eyes in a visor-like helmet, a hexagon emblem on its chest plate, oversized fists and
boots. Dynamic action pose, 3D game-art render with orange hexagonal geometric shapes in the
background, same design as the reference image.
```
Notes: energetic poses work well (pointing forward, charging, lifting). Keep the white/orange
palette and the chest hexagon.

### cli_boy — DI CLI
```
A chibi anime-style boy with messy chestnut-brown hair, big brown eyes, wearing an orange
headband printed with the letters "DI CLI" tied at the side, and a navy-blue hoodie. Sticker-like
illustration with a thick white outline, energetic expression, same character as the reference
image.
```
Notes: the "DI CLI" headband text is part of the identity — check it is spelled correctly in
every generation. In the September edition he appears with a large golden bull/ox companion
that also wears a "DI CLI" headband; the bull is optional but if used must keep that headband.

## Combined hero banner (edition cover)
The edition hero shows several mascots together in one bright outdoor scene (blue sky, green
field, sparkles) with the title "Data Infra What's New" and a pill subtitle
"Newsletter <Mon YYYY> Release". Include only the mascots of products that appear in this
edition. Each mascot gets its own identity block in the prompt.
