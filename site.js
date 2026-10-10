(() => {
  "use strict";

  const state = {
    tasks: [],
    results: [],
    summary: [],
    media: [],
    filters: { family: "all", embodiment: "all", status: "all" },
    resultTab: "hanoi",
  };

  const fallbackData = {
    tasks: [
      { id: "hanoi-franka", title: "Tower of Hanoi", family: "hanoi", family_label: "Symbolic puzzle", embodiments: ["Franka Panda"], observation_profiles: ["rgb", "rgbd", "privileged"], skills: ["planning", "rules", "grasp"], status: "validated", summary: "Five handled rings. Legal moves, stable grasping, and a long sequence with no shortcut.", success_criteria: "Transfer the full stack while respecting top-only and size-order rules.", source: "env/franka_hanoi/README.md", media: ["hanoi-4090"] },
      { id: "pocket-cube-dual", title: "2×2 Pocket Cube", family: "cube", family_label: "Bimanual state tracking", embodiments: ["Dual ALOHA", "Dual Sharpa"], observation_profiles: ["rgb", "state"], skills: ["state_tracking", "bimanual", "regrasping"], status: "validated", summary: "Paired embodiments execute the same compact cube transitions under matched physical conditions.", success_criteria: "Complete the declared turn and preserve the cube's mechanical state.", source: "pocket_cube.md", media: ["cube-sharpa"] },
      { id: "rubiks-franka", title: "3×3 Rubik's Cube", family: "cube", family_label: "Contact-rich manipulation", embodiments: ["Franka Panda"], observation_profiles: ["rgb"], skills: ["state_tracking", "dexterity", "regrasping"], status: "experimental", summary: "Face turns and whole-cube reorientation expose state estimation, clearance, and contact timing.", success_criteria: "Reach the declared target state through a validated sequence of face turns.", source: "docs/rubiks_cube.md", media: ["rubiks-franka"] },
      { id: "rubiks-sharpa", title: "Floating Sharpa Cube", family: "cube", family_label: "Dexterous embodiment", embodiments: ["Floating Sharpa"], observation_profiles: ["rgb"], skills: ["dexterity", "bimanual", "transfer"], status: "experimental", summary: "A floating hand route for 3×3 cube turns, with calibration and visual-review limits kept explicit.", success_criteria: "Execute the declared turn sequence and place the cube within tolerance.", source: "docs/rubiks_cube.md", media: ["rubiks-sharpa"] },
      { id: "marble-campaign", title: "Franka Marble Campaign", family: "marble", family_label: "Physics & recovery", embodiments: ["Franka Panda", "Dual Franka"], observation_profiles: ["rgb", "rgbd", "state"], skills: ["physics", "planning", "recovery"], status: "validated", summary: "Angry Birds-inspired launching tasks with shields, bridges, dominoes, materials, and finite ammunition.", success_criteria: "Load, aim, release, and complete the scene-specific physical objective.", source: "env/franka_marble/ENVIRONMENT_CATALOG.md", media: [] },
      { id: "kongming-dual-franka", title: "Kongming Lock", family: "kongming", family_label: "Assembly & disassembly", embodiments: ["Dual Franka"], observation_profiles: ["rgb", "rgbd", "privileged"], skills: ["bimanual", "contact", "recovery"], status: "validated", summary: "A six-piece burr puzzle that requires coordinated support, separation, insertion, and release.", success_criteria: "Assemble or disassemble the six-piece lock without forbidden contact or penetration.", source: "env/kongming_lock/README.md", media: ["kongming-franka"] },
      { id: "kongming-sharpa", title: "Floating Sharpa Lock", family: "kongming", family_label: "Dexterous assembly", embodiments: ["Floating Sharpa"], observation_profiles: ["rgb"], skills: ["dexterity", "bimanual", "contact"], status: "experimental", summary: "Measured native traces show the direction of a future floating-hand lock benchmark.", success_criteria: "Separate or merge the lock pieces under an auditable physical trace.", source: "source/agentbench/agentbench_platform", media: ["kongming-floating-sharpa-a06-reference", "kongming-floating-sharpa-d06-reference"] },
      { id: "tabletop-micro-skills", title: "Tabletop Micro-skills", family: "tabletop", family_label: "Household affordances", embodiments: ["Floating Shadow", "Franka + hand"], observation_profiles: ["rgb", "state"], skills: ["perception", "tool_use", "control"], status: "validated", summary: "A growing bank of object-centric tasks: open, lift, pour, press, rotate, and relocate.", success_criteria: "Complete the object-specific affordance with the registered controller and evaluator.", source: "source/agentbench/agentbench/tasks/manager_based/table_top_manipulation/config", media: [] },
      { id: "bookshelf-candidate", title: "Bookshelf Organization", family: "tabletop", family_label: "Candidate task", embodiments: ["FR3 + Sharpa"], observation_profiles: ["rgb", "depth", "pointcloud"], skills: ["perception", "planning", "placement"], status: "experimental", summary: "Three randomly placed books, a three-level shelf, and constrained packing from the feature branch.", success_criteria: "Place books upright, supported, still, and packed against the shelf wall.", source: "feat/organize-bookshelf:env/organize_bookshelf/README.md", media: [] },
      { id: "desk-organization", title: "Desk Organization", family: "tabletop", family_label: "Planned", embodiments: ["TBD"], observation_profiles: ["TBD"], skills: ["perception", "planning", "tool_use"], status: "planned", summary: "A future multi-object tidying suite for sorting, placement, and workspace state tracking.", success_criteria: "Planned task family — no public evaluator or media yet.", source: "planned", media: [] },
    ],
    results: [
      { id: "hanoi-l3", family: "hanoi", task: "Franka Hanoi", profile: "Vision / Level 3", level: "L3", attempts: "5", success: "5/5", metric: "31/31 moves", tokens: "23.67M", status: "preliminary", caveat: "5-ring run; max penetration 1.60 mm.", detail: "Claude Opus 5.5, cold start, one fresh agent per attempt. Independent evaluator and 30M-token cap." },
      { id: "hanoi-l2", family: "hanoi", task: "Franka Hanoi", profile: "Vision / Level 2", level: "L2", attempts: "5", success: "1/5", metric: "31/31 moves", tokens: "8.95M", status: "preliminary", caveat: "Other attempts stopped on joint limit, penetration, or unfinished move.", detail: "The successful attempt completed the five-ring sequence; failed attempts remain part of the evidence." },
      { id: "hanoi-l1", family: "hanoi", task: "Franka Hanoi", profile: "Vision / Level 1", level: "L1", attempts: "5", success: "0/5", metric: "3/31 best", tokens: "25.95M", status: "preliminary", caveat: "Failure modes include target, seating, unfinished move, penetration, and joint limit.", detail: "A strict observation-bound profile; no privileged simulator state." },
      { id: "marble-l3", family: "marble", task: "Franka Marble campaign", profile: "Vision / Level 3", level: "L3", attempts: "408 episodes", success: "106 / 408", metric: "0.2598 mean task success", tokens: "25.47M", status: "preliminary", caveat: "6 tasks reached 4/4; 48 tasks reached at least 1/4.", detail: "100-scene campaign test split with loaded/ground initial modes and multiple seeds." },
      { id: "marble-state", family: "marble", task: "Franka Marble campaign", profile: "State / Level 3", level: "L3", attempts: "408 episodes", success: "25", metric: "0.0613 mean task success", tokens: "25.64M", status: "preliminary", caveat: "State result is kept separate from vision profiles.", detail: "Different observation and tool contract; do not compare as a single leaderboard score." },
      { id: "marble-l2", family: "marble", task: "Franka Marble campaign", profile: "Vision / Level 2", level: "L2", attempts: "408 episodes", success: "24", metric: "0.0588 mean task success", tokens: "24.61M", status: "preliminary", caveat: "1 task reached 4/4; 13 tasks reached at least 1/4.", detail: "RGB-D and grasp/contact tool profile." },
      { id: "marble-l1", family: "marble", task: "Franka Marble campaign", profile: "Vision / Level 1", level: "L1", attempts: "408 episodes", success: "6", metric: "0.0147 mean task success", tokens: "28.50M", status: "preliminary", caveat: "A strict rerun using current RGB geometry scored 0.0000 after handle grasp failure.", detail: "The first run has a compliance caveat; the rerun is shown to make that limitation visible." },
      { id: "kongming-a11", family: "kongming", task: "Kongming public case A11", profile: "Privileged / Level 3", level: "L3", attempts: "1", success: "success", metric: "2 pieces / subtask", tokens: "8.77M", status: "reference", caveat: "Public key-plus-bar subtask; not a full six-piece claim.", detail: "Reference run was independently recomputed with the trusted case specification." },
      { id: "kongming-d01", family: "kongming", task: "Kongming public case D01", profile: "Privileged / Level 3", level: "L3", attempts: "1", success: "success", metric: "complete", tokens: "26.52M", status: "reference", caveat: "Public complete subtask; disassembly subtasks have known scorer contradictions.", detail: "Reference run was independently recomputed with --require-success." },
      { id: "kongming-fixed", family: "kongming", task: "Kongming fixed initial state", profile: "RGB / RGB-D / privileged", level: "L1–L3", attempts: "6", success: "0/6", metric: "2/6 max assemble progress", tokens: "4.69–24.39M", status: "preliminary", caveat: "Penetration and forbidden-contact hard failures dominate.", detail: "Rows are kept grouped by profile in the full result file; no cross-profile ranking is implied." },
      { id: "rubik-franka", family: "rubik", task: "3×3 Rubik's Cube", profile: "RGB / Level 1", level: "L1", attempts: "7", success: "1 agent finish", metric: "1 U turn", tokens: "28.40M", status: "preliminary", caveat: "Several rows hit fixed-joint scorer regressions at the recorded commit.", detail: "C11 reached agent_finish after one U; C01/C21 and sequence cases hit harness issues." },
      { id: "rubik-sharpa", family: "rubik", task: "Floating Sharpa cube", profile: "RGB / Level 1", level: "L1", attempts: "1", success: "agent finish", metric: "0 turns", tokens: "23.85M", status: "preliminary", caveat: "Mechanism unavailable in describe(); a face turn could not begin.", detail: "This is a harness-limited initial result, not a solve claim." },
    ],
    media: [
      { id: "rubiks-franka", path: "assets/media/rubiks-franka-reference-cycle.mp4", poster: "assets/posters/rubiks-franka-reference-cycle.jpg", title: "3×3 Rubik / Franka Panda", family: "cube", embodiment: "Franka Panda", caption: "Franka Panda U×4 reference cycle. Privileged trajectory demonstration; not a complete-agent score.", source_type: "native reference trajectory", claim_status: "reference-execution", fallback: "assets/images/pocket-cube-dual-aloha.png" },
      { id: "kongming-franka", path: "assets/media/kongming-assembly.mp4", poster: "assets/posters/kongming-assembly.jpg", title: "Kongming Lock / Dual Franka", family: "kongming", embodiment: "Dual Franka", caption: "Six-piece assembly reference execution. Captioned as a native trace, not an Opus score.", source_type: "native delivery", claim_status: "reference", fallback: "assets/images/hanoi-franka-panda.png" },
      { id: "hanoi-4090", path: "assets/media/hanoi-strict-4090.mp4", poster: "assets/posters/hanoi-strict-4090.jpg", title: "Tower of Hanoi / Franka", family: "hanoi", embodiment: "Franka Panda", caption: "Strict-contact simulation demo from the 4090 reproduction. Visual demo only.", source_type: "simulation demo", claim_status: "demo", fallback: "assets/images/hanoi-franka-panda.png" },
      { id: "rubiks-sharpa", path: "assets/media/sharpa-rubiks-a3.mp4", poster: "assets/posters/sharpa-rubiks-a3.jpg", title: "3×3 Cube / Floating Sharpa", family: "cube", embodiment: "Floating Sharpa", caption: "Compact candidate preview. Experimental calibration; visual qualification remains pending.", source_type: "candidate preview", claim_status: "experimental", fallback: "assets/images/pocket-cube-dual-sharpa.png" },
      { id: "kongming-floating-sharpa-a06-reference", path: "assets/media/sharpa-kongming-a06-native.mp4", poster: "assets/posters/sharpa-kongming-a06-native.jpg", title: "Kongming / Floating Sharpa", family: "kongming", embodiment: "Floating Sharpa", caption: "A06 native fixed-camera acceptance preview; no external-agent score is claimed.", source_type: "native fixed-camera", claim_status: "reference-acceptance-preview", fallback: "assets/images/pocket-cube-dual-sharpa.png" },
      { id: "kongming-floating-sharpa-d06-reference", path: "assets/media/sharpa-kongming-d06-native.mp4", poster: "assets/posters/sharpa-kongming-d06-native.jpg", title: "Kongming / Floating Sharpa", family: "kongming", embodiment: "Floating Sharpa", caption: "D06 native fixed-camera acceptance preview; no external-agent score is claimed.", source_type: "native fixed-camera", claim_status: "reference-acceptance-preview", fallback: "assets/images/pocket-cube-dual-sharpa.png" },
      { id: "marble-pending", title: "Franka Marble / Angry Birds", family: "marble", embodiment: "Franka / Dual Franka", caption: "Media coming soon. The campaign catalog and preliminary results are available.", claim_status: "pending", fallback: "assets/images/marble-placeholder.svg" },
      { id: "desk-pending", title: "Desk Organization", family: "tabletop", embodiment: "Planned", caption: "Media coming soon. This card marks a future multi-object organization suite.", claim_status: "pending", fallback: "assets/images/desk-placeholder.svg" },
    ],
  };

  const $ = (selector, scope = document) => scope.querySelector(selector);
  const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];
  const escapeHTML = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
  const slug = (value) => String(value || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

  async function loadJSON(path, fallback) {
    try {
      const response = await fetch(path, { cache: "no-store" });
      if (!response.ok) throw new Error(`${response.status} ${path}`);
      return await response.json();
    } catch (error) {
      console.warn(`Using inline fallback for ${path}`, error);
      return fallback;
    }
  }

  function setMediaSource(video, media) {
    if (!video || !media?.path) return false;
    video.poster = media.poster || media.fallback || "";
    video.src = media.path;
    video.addEventListener("loadeddata", () => {
      video.classList.add("is-ready");
      const poster = video.previousElementSibling;
      if (poster?.classList.contains("hero-poster")) poster.style.opacity = "0";
    }, { once: true });
    video.addEventListener("error", () => {
      video.removeAttribute("src");
      video.load();
    }, { once: true });
    return true;
  }

  function mediaById(id) { return state.media.find((item) => item.id === id); }

  function mediaIsVideo(item) {
    return Boolean(item?.path && /\.(mp4|webm|mov|m4v)$/i.test(item.path));
  }

  function resultFamily(task) {
    const value = String(task || "").toLowerCase();
    if (value.includes("hanoi")) return "hanoi";
    if (value.includes("marble") || value.includes("angry")) return "marble";
    if (value.includes("kongming")) return "kongming";
    if (value.includes("rubik")) return "rubik";
    return "other";
  }

  function normalizeResults(payload) {
    const raw = Array.isArray(payload) ? payload : (Array.isArray(payload?.results) ? payload.results : []);
    state.summary = Array.isArray(payload?.summary) ? payload.summary : [];
    return raw.map((row) => {
      const family = resultFamily(row.task);
      const status = String(row.claim_status || "").includes("reference") || String(row.claim_status || "").includes("public-cases") || String(row.evidence_type || "").includes("reference") ? "reference" : "preliminary";
      const metric = row.completed_moves || row.metric || (row.quarter_turns_measured !== undefined ? `${row.quarter_turns_measured} quarter-turns` : row.termination || "—");
      const success = typeof row.success === "string" ? row.success : (row.success === true ? "success" : row.status === "success" ? "success" : row.status || "fail");
      const attempts = row.attempt && row.attempts ? `${row.attempt}/${row.attempts}` : row.attempts || "1";
      const caveat = row.caveat || row.first_failure || row.failure_reason || (row.termination === "hard_failure" ? "Hard failure" : "Recorded evaluation row");
      const detail = [row.mode, row.case, row.embodiment, row.steps ? `${row.steps} steps` : "", row.max_penetration_mm !== undefined ? `max penetration ${row.max_penetration_mm} mm` : ""].filter(Boolean).join(" · ");
      return { ...row, family, profile: `${row.profile || "profile"} / L${row.level ?? "—"}`, attempts, success, metric, tokens: row.tokens || "—", status, caveat, detail: detail || "Initial evidence row from the published Opus 5.5 result file." };
    });
  }

  function taskStatusClass(status) {
    const value = String(status || "").toLowerCase();
    if (value.includes("planned")) return "planned";
    if (value.includes("experimental") || value.includes("candidate")) return "experimental";
    if (value.includes("valid") || value.includes("active")) return "validated";
    return "experimental";
  }

  function renderTaskCards() {
    const grid = $("#task-grid");
    const empty = $("#task-empty");
    if (!grid) return;
    const filtered = state.tasks.filter((task) => {
      const familyMatch = state.filters.family === "all" || task.family === state.filters.family;
      const embodimentMatch = state.filters.embodiment === "all" || (task.embodiments || []).some((item) => slug(item).includes(state.filters.embodiment));
      const statusMatch = state.filters.status === "all" || task.status === state.filters.status;
      return familyMatch && embodimentMatch && statusMatch;
    });
    grid.innerHTML = filtered.map((task) => {
      const media = (task.media || []).map(mediaById).find(Boolean);
      const image = media?.poster || media?.fallback || "";
      const video = mediaIsVideo(media) ? `<video muted loop playsinline preload="none" poster="${escapeHTML(image)}" data-lazy-video="${escapeHTML(media.path)}"></video>` : image ? `<img src="${escapeHTML(media.path || image)}" alt="" loading="lazy" />` : "";
      const badges = (task.observation_profiles || []).slice(0, 3).map((item) => `<span>${escapeHTML(item)}</span>`).join("");
      const skills = (task.skills || []).slice(0, 3).map((item) => `<span>${escapeHTML(item.replaceAll("_", " "))}</span>`).join("");
      const badgeClass = taskStatusClass(task.status);
      return `<article class="task-card reveal is-visible" data-family="${escapeHTML(task.family)}" data-status="${escapeHTML(task.status)}">
        <div class="task-media">${video}<span class="task-badge ${badgeClass}">${escapeHTML(task.status.replaceAll("-", " "))}</span></div>
        <div class="task-body"><span class="task-family">${escapeHTML(task.family_label || task.family)}</span><h3>${escapeHTML(task.title)}</h3><p>${escapeHTML(task.summary)}</p><div class="task-meta">${skills}</div><div class="task-footer"><span class="task-embodiment">${escapeHTML((task.embodiments || []).join(" · "))}</span><span>${escapeHTML((task.source || "").split("/").pop())}</span></div></div>
      </article>`;
    }).join("");
    empty.hidden = filtered.length > 0;
    activateLazyVideos(grid);
  }

  function renderHighlights() {
    const target = $("#result-highlights");
    if (!target) return;
    const summary = state.summary;
    const find = (task, level) => summary.find((item) => item.task === task && item.level === level);
    const hanoi = find("franka-hanoi-5-ring", 3);
    const marble = find("franka-marble-campaign", 3);
    const kongming = find("kongming-dual-franka-assemble", 3);
    const rubik = find("rubiks-franka-3x3", 1);
    const cards = [
      ["HANOI / L3", hanoi ? `${hanoi.successes} / ${hanoi.attempts}` : "—", "reported five-ring attempts"],
      ["MARBLE / VISION L3", marble ? `${(marble.success_rate * 100).toFixed(2)}%` : "—", marble ? `${marble.successes} / ${marble.attempts} episodes` : "campaign result"],
      ["KONGMING / PUBLIC", kongming ? `${kongming.successes} cases` : "—", "verified public reference cases"],
      ["CUBE / EARLY", rubik ? rubik.metric.replace("0 measured quarter-turns on failing rows", "0 turns") : "—", "Franka initial harness result"],
    ];
    target.innerHTML = cards.map(([label, value, copy]) => `<article class="highlight-card"><span class="highlight-label">${escapeHTML(label)}</span><strong>${escapeHTML(value)}</strong><p>${escapeHTML(copy)}</p></article>`).join("");
  }

  function renderResults(family = state.resultTab) {
    const target = $("#result-table-wrap");
    if (!target) return;
    const rows = state.results.filter((result) => result.family === family);
    if (!rows.length) {
      target.innerHTML = `<p class="empty-state">No result rows are published for this family yet.</p>`;
      return;
    }
    target.innerHTML = `<table class="result-table"><thead><tr><th>Run</th><th>Profile</th><th>Attempts</th><th>Success</th><th>Metric</th><th>Budget</th><th>Status</th><th></th></tr></thead><tbody>${rows.map((row, index) => {
      const reference = row.status === "reference";
      return `<tr class="result-row" data-result-row="${index}"><td>${escapeHTML(row.task)}</td><td>${escapeHTML(row.profile)}</td><td>${escapeHTML(row.attempts)}</td><td class="result-emphasis">${escapeHTML(row.success)}</td><td>${escapeHTML(row.metric)}</td><td>${escapeHTML(row.tokens)}</td><td><span class="result-status ${reference ? "reference" : ""}"><i class="dot ${reference ? "dot-reference" : "dot-preliminary"}"></i>${escapeHTML(row.status)}</span></td><td><button class="result-expand" type="button" aria-expanded="false" aria-label="Show details for ${escapeHTML(row.task)}">+</button></td></tr><tr class="result-details"><td colspan="8" class="detail-cell"><strong>${escapeHTML(row.caveat)}</strong><br />${escapeHTML(row.detail)}</td></tr>`;
    }).join("")}</tbody></table>`;
  }

  function renderMedia() {
    const target = $("#media-grid");
    if (!target) return;
    target.innerHTML = state.media.map((item) => {
      const pending = !item.path || String(item.claim_status || "").includes("coming-soon") || String(item.claim_status || "").includes("planned");
      const poster = item.poster || item.fallback || "";
      const visual = pending ? "" : mediaIsVideo(item) ? `<video muted loop playsinline preload="none" poster="${escapeHTML(poster)}" data-lazy-video="${escapeHTML(item.path)}" aria-label="${escapeHTML(item.title)}"></video>` : item.path ? `<img src="${escapeHTML(item.path)}" alt="${escapeHTML(item.title)}" loading="lazy" />` : `<img src="${escapeHTML(poster)}" alt="${escapeHTML(item.title)}" loading="lazy" />`;
      const statusLabel = pending ? "media coming soon" : item.claim_status;
      return `<article class="media-card ${pending ? "placeholder" : ""}">${visual}<span class="media-status ${pending ? "pending" : ""}">${escapeHTML(statusLabel)}</span><div class="media-info"><small>${escapeHTML(item.source_type || item.family || "evidence")}</small><h3>${escapeHTML(item.title)}</h3><p>${escapeHTML(item.caption)}</p></div></article>`;
    }).join("");
    activateLazyVideos(target);
  }

  function activateLazyVideos(scope = document) {
    const videos = $$('[data-lazy-video]', scope);
    if (!videos.length) return;
    const load = (video) => {
      if (video.dataset.loaded) return;
      video.dataset.loaded = "true";
      video.src = video.dataset.lazyVideo;
      video.addEventListener("loadeddata", () => {
        video.classList.add("is-ready");
        video.play().catch(() => {});
      }, { once: true });
    };
    if (!("IntersectionObserver" in window)) { videos.forEach(load); return; }
    const observer = new IntersectionObserver((entries, obs) => entries.forEach((entry) => { if (entry.isIntersecting) { load(entry.target); obs.unobserve(entry.target); } }), { rootMargin: "180px 0px" });
    videos.forEach((video) => observer.observe(video));
  }

  function setupFilters() {
    $$(".filter-button").forEach((button) => button.addEventListener("click", () => {
      const group = button.dataset.filterGroup;
      state.filters[group] = button.dataset.filter;
      $$(`.filter-button[data-filter-group="${group}"]`).forEach((candidate) => candidate.classList.toggle("active", candidate === button));
      renderTaskCards();
    }));
  }

  function setupResults() {
    $$(".console-tab").forEach((button) => button.addEventListener("click", () => {
      state.resultTab = button.dataset.resultTab;
      $$(".console-tab").forEach((candidate) => { const active = candidate === button; candidate.classList.toggle("active", active); candidate.setAttribute("aria-selected", active ? "true" : "false"); });
      renderResults(state.resultTab);
    }));
    $("#result-table-wrap")?.addEventListener("click", (event) => {
      const button = event.target.closest(".result-expand");
      if (!button) return;
      const row = button.closest(".result-row");
      const expanded = row.classList.toggle("is-expanded");
      button.textContent = expanded ? "−" : "+";
      button.setAttribute("aria-expanded", expanded ? "true" : "false");
    });
  }

  function setupHero() {
    const video = $("#hero-video");
    const media = mediaById("rubiks-franka-three-step") || mediaById("hanoi-4090-demo");
    if (media) setMediaSource(video, media);
    const play = $(".stage-play");
    play?.addEventListener("click", () => {
      if (!video?.src) return;
      if (video.paused) { video.play().then(() => { video.classList.add("is-playing"); play.querySelector("span:last-child").textContent = "PAUSE ROLLOUT"; }).catch(() => {}); }
      else { video.pause(); video.classList.remove("is-playing"); play.querySelector("span:last-child").textContent = "PLAY ROLLOUT"; }
    });
  }

  function setupChrome() {
    const topbar = $("[data-topbar]");
    const progress = $(".site-progress span");
    const update = () => {
      topbar?.classList.toggle("is-scrolled", window.scrollY > 20);
      const max = document.documentElement.scrollHeight - window.innerHeight;
      if (progress) progress.style.width = `${max > 0 ? (window.scrollY / max) * 100 : 0}%`;
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    const toggle = $(".menu-toggle");
    const mobile = $(".mobile-nav");
    toggle?.addEventListener("click", () => { const open = mobile.classList.toggle("is-open"); toggle.setAttribute("aria-expanded", open ? "true" : "false"); });
    $$(".mobile-nav a").forEach((link) => link.addEventListener("click", () => { mobile.classList.remove("is-open"); toggle?.setAttribute("aria-expanded", "false"); }));
  }

  function setupReveal() {
    const items = $$(".reveal");
    if (!("IntersectionObserver" in window)) { items.forEach((item) => item.classList.add("is-visible")); return; }
    const observer = new IntersectionObserver((entries, obs) => entries.forEach((entry) => { if (entry.isIntersecting) { entry.target.classList.add("is-visible"); obs.unobserve(entry.target); } }), { threshold: .12 });
    items.forEach((item) => observer.observe(item));
  }

  async function init() {
    const [tasks, results, media] = await Promise.all([
      loadJSON("data/tasks.json", fallbackData.tasks),
      loadJSON("data/results.json", fallbackData.results),
      loadJSON("data/media.json", fallbackData.media),
    ]);
    state.tasks = Array.isArray(tasks) ? tasks : fallbackData.tasks;
    state.results = normalizeResults(results);
    if (!state.results.length) state.results = normalizeResults(fallbackData.results);
    state.media = Array.isArray(media) ? media : fallbackData.media;
    renderTaskCards();
    renderHighlights();
    renderResults();
    renderMedia();
    setupFilters();
    setupResults();
    setupHero();
    setupChrome();
    setupReveal();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
