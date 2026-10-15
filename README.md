# Embodied Playground / AgentBench website

A dependency-free static website for the AgentBench environment scope. Benchmark
code, environments and evaluation contracts live in
[Agent-bench](https://github.com/Winniechen2002/Agent-bench). This repository contains
the website, a portable public metadata snapshot and selected historical previews.

## Preview and check

```bash
python3 -m http.server 4174 --bind 127.0.0.1
```

Open [the local preview](http://127.0.0.1:4174/). Serve over HTTP so the page can
load JSON. `npm run dev` and `npm start` run the same command when Node is installed.

```bash
python3 scripts/check_site.py          # npm run check / npm run build
python3 scripts/sync_benchmark.py ../Agent-bench --check  # npm run check:sync
```

Build validates the existing static site; it never overwrites the homepage.
There are no runtime package dependencies. The portable check does not require
a sibling checkout; the synchronization check does.

## Source of truth and updates

The current scope is **410 task entries**, **510 evaluation groups** and **2040
planned episodes** per base seed and fixed access/observation combination. These
are schedule counts, not completed evaluations. The protocol is
`environment-four-trial-v2`; permissions are `2026-10-09-environment-l0-l3`.
Full engineering qualification remains incomplete and release readiness is false.

```bash
python3 scripts/sync_benchmark.py ../Agent-bench
python3 scripts/sync_media.py ../Agent-bench
```

This standard-library-only importer reads the benchmark's generated
`docs/evaluation/tasks.json`, verifies its source hashes, checks counts against
`environment_catalog.py`, and writes:

- `data/tasks.json`: 12 catalog groups with exact task IDs and embodiment counts.
- `data/environment-catalog.json`: all 410 IDs, public budgets and group names.
- `data/benchmark.json`: versions, scope, qualification state and source hashes.
- `data/results.json`: an explicitly empty current-protocol result set.

The snapshot includes the source working tree, including uncommitted changes;
it is not a claim that those changes are already available on GitHub. If the
source export is stale, regenerate it in Agent-bench using its configured Python
runtime and `scripts/export_evaluation_protocol.py`, then sync again. Never
silently fall back to an older catalog or model score after a failed fetch.

## Historical material

`data/media.json` supplies scene previews and historical reference/calibration
clips. Videos are explicitly outside the current four-trial results and do not
establish full engineering qualification. Original videos/trajectories remain in
their experiment locations; `evidence/demo-manifest.json` retains their provenance.

All 12 catalog groups now have media. Eight additions are selected in Agent-bench's
`docs/website_media_catalog.json`: Angry Birds scene/recordings, floating Sharpa
Hanoi, a native bookshelf render, and three ManiSkill contact sheets covering 30 tasks.
`sync_media.py` copies original bytes and records provenance in
`data/media-sources.json`; `--check` verifies source and destination hashes. The bookshelf cover is a 1600 × 1000 native Isaac Sim RTX render of
ShelfTableD3 (seed 7), produced by `scripts/render_bookshelf_preview.py` in
Agent-bench. It shows the initial scene after neutral hold controls; no policy
success is claimed. The layout schematic stays in repository documentation; a rollout is still missing. See [the media inventory](docs/media-inventory.md).

The homepage cover features A099, a two-target Angry Birds bank-shot corridor,
with its matching native poster and historical reference recording.

The gallery supports per-task filtering, task-card navigation, full-image links,
and user-controlled video playback. Captions stay below images rather than
covering scene details. `npm run sync` runs both metadata and media importers;
`npm run check:sync` checks both.

The previous task metadata and model scores are preserved in
`archive/pre-alignment-20261011/`. The old 200-task `data/catalog.json`,
`data/evidence.json`, `data/source-manifest.json`, `app.js` and their atlas images
belong to an earlier site version and are not loaded by the current homepage.
`scripts/import_sources.py` only refreshes that historical atlas.

`docs/website-outline.md`, `docs/technical-report.md`, and `report.html` are
historical planning documents. `npm run build:outlines` generates `outline.html`
and `report.html`; it cannot overwrite `index.html`. This optional legacy renderer
requires the packages in `requirements-report.txt`.

## Hosting

Serve this directory as a static site. Relative asset paths support a GitHub
Pages project subpath and `.nojekyll` preserves static files. This alignment does
not configure hosting, push commits or publish a deployment.

See [the alignment notes](docs/alignment-audit.md) for the corrected differences
and verification scope.
