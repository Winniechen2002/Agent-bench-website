(() => {
  "use strict";

  const state = { tasks: [], entries: [], media: [], filters: { family: "all", embodiment: "all" }, selectedMedia: new Map() };
  const $ = (selector, scope = document) => scope.querySelector(selector);
  const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];
  const escapeHTML = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
  const videoObservers = new Set();
  const mediaById = (id) => state.media.find((item) => item.id === id);
  const isVideo = (item) => /\.(mp4|webm|mov|m4v)$/i.test(item?.path || "");
  const imagePath = (value) => /\.(png|jpe?g|webp|svg|gif)$/i.test(value || "") ? value : "";
  const number = (value) => Number(value).toLocaleString("en-US");

  async function loadJSON(path) {
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok) throw new Error(`${response.status} ${path}`);
    return response.json();
  }

  function robotMatches(robot, filter) {
    const name = robot.toLowerCase().replaceAll("_", "-");
    if (filter === "all") return true;
    if (filter === "franka") return /franka|panda|fr3/.test(name);
    return name.includes(filter);
  }

  function entriesFor(task) {
    const ids = new Set(task.task_ids);
    return state.entries.filter((entry) => ids.has(entry.id) && robotMatches(entry.embodiment, state.filters.embodiment));
  }

  function mediaFor(task) {
    const items = task.media.map(mediaById).filter(Boolean);
    if (state.filters.embodiment === "all" || Object.keys(task.counts_by_embodiment).length === 1) return items;
    const matching = items.filter((item) => robotMatches(item.title, state.filters.embodiment));
    return matching.length ? matching : items;
  }

  function mediaHTML(item) {
    if (!item) return '<div class="catalog-unavailable">Media coming soon</div>';
    const poster = imagePath(item.poster) || imagePath(item.fallback);
    return isVideo(item)
      ? `<video controls muted playsinline preload="none" poster="${escapeHTML(poster)}" data-lazy-video="${escapeHTML(item.path)}" aria-label="${escapeHTML(item.title)}"></video>`
      : `<a href="${escapeHTML(item.path)}" target="_blank" rel="noreferrer" aria-label="View full image: ${escapeHTML(item.title)}"><img src="${escapeHTML(item.path)}" alt="${escapeHTML(item.title)}" loading="lazy" data-fallback="${escapeHTML(imagePath(item.fallback))}" /></a>`;
  }

  function mediaCaptionHTML(item) {
    const label = item?.playback_label ? ` <span class="media-playback-label">${escapeHTML(item.playback_label)}</span>` : "";
    return `${escapeHTML(item?.caption || "An execution recording is not yet available.")}${label}`;
  }

  function pauseVideos(scope = document) {
    $$("video", scope).forEach((video) => video.pause());
  }

  function activateMedia(scope) {
    $$("img", scope).forEach((image) => image.addEventListener("error", () => {
      const fallback = image.dataset.fallback;
      if (fallback && image.getAttribute("src") !== fallback) {
        image.src = fallback;
        if (image.parentElement.matches("a")) image.parentElement.href = fallback;
      } else {
        const notice = document.createElement("div");
        notice.className = "catalog-unavailable";
        notice.textContent = "Media unavailable";
        (image.closest("a") || image).replaceWith(notice);
      }
    }));
    $$('[data-lazy-video]', scope).forEach((video) => {
      const load = () => {
        if (!video.hasAttribute("src")) video.src = video.dataset.lazyVideo;
      };
      video.addEventListener("error", () => {
        const notice = document.createElement("div");
        notice.className = "catalog-unavailable";
        notice.textContent = "Video unavailable. Try the open video link below.";
        video.replaceWith(notice);
      }, { once: true });
      if (!("IntersectionObserver" in window)) { load(); return; }
      const observer = new IntersectionObserver((entries) => entries.forEach((entry) => {
        if (entry.isIntersecting) load();
        else video.pause();
      }), { threshold: 0.01 });
      observer.observe(video);
      videoObservers.add(observer);
    });
  }

  function renderTaskCards() {
    const grid = $("#task-grid");
    pauseVideos(grid);
    videoObservers.forEach((observer) => observer.disconnect());
    videoObservers.clear();
    const tasks = state.tasks.filter((task) => state.filters.family === "all" || task.family === state.filters.family)
      .map((task) => ({ task, entries: entriesFor(task) })).filter(({ entries }) => entries.length);
    grid.innerHTML = tasks.map(({ task, entries }) => {
      const media = mediaFor(task);
      const selected = media.find((item) => item.id === state.selectedMedia.get(task.id)) || media[0];
      const robots = Object.keys(task.counts_by_embodiment).filter((robot) => robotMatches(robot, state.filters.embodiment));
      const mediaSelector = media.length > 1 ? `<label class="catalog-media-label" for="media-${escapeHTML(task.id)}">Video<select class="catalog-media-select" id="media-${escapeHTML(task.id)}" data-media-task="${escapeHTML(task.id)}">${media.map((item) => `<option value="${escapeHTML(item.id)}"${item === selected ? " selected" : ""}>${escapeHTML(item.title)}</option>`).join("")}</select></label>` : "";
      const entryHTML = entries.map((entry) => {
        const budget = entry.budgets;
        return `<div class="catalog-entry"><code>${escapeHTML(entry.id)}</code><span>${escapeHTML(entry.groups.join(" / "))} · ${number(budget.simulation_seconds)} s simulation · ${number(budget.max_steps)} steps · ${number(budget.wall_seconds)} s wall limit</span></div>`;
      }).join("");
      return `<article class="task-card" data-task-id="${escapeHTML(task.id)}" data-family="${escapeHTML(task.family)}">
        <div class="task-media">${mediaHTML(selected)}</div>
        <div class="task-body"><span class="task-family">${escapeHTML(task.family_label || task.family)}</span><h2>${escapeHTML(task.title)}</h2><span class="catalog-task-count">${entries.length} ${state.filters.embodiment === "all" ? "task entries" : "matching task entries"}</span><p>${escapeHTML(task.summary)}</p>
        <div class="task-meta">${(task.skills || []).map((skill) => `<span>${escapeHTML(skill.replaceAll("_", " "))}</span>`).join("")}</div>
        ${mediaSelector}<p class="catalog-media-caption">${mediaCaptionHTML(selected)}</p><a class="catalog-open-media" href="${escapeHTML(selected?.path || "#tasks")}" target="_blank" rel="noreferrer"${selected ? "" : " hidden"}>${isVideo(selected) ? "Open video" : "View full image"} ↗</a>
        <div class="task-footer"><span class="task-embodiment">${escapeHTML(robots.join(" · "))}</span><a href="https://github.com/Winniechen2002/Embodied-Playground/blob/main/${escapeHTML(task.source)}" target="_blank" rel="noreferrer">Task protocol ↗</a></div>
        <details class="catalog-entries"><summary>Browse ${entries.length} task entries</summary><div class="catalog-entry-list" tabindex="0" role="region" aria-label="${escapeHTML(task.title)} task entries">${entryHTML}</div></details></div>
      </article>`;
    }).join("");
    $("#task-empty").hidden = tasks.length > 0;
    $("#task-count").textContent = `${tasks.reduce((sum, { entries }) => sum + entries.length, 0)} task entries in ${tasks.length} catalog groups`;
    activateMedia(grid);
  }

  function setupFilters() {
    $$(".filter-button").forEach((button) => button.addEventListener("click", () => {
      const group = button.dataset.filterGroup;
      state.filters[group] = button.dataset.filter;
      $$(`.filter-button[data-filter-group="${group}"]`).forEach((item) => {
        item.classList.toggle("active", item === button);
        item.setAttribute("aria-pressed", String(item === button));
      });
      renderTaskCards();
    }));
    $("#task-grid").addEventListener("change", (event) => {
      const select = event.target.closest(".catalog-media-select");
      if (!select) return;
      const card = select.closest(".task-card");
      const item = mediaById(select.value);
      if (!item) return;
      state.selectedMedia.set(select.dataset.mediaTask, item.id);
      pauseVideos(card);
      $(".task-media", card).innerHTML = mediaHTML(item);
      $(".catalog-media-caption", card).innerHTML = mediaCaptionHTML(item);
      const link = $(".catalog-open-media", card);
      link.href = item.path;
      link.textContent = `${isVideo(item) ? "Open video" : "View full image"} ↗`;
      activateMedia(card);
    });
  }

  function setupNavigation() {
    const toggle = $(".menu-toggle");
    const menu = $(".mobile-nav");
    const setMenu = (open) => {
      menu.classList.toggle("is-open", open);
      menu.inert = !open;
      toggle.setAttribute("aria-expanded", String(open));
      $(".sr-only", toggle).textContent = open ? "Close menu" : "Open menu";
    };
    toggle.addEventListener("click", () => setMenu(toggle.getAttribute("aria-expanded") !== "true"));
    $$("a", menu).forEach((link) => link.addEventListener("click", () => setMenu(false)));
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") { setMenu(false); toggle.focus(); }
    });
    window.matchMedia("(min-width: 701px)").addEventListener("change", (event) => { if (event.matches) setMenu(false); });
    document.addEventListener("visibilitychange", () => { if (document.hidden) pauseVideos(); });
  }

  async function init() {
    setupNavigation();
    setupFilters();
    try {
      const [tasks, benchmark, media, entries] = await Promise.all([loadJSON("data/environment-groups.json"), loadJSON("data/benchmark.json"), loadJSON("data/environment-media.json"), loadJSON("data/environment-catalog.json")]);
      if (!Array.isArray(tasks) || !Array.isArray(media) || !Array.isArray(entries) || entries.length !== benchmark.task_count || tasks.reduce((sum, task) => sum + task.count, 0) !== benchmark.task_count) throw new Error("Inconsistent catalog snapshot");
      Object.assign(state, { tasks, media, entries });
      renderTaskCards();
      $("#native-schedule").textContent = `${number(benchmark.group_count)} evaluation groups and ${number(benchmark.planned_episodes)} planned episodes`;
      document.body.dataset.ready = "true";
    } catch (error) {
      console.error("Task directory could not be loaded", error);
      $("#task-empty").hidden = false;
      $("#task-empty").textContent = "The task directory could not be loaded. Reload the page or use the download below.";
      $("#task-count").textContent = "Directory unavailable";
      document.body.dataset.ready = "error";
    }
  }
  document.addEventListener("DOMContentLoaded", init);
})();
