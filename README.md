# Embodied Playground: An Agentic Robotics Benchmark for Physics, Strategic, and Spatial Reasoning

The self-contained, light-theme website for **Embodied Playground**. Website
source lives in [Agent-bench-website](https://github.com/Winniechen2002/Agent-bench-website);
benchmark code, environments, and evaluation documentation remain in
[Agent-bench](https://github.com/Winniechen2002/Agent-bench). `index.html` lives
at the website repository root. The site has no dependency on the sibling
dark-theme directory.

## Local preview

This is a dependency-free static site. Open a terminal in the website directory
(`Agent-bench-website` after cloning, or `embodied-agentic-playground-light`
in the original workspace) and serve it over HTTP so the page can load JSON:

```bash
python3 -m http.server 4174
```

Open [the local preview](http://127.0.0.1:4174/). The page reads task, result, and media metadata
from `data/` and only references files under `assets/` at runtime. Media cards
carry their evidence status (`reference`, `experimental`, `preliminary`, or
`media coming soon`) in the data rather than inferring it from the filename.

The compressed MP4s and JPEG posters are selected web previews. Original
recordings remain in their existing experiment/evidence locations and are not
required for the site to render.

## Publish with GitHub Pages later

The repository is ready for static hosting; GitHub Pages has not been enabled
as part of this website update. To publish later:

1. Open the repository's **Settings → Pages**.
2. Under **Build and deployment**, choose **Deploy from a branch** as the source.
3. Select branch **main** and folder **/(root)**, then click **Save**.

After a successful deployment, the expected site address is
[winniechen2002.github.io/Agent-bench-website/](https://winniechen2002.github.io/Agent-bench-website/).
This is a future deployment address, not a claim that the site is live.
See [GitHub's publishing-source instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).
Relative asset paths support this project subpath, and `.nojekyll` keeps the
site's static files intact.

## Demo provenance

`evidence/demo-manifest.json` records the source checkout or `sharpa_4090`
location, native video hash, trajectory hash, result files, and the command
used to reproduce each of the four focused demo groups:

- Franka Panda 3×3 Rubik reference cycle
- Floating Sharpa 3×3 Rubik calibration preview
- Dual Franka Kongming assembly and disassembly
- Floating Sharpa Kongming A06 and D06 acceptance previews

Raw trajectory files stay outside this Pages folder. To re-render after a
background or camera change, create a new run directory, replay the recorded
command, and update the manifest with the new derivative hash. The manifest
keeps the experimental Sharpa Rubik calibration and the fixed-camera Sharpa
Kongming clips explicitly separate from external-agent benchmark scores.
