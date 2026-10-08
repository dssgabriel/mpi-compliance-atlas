"""Build the evidence-based catalogue from saved public source extracts."""
import collections
import json
import pathlib
import re

from standard_taxonomy import classify, TAXONOMY

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'data/source-extracts'
NAME = re.compile(r'\bMPI_[A-Za-z][A-Za-z0-9_]*(?=\s*\()')
PDF = 'https://www.mpi-forum.org/docs/mpi-5.0/mpi50-report.pdf'

def historical(version):
    names = set()
    for p in list(SOURCES.glob(f'mpi{version}-*.txt')) + list(SOURCES.glob(f'pdf{version}-*.txt')):
        text = p.read_text()
        if 'Internal Error' not in text:
            names.update(NAME.findall(text))
    return names

lines = {}
for p in SOURCES.glob('pdf5-*.txt'):
    for m in re.finditer(r'L(\d+)@P(\d+)(?:-\d+)?: ([^\n]*)', p.read_text()):
        if 80946 <= int(m[1]) <= 84160:
            lines[int(m[1])] = (int(m[2]), m[3])
assert set(range(80946, 84161)) <= lines.keys(), 'Official C summary has gaps'
catalog = {}
section = ''
for _, (page, text) in sorted(lines.items()):
    if re.search(r'A\.3\.\d+ ', text):
        section = text
    for name in NAME.findall(text):
        catalog[name] = {'name': name, 'standard': PDF + f'#page={page+1}', 'section': section}

old11, old22, old31 = (historical(v) for v in ('11', '22', '31'))
refresh_path = ROOT / 'data/refreshed-snapshots.json'
refreshed = json.loads(refresh_path.read_text()) if refresh_path.exists() else None
if refreshed:
    catalog = refreshed['standards']['5']
    old11, old22, old31 = (set(refreshed['standards'][v]) for v in ('11', '22', '31'))
removed = {'MPI_Address', 'MPI_Errhandler_create', 'MPI_Errhandler_get', 'MPI_Errhandler_set', 'MPI_Type_extent', 'MPI_Type_hindexed', 'MPI_Type_hvector', 'MPI_Type_lb', 'MPI_Type_struct', 'MPI_Type_ub'}
for name in removed:
    catalog[name] = {'name': name, 'standard': 'https://www.mpi-forum.org/docs/mpi-1.1/mpi-11-html/mpi-report.html', 'section': 'Removed MPI-1 APIs'}
for name in ['MPI_Aint_add', 'MPI_Aint_diff']:
    catalog[name] = {'name': name, 'standard': PDF+'#page=199', 'section': 'Address arithmetic'}
for name, page in [('MPI_Wtime', 519), ('MPI_Wtick', 520)]:
    catalog[name] = {'name': name, 'standard': PDF+f'#page={page}', 'section': 'Timers and synchronization'}

new22 = {'MPI_Reduce_local','MPI_Op_commutative','MPI_Reduce_scatter_block','MPI_Dist_graph_create','MPI_Dist_graph_create_adjacent','MPI_Dist_graph_neighbors','MPI_Dist_graph_neighbors_count'}
new31 = {'MPI_Aint_add','MPI_Aint_diff','MPI_File_iread_all','MPI_File_iwrite_all','MPI_File_iread_at_all','MPI_File_iwrite_at_all','MPI_T_cvar_get_index','MPI_T_pvar_get_index','MPI_T_category_get_index'}
new41 = set('MPI_Status_get_source MPI_Status_get_tag MPI_Status_get_error MPI_Status_set_source MPI_Status_set_tag MPI_Status_set_error MPI_Comm_attach_buffer MPI_Comm_detach_buffer MPI_Session_attach_buffer MPI_Session_detach_buffer MPI_Comm_flush_buffer MPI_Session_flush_buffer MPI_Buffer_flush MPI_Comm_iflush_buffer MPI_Session_iflush_buffer MPI_Buffer_iflush MPI_Request_get_status_any MPI_Request_get_status_some MPI_Request_get_status_all MPI_Type_get_value_index MPI_Get_hw_resource_info MPI_Remove_error_class MPI_Remove_error_code MPI_Remove_error_string'.split())
new41 |= {n+'_c' for n in new41 if n.endswith(('attach_buffer','detach_buffer'))}
intro_sources = {'1.0':'https://www.mpi-forum.org/docs/mpi-1.1/mpi-11-html/mpi-report.html','1.2':'https://www.mpi-forum.org/docs/mpi-5.0/mpi50-report/mpi50-report.htm','2.0':'https://www.mpi-forum.org/docs/mpi-2.2/mpi22-report.pdf','2.2':'https://www.mpi-forum.org/docs/mpi-3.1/mpi31-report/node520.htm','3.0':'https://www.mpi-forum.org/docs/mpi-3.1/mpi31-report.pdf','3.1':'https://www.mpi-forum.org/docs/mpi-3.1/mpi31-report/node516.htm','4.0':'https://www.mpi-forum.org/docs/mpi-5.0/mpi50-report/node617.htm','4.1':'https://www.mpi-forum.org/docs/mpi-5.0/mpi50-report/node614.htm','5.0':PDF+'#page=1111'}

releases = json.loads((ROOT/'data/releases.json').read_text())
audit_path = ROOT/'data/source-audit.json'
audit = json.loads(audit_path.read_text()) if audit_path.exists() else {}
ompi_source = 'https://docs.open-mpi.org/en/v5.0.10/release-notes/mpi.html'
mpc_source = 'https://github.com/cea-hpc/mpc'
mpc_changes = mpc_source+'/blob/main/CHANGELOG.md'
ompi_index = (SOURCES/'ompi-5.0.10-index.txt').read_text() + (SOURCES/'ompi-5.0.10-tail.txt').read_text()
tails = (SOURCES/'implementation-index-tail.txt').read_text()
ompi_names = set(re.findall(r'†(?:[0-9.]+\s+)?(MPI_[A-Za-z0-9_]+)', ompi_index))
mpich_names = set(re.findall(r'†(MPI_[A-Za-z0-9_]+)', (SOURCES/'mpich-index.txt').read_text() + (SOURCES/'mpich-tail.txt').read_text()))
if refreshed:
    if refreshed.get('implementations', {}).get('openmpi') == releases['openmpi']['version']:
        ompi_names = set(refreshed['indexes']['openmpi'])
    mpich_names = set(refreshed['indexes']['mpich'])


vault_audit = json.loads((ROOT/'data/standard-vault-audit.json').read_text())
rows=[]
for n, row in sorted(catalog.items()):
    rev = '5.0' if n.startswith('MPI_Abi_') or n.endswith(('_fromint','_toint')) else '4.1' if n in new41 else '3.1' if n in new31 else '2.2' if n in new22 else '1.2' if n=='MPI_Get_version' else '1.0' if n in old11 or n in {'MPI_DUP_FN','MPI_NULL_COPY_FN','MPI_NULL_DELETE_FN'} else '2.0' if n in old22 else '3.0' if n in old31 else '4.0'
    row.update(introduced=rev, introduction_source=intro_sources[rev], large_count=n.lower().endswith('_c'), lifecycle='removed' if n in removed else 'deprecated' if 'Deprecated' in row['section'] else 'current')
    row.update(classify(n, row['section']))
    binding = vault_audit['bindings'].get(n)
    row['entry_type'] = 'callback sentinel' if n.startswith('MPI_CONVERSION_FN_NULL') else 'predefined callback' if n.isupper() else 'routine'
    if binding:
        row['c_prototype'] = binding['prototype']
        row['standard_procedure'] = binding['procedure']
        row['vault_source'] = binding['source']
    correction = vault_audit['history_corrections'].get(n)
    if correction:
        row.update(introduced=correction['introduced'], introduction_source=correction['source'], introduction_note=correction['reason'])
    def status(label,source,reason):return {'status':label,'source':source,'reason':reason}
    for impl, names in [('openmpi',ompi_names), ('mpich',mpich_names), ('mpc',set())]:
        release = releases[impl]
        entry = audit.get('implementations',{}).get(impl,{})
        if entry and entry['version'] != release['version']:
            raise ValueError(f'Source audit version mismatch for {impl}')
        evidence = entry.get('rows',{}).get(n)
        if evidence:
            row[impl] = evidence
        elif n in names:
            url = ('https://docs.open-mpi.org/en/v5.0.10/man-openmpi/man3/'+n+'.3.html') if impl=='openmpi' else ('https://www.mpich.org/static/docs/v5.0.2/www3/'+n+'.html')
            row[impl]=status('supported',url,f'Exact API listed in the {release["version"]} manual. Source audit pending; documentation is positive evidence, not runtime verification.')
            row[impl]['basis']='documentation'
        elif impl=='openmpi' and n in removed:
            row[impl]=status('supported',ompi_source,'Retained library symbol documented for this release. Declarations require --enable-mpi1-compatibility. Source audit pending.')
            row[impl]['basis']='documentation'
        else:
            row[impl]=status('unknown',release['release'],f'Could not retrieve the {release["version"]} sources. No per-API evidence in the checked release documentation. Unknown reflects missing source access, not an API missing from a checked source tree.')
            row[impl]['basis']='unavailable sources'
    rows.append(row)

payload={'checked':max(releases['checked'], audit.get('checked','0000-00-00'), refreshed['checked'] if refreshed else '0000-00-00'),'standard':'5.0','implementations':{k:releases[k]['version'] for k in ('openmpi','mpich','mpc')},'audit':{k: audit.get('implementations',{}).get(k,{}).get('scan','pending — release sources unavailable') for k in ('openmpi','mpich','mpc')},'source_archives':{k:{field: entry[field] for field in ('version','archive','sha256','files_scanned','unresolved') if field in entry} for k,entry in audit.get('implementations',{}).items()},'taxonomy':TAXONOMY,'standard_audit':{key:vault_audit[key] for key in ('repository','commit','coverage','scope','limitations')},'rows':rows}
(ROOT/'dist/apis.json').write_text(json.dumps(payload,indent=2)+'\n')
print('APIs:',len(rows),'introductions:',dict(collections.Counter(r['introduced'] for r in rows)))
