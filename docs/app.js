/* No API keys or provider calls belong in this public dashboard. */
const $ = (selector) => document.querySelector(selector);
const state = {events: [], category: 'all', format: 'all', mode: 'live'};
const pkt = (date, options) => new Intl.DateTimeFormat('en-GB', {timeZone:'Asia/Karachi', ...options}).format(new Date(date));
const localDate = date => new Intl.DateTimeFormat('en-CA', {timeZone:'Asia/Karachi', year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(date));
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function safeURL(value) { try { const u = new URL(value); return ['https:', 'http:'].includes(u.protocol) && !u.username && !u.password ? u.href : ''; } catch { return ''; } }
const icon = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z"/><circle cx="12" cy="10" r="2.5"/></svg>';
const tagClasses = {'AI/ML':'tag-ai', Agents:'tag-agents', Sustainability:'tag-sustainability', Students:'tag-students'};
function card(event) {
  const demo = state.mode === 'demo';
  const newThisWeek = Date.now() - new Date(event.first_seen).getTime() < 7*86400000;
  const source = safeURL(event.source_url);
  const registration = safeURL(event.registration_url) || source;
  const verified = event.verification === 'verified';
  const categoryTags = event.categories.map(c => `<span class="tag ${tagClasses[c] || ''}">${escapeHTML(c)}</span>`).join('');
  return `<article class="event-card">
    <div class="card-top"><div class="date-tile"><div class="date-box"><span>${pkt(event.start,{month:'short'})}</span><strong>${pkt(event.start,{day:'2-digit'})}</strong></div><div class="date-meta">${pkt(event.start,{weekday:'long'})}<span>${event.time_known === false ? 'Time to be confirmed' : pkt(event.start,{hour:'numeric',minute:'2-digit',hour12:true})+' PKT'}</span></div></div>${newThisWeek ? '<span class="new-badge">New this week</span>' : ''}</div>
    <h3>${escapeHTML(event.title)}</h3><p class="organizer">${escapeHTML(event.organizer || 'Organizer not listed')}</p>
    <div class="event-meta"><span class="meta-line">${icon}${escapeHTML(event.format === 'online' ? 'Online' : event.venue || 'Karachi · venue TBC')}</span><span class="meta-line">${escapeHTML(event.cost || 'Cost not listed')}</span></div>
    <p class="description">${escapeHTML(event.description)}</p><div class="tags">${categoryTags}${event.student_only ? '<span class="tag tag-students">Students only</span>' : ''}</div>
    <div class="card-bottom"><div class="source-info"><span class="verification ${verified && !demo ? 'verified' : ''}">${demo ? '◇ SAMPLE EVENT' : verified ? '✓ SOURCE VERIFIED' : '◇ UNVERIFIED'}</span>${source && !demo ? `<a href="${escapeHTML(source)}" target="_blank" rel="noopener noreferrer">${escapeHTML(event.source_name)}</a>` : `<span style="display:block;margin-top:3px">${escapeHTML(event.source_name)}</span>`}</div>${demo || !registration ? '<button class="register" disabled>Sample event</button>' : `<a class="register" href="${escapeHTML(registration)}" target="_blank" rel="noopener noreferrer">${event.registration_url ? 'Register' : 'View event'}</a>`}</div>
    ${!demo ? `<details class="evidence"><summary>Evidence · ${Number(event.confidence)||0}/100</summary><p>${escapeHTML(event.verification_reason)}<br>Last checked: ${event.last_checked ? pkt(event.last_checked,{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'})+' PKT' : 'Not checked'}</p></details>` : ''}
  </article>`;
}
function render() {
  const now = Date.now(), query = $('#search').value.trim().toLowerCase();
  const range = $('#range').value, from = $('#date-from').value, to = $('#date-to').value;
  const invalidRange = range === 'custom' && from && to && from > to;
  $('#date-error').hidden = !invalidRange;
  const filtered = state.events.filter(e => {
    const date = new Date(e.start).getTime(), day = localDate(e.start);
    return !invalidRange && (state.category === 'all' || e.categories.includes(state.category)) &&
      (state.format === 'all' || e.format === state.format || e.format === 'hybrid') &&
      (!$('#free').checked || e.is_free === true) && (!$('#students').checked || e.student_only === true) &&
      (!$('#verified').checked || (state.mode !== 'demo' && e.verification === 'verified')) &&
      (!query || [e.title,e.description,e.organizer,e.venue,...e.categories].join(' ').toLowerCase().includes(query)) &&
      (range === 'all' || range === 'custom' || date < now + Number(range)*86400000) &&
      (range !== 'custom' || ((!from || day >= from) && (!to || day <= to)));
  }).sort((a,b) => $('#sort').value === 'new' ? new Date(b.first_seen)-new Date(a.first_seen) : new Date(a.start)-new Date(b.start));
  $('#result-count').textContent = `${filtered.length} event${filtered.length === 1 ? '' : 's'}`;
  $('#events-title').textContent = state.category === 'all' ? 'Coming up' : state.category === 'AI/ML' ? 'AI & machine learning' : state.category;
  $('#events').innerHTML = filtered.map(card).join('');
  $('#empty').hidden = filtered.length > 0;
  $('#events').setAttribute('aria-busy','false');
}
function resetFilters() {
  state.category = 'all'; state.format = 'all';
  for (const id of ['search','date-from','date-to']) $('#'+id).value = '';
  for (const id of ['free','students','verified']) $('#'+id).checked = false;
  $('#range').value = 'all'; $('#custom-dates').hidden = true;
  syncButtons(); render();
}
function syncButtons() {
  document.querySelectorAll('[data-category]').forEach(b => {const active = b.dataset.category === state.category; b.classList.toggle('active',active); b.setAttribute('aria-pressed',String(active));});
  document.querySelectorAll('[data-format]').forEach(b => {const active = b.dataset.format === state.format; b.classList.toggle('selected',active); b.setAttribute('aria-pressed',String(active));});
}
document.querySelectorAll('[data-category]').forEach(b => b.addEventListener('click', () => {state.category = b.dataset.category; syncButtons(); render();}));
document.querySelectorAll('[data-format]').forEach(b => b.addEventListener('click', () => {state.format = b.dataset.format; syncButtons(); render();}));
for (const id of ['search','range','free','students','verified','sort','date-from','date-to']) $('#'+id).addEventListener('input', () => {$('#custom-dates').hidden = $('#range').value !== 'custom'; render();});
$('#reset').addEventListener('click',resetFilters); $('#empty-reset').addEventListener('click',resetFilters);
$('#about-open').addEventListener('click', () => $('#about').showModal()); $('#about-close').addEventListener('click', () => $('#about').close());
$('#about').addEventListener('click', e => {if (e.target === $('#about') && (e.clientX < e.target.getBoundingClientRect().left || e.clientX > e.target.getBoundingClientRect().right || e.clientY < e.target.getBoundingClientRect().top || e.clientY > e.target.getBoundingClientRect().bottom)) $('#about').close();});
function setTheme(theme) {document.documentElement.dataset.theme = theme; $('#theme').setAttribute('aria-label',`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`);}
let initialTheme; try {initialTheme = localStorage.getItem('radar-theme');} catch {}
setTheme(initialTheme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
$('#theme').addEventListener('click', () => {const theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'; setTheme(theme); try {localStorage.setItem('radar-theme',theme);} catch {}});
function tick(){ $('#clock').textContent = pkt(Date.now(),{hour:'2-digit',minute:'2-digit',hour12:false}); } tick(); setInterval(tick,60000);
async function load() {
  try {
    const response = await fetch('events.json',{cache:'no-store'});
    if (!response.ok) throw new Error('The event file could not be loaded.');
    const data = await response.json();
    if (!Array.isArray(data.events)) throw new Error('The event file is invalid.');
    state.mode = data.mode;
    state.events = data.events.filter(e => e.title && Array.isArray(e.categories) && Number.isFinite(new Date(e.start).getTime()) && new Date(e.end || e.start).getTime() >= Date.now());
    const statusResponse = await fetch('status.json',{cache:'no-store'}).catch(() => null);
    const status = statusResponse?.ok ? await statusResponse.json().catch(() => null) : null;
    const updated = data.generated_at;
    $('#total').textContent = state.events.length.toString().padStart(2,'0');
    $('#week').textContent = state.events.filter(e => new Date(e.start).getTime() < Date.now()+7*86400000).length.toString().padStart(2,'0');
    $('#free-count').textContent = state.events.filter(e => e.is_free).length.toString().padStart(2,'0');
    $('#updated').textContent = updated ? pkt(updated,{day:'numeric',month:'short'}) : 'Not yet';
    $('#freshness').textContent = updated ? pkt(updated,{hour:'numeric',minute:'2-digit',hour12:true})+' PKT' : 'Awaiting first update';
    for (const count of document.querySelectorAll('[data-count]')) count.textContent = state.events.filter(e => count.dataset.count === 'all' || e.categories.includes(count.dataset.count)).length;
    if (data.mode === 'demo') {$('#notice').className = 'notice demo'; $('#notice').innerHTML = '<strong>Preview mode</strong><span>These are fictional sample events. Connect the agent to discover real ones.</span>';}
    else if (status?.state === 'failed' || status?.state === 'partial' || !updated || Date.now()-new Date(updated).getTime()>36*3600000) {$('#notice').className = 'notice warning'; $('#notice').textContent = status?.state === 'failed' ? 'The last update failed. Showing earlier results; check event sources before making plans.' : status?.state === 'partial' ? 'Some sources could not be checked. Results may be incomplete; see each event’s evidence.' : 'These results are more than 36 hours old. Check the source for changes.';}
    else {$('#notice').textContent = 'Your radar is up to date. Always confirm details on the organizer’s page.';}
    render();
  } catch(error) {$('#notice').className = 'notice warning'; $('#notice').textContent = 'Events could not be loaded. Refresh the page to try again.'; $('#events').setAttribute('aria-busy','false'); $('#result-count').textContent = 'Unavailable';}
}
load();

// Optional browser-native tools use the same visible filters; no external actions.
if (document.modelContext?.registerTool) {
  const lifecycle = new AbortController();
  const tool = {
    name:'filter_events', title:'Filter Karachi events',
    description:'Set the visible category, search, format and free-only filters. Resets other filters. Returns the visible event titles; never registers for an event.',
    inputSchema:{type:'object',properties:{query:{type:'string',maxLength:200},category:{type:'string',enum:['all','AI/ML','Agents','Sustainability','Emerging Tech','Students']},format:{type:'string',enum:['all','in-person','online']},free_only:{type:'boolean'}},additionalProperties:false},
    annotations:{readOnlyHint:false,untrustedContentHint:true},
    execute(input) {
      if (!input || typeof input !== 'object' || Array.isArray(input) || Object.keys(input).some(k => !['query','category','format','free_only'].includes(k)) || (input.query !== undefined && (typeof input.query !== 'string' || input.query.length>200)) || (input.category !== undefined && !['all','AI/ML','Agents','Sustainability','Emerging Tech','Students'].includes(input.category)) || (input.format !== undefined && !['all','in-person','online'].includes(input.format)) || (input.free_only !== undefined && typeof input.free_only !== 'boolean')) throw new Error('Invalid event filters');
      resetFilters();
      state.category = input.category || 'all'; state.format = input.format || 'all';
      $('#search').value = input.query || ''; $('#free').checked = input.free_only || false;
      syncButtons(); render();
      return {mode:state.mode,events:[...document.querySelectorAll('.event-card h3')].map(el => el.textContent)};
    }
  };
  try {Promise.resolve(document.modelContext.registerTool(tool,{signal:lifecycle.signal})).catch(() => {});} catch {}
  addEventListener('pagehide',()=>lifecycle.abort(),{once:true});
}
