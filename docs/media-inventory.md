# Website media inventory — 2026-10-11

All 12 task groups have preview material. The gallery contains 20 records, including eight additions copied byte-for-byte from Agent-bench (10,487,442 bytes including video posters).

| Catalog group | Available media |
| --- | --- |
| Angry Birds / Marble | [Angry Birds · A099 homepage rollout](../assets/media/marble-a099-reference.mp4) · [Angry Birds · A007](../assets/images/marble-a007.png) · [Angry Birds · A057 reference rollout](../assets/media/marble-a057-reference.mp4) |
| Hanoi · Franka Panda | [Franka Hanoi scene preview](../assets/images/hanoi-franka-panda.png) · [Hanoi 4090 replay](../assets/media/hanoi-strict-4090.mp4) |
| Hanoi · FR3 + Sharpa | [Sharpa Hanoi scene preview](../assets/images/hanoi-sharpa.png) |
| Hanoi · Floating Sharpa | [Floating Sharpa Hanoi · H29](../assets/images/hanoi-floating-h29.png) |
| 2×2 Pocket Cube | [Dual ALOHA Pocket Cube](../assets/images/pocket-cube-dual-aloha.png) · [Dual Sharpa Pocket Cube](../assets/images/pocket-cube-dual-sharpa.png) |
| 3×3 Rubik · Franka Panda | [Franka 3×3 cube three-step demo](../assets/media/rubiks-three-step.mp4) · [3×3 Rubik / Franka Panda reference cycle](../assets/media/rubiks-franka-reference-cycle.mp4) |
| 3×3 Rubik · Floating Sharpa | [Floating Sharpa cube preview](../assets/media/sharpa-rubiks-a3.mp4) |
| Kongming Lock | [Dual Franka Kongming assembly reference](../assets/media/kongming-assembly.mp4) · [Floating Sharpa Kongming A06](../assets/media/sharpa-kongming-a06-native.mp4) · [Floating Sharpa Kongming D06](../assets/media/sharpa-kongming-d06-native.mp4) · [Kongming lock / Dual Franka disassembly](../assets/media/kongming-disassembly.mp4) |
| Bookshelf Organization | [Bookshelf · Dual Panda native scene](../assets/images/bookshelf-native-shelftable-d3.png) |
| ManiSkill · Long horizon | [ManiSkill · Long horizon scene atlas](../assets/images/maniskill-category1.jpg) |
| ManiSkill · Geometry | [ManiSkill · Geometry scene atlas](../assets/images/maniskill-category2.jpg) |
| ManiSkill · Dynamics | [ManiSkill · Dynamics scene atlas](../assets/images/maniskill-category3.jpg) |

## Provenance and remaining gaps

- Added media: `data/media-sources.json`, imported from Agent-bench `docs/website_media_catalog.json`.
- Existing recordings: `evidence/demo-manifest.json` and original `data/media.json` source paths.
- ManiSkill contact sheets cover all 30 authored codes; original render appearance may differ from the current runtime.
- Bookshelf uses a new 1600 × 1000 native Isaac Sim RTX render (ShelfTableD3, seed 7) as its primary preview. The layout diagram stays in repository documentation only; a robot rollout is still missing. The source render manifest records camera poses and source hashes.
- Previews and historical engineering recordings are not current-protocol model results or full qualification evidence.

## Refresh

```bash
python3 scripts/sync_benchmark.py ../Agent-bench
python3 scripts/sync_media.py ../Agent-bench
python3 scripts/check_site.py
python3 scripts/sync_benchmark.py ../Agent-bench --check
python3 scripts/sync_media.py ../Agent-bench --check
```
