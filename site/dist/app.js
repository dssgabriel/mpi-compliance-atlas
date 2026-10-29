'use strict';
const kinds = {all:'All chapters'};
const statuses = {supported:'Supported',unsupported:'Unsupported',unknown:'Unknown'};
const symbols = {supported:'+',unsupported:'−',unknown:'?'};
const implementationNames = {openmpi:'Open MPI',mpich:'MPICH',mpc:'MPC MPI'};
const implementations = Object.keys(implementationNames);
const rank = [];
const families = [];
let data,  selectedAPI=null, visibleNames=new Set();
const records = new Map();
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
const classifications = [
  {id:'chapter',label:'Chapters',value:row=>row.kind,labelFor:value=>kinds[value]},
  {id:'revision',label:'Introduced in',value:row=>row.introduced,labelFor:value=>'MPI '+value},
  {id:'lifecycle',label:'Standard lifecycle',value:row=>row.lifecycle},
  {id:'count',label:'Count binding',value:row=>row.large_count?'large':'normal',labelFor:value=>value==='large'?'Large count (_c)':'Standard count'},
  ...implementations.map(key=>({id:'status-'+key,label:implementationNames[key]+' status',value:row=>row[key].status,labelFor:value=>statuses[value]}))
];
const urlKeys={search:'q',chapter:'ch',revision:'rev',lifecycle:'life',count:'cnt','status-openmpi':'ompi','status-mpich':'mpich','status-mpc':'mpc'};
const rangeAnchors=new Map();
function selectedValues(id) {
  return [...el(id).querySelectorAll('input:checked')].map(input=>input.value);
}
function buildFilters() {
  el('classification-filters').innerHTML=classifications.map(filter=>{
    const values=[...new Set(data.rows.map(filter.value))];
    if(filter.id==='revision')values.sort((a,b)=>parseFloat(a)-parseFloat(b));
    filter.options=values.map(value=>({value,label:filter.labelFor?filter.labelFor(value):value}));
    return '<div class="classification-filter"><span id="'+filter.id+'-label">'+escape(filter.label)+'</span><details><summary id="'+filter.id+'-summary" aria-labelledby="'+filter.id+'-label '+filter.id+'-summary">All</summary><div class="checkbox-options" id="'+filter.id+'" role="group" aria-labelledby="'+filter.id+'-label" aria-describedby="classification-help">'+filter.options.map(option=>'<label><input type="checkbox" value="'+escape(option.value)+'">'+escape(option.label)+'</label>').join('')+'</div></details></div>';
  }).join('');
}
function restoreFilters() {
  const params=new URLSearchParams(location.search);
  el('search').value=params.get(urlKeys.search)??'';
  for(const filter of classifications) {
    const values=(params.get(urlKeys[filter.id])||'').split(',');
    el(filter.id).querySelectorAll('input').forEach(input=>{input.checked=values.includes(input.value);});
  }
  rangeAnchors.clear();
}
function updateFilterURL() {
  const url=new URL(location.href);
  url.searchParams.delete(urlKeys.search);
  if(el('search').value)url.searchParams.set(urlKeys.search,el('search').value);
  for(const filter of classifications) {
    url.searchParams.delete(urlKeys[filter.id]);
    const values=selectedValues(filter.id);
    if(values.length)url.searchParams.set(urlKeys[filter.id],values.join(','));
  }
  const href=url.href.replace(/%2C/gi,',');
  if(href!==location.href)history.replaceState(null,'',href);
}
window.addEventListener('popstate',()=>{if(data){restoreFilters();render();}});
function filtered() {
  const query=el('search').value.trim().toLowerCase();
  const filters=classifications.map(filter=>({filter,values:selectedValues(filter.id)}));
  return data.rows.filter(row=>filters.every(({filter,values})=>!values.length||values.includes(filter.value(row))) && (!query||row.name.toLowerCase().includes(query)));
}
function compare(a,b) {
  return rank.indexOf(a.kind)-rank.indexOf(b.kind) || ((families.indexOf(a.family)+1||99)-(families.indexOf(b.family)+1||99)) || a.family.localeCompare(b.family) || (a.variant===b.variant?0:a.variant==='normal'?-1:b.variant==='normal'?1:a.variant.localeCompare(b.variant)) || a.name.localeCompare(b.name);
}
function filterState() {
  const descriptions=classifications.map(filter=>{
    const values=selectedValues(filter.id);
    const label=filter.options.filter(option=>values.includes(option.value)).map(option=>option.label).join(', ')||'All';
    el(filter.id+'-summary').textContent=label;
    return filter.label+'='+label;
  });
  el('filter-state').textContent='FILTER STATE: query='+JSON.stringify(el('search').value.trim())+' / '+descriptions.join(' / ');
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
el('search').addEventListener('input',()=>{if(data)render();});
el('classification-filters').addEventListener('click',event=>{
  const input=event.target;
  if(!input.matches('input[type="checkbox"]'))return;
  const group=input.closest('.checkbox-options');
  const inputs=[...group.querySelectorAll('input')];
  const index=inputs.indexOf(input), anchor=rangeAnchors.get(group.id);
  if(event.shiftKey && anchor!==undefined) {
    for(let i=Math.min(anchor,index);i<=Math.max(anchor,index);i++)inputs[i].checked=input.checked;
  }
  rangeAnchors.set(group.id,index);
});
el('classification-filters').addEventListener('change',()=>{if(data)render();});
el('rows').addEventListener('click',event=>{
  const button=event.target.closest('[data-api]');
  if(button) {
    showDetail(button.dataset.api);
  }
});
el('reset').addEventListener('click',()=>{
  el('classification-filters').querySelectorAll('input').forEach(input=>{input.checked=false;});
  rangeAnchors.clear();
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
    kindCounts.set(row.kind,(kindCounts.get(row.kind)||0)+1);
  }
  for(const key of implementations)el('version-'+key).textContent=data.implementations[key];
  el('checked').textContent='SOURCE SNAPSHOT '+data.checked;
  el('audit-state').textContent=implementations.map(key=>implementationNames[key]+' '+data.implementations[key]+': '+data.audit[key]).join(' / ');
  el('summary').innerHTML=[[data.rows.length,'C entries'],[kindCounts.size,'standard chapters'],[new Set(data.rows.map(row=>row.introduced)).size,'introduction revisions'],[implementations.length,'release source trees']].map(([count,label])=>'<span class="inventory-item"><strong>'+count+'</strong> '+label+'</span>').join('');
  buildFilters();
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
