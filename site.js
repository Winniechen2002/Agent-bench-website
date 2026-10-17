(() => {
  'use strict';
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const escape = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const percent = (value) => Number.isFinite(value) ? `${(value * 100).toFixed(2)}%` : 'Not reported';
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const canHover = window.matchMedia('(hover: hover)');
  const suites = ['Launch', 'Tower', 'Lock', 'Cube', 'Home'];
  const state = { tasks: [], media: [], experiment: null, subset: 'EP-100', suite: 'all', embodiment: 'all', mediaSuite: 'all', mediaTask: 'all' };
  const mediaById = (id) => state.media.find((item) => item.id === id);
  const isVideo = (item) => /\.(mp4|webm)(?:$|\?)/i.test(item?.path || '');
  const suiteFor = (item) => item.suite || ({marble:'Launch',hanoi:'Tower',kongming:'Lock',cube:'Cube',rubik:'Cube',tabletop:'Home',bookshelf:'Home',maniskill:'Home'}[item.family]) || '';

  async function loadJSON(path) {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
    return response.json();
  }

  function mediaMarkup(item) {
    if (!item?.path) return '<div class="media-unavailable">Video unavailable</div>';
    const poster = item.poster || item.fallback || '';
    if (!isVideo(item)) return `<a class="media-image-link" href="${escape(item.path)}" target="_blank" rel="noopener" aria-label="Open full image: ${escape(item.title)}"><img src="${escape(item.path)}" alt="${escape(item.title)}" loading="lazy" data-fallback="${escape(item.fallback || '')}" /><span>View full image ↗</span></a>`;
    return `<video muted loop playsinline preload="none" poster="${escape(poster)}" data-video-src="${escape(item.path)}" aria-label="${escape(item.title)}"></video><button class="preview-play" type="button" aria-label="Play ${escape(item.title)}"><span aria-hidden="true">▶</span> Play video</button>`;
  }

  function mediaCaptionMarkup(item) {
    const label = item?.playback_label ? ` <span class="media-playback-label">${escape(item.playback_label)}</span>` : '';
    return `${escape(item?.caption || '')}${label}`;
  }

  async function playVideo(video) {
    if (!video.src) { video.src = video.dataset.videoSrc; video.load(); }
    video.controls = true;
    try { await video.play(); video.parentElement.querySelector('.preview-play')?.setAttribute('hidden', ''); }
    catch { /* Native controls remain available when autoplay is blocked. */ }
  }

  const videoObserver = 'IntersectionObserver' in window ? new IntersectionObserver((entries) => {
    entries.forEach(({target, isIntersecting}) => { if (!isIntersecting) target.pause(); });
  }) : null;

  function bindMedia(root) {
    $$('img', root).forEach((img) => img.addEventListener('error', () => {
      const fallback = img.dataset.fallback;
      if (fallback && !img.dataset.fallbackUsed && img.getAttribute('src') !== fallback) { img.dataset.fallbackUsed = 'true'; img.src = fallback; const link = img.closest('.media-image-link'); if (link) link.href = fallback; return; }
      const target = img.closest('.media-image-link') || img;
      target.replaceWith(Object.assign(document.createElement('div'), {className:'media-unavailable',textContent:'Video unavailable'}));
    }));
    $$('video[data-video-src]', root).forEach((video) => {
      video.muted = true;
      videoObserver?.observe(video);
      const frame = video.parentElement;
      $('.preview-play', frame)?.addEventListener('click', () => playVideo(video));
      frame.addEventListener('pointerenter', () => { if (canHover.matches && !reduced.matches) playVideo(video); });
      frame.addEventListener('pointerleave', () => video.pause());
      video.addEventListener('error', () => {
        video.pause(); video.controls = false;
        const button = $('.preview-play', frame);
        if (button) { button.hidden = false; button.textContent = 'Video unavailable'; button.disabled = true; }
      });
    });
  }

  function clearVideos(root) {
    $$('video', root).forEach((video) => { video.pause(); videoObserver?.unobserve(video); video.removeAttribute('src'); video.load(); });
  }

  function renderTasks() {
    const grid = $('#task-grid');
    clearVideos(grid);
    const filtered = state.tasks.filter((task) => (state.suite === 'all' || task.suite === state.suite) && (state.embodiment === 'all' || task.embodiments.some((name) => name.toLowerCase().includes(state.embodiment)))).map((task) => {
      if (state.embodiment === 'all') return task;
      const robots = Object.entries(task.counts_by_embodiment).filter(([name]) => name.toLowerCase().includes(state.embodiment));
      return {...task, task_count: robots.reduce((sum,[,count]) => sum + count,0), embodiments: robots.map(([name]) => name)};
    });
    $('#task-count').textContent = `${filtered.length} of ${state.tasks.length} task types · ${filtered.reduce((sum,t) => sum + t.task_count, 0)} ${state.embodiment === 'all' ? '' : 'matching '}EP-100 tasks`;
    $('#task-empty').hidden = filtered.length > 0;
    grid.innerHTML = filtered.map((task) => {
      const media = task.media.map(mediaById).filter(Boolean);
      const selected = media.find((item) => state.embodiment !== 'all' && String(item.embodiment).toLowerCase().includes(state.embodiment)) || media[0];
      return `<article class="task-card" data-task="${escape(task.id)}"><div class="task-media">${mediaMarkup(selected)}<span class="task-badge">${escape(task.task_count)} ${state.embodiment === 'all' ? '' : 'matching '}EP-100 tasks</span></div><div class="task-body"><span class="task-family">${escape(task.suite)} / ${escape(task.type)}</span><h3>${escape(task.title.replace(/^.*? · /,''))}</h3><p>${escape(task.summary)}</p><div class="task-meta">${task.skills.slice(0,3).map((skill) => `<span>${escape(skill.replaceAll('_',' '))}</span>`).join('')}</div><div class="task-footer"><span class="task-embodiment">${escape(task.embodiments.join(' · '))}</span></div>${media.length > 1 ? `<label class="media-select-label">Video<select data-task-media="${escape(task.id)}">${media.map((item) => `<option value="${escape(item.id)}"${item.id === selected.id ? ' selected' : ''}>${escape(item.title)}</option>`).join('')}</select></label>` : ''}<p class="selected-media-caption">${mediaCaptionMarkup(selected)}</p><div class="task-documentation">${(task.documentation || []).map((doc) => `<a href="https://github.com/Winniechen2002/Embodied-Playgroud/blob/main/${escape(doc.path)}" target="_blank" rel="noreferrer">${escape(doc.label)} protocol ↗</a>`).join('')}</div><button class="media-browse" type="button" data-media-task="${escape(task.id)}">View ${media.length} ${media.length === 1 ? 'video' : 'videos'} ↓</button><details class="task-scope"><summary>Task &amp; video scope</summary><p>${escape(task.success_criteria)}</p><p class="demo-scope">${escape(task.demo_scope)}</p><p>Complete type: ${escape(task.split_counts.Easy || 0)} Easy · ${escape(task.split_counts.Hard || 0)} Hard · ${escape(task.ep20_count)} in EP-20</p></details></div></article>`;
    }).join('');
    bindMedia(grid);
    $$('[data-task-media]',grid).forEach((select) => select.addEventListener('change', () => {
      const card = select.closest('.task-card');
      const frame = $('.task-media',card);
      const badge = $('.task-badge',frame).outerHTML;
      const selected = mediaById(select.value);
      clearVideos(frame); frame.innerHTML = mediaMarkup(selected) + badge;
      $('.selected-media-caption',card).innerHTML = mediaCaptionMarkup(selected);
      bindMedia(frame);
    }));
  }

  function renderIndex(index) {
    if (!Array.isArray(index.task_results) || index.task_results.length !== 100) throw new Error('Incomplete task index');
    $('#ep100-table').innerHTML = `<table class="result-table index-table"><thead><tr><th>Index</th><th>Type / task</th><th>Embodiment</th><th>Split</th><th>EP-20</th></tr></thead><tbody>${index.task_results.map((task) => `<tr><td>${escape(task.index)}</td><td><strong>${escape(task.type)} · ${escape(task.title)}</strong><code>${escape(task.task_id)}</code></td><td>${escape(task.embodiment)}</td><td>${escape(task.split)}</td><td>${task.ep20 ? 'Included' : '—'}</td></tr>`).join('')}</tbody></table>`;
  }

  function renderResults() {
    const experiment = state.experiment;
    const subset = experiment.subsets[state.subset];
    const cards = [['SUITE-BALANCED PASS@1', percent(subset.suite_balanced_pass_at_1), 'First valid opportunity'],['SUITE-BALANCED PASS@2',percent(subset.suite_balanced_pass_at_2),'Within two valid opportunities'],['TASKS / CONDITIONS',`${subset.tasks} / ${subset.conditions}`,'Four prescribed conditions per task'],['SCORED ATTEMPTS',String(subset.valid_attempts),'Stop at first success; at most two']];
    $('#result-highlights').innerHTML = cards.map(([label,value,note]) => `<article class="highlight-card"><span class="highlight-label">${label}</span><strong>${value}</strong><p>${note}</p></article>`).join('');
    $('#suite-chart').innerHTML = `<div class="chart-axis"><span>Suite / success rate</span><span>0</span><span>100%</span></div>${suites.map((name) => {
      const result = subset.suites[name];
      return `<details class="suite-result"><summary><span class="suite-result-name">${name}<small>${result.tasks} tasks · ${result.conditions} conditions</small></span><span class="bar-pair"><span class="bar-track"><span class="bar-fill first" style="width:${result.pass_at_1*100}%"></span><span class="bar-number">${percent(result.pass_at_1)}<span class="sr-only"> Pass@1</span></span></span><span class="bar-track"><span class="bar-fill second" style="width:${result.pass_at_2*100}%"></span><span class="bar-number">${percent(result.pass_at_2)}<span class="sr-only"> Pass@2</span></span></span></span><span class="suite-expand" aria-hidden="true">+</span></summary><div class="suite-result-detail"><p><strong>${result.first_successes} / ${result.conditions}</strong> conditions succeed on attempt one; <strong>${result.within_two_successes} / ${result.conditions}</strong> succeed within two. ${result.valid_attempts} valid opportunities were used.</p><p>Tasks and their four conditions carry equal weight within ${name}. The headline ${state.subset} score then averages the five suites equally.</p></div></details>`;
    }).join('')}`;
    $('#subset-detail').innerHTML = `<p><strong>${state.subset}</strong> · Pooled condition rates: ${percent(subset.pooled_pass_at_1)} Pass@1 (${subset.first_successes}/${subset.conditions}) and ${percent(subset.pooled_pass_at_2)} Pass@2 (${subset.within_two_successes}/${subset.conditions}). These pooled rates are not the suite-balanced headline scores.</p>${state.subset === 'EP-20' ? '<p>EP-20 reuses records from ten Easy and ten Hard tasks. Its pilot-informed selection supports compact diagnosis, not an unbiased estimate of full-set performance.</p>' : ''}`;
  }

  function renderAudit() {
    const ex = state.experiment;
    const audit = ex.audit_counts;
    $('#audit-content').innerHTML = `<div class="evaluation-summary"><section><h4>Setting</h4><p>Codex / ${escape(ex.model)} · ${escape(ex.reasoning)} reasoning · ${escape(ex.access_level)} access with privileged observations. The agent uses the public SDK without reference solutions or pretrained action controllers.</p><p>Each attempt allows ${(ex.protocol.token_budget/1e6).toFixed(0)}M tokens, including cached input, and ${ex.protocol.image_budget} images. These are budgets, not measured consumption; execution limits vary by task.</p></section><section><h4>Scoring</h4><p>EP-100 covers 400 prescribed conditions and ${audit.valid} scored attempts. Pass@1 uses the first valid opportunity; Pass@2 uses the first two, stopping after success. Ordinary failures and budget exhaustion count.</p><p>The audit excludes ${audit.excluded} confirmed infrastructure incidents; ${audit.superseded} extra attempts outside the scoring window are unscored.</p></section><section><h4>Scope</h4><p>One model and agent configuration. Attempts use separate agent sessions; complete simulator and host-cache isolation has not been certified. These results do not establish a model ranking or token-efficiency comparison.</p></section></div>`;
  }

  function renderMedia() {
    const root = $('#media-grid'); clearVideos(root);
    const task = state.tasks.find((entry) => entry.id === state.mediaTask);
    const items = state.media.filter((item) => item.path && (task ? task.media.includes(item.id) : item.showcase !== false) && (state.mediaSuite === 'all' || suiteFor(item) === state.mediaSuite));
    $('#media-count').textContent = `${items.length} videos · ${task ? task.title : state.mediaSuite === 'all' ? 'All suites' : state.mediaSuite}`;
    root.innerHTML = items.map((item) => `<article class="media-card" data-media-id="${escape(item.id)}"><div class="evidence-frame">${mediaMarkup(item)}</div><div class="media-info"><small>${escape(suiteFor(item))}</small><h3>${escape(item.title)}</h3><p>${mediaCaptionMarkup(item)}</p><span class="media-embodiment">${escape(item.embodiment || '')}</span>${isVideo(item) ? `<a class="media-open" href="${escape(item.path)}" target="_blank" rel="noopener">Open video ↗</a>` : ''}</div></article>`).join('');
    if (!items.length) root.innerHTML = '<p class="empty-state">No videos are available for this selection.</p>';
    bindMedia(root);
  }

  function setupHero() {
    const media = mediaById('embodied-playground-film');
    const video = $('#hero-video'); const button = $('.stage-play');
    if (!media?.path) { button.textContent = 'Video unavailable'; button.disabled = true; return; }
    const title = media.title || $('#hero-media-title').textContent;
    $('#hero-media-title').textContent = title;
    $('.hero-stage').setAttribute('aria-label', title);
    video.setAttribute('aria-label', title);
    $('#hero-poster').alt = title;
    video.dataset.videoSrc = media.path;
    video.poster = media.poster || '';
    $('#hero-poster').src = media.poster || media.fallback;
    button.addEventListener('click', async () => { if (video.paused) await playVideo(video); else video.pause(); });
    const update = () => {
      if (!video.paused) video.classList.add('is-ready');
      button.querySelector('span:last-child').textContent = video.paused ? 'PLAY VIDEO' : 'PAUSE VIDEO';
      button.setAttribute('aria-label', `${video.paused ? 'Play' : 'Pause'} ${title}`);
      button.setAttribute('aria-pressed', String(!video.paused));
    };
    video.addEventListener('play', update); video.addEventListener('pause', update); update();
    video.addEventListener('error', () => { button.hidden = false; button.textContent = 'Video unavailable'; button.disabled = true; });
    videoObserver?.observe(video);
  }

  function selectSuite(suite) {
    state.suite = suite;
    $$('[data-filter-group="suite"]').forEach((button) => { const active = button.dataset.filter === suite; button.classList.toggle('active',active); button.setAttribute('aria-pressed',String(active)); });
    renderTasks();
  }

  function setupInteractions() {
    $$('[data-filter-group]').forEach((button) => button.addEventListener('click', () => {
      const group = button.dataset.filterGroup; state[group] = button.dataset.filter;
      $$(`[data-filter-group="${group}"]`).forEach((other) => { const active = other === button; other.classList.toggle('active',active); other.setAttribute('aria-pressed',String(active)); }); renderTasks();
    }));
    $$('[data-suite-link]').forEach((link) => link.addEventListener('click', () => selectSuite(link.dataset.suiteLink)));
    const tabs = $$('[data-subset]');
    const activate = (tab, focus = false) => {
      if (!state.experiment) return;
      state.subset = tab.dataset.subset;
      tabs.forEach((button) => { const selected = button === tab; button.classList.toggle('active',selected); button.setAttribute('aria-selected',String(selected)); button.tabIndex = selected ? 0 : -1; });
      $('#subset-panel').setAttribute('aria-labelledby',tab.id); renderResults(); if (focus) tab.focus();
    };
    tabs.forEach((tab,index) => {
      tab.addEventListener('click', () => activate(tab));
      tab.addEventListener('keydown', (event) => { let target; if (event.key === 'ArrowRight') target = (index+1)%tabs.length; if (event.key === 'ArrowLeft') target=(index+tabs.length-1)%tabs.length; if(event.key==='Home')target=0;if(event.key==='End')target=tabs.length-1;if(target!==undefined){event.preventDefault();activate(tabs[target],true);} });
    });
    const selectMedia = (suite, task = 'all') => {
      state.mediaSuite = suite; state.mediaTask = task; $('#media-task').value = task;
      $$('[data-media-suite]').forEach((other) => {const active=other.dataset.mediaSuite===suite;other.classList.toggle('active',active);other.setAttribute('aria-pressed',String(active));}); renderMedia();
    };
    $$('[data-media-suite]').forEach((button) => button.addEventListener('click', () => selectMedia(button.dataset.mediaSuite)));
    $('#media-task').addEventListener('change', (event) => { const task=state.tasks.find((entry)=>entry.id===event.target.value);selectMedia(task?.suite || 'all',task?.id || 'all'); });
    $('#task-grid').addEventListener('click', (event) => {
      const button=event.target.closest('[data-media-task]');if(!button)return;
      const task=state.tasks.find((entry)=>entry.id===button.dataset.mediaTask);selectMedia(task.suite,task.id);
      $('#evidence').scrollIntoView({behavior: reduced.matches ? 'instant' : 'smooth'});$('#media-task').focus({preventScroll:true});
    });
    reduced.addEventListener('change', () => { if (reduced.matches) $$('video').forEach((video) => video.pause()); });
    document.addEventListener('visibilitychange', () => { if (document.hidden) $$('video').forEach((video) => video.pause()); });
  }

  function setupChrome() {
    const topbar=$('[data-topbar]'); const progress=$('.site-progress span');
    const navLinks = $$('.main-nav a[href^="#"], .mobile-nav a[href^="#"]');
    const sectionIds = [...new Set(navLinks.map((link) => link.hash.slice(1)))];
    const sections = sectionIds.map((id) => document.getElementById(id)).filter(Boolean);
    const update = () => {
      topbar.classList.toggle('is-scrolled', window.scrollY > 20);
      const total = document.documentElement.scrollHeight - innerHeight;
      progress.style.width = `${total > 0 ? window.scrollY / total * 100 : 0}%`;
      const readingLine = topbar.getBoundingClientRect().bottom + Math.min(innerHeight * .18, 150);
      let active = sections[0]?.id;
      for (const section of sections) { if (section.getBoundingClientRect().top <= readingLine) active = section.id; }
      navLinks.forEach((link) => {
        const current = link.hash === `#${active}`;
        if (current) link.setAttribute('aria-current', 'location'); else link.removeAttribute('aria-current');
      });
    };
    let pendingFrame = false;
    const scheduleUpdate = () => {
      if (pendingFrame) return;
      pendingFrame = true;
      requestAnimationFrame(() => { pendingFrame = false; update(); });
    };
    update();
    window.addEventListener('scroll', scheduleUpdate, {passive:true});
    window.addEventListener('resize', scheduleUpdate);
    window.addEventListener('hashchange', scheduleUpdate);
    window.addEventListener('load', scheduleUpdate);
    if ('ResizeObserver' in window) new ResizeObserver(scheduleUpdate).observe(document.querySelector('main'));
    const menu=$('#mobile-nav'); const toggle=$('.menu-toggle');
    const close=()=>{menu.classList.remove('is-open');menu.inert=true;toggle.setAttribute('aria-expanded','false');};
    toggle.addEventListener('click',()=>{const open=!menu.classList.contains('is-open');menu.classList.toggle('is-open',open);menu.inert=!open;toggle.setAttribute('aria-expanded',String(open));});
    $$('a',menu).forEach((link)=>link.addEventListener('click',close));
    document.addEventListener('keydown',(event)=>{if(event.key==='Escape'&&menu.classList.contains('is-open')){close();toggle.focus();}});
    if('IntersectionObserver' in window){const observer=new IntersectionObserver((entries)=>entries.forEach(({target,isIntersecting})=>{if(isIntersecting){target.classList.add('is-visible');observer.unobserve(target);}}),{threshold:.08});$$('.reveal').forEach((el)=>observer.observe(el));}else{$$('.reveal').forEach((el)=>el.classList.add('is-visible'));}
  }

  function setupCommunityLinks() {
    const dialog = $('#wechat-dialog');
    $('#wechat-group-link').addEventListener('click', (event) => {
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      dialog.showModal();
      document.documentElement.classList.add('wechat-open');
    });
    $('.wechat-close', dialog).addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', (event) => {
      if (event.target !== dialog) return;
      const bounds = dialog.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
    });
    dialog.addEventListener('close', () => document.documentElement.classList.remove('wechat-open'));
  }

  function setupRobotPointer() {
    const mouse = window.matchMedia('(hover: hover) and (pointer: fine)');
    const robot = document.createElement('div');
    robot.className = 'robot-pointer';
    robot.setAttribute('aria-hidden', 'true');
    robot.innerHTML = `<svg width="56" height="63" viewBox="0 0 64 72" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="pointer-shell" x1="18" y1="12" x2="46" y2="59" gradientUnits="userSpaceOnUse">
          <stop stop-color="#fbfcf8"/><stop offset=".6" stop-color="#f6f8f5"/><stop offset="1" stop-color="#dce7dc"/>
        </linearGradient>
        <linearGradient id="pointer-screen" x1="20" y1="16" x2="43" y2="35" gradientUnits="userSpaceOnUse">
          <stop stop-color="#315958"/><stop offset=".55" stop-color="#172f32"/><stop offset="1" stop-color="#264546"/>
        </linearGradient>
        <linearGradient id="pointer-chest" x1="32" y1="43" x2="32" y2="55" gradientUnits="userSpaceOnUse">
          <stop stop-color="#a7cf79"/><stop offset="1" stop-color="#5c8d38"/>
        </linearGradient>
        <filter id="pointer-eye-glow" x="-150%" y="-80%" width="400%" height="260%">
          <feGaussianBlur stdDeviation="1"/>
        </filter>
      </defs>
      <ellipse cx="32" cy="67" rx="16" ry="2.3" fill="#668578" opacity=".16"/>
      <g class="robot-pointer-body" stroke="#526b61" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round">
        <g class="robot-arm robot-arm-left">
          <path d="M22 40C17 38 10 44 7 51C5 57 10 59 15 55C19 52 23 46 22 40Z" fill="url(#pointer-shell)"/>
          <path d="M10 53q3-1 5-4" stroke="#dbe5d8" stroke-width="2.4"/>
        </g>
        <g class="robot-arm robot-arm-right">
          <path d="M43 41C46 38 49 33 54 32C60 31 61 36 58 41C55 47 50 50 45 48Z" fill="url(#pointer-shell)"/>
          <path d="M49 45q5-2 7-6" stroke="#dbe5d8" stroke-width="2.4"/>
        </g>
        <path d="M19 36C15 45 20 57 29 61C31 62 33 62 35 61C44 57 49 45 45 36Z" fill="url(#pointer-shell)"/>
        <path d="M24 55q8 9 16-1" stroke="#d4dfd0" stroke-width="2"/>
        <path d="M24 43Q32 40 40 43C43 48 39 54 32 55C25 54 21 48 24 43Z" fill="url(#pointer-chest)"/>
        <path d="M26 44q6-2 12 0" stroke="#dfedcc" stroke-width="1.5"/>
        <path d="M26 10V7C26 3 38 3 38 7V10" fill="#fbfcf8"/>
        <rect x="8" y="19" width="6" height="14" rx="2.5" fill="#edf3e8"/>
        <rect x="50" y="19" width="6" height="14" rx="2.5" fill="#edf3e8"/>
        <path d="M13 15C14 8 24 8 32 8C40 8 50 8 51 15L52 31C52 39 43 41 32 41C21 41 12 39 12 31Z" fill="url(#pointer-shell)"/>
        <path d="M19 13q12-5 25 0" stroke="#fbfcf8" stroke-width="2.5"/>
        <path d="M18 19C18 14 24 13 32 13C40 13 46 14 46 19V30C46 35 40 37 32 37C24 37 18 35 18 30Z" fill="url(#pointer-screen)"/>
        <path d="M21 20q0-4 7-4" stroke="#607e71" stroke-width="1.5"/>
        <g stroke="none" fill="#b5d990" filter="url(#pointer-eye-glow)">
          <ellipse cx="25" cy="24" rx="3" ry="5"/><ellipse cx="39" cy="24" rx="3" ry="5"/>
        </g>
        <g stroke="none">
          <ellipse cx="25" cy="24" rx="2.2" ry="4.4" fill="#c2e49f"/>
          <ellipse cx="39" cy="24" rx="2.2" ry="4.4" fill="#c2e49f"/>
          <ellipse cx="24.5" cy="22.8" rx=".8" ry="1.6" fill="#f3f9e9"/>
          <ellipse cx="38.5" cy="22.8" rx=".8" ry="1.6" fill="#f3f9e9"/>
        </g>
        <path d="M29 31q3 2 6 0" stroke="#9bbe89" stroke-width="1"/>
      </g>
    </svg>`;
    document.body.append(robot);
    const leftArm = $('.robot-arm-left', robot);
    const rightArm = $('.robot-arm-right', robot);
    let frame = 0;
    let x = 0;
    let y = 0;
    let animations = [];
    const enabled = () => mouse.matches && !reduced.matches;
    const hide = () => {
      cancelAnimationFrame(frame); frame = 0;
      robot.classList.remove('is-visible');
      animations.forEach((animation) => animation.cancel());
      animations = [];
    };
    const move = (event) => {
      if (event.pointerType !== 'mouse' || !enabled()) { hide(); return; }
      x = event.clientX; y = event.clientY;
      if (frame) return;
      frame = requestAnimationFrame(() => {
        frame = 0;
        // Keep the robot beside the click target and inside the viewport.
        const left = x + 16 + 56 > innerWidth ? x - 72 : x + 16;
        const top = y + 12 + 63 > innerHeight ? y - 75 : y + 12;
        robot.style.transform = `translate3d(${Math.max(0, left)}px, ${Math.max(0, top)}px, 0)`;
        robot.classList.add('is-visible');
      });
    };
    window.addEventListener('pointermove', move, { passive: true });
    window.addEventListener('pointerdown', (event) => {
      move(event);
      if (event.pointerType !== 'mouse' || event.button !== 0 || !enabled()) return;
      animations.forEach((animation) => animation.cancel());
      animations = [[leftArm, 1], [rightArm, -.45]].map(([arm, direction]) => arm.animate(
        [0, 105, 65, 110, 65, 0].map((angle) => ({ transform: `rotate(${angle * direction}deg)` })),
        { duration: 700, easing: 'ease-in-out' }
      ));
    }, { passive: true });
    window.addEventListener('pointerout', (event) => { if (!event.relatedTarget) hide(); });
    window.addEventListener('blur', hide);
    document.addEventListener('visibilitychange', () => { if (document.hidden) hide(); });
    document.addEventListener('keydown', (event) => { if (event.key === 'Tab') hide(); });
    mouse.addEventListener('change', hide);
    reduced.addEventListener('change', hide);
  }

  async function init() {
    setupChrome(); setupInteractions(); setupCommunityLinks(); setupRobotPointer();
    const [tasks,media,results,index]=await Promise.allSettled([loadJSON('data/tasks.json'),loadJSON('data/media.json'),loadJSON('data/results.json'),loadJSON('data/ep100-index.json')]);
    if(media.status==='fulfilled'&&Array.isArray(media.value))state.media=media.value;
    if(tasks.status==='fulfilled'&&Array.isArray(tasks.value)){state.tasks=tasks.value;renderTasks();}else{$('#task-grid').innerHTML='<p class="empty-state">Task data could not be loaded. Please reload the page or open the task index.</p>';}
    $('#media-task').innerHTML = '<option value="all">All task types</option>' + state.tasks.map((task) => `<option value="${escape(task.id)}">${escape(task.title)}</option>`).join('');
    if(media.status==='fulfilled')renderMedia();else $('#media-grid').innerHTML='<p class="empty-state">Video metadata could not be loaded. Please reload the page.</p>';
    try {
      if(results.status!=='fulfilled'||results.value.schema_version!==2)throw new Error('Result data unavailable');
      const experiment=results.value.experiments.find((item)=>item.id===results.value.default_experiment);
      if(!experiment||!['EP-100','EP-Easy','EP-Hard','EP-20'].every((name)=>Number.isFinite(experiment.subsets?.[name]?.suite_balanced_pass_at_1)&&Number.isFinite(experiment.subsets?.[name]?.suite_balanced_pass_at_2)))throw new Error('Incomplete result data');
      state.experiment=experiment;renderResults();renderAudit();
    } catch { state.experiment=null;$('#audited-results').hidden=true;const message=$('#results-unavailable');message.hidden=false;message.textContent='Audited result data could not be loaded. No scores are substituted. Reload the page or open the result JSON in Resources.'; }
    try { if(index.status!=='fulfilled')throw new Error('No index');renderIndex(index.value); } catch { $('#ep100-table').textContent='The task index could not be loaded. Please use the JSON download above.'; }
    setupHero();document.body.dataset.ready='true';
  }
  document.addEventListener('DOMContentLoaded',init);
})();
