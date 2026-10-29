'use strict';
const kinds = {all:'All chapters'};
const statuses = {supported:'Supported',unsupported:'Unsupported',unknown:'Unknown'};
const symbols = {supported:'+',unsupported:'−',unknown:'?'};
const implementationNames = {openmpi:'Open MPI',mpich:'MPICH',mpc:'MPC MPI'};
const implementations = Object.keys(implementationNames);
const rank = [];
const families = [];
let data, selectedKind='all', selectedAPI=null, visibleNames=new Set();
const records = new Map();
const searchText = new Map();
const el = id => document.getElementById(id);
const escape = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const external = (url,label) => '<a href="'+escape(url)+'" target="_blank" rel="noopener noreferrer">'+escape(label)+' ↗</a>';
function evidenceBasis(evidence) {
  const reason=evidence.reason.toLowerCase();
  if(evidence.status==='unknown') return 'linkage unresolved';
  if(evidence.status==='unsupported') {
    if(reason.includes('success') && reason.includes('stub')) return 'success-only stub';
    if(reason.includes('not_supported')) return 'returns unsupported';
    if(reason.includes('not-implemented') || reason.includes('unimplemented release')) return 'aborting stub';
    if(reason.includes('only declarations')) return 'declaration only';
    return 'API absent';
  }
  if(reason.includes('sentinel') || reason.includes('callback')) return 'callback / sentinel';
  if(reason.includes('macro')) return 'C macro';
  if(evidence.basis==='documentation') return 'documentation';
  return 'C implementation';
}
function statusLabel(evidence,link=true) {
  const content='<span class="status-symbol" aria-hidden="true">'+symbols[evidence.status]+'</span>'+statuses[evidence.status];
  return link ? '<a class="badge '+evidence.status+'" href="'+escape(evidence.source)+'" target="_blank" rel="noopener noreferrer" title="'+escape(evidence.reason)+'">'+content+'</a>' : '<span class="badge '+evidence.status+'">'+content+'</span>';
}
function selectedRevisions() {
  return [...el('revision').querySelectorAll('input:checked')].map(input=>input.value);
}
const urlFilters = ['search','lifecycle','count',...implementations.map(key=>'status-'+key)];
function restoreFilters() {
  const params=new URLSearchParams(location.search);
  for(const id of urlFilters) {
    const control=el(id), value=params.get(id)||'';
    control.value=control.tagName==='SELECT' && ![...control.options].some(option=>option.value===value)?'':value;
  }
  const revisions=params.getAll('revision');
  el('revision').querySelectorAll('input').forEach(input=>{input.checked=revisions.includes(input.value);});
  const chapter=params.get('chapter');
  selectedKind=Object.hasOwn(kinds,chapter)?chapter:'all';
}
function updateFilterURL() {
  const url=new URL(location.href);
  for(const id of urlFilters) {
    url.searchParams.delete(id);
    if(el(id).value)url.searchParams.set(id,el(id).value);
  }
  url.searchParams.delete('revision');
  selectedRevisions().forEach(revision=>url.searchParams.append('revision',revision));
  url.searchParams.delete('chapter');
  if(selectedKind!=='all')url.searchParams.set('chapter',selectedKind);
  if(url.href!==location.href)history.replaceState(null,'',url.href);
}
window.addEventListener('popstate',()=>{if(data){restoreFilters();render();}});
function filtered() {
  const query=el('search').value.trim().toLowerCase();
  const revisions=selectedRevisions(), lifecycle=el('lifecycle').value, count=el('count').value;
  return data.rows.filter(row=>(selectedKind==='all'||row.kind===selectedKind) && (!revisions.length||revisions.includes(row.introduced)) && (!lifecycle||row.lifecycle===lifecycle) && (!count||row.large_count===(count==='large')) && implementations.every(key=>!el('status-'+key).value||row[key].status===el('status-'+key).value) && (!query||searchText.get(row.name).includes(query)));
}
function compare(a,b) {
  return rank.indexOf(a.kind)-rank.indexOf(b.kind) || ((families.indexOf(a.family)+1||99)-(families.indexOf(b.family)+1||99)) || a.family.localeCompare(b.family) || (a.variant===b.variant?0:a.variant==='normal'?-1:b.variant==='normal'?1:a.variant.localeCompare(b.variant)) || a.name.localeCompare(b.name);
}
function filterState() {
  const query=el('search').value.trim();
  el('filter-state').textContent='FILTER STATE: query='+JSON.stringify(query)+' / chapter='+kinds[selectedKind]+' / revision='+(selectedRevisions().join(', ')||'all')+' / lifecycle='+(el('lifecycle').value||'all')+' / count='+(el('count').value||'all')+implementations.map(key=>' / '+implementationNames[key]+'='+(el('status-'+key).value||'all')).join('');
}
function selectionState() {
  const visible=selectedAPI && visibleNames.has(selectedAPI);
  el('selection-state').textContent='SELECTED API: '+(selectedAPI||'none')+(selectedAPI&&!visible?' / outside current filters':'');
  const warning=el('selection-warning');
  if(warning) warning.hidden=!selectedAPI||visible;
}
function totalsHTML(rows) {
  return implementations.map(key=>{
    const totals={supported:0,unsupported:0,unknown:0};
    for(const row of rows) totals[row[key].status]++;
    return '<div class="support-total"><strong>'+implementationNames[key]+' '+escape(data.implementations[key])+' / filtered totals</strong>'+Object.entries(totals).map(([status,count])=>'<span class="'+status+'">'+symbols[status]+' '+count+' '+statuses[status]+'</span>').join(' ')+'</div>';
  }).join('');
}
function render() {
  const rows=filtered();
  visibleNames=new Set(rows.map(row=>row.name));
  el('results').textContent=rows.length.toLocaleString()+' of '+data.rows.length.toLocaleString()+' APIs';
  el('empty').hidden=rows.length>0;
  el('revision-summary').textContent=selectedRevisions().map(revision=>'MPI '+revision).join(', ')||'All revisions';
  filterState();
  updateFilterURL();
  let previous=null;
  const html=[];
  for(const row of rows) {
    const boundary=!previous||previous.kind!==row.kind?'kind-start':previous.family!==row.family?'family-start':previous.variant!==row.variant?'variant-start':'';
    html.push('<tr class="api-row '+boundary+(row.name===selectedAPI?' selected':'')+'" data-record="'+escape(row.name)+'"><td><button class="api-name" data-api="'+escape(row.name)+'" aria-controls="detail" aria-pressed="'+(row.name===selectedAPI)+'">'+escape(row.name)+'</button><span class="api-annotations">'+(row.large_count?'large count (_c)':'standard count')+' / '+escape(row.lifecycle)+'</span></td><td class="class-cell kind-cell">'+kinds[row.kind]+'</td><td class="class-cell">'+escape(row.family)+'</td><td class="class-cell">'+escape(row.variant)+'</td><td>'+external(row.introduction_source,'MPI '+row.introduced)+'</td>'+implementations.map(key=>'<td class="support-cell">'+statusLabel(row[key])+'<span class="support-basis">'+escape(evidenceBasis(row[key]))+'</span></td>').join('')+'</tr>');
    previous=row;
  }
  el('rows').innerHTML=html.join('');
  el('support-totals').innerHTML=totalsHTML(rows);
  for(const button of el('kinds').children) button.setAttribute('aria-pressed',String(button.dataset.kind===selectedKind));
  selectionState();
}
function markSelection(name,selected) {
  if(!name)return;
  const row=el('rows').querySelector('[data-record="'+name+'"]');
  if(row) {
    row.classList.toggle('selected',selected);
    row.querySelector('[data-api]').setAttribute('aria-pressed',String(selected));
  }
}
function showDetail(name) {
  const row=records.get(name);
  if(!row) return;
  markSelection(selectedAPI,false);
  selectedAPI=name;
  const fields=[['Chapter',row.chapter.number+'. '+kinds[row.kind]],['Section',(row.section_path||[row.family]).join(' → ')],['Operation form',row.variant],['Entry type',row.entry_type],['Grouping evidence',row.classification_basis],['Introduced','MPI '+row.introduced],['Lifecycle',row.lifecycle],['Count',row.large_count?'large count (_c)':'standard count']];
  for(const [key,label] of Object.entries({communication_mode:'Communication mode',message_matching:'Matching',collective_scope:'Collective scope',io_positioning:'I/O positioning',io_coordination:'I/O coordination',rma_completion:'RMA completion',topology_type:'Topology',procedure_role:'Procedure role',procedure_blocking:'Procedure blocking'})) if(row[key])fields.push([label,row[key]]);
  el('detail-content').innerHTML='<div class="inspector-heading"><h3>'+escape(row.name)+'</h3><dl class="record-fields">'+fields.map(([key,value])=>'<dt>'+key+'</dt><dd>'+escape(value)+'</dd>').join('')+'</dl><div class="record-links">'+external(row.standard,'C binding summary')+external(row.taxonomy_source,'Standard chapter / section')+(row.vault_source?external(row.vault_source,'Procedure bindings'): '')+external(row.introduction_source,'Introduction evidence')+'</div>'+(row.c_prototype?'<pre class="prototype">'+escape(row.c_prototype)+'</pre>':'')+(row.introduction_note?'<p>'+escape(row.introduction_note)+'</p>':'')+'</div><p id="selection-warning" class="selection-warning" hidden>Selected API is outside the current filtered set. Its source evidence remains visible.</p><div class="evidence-grid">'+implementations.map(key=>{
    const evidence=row[key];
    const locations=evidence.locations||[];
    return '<section class="evidence"><div class="evidence-title"><h4>'+implementationNames[key]+'<br>'+escape(data.implementations[key])+'</h4>'+statusLabel(evidence,false)+'</div><p class="evidence-basis">BASIS: '+escape(evidence.basis||'source review')+' / '+escape(evidenceBasis(evidence))+'</p><p>'+escape(evidence.reason)+'</p><div class="evidence-links">'+external(evidence.source,'Source evidence')+(evidence.additional_sources||[]).map(source=>external(source.url,source.title)).join('')+'</div>'+(locations.length?'<ul class="source-locations" aria-label="Locations in the released archive">'+locations.map(location=>'<li>ARCHIVE '+escape(location.path)+':'+location.line+'</li>').join('')+'</ul>':'')+'</section>';
  }).join('')+'</div>';
  markSelection(selectedAPI,true);
  el('detail').scrollTop=0;
  selectionState();
}
function sourceLedger() {
  el('source-ledger').innerHTML=implementations.map(key=>{
    const source=data.source_archives?.[key];
    if(!source) return '<div class="source-record"><h3>'+implementationNames[key]+' '+escape(data.implementations[key])+'</h3><p>Release archive metadata unavailable.</p></div>';
    return '<div class="source-record"><h3>'+implementationNames[key]+' / '+escape(source.version)+'</h3><p>PRODUCTION FILES SCANNED: '+source.files_scanned.toLocaleString()+'</p><p>UNRESOLVED APIs: '+(source.unresolved||[]).length+'</p><div class="record-links">'+external(source.archive,'Official release archive')+'</div><p class="checksum"><span>ARCHIVE SHA-256</span>'+escape(source.sha256)+'</p></div>';
  }).join('');
}
['search','revision','lifecycle','count',...implementations.map(key=>'status-'+key)].forEach(id=>el(id).addEventListener(id==='search'?'input':'change',()=>{if(data)render();}));
el('kinds').addEventListener('click',event=>{
  const button=event.target.closest('[data-kind]');
  if(button&&data) {selectedKind=button.dataset.kind;render();}
});
el('rows').addEventListener('click',event=>{
  const button=event.target.closest('[data-api]');
  if(button) {
    showDetail(button.dataset.api);
  }
});
el('reset').addEventListener('click',()=>{
  for(const id of ['search','lifecycle','count',...implementations.map(key=>'status-'+key)])el(id).value='';
  el('revision').querySelectorAll('input').forEach(input=>{input.checked=false;});
  selectedKind='all';
  if(data)render();
});
el('close').addEventListener('click',()=>{
  markSelection(selectedAPI,false);
  selectedAPI=null;
  el('detail-content').innerHTML='<p class="no-selection">No API selected. API names in the register select a record for source inspection.</p>';
  selectionState();
});
fetch('apis.json').then(r=>{if(!r.ok)throw Error(r.status);return r.json();}).then(catalogue=>{
  data=catalogue;
  for(const [key,chapter] of Object.entries(data.taxonomy.chapters)){kinds[key]=chapter.title;rank.push(key);}
  data.rows.sort(compare);
  const kindCounts=new Map();
  for(const row of data.rows) {
    records.set(row.name,row);
    searchText.set(row.name,[row.name,row.kind,kinds[row.kind],row.family,row.variant,row.section,...(row.section_path||[]),row.communication_mode,row.collective_scope,row.io_positioning,row.io_coordination,row.procedure_role,row.entry_type].join(' ').toLowerCase());
    kindCounts.set(row.kind,(kindCounts.get(row.kind)||0)+1);
  }
  for(const key of implementations)el('version-'+key).textContent=data.implementations[key];
  el('checked').textContent='SOURCE SNAPSHOT '+data.checked;
  el('audit-state').textContent=implementations.map(key=>implementationNames[key]+' '+data.implementations[key]+': '+data.audit[key]).join(' / ');
  el('summary').innerHTML=[[data.rows.length,'C entries'],[kindCounts.size,'standard chapters'],[new Set(data.rows.map(row=>row.introduced)).size,'introduction revisions'],[implementations.length,'release source trees']].map(([count,label])=>'<span class="inventory-item"><strong>'+count+'</strong> '+label+'</span>').join('');
  el('kinds').innerHTML=Object.entries(kinds).filter(([key])=>key==='all'||kindCounts.has(key)).map(([key,label])=>'<button data-kind="'+key+'" aria-pressed="'+(key==='all')+'">'+label+'<span class="count">'+(key==='all'?data.rows.length:kindCounts.get(key))+'</span></button>').join('');
  [...new Set(data.rows.map(row=>row.introduced))].sort((a,b)=>parseFloat(a)-parseFloat(b)).forEach(revision=>el('revision').insertAdjacentHTML('beforeend','<label><input type="checkbox" value="'+escape(revision)+'"> MPI '+escape(revision)+'</label>'));
  const coverage=data.standard_audit.coverage;
  el('standard-audit-state').textContent='VAULT AUDIT: '+coverage.matched_standard_entries+' / '+coverage.standard_entries+' standard C entries matched; '+coverage.missing.length+' missing; '+coverage.unexpected_current_entries.length+' unexpected. '+coverage.retained_removed_entries.length+' removed MPI-1 entries retained. This checks catalogue coverage; implementation behavior requires runtime conformance tests.';
  sourceLedger();
  restoreFilters();
  render();
  showDetail(data.rows[0].name);
}).catch(()=>{
  el('results').textContent='Catalogue unavailable';
  el('filter-state').textContent='FILTER STATE: no catalogue loaded';
  el('load-error').hidden=false;
});
