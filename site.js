(() => {
  "use strict";

  const state = {
    tasks: [],
    benchmark: null,
    media: [],
    mediaFilter: "all",
    filters: { family: "all", embodiment: "all" },
  };

  const $ = (selector, scope = document) => scope.querySelector(selector);
  const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];
  const escapeHTML = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
  const slug = (value) => String(value || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

  async function loadJSON(path) {
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok) throw new Error(`${response.status} ${path}`);
    return response.json();
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

  function renderTaskCards() {
    const grid = $("#task-grid");
    const empty = $("#task-empty");
    if (!grid) return;
    const filtered = state.tasks.filter((task) => {
      const familyMatch = state.filters.family === "all" || task.family === state.filters.family;
      const embodimentMatch = state.filters.embodiment === "all" || (task.embodiments || []).some((item) => slug(item).includes(state.filters.embodiment));
      return familyMatch && embodimentMatch;
    }).map((task) => {
      if (state.filters.embodiment === "all") return task;
      const robots = Object.entries(task.counts_by_embodiment).filter(([name]) => slug(name).includes(state.filters.embodiment));
      return { ...task, count: robots.reduce((n, [, count]) => n + count, 0), embodiments: robots.map(([name]) => name) };
    });
    grid.innerHTML = filtered.map((task) => {
      const media = (task.media || []).map(mediaById).find(Boolean);
      const image = media?.poster || media?.fallback || "";
      const video = mediaIsVideo(media) ? `<video muted loop playsinline preload="none" poster="${escapeHTML(image)}" data-lazy-video="${escapeHTML(media.path)}"></video>` : image ? `<img src="${escapeHTML(media.path || image)}" alt="${escapeHTML(media.title)}" loading="lazy" />` : "";
      const skills = (task.skills || []).slice(0, 3).map((item) => `<span>${escapeHTML(item.replaceAll("_", " "))}</span>`).join("");
      const badgeClass = "experimental";
      return `<article class="task-card reveal is-visible" data-family="${escapeHTML(task.family)}" data-status="${escapeHTML(task.status)}">
        <div class="task-media ${escapeHTML(media?.display || "scene")}">${video}<span class="task-badge ${badgeClass}">qualification pending</span></div>
        <div class="task-body"><span class="task-family">${escapeHTML(task.family_label || task.family)}</span><h3>${escapeHTML(task.title)}</h3><span class="task-count">${escapeHTML(task.count)} ${state.filters.embodiment === "all" ? "task entries" : "matching task entries"}</span><p>${escapeHTML(task.summary)}</p><div class="task-meta">${skills}</div><button class="media-browse" type="button" data-media-task="${escapeHTML(task.id)}">View ${(task.media || []).length} media ${(task.media || []).length === 1 ? "item" : "items"} ↗</button><div class="task-footer"><span class="task-embodiment">${escapeHTML((task.embodiments || []).join(" · "))}</span><a href="https://github.com/Winniechen2002/Agent-bench/blob/main/${escapeHTML(task.source)}" target="_blank" rel="noreferrer">Task protocol ↗</a></div></div>
      </article>`;
    }).join("");
    empty.hidden = filtered.length > 0;
    $("#task-count").textContent = `${filtered.reduce((total, task) => total + task.count, 0)} task entries in ${filtered.length} catalog groups`;

    activateLazyVideos(grid);
  }

  function renderScope() {
    const data = state.benchmark;
    const cards = [
      ["TASK ENTRIES", data.task_count, "Aliases, seeds and initial modes do not add tasks."],
      ["EVALUATION GROUPS", data.group_count, "Loaded and ground groups are separate for Angry Birds."],
      ["PLANNED EPISODES", data.planned_episodes, "Per base seed and fixed access/observation combination."],
      ["TRIALS PER GROUP", data.trials_per_group, "Fresh environment and client session for every trial."],
    ];
    $("#result-highlights").innerHTML = cards.map(([label, value, copy]) => `<article class="highlight-card"><span class="highlight-label">${escapeHTML(label)}</span><strong>${escapeHTML(value)}</strong><p>${escapeHTML(copy)}</p></article>`).join("");
    $("#protocol-version").textContent = data.protocol_version;
    $("#capability-version").textContent = data.capability_version;
    $("#scope-status").textContent = data.qualification === "not_established" && data.release_ready === false
      ? "Full engineering qualification remains incomplete; source release readiness is false."
      : "Consult the repository’s current engineering and release status.";
    $("#hero-task-count").textContent = data.task_count;
    $("#hero-hanoi-count").textContent = data.counts.hanoi_panda + data.counts.hanoi_sharpa + data.counts.hanoi_floating;
    $("#hero-marble-count").textContent = data.counts.marble;
  }

  function renderMedia() {
    const target = $("#media-grid");
    if (!target) return;
    const items = state.media.filter((item) => state.mediaFilter === "all" || item.task === state.mediaFilter);
    $("#media-count").textContent = `${items.length} media ${items.length === 1 ? "item" : "items"} · previews, diagrams and historical recordings`;
    target.innerHTML = items.map((item) => {
      const poster = item.poster || item.fallback || "";
      const isVideo = mediaIsVideo(item);
      const visual = isVideo
        ? `<video controls muted loop playsinline preload="none" poster="${escapeHTML(poster)}" data-lazy-video="${escapeHTML(item.path)}" aria-label="${escapeHTML(item.title)}"></video>`
        : `<a href="${escapeHTML(item.path)}" target="_blank" rel="noreferrer" aria-label="View full image: ${escapeHTML(item.title)}"><img src="${escapeHTML(item.path)}" alt="${escapeHTML(item.title)}" loading="lazy" /></a>`;
      const statusLabel = item.claim_status.replaceAll("-", " ");
      return `<article class="media-card media-entry">
        <div class="media-visual ${escapeHTML(item.display || "scene")}">${visual}</div>
        <div class="media-info"><span class="media-status">${escapeHTML(statusLabel)}</span><small>${escapeHTML(item.source_type || "repository media")}</small><h3>${escapeHTML(item.title)}</h3><p>${escapeHTML(item.caption)}</p>
        <a class="media-open" href="${escapeHTML(item.path)}" target="_blank" rel="noreferrer">${isVideo ? "Open video" : item.display === "contact-sheet" ? "View all 10 scenes" : "View full image"} ↗</a></div>
      </article>`;
    }).join("");
    activateLazyVideos(target);
  }

  function setupMedia() {
    const select = $("#media-family");
    select.innerHTML = `<option value="all">All task groups</option>` + state.tasks.map((task) => `<option value="${escapeHTML(task.id)}">${escapeHTML(task.title)}</option>`).join("");
    select.addEventListener("change", () => { state.mediaFilter = select.value; renderMedia(); });
    $("#task-grid").addEventListener("click", (event) => {
      const button = event.target.closest("[data-media-task]");
      if (!button) return;
      state.mediaFilter = button.dataset.mediaTask;
      select.value = state.mediaFilter;
      renderMedia();
      $("#evidence").scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth" });
      select.focus({ preventScroll: true });
    });
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
        if (!video.controls && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) video.play().catch(() => {});
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
      $$(`.filter-button[data-filter-group="${group}"]`).forEach((candidate) => { candidate.classList.toggle("active", candidate === button); candidate.setAttribute("aria-pressed", String(candidate === button)); });
      renderTaskCards();
    }));
  }

  function setupHero() {
    const video = $("#hero-video");
    const media = mediaById("marble-a099-historical");
    if (media) {
      setMediaSource(video, media);
      $("#hero-poster").src = media.poster;
      $("#hero-poster").alt = media.title;
      video.setAttribute("aria-label", media.title);
    }
    const play = $(".stage-play");
    play?.addEventListener("click", () => {
      if (!video?.src) return;
      if (video.paused) { video.play().then(() => { video.classList.add("is-playing"); play.querySelector("span:last-child").textContent = "PAUSE ROLLOUT"; play.setAttribute("aria-label", "Pause selected benchmark video"); }).catch(() => {}); }
      else { video.pause(); video.classList.remove("is-playing"); play.querySelector("span:last-child").textContent = "PLAY ROLLOUT"; play.setAttribute("aria-label", "Play selected benchmark video"); }
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
    setupFilters();
    try {
      const [tasks, benchmark, media] = await Promise.all([
        loadJSON("data/tasks.json"), loadJSON("data/benchmark.json"), loadJSON("data/media.json"),
      ]);
      if (!Array.isArray(tasks) || !Array.isArray(media) || tasks.reduce((n, t) => n + t.count, 0) !== benchmark.task_count) {
        throw new Error("Inconsistent benchmark snapshot");
      }
      state.tasks = tasks;
      state.benchmark = benchmark;
      state.media = media;
      renderTaskCards();
      renderScope();
      renderMedia();
      setupMedia();
      setupHero();
    } catch (error) {
      console.error("Benchmark data could not be loaded", error);
      $("#task-empty").hidden = false;
      $("#task-empty").textContent = "Benchmark data could not be loaded. Reload the page or open the repository for the current catalog.";
      $("#task-count").textContent = "Catalog unavailable";
      $("#scope-status").textContent = "The current snapshot could not be loaded. Consult the repository for status.";
    }
    setupChrome();
    setupReveal();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
