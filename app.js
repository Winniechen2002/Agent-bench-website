'use strict';

const zh = {
  skip:'跳转到正文',navOverview:'项目概览',navTasks:'任务图谱',navProtocol:'评测协议',navReport:'技术报告 ↗',
  heroEyebrow:'面向具身智能体的研究平台',heroTitle:'让智能，<br>付诸<em>行动。</em>',
  heroDescription:'让规划接受物理世界的检验。评测智能体在长时程机器人任务中感知、推理、调用工具与执行动作的能力。',
  explore:'探索评测任务 <span aria-hidden="true">↗</span>',readReport:'阅读技术报告 ↗',heroNote:'基于物理仿真，研究闭环推理。',
  heroCaptionLabel:'01 / 从符号规划到物理执行',heroCaption:'每一步，都影响下一步。',sceneRender:'场景渲染',
  metricTasks:'核心任务定义',metricGroups:'任务图谱分组',metricLevels:'明确的能力权限等级',metricNoteLabel:'更清晰的评测边界',metricNote:'明确智能体能看到什么、<br>能使用什么，以及实际完成了什么。',
  questionLabel:'研究问题',questionTitle:'正确的计划，<br>只是开始。',questionDescription:'面对接触、误差与失败，智能体能否完成整个计划？Agent Bench 将符号目标连接到物理执行，并明确观测、工具、动作与预算的边界。',
  p1title:'跨步骤推理',p1body:'跟踪任务状态，在相互依赖的动作之间持续维护约束。',p2title:'形成执行闭环',p2body:'观察动作结果，诊断失败，并调整下一步计划。',p3title:'以物理证据判定',p3body:'由独立于智能体的评测器判断任务是否真正完成。',
  atlasLabel:'任务图谱',atlasTitle:'小小的场景，<br>长时程的挑战。',atlasDescription:'浏览涵盖操作与物理推理的 200 项任务定义。每项任务都明确描述场景、目标与评测条件。',
  filterAll:'全部任务 <span>200</span>',filterBirds:'物理推理 <span>100</span>',filterPanda:'Panda 汉诺塔 <span>40</span>',filterHand:'Sharpa 汉诺塔 <span>40</span>',filterCube:'二阶魔方 <span>20</span>',
  atlasScope:'场景示意图 · 执行状态见各任务详情',countNote:'不同机器人变体单独计数；随机种子与观测模式不增加任务数量。',loadMore:'显示更多任务 ↓',
  protocolLabel:'评测约定',protocolTitle:'开放的智能体，<br>明确的边界。',protocolDescription:'v1 平台将智能体、工具、物理环境与评分器分离。目前接入孔明锁与单 Panda 魔方任务。',
  archAgentLabel:'隔离工作区',archAgent:'智能体',archAgentBody:'观察 · 规划 · 行动',memory:'记忆',tools:'获准工具',sdk:'公共 SDK',actionObs:'动作 / 观测',
  archGatewayLabel:'可信边界',archGateway:'协议网关',archGatewayBody:'权限 · 预算 · 校验',archSim:'物理环境',archSimBody:'机器人控制与传感反馈',archScorer:'独立评分器',archScorerBody:'私有状态 · 物理证据',
  protocolFooter:'智能体可见的反馈与私有评分证据保持分离。',platformDocs:'平台文档 ↗',
  levelsLabel:'能力等级',levelsTitle:'工具改变时，<br>能力如何变化？',levelsDescription:'四个权限等级明确可用的辅助能力。任务难度、平台观测配置与能力等级是不同维度。',readRules:'查看能力等级规则 ↗',levelFootnote:'所有等级均未授权额外的预训练动作策略工具。工具插件列表为空，也不代表满足 L0 要求。',
  evidenceLabel:'证据与适用范围',evidenceTitle:'可以核查的进展。',evidenceDescription:'环境覆盖、参考控制器执行与模型表现回答不同的问题，因此分别报告。',evidenceCol1:'证据',evidenceCol2:'记录范围',evidenceCol3:'如何解读',
  ev1name:'核心任务定义',ev1scope:'20 项魔方 + 100 项物理推理 + 80 项汉诺塔变体。',ev1limit:'代表任务目录覆盖，并非 200 项任务已通关。',
  ev2name:'历史完整执行通过',ev2scope:'81 项物理推理任务和 1 项 Panda 汉诺塔任务，在记录的工程控制条件下完成。',ev2limit:'于 2026 年 10 月 8 日审查。不是模型成功率，也不是新四次测试协议成绩。',
  ev3name:'孔明锁参考控制器通关',ev3scope:'通过公共 SDK 完成装配与拆解，并以独立进程回放核查。',ev3limit:'属于 200 项核心任务之外的扩展证据，使用特权参考控制器。',
  integration:'集成验证',ev4name:'真实编程智能体检查',ev4scope:'核验了图像送达、自编控制代码、重新观测和显式结束。',ev4limit:'集成检查通过，但未解开孔明锁。不据此建立模型排行榜。',
  evidenceNote:'历史运行保留原始条件。仿真场景图不代表任务执行成功。',inspectEvidence:'查看证据说明 ↗',
  reportLabel:'技术报告 · 草稿 V0.1',reportTitle:'深入了解 Agent Bench。',reportDescription:'任务设计、评测约定、平台架构，<br>以及支撑评测的证据。',downloadPdf:'下载英文 PDF ↓',
  footerNote:'面向具身智能的研究平台。',provenance:'来源与版本 ↗',footerScope:'仿真研究 · 不作真实硬件性能声明'
};
const levels = {
  en:[
    ['MODEL-ONLY BASELINE','Direct model control','The evaluated model consumes allowed RGB and proprioception, then emits robot actions directly. No auxiliary tools, including vision tools or code execution.',['RGB + proprioception','Model-output actions']],
    ['OBSERVATION-GROUNDED TOOLS','Perceive, plan, and program','Adds vision, geometry, inverse kinematics, retargeting, motion planning, and RL or optimization inside a proxy simulator reconstructed from legal observations.',['Vision & geometry','IK & motion planning','Observation-derived proxy']],
    ['PRETRAINED GRASP ASSISTANCE','Add grasp and contact models','Inherits L1 and adds pretrained grasp or contact-generation models. The observation boundary and shared physical constraints still apply.',['All L1 tools','Grasp generation','Contact generation']],
    ['PRIVILEGED INFORMATION','Inspect simulator state','Inherits L1–L2 and adds read access to privileged simulator fields exposed by the selected interface. It does not grant permission to change hidden physical state.',['All L1–L2 tools','Exposed privileged state','Read-only access']]
  ],
  zh:[
    ['纯模型基线','模型直接控制','被测模型读取允许的 RGB 和本体感知，直接输出机器人动作。不使用额外工具，包括视觉工具或代码执行。',['RGB 与本体感知','模型输出动作']],
    ['来自合法观测的工具','感知、规划与编程','增加视觉、几何、逆运动学、动作重定向和运动规划；也可在由合法观测重建的代理仿真器内使用强化学习或优化。',['视觉与几何','逆运动学与规划','观测重建的代理仿真']],
    ['预训练抓取辅助','引入抓取与接触模型','继承 L1，并增加预训练抓取或接触生成模型。仍遵守观测边界与共有物理约束。',['全部 L1 工具','抓取生成','接触生成']],
    ['特权信息','读取仿真器状态','继承 L1–L2，并可读取所选接口明确暴露的仿真器特权字段。该权限不允许修改隐藏物理状态。',['全部 L1–L2 工具','接口暴露的特权状态','只读访问']]
  ]
};
const groupNames={en:{birds:'Physical reasoning',panda:'Panda · Tower of Hanoi',hand:'Sharpa · Tower of Hanoi',cube:'Bimanual · Pocket cube'},zh:{birds:'物理推理',panda:'Panda · 汉诺塔',hand:'Sharpa · 汉诺塔',cube:'双手操作 · 二阶魔方'}};
const english = new Map([...document.querySelectorAll('[data-i18n]')].map(el=>[el,el.innerHTML]));
let lang='en',catalog=[],filter='all',visible=8,selectedLevel=0,activeTask=null,loadFailed=false;
try{if(localStorage.getItem('agentbench-language')==='zh')lang='zh';}catch{/* Storage is optional. */}
const $=s=>document.querySelector(s);
const escapeHTML=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function renderLevel(){
  const [label,title,body,chips]=levels[lang][selectedLevel];
  $('#level-panel').innerHTML=`<span class="mono">${label}</span><h3>${title}</h3><p>${body}</p><div class="permission-chips">${chips.map(c=>`<span>${c}</span>`).join('')}</div>`;
  $('#level-panel').setAttribute('aria-labelledby',`tab-${selectedLevel}`);
  document.querySelectorAll('[data-level]').forEach(b=>{const active=Number(b.dataset.level)===selectedLevel;b.setAttribute('aria-selected',active);b.tabIndex=active?0:-1;});
}
function setLanguage(){
  document.documentElement.lang=lang==='zh'?'zh-CN':'en';
  english.forEach((value,el)=>{el.innerHTML=lang==='zh'?(zh[el.dataset.i18n]??value):value;});
  $('#language').textContent=lang==='zh'?'EN':'中文';
  $('#language').setAttribute('aria-label',lang==='zh'?'Switch to English':'切换到中文');
  $('#search').placeholder=lang==='zh'?'搜索任务或编号':'Search tasks or IDs';
  $('#search').setAttribute('aria-label',$('#search').placeholder);
  $('#close-dialog').setAttribute('aria-label',lang==='zh'?'关闭任务详情':'Close task details');
  document.title=lang==='zh'?'Agent Bench — 让智能付诸行动':'Agent Bench — Intelligence, put into motion.';
  renderLevel();renderTasks();if(activeTask)renderDialog(activeTask);
  try{localStorage.setItem('agentbench-language',lang);}catch{/* Storage is optional. */}
}
function filteredTasks(){
  const q=$('#search').value.trim().toLowerCase();
  return catalog.filter(t=>(filter==='all'||t.group===filter)&&(!q||`${t.id} ${t.en.title} ${t.zh.title} ${t.en.subtitle} ${t.zh.subtitle} ${groupNames.en[t.group]} ${groupNames.zh[t.group]}`.toLowerCase().includes(q)));
}
function renderTasks(){
  const grid=$('#task-grid');
  if(!catalog.length){
    if(loadFailed){grid.innerHTML=`<div class="empty-state">${lang==='zh'?'任务目录暂时无法加载，请刷新页面或下载数据。':'The task catalog could not be loaded. Refresh the page or download the data.'}<br><a class="text-link" href="data/catalog.json">${lang==='zh'?'下载任务数据 ↗':'Download task data ↗'}</a></div>`;$('#result-count').textContent=lang==='zh'?'目录加载失败':'Catalog unavailable';grid.setAttribute('aria-busy','false');}
    return;
  }
  const tasks=filteredTasks(),shown=tasks.slice(0,visible);
  grid.setAttribute('aria-busy','false');
  grid.innerHTML=shown.map(t=>`<button class="task-card" data-task="${escapeHTML(t.id)}" aria-haspopup="dialog" aria-label="${escapeHTML(`${t.id} — ${t[lang].title}`)}"><div class="task-image"><img src="${escapeHTML(t.image)}" alt="${escapeHTML(t[lang].title)} — ${lang==='zh'?'仿真场景图':'simulation scene render'}" width="${t.width}" height="${t.height}" loading="lazy"><span class="task-tag">${escapeHTML(t.id)}</span><span class="task-open" aria-hidden="true">↗</span></div><p class="task-category">${groupNames[lang][t.group]}</p><h3>${escapeHTML(t[lang].title)}</h3><div class="task-status ${t.completed?'passed':''}">${lang==='zh'?(t.completed?'历史工程执行通过':'未记录完整执行通过'):(t.completed?'Historical engineering pass':'No complete pass recorded')}</div></button>`).join('');
  if(!tasks.length)grid.innerHTML=`<div class="empty-state">${lang==='zh'?'没有匹配的任务。请尝试其他关键词或切换分类。':'No matching tasks. Try another keyword or choose a different family.'}</div>`;
  $('#result-count').textContent=lang==='zh'?`显示 ${shown.length} / ${tasks.length} 项任务`:`Showing ${shown.length} of ${tasks.length} tasks`;
  $('#load-more').hidden=shown.length>=tasks.length;
}
function renderDialog(t){
  const d=t[lang];
  $('#dialog-content').innerHTML=`<div class="dialog-layout"><img class="dialog-image" src="${escapeHTML(t.image)}" alt="${escapeHTML(d.title)}"><div class="dialog-details"><span class="mono">${escapeHTML(t.id)} / ${groupNames[lang][t.group]}</span><h2 id="dialog-title">${escapeHTML(d.title)}</h2><p class="dialog-subtitle">${escapeHTML(d.subtitle)}</p><dl>${d.lines.map(([k,v])=>`<dt>${escapeHTML(k)}</dt><dd>${escapeHTML(v)}</dd>`).join('')}</dl><p class="dialog-evidence"><b>${lang==='zh'?'执行证据':'Execution evidence'}</b><br>${escapeHTML(d.status)}</p><p class="dialog-note">${lang==='zh'?'场景图为原生仿真渲染，不是执行录像。历史记录不能作为当前四次测试协议下的成绩。':'Native simulation illustration, not a rollout recording. Historical passes are not scores under the current four-trial protocol.'}</p><a class="text-link" href="report.html#evidence">${lang==='zh'?'阅读证据说明 ↗':'Read the evidence notes ↗'}</a></div></div>`;
}
$('#language').addEventListener('click',()=>{lang=lang==='en'?'zh':'en';setLanguage();});
document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{filter=b.dataset.filter;visible=8;document.querySelectorAll('[data-filter]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',x===b);});renderTasks();}));
$('#search').addEventListener('input',()=>{visible=8;renderTasks();});
$('#load-more').addEventListener('click',()=>{const before=Math.min(visible,filteredTasks().length);visible+=8;renderTasks();const added=$('#task-grid').children[before];if(added)added.focus({preventScroll:true});});
$('#task-grid').addEventListener('click',e=>{const b=e.target.closest('[data-task]');if(!b)return;activeTask=catalog.find(t=>t.id===b.dataset.task);renderDialog(activeTask);$('#task-dialog').showModal();document.body.classList.add('modal-open');$('#close-dialog').focus();});
$('#close-dialog').addEventListener('click',()=>$('#task-dialog').close());
$('#task-dialog').addEventListener('click',e=>{if(e.target!==$('#task-dialog'))return;const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close();});
$('#task-dialog').addEventListener('close',()=>{activeTask=null;document.body.classList.remove('modal-open');});
document.querySelectorAll('[data-level]').forEach(b=>{
  b.addEventListener('click',()=>{selectedLevel=Number(b.dataset.level);renderLevel();});
  b.addEventListener('keydown',e=>{let n=selectedLevel;if(e.key==='ArrowRight')n=(n+1)%4;else if(e.key==='ArrowLeft')n=(n+3)%4;else if(e.key==='Home')n=0;else if(e.key==='End')n=3;else return;e.preventDefault();selectedLevel=n;renderLevel();$(`#tab-${n}`).focus();});
});
setLanguage();
fetch('data/catalog.json').then(r=>{if(!r.ok)throw new Error(`Catalog: ${r.status}`);return r.json();}).then(data=>{
  if(!Array.isArray(data)||data.length!==200)throw new Error('Invalid catalog');
  const featured=['HP-H03','C01-AL','A024','HN-H02','A039','C14-SH','A031','HP-H17'];
  const rank=id=>{const i=featured.indexOf(id);return i<0?featured.length:i;};
  catalog=data.sort((a,b)=>rank(a.id)-rank(b.id));renderTasks();
}).catch(()=>{loadFailed=true;renderTasks();});
