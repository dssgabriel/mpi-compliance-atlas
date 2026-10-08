"""Extract exact API chapter/heading paths from the MPI release vault.

Usage: python3 site/scripts/build_standard_grouping.py ../mpi-md-vaults-release
"""
import argparse
import subprocess
import json,re,pathlib,hashlib
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('vault_repository', type=pathlib.Path, nargs='?')
parser.add_argument('--vault-root', type=pathlib.Path, help='Release repository root or its vaults directory')
args = parser.parse_args()
repository_arg = args.vault_root or args.vault_repository
if repository_arg is None:
 parser.error('Provide --vault-root or a positional release repository path')
repository = repository_arg.resolve()
if (repository / 'vault-mpi-50').is_dir():
 repository = repository.parent
v = repository / 'vaults/vault-mpi-50'
revision = subprocess.check_output(['git', '-C', str(repository), 'rev-parse', 'HEAD'], text=True).strip()
j=json.loads((v/'signatures.json').read_text())
chapters={'pt2pt':'p2p','part':'partitioned','datatypes':'datatypes','coll':'colls','context':'communicator','topol':'topology','inquiry':'environment','misc':'info','dynamic':'process','one-side':'one-sided','ei':'external','io':'io','tools':'tools','binding':'language','abi':'abi'}
loc={}
section_hashes={}
for slug,kind in chapters.items():
 p=v/'sections'/f'{slug}.md'; stack=[]; fenced=False
 section_hashes[f'vaults/vault-mpi-50/sections/{slug}.md'] = hashlib.sha256(p.read_bytes()).hexdigest()
 for lineno,line in enumerate(p.read_text().splitlines(),1):
  if line.startswith('```'): fenced=not fenced
  if fenced: continue
  m=re.match(r'^(#{1,6}) (.+)$',line)
  if m:
   level=len(m[1]); stack=[x for x in stack if x[0]<level]+[(level,m[2])]
  for api in re.findall(r'!\[\[API/([^\]|]+)(?:\|[^\]]*)?\]\]',line):
   loc.setdefault(api,[]).append({'kind':kind,'chapter_slug':slug,'section_path':[x[1] for x in stack[1:]],'vault_file':f'vaults/vault-mpi-50/sections/{slug}.md','line':lineno})
rows={}
for f in j['functions']:
 locations=loc.get(f['lis_name'],[])
 preferred=next((x for x in locations if x['chapter_slug']==f['chapter']),locations[0] if locations else None)
 if not preferred: continue
 for proto in f['c_bindings']:
  if re.match(r'\s*typedef\b', proto): continue
  m=re.search(r'\b(MPI_[A-Za-z0-9_]+)\s*\(',proto)
  if m: rows[m[1]]={**preferred,'lis_name':f['lis_name'],'signature_chapter':f['chapter']}
output={'source':'https://github.com/tonyskjellum/mpi-md-vaults-release','version':'MPI 5.0','revision':revision,'signatures_sha256':hashlib.sha256((v/'signatures.json').read_bytes()).hexdigest(),'section_sha256':section_hashes,'method':'Exact C bindings linked through API note transclusions in normative chapter prose; nearest Markdown heading path. Prefer signature chapter when repeated. Appendix-only bindings use final PDF C summary fallback.','rows':rows}
(pathlib.Path(__file__).resolve().parents[1] / 'data/standard-grouping.json').write_text(json.dumps(output,indent=2)+'\n')
print(len(rows), 'exact chapter/section locations')
