# Website / AgentBench alignment — 2026-10-11

The comparison uses the local Agent-bench working tree, including its existing
uncommitted changes. Exact source hashes are recorded in `data/benchmark.json`.
The site retains its Embodied Playground visual identity and identifies AgentBench
as the environment inventory.

| Area | Previous mismatch | Aligned behavior |
| --- | --- | --- |
| Inventory | Legacy 15-card selection, 40 Hanoi headline, duplicate Marble/Birds concepts | 410 exact IDs in 12 catalog groups; 120 Hanoi entries across three embodiments |
| Added tasks | Missing ManiSkill; Sharpa lock treated as future; bookshelf was a feature-branch candidate with the wrong robot | 30 ManiSkill tasks, 60 Kongming entries (30 per embodiment), 20 dual-Panda bookshelf variants |
| Scope | Appliance micro-skills and planned desk organization mixed with benchmark tasks | Current 410-entry scope only; development examples excluded |
| Status | Scene previews and partial checks called validated | Full engineering qualification explicitly pending; no missing checks treated as passes |
| Permissions | L1–L4 and observation/tool access conflated | Current L0–L3 definition, explicit grants and installed tools; privileged access is read-only |
| Protocol | Old four-trial-v1 results, 408 episodes and model token budget treated as current | environment-four-trial-v2: 510 groups / 2040 planned episodes; fixed denominator and partial/invalid rules |
| Results | Ambiguous 5/5 Hanoi headline and old model scores | Historical JSON preserved in archive; current result set empty as required by current environment scope |
| Media | Historical recordings implied current benchmark evidence | Existing provenance retained, recordings explicitly historical; unsupported/out-of-scope placeholders removed |
| Links | Older external-agent workflow and static catalogs | Current evaluation protocol, per-family contracts and a downloadable 410-entry public catalog |
| Build | `npm run build` replaced the homepage with an old outline; checks prohibited the site's JavaScript | Static-site validation is the build; optional outlines write to outline.html |
| Runtime failure | Stale hard-coded scores and tasks reappeared after failed JSON fetches | Visible load error, no historical fallback |
| Source documentation | Three evaluation protocol documents specified 20,400 Hanoi/pocket controls | Corrected to 18,000, matching the runtime and generated per-task budgets |

The synchronization command validates the source export's hashes and compares all
website-generated data. The portable checker verifies unique IDs, counts, groups,
budgets, links, media files, scope and absence of stale fallback results. Browser
checks cover rendering and task filters. These are website/data checks; no robot
simulation, full condition matrix, agent evaluation or deployment is performed.

Verification completed: portable site check and source synchronization check passed;
the source protocol export passed `--check`; two focused protocol tests passed.
Browser checks confirmed all six category totals, 10 ALOHA cube entries, empty
Bookshelf + ALOHA results, restoration to 410 entries, no console errors and no
horizontal overflow at the browser’s 1280-pixel viewport.
