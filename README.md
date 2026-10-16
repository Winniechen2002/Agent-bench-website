# Embodied Playground

**Agentic Robotics Benchmark on Physics, Strategic and Spatial Reasoning**

Standalone light website for [Embodied Playground](https://github.com/Winniechen2002/Embodied-Playgroud). It uses static HTML, CSS, and vanilla JavaScript with relative URLs suitable for a GitHub Pages project subpath. [Website repository](https://github.com/Winniechen2002/Agent-bench-website).

## Preview and validate

From this directory:

```sh
npm run dev
```

Open [the local preview](http://127.0.0.1:4174/). This first builds `dist/`, then serves only its reviewed files on IPv4 loopback. The same preview supports `/Agent-bench-website/`. Do not serve or upload the repository root: `.gitignore` does not restrict HTTP access. JSON loading is not designed for `file://` URLs.

```sh
npm run check
npm run build
node --check site.js
node --check environment.js
```

`npm run check` validates public data, page/data consistency, and isolation regression tests. `npm run build` recreates `dist/` from an explicit allowlist and validates both source and output. Only current pages, approved JSON, and referenced web assets are copied. Git metadata, source scripts, README, archives, unknown files, and symlinks are excluded or rejected. Python 3.10+ and Node/npm are used; there are no third-party runtime packages.

## Repository layout

| Path | Purpose |
| --- | --- |
| `index.html`, `site.css`, `site.js` | Paper narrative, EP-100 results, and demonstrations |
| `environment.html`, `environment.css`, `environment.js` | Compact, filterable directory of all 410 environments |
| `assets/` | Web videos, posters, scene images, fallbacks, and favicon |
| `data/` | Paper results and membership, native catalog, and media metadata |
| `evidence/demo-manifest.json` | Public artifact IDs, hashes, conditions, and replay limitations |
| `scripts/` | Validation, public-data projection, import, build, and isolated preview tools |
| `.github/workflows/pages.yml` | Manual deployment of the audited `dist/` artifact |
| `dist/` (ignored) | Rebuilt release directory; the only upload/preview root |
| `.nojekyll` | Static GitHub Pages serving |

The paper presents 100 tasks in 16 task types and five suites. `data/tasks.json` drives those task cards; `data/ep100-index.json` records exact membership, Easy/Hard splits, EP-20 inclusion, and per-task results. `data/results.json` contains versioned experiments; headline Pass@1 and Pass@2 use five-suite macro averages, with pooled condition rates reported separately. Unfinished exploratory evaluations are not published.

The full directory counts 410 task–embodiment combinations in 12 implementation groups. Its native schedule includes loaded and ground Launch modes: 510 evaluation groups and 2,040 planned episodes per fixed access/observation setting. The paper uses loaded-only Launch and 400 EP-100 conditions. Schedule sizes are not scored results.

## Refresh data

Regenerate the paper exports from a local manuscript directory:

```sh
python3 scripts/refresh-paper-data.py /path/to/manuscript
python3 scripts/refresh-paper-data.py /path/to/manuscript --check
```

This reads `data/codex_experiments.json` from the manuscript and writes only `data/results.json`, `data/ep100-index.json`, and `data/tasks.json`. It verifies membership, subset metrics, and source hashes. No local archive is required. Add future models as separate experiments with explicit observation/tool settings, protocols, and budgets; compare only compatible settings.

Native exports use the `data/environment-*.json` names and `data/benchmark.json`, so native sync cannot overwrite paper results:

```sh
python3 scripts/sync_benchmark.py ../Agent-bench --check
python3 scripts/sync_media.py ../Agent-bench --check
```

`--check` performs no writes. Remove it to import from the benchmark checkout. Native sync requires matching source hashes and original media, and refuses stale exports or missing recordings. Imported media metadata passes through the same public projection and private-data guard before it is written. The shipped website is self-contained and passes portable validation without that checkout. Do not bypass source checks or regenerate benchmark evidence to make a website sync pass.

## Media and evidence

The A099 bank-shot corridor is the hero recording. Demonstrations are reference behavior or scene previews, separate from scored Codex attempts. Preserve embodiment, task scope, playback-speed labels, and source hashes when replacing media.

`data/media.json` and `data/environment-media.json` describe presentation assets. The public provenance files retain artifact IDs, content hashes, relative web paths, experimental conditions, playback transformations, and replay limitations. Full source locations, server/account details, and exact execution/encoding commands are private maintainer records stored outside this repository. Opaque source IDs identify those records; they are not downloadable links or content hashes. A trace or event log alone does not establish exact replay. To rerender, resolve the artifact ID in the private location map and use its original manifest/commands while preserving the stated conditions.

Only web derivatives and posters belong in `assets/`. Keep raw recordings and trajectories outside the published tree. New videos should remain below 5 MB each; the collaborator's existing 5.37 MB A099 recording is preserved unchanged. All assets must remain below the 40 MB budget.

Home execution videos, a qualified full Sharpa cube solve, and full six-piece Sharpa lock demos remain gaps. Existing Sharpa lock videos show key-only A06/D06 assembly/disassembly. Cube calibration clips are not complete benchmark solves.

## Private working material

Keep private backups, full provenance, raw recordings, and trajectories outside the website repository. The local cleanup archive and the unsanitized provenance snapshot are preserved in the sibling `../.codex-local/website-private-20261016/` directory, including an artifact-ID location map. They are not required to run, validate, or deploy a fresh checkout. `.gitignore` also excludes local artifacts and caches as a fallback; it is not an access-control mechanism.

The public projection lives in `scripts/public_data.py`. Media imports remove source locators, and every import/build checks for prohibited paths, private account fields, and run commands before writing or publishing. The guard is a regression check, not a claim that arbitrary new material is safe without review. Keep source snapshots before making public projections; never replace the only copy of a trajectory manifest with its public export.

## Check the actual publication commit

After reviewing and committing the cleanup, but before pushing, run:

```sh
python3 scripts/check_release_commit.py --ref HEAD
```

This reads the exact committed tree without changing Git, exports it to a temporary directory, checks the source/release allowlists, and runs the current validators. It catches forgotten additions/deletions and private public-data fields that a clean working-tree preview could hide. The Pages workflow runs the same gate against its selected commit. It intentionally rejects the old pre-cleanup commit. A passing check certifies the selected tree, not its ancestors.

**History policy: retain existing history and publish only the cleaned new version.** Old report files, exploratory results, archives, and source locations remain accessible in earlier commits after a normal deletion commit. Cleaning the new tree and deploying `dist/` do not erase that history. Do not describe a normal push as historical removal. If the repository itself must have no such historical content, coordinate a separate history cleanup with collaborators before pushing; commit IDs and other clones are affected. This change does not rewrite history, force-push, delete repositories, or change remote visibility. See [GitHub's history-removal guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).

## Hosting

Use **Settings → Pages → Source: GitHub Actions**, not the repository-root branch publishing mode. The included **Deploy audited static release** workflow is manual (`workflow_dispatch`): pushing source does not trigger it. After the reviewed commit is on GitHub, select it in Actions and run the workflow. It checks the exact commit, builds the allowlisted release, and uploads only `dist/` to Pages. No remote settings or deployments are changed by local preview/build commands. Configure the Pages source before triggering the workflow; its configuration step does not enable Pages automatically.

For any other static host, upload only the freshly built `dist/` contents, never the repository directory or a recursively zipped checkout. Relative URLs support both the domain root and `/Agent-bench-website/`. See [GitHub's custom Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
