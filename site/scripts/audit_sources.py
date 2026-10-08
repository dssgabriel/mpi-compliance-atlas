"""Scan release archives for C definitions, aliases, missing APIs and stub candidates.

This is a static inventory, not a conformance test. Ambiguous templates,
conditional code and possible stubs are recorded for review. A reviewed override
can resolve these cases in data/source-overrides.json. Downloads never overwrite
an existing audit on failure. Older archives cannot populate release columns.
"""
import argparse
import collections
import datetime
import hashlib
import json
import pathlib
import re
import tarfile
import urllib.parse
import urllib.request
import urllib.error

ROOT = pathlib.Path(__file__).resolve().parents[1]
RELEASES = json.loads((ROOT/'data/releases.json').read_text())
TOKEN = re.compile(r'\bP?MPI_[A-Za-z0-9_]+\b')
# Match function definitions rather than declarations or calls; strings and
# comments are masked first, preserving offsets for evidence line numbers.
DEFINITION = re.compile(r'(?m)^\s*(?:[A-Za-z_]\w*\s+|\*\s*)+?(P?MPI_\w+)\s*\([^;{}]*\)\s*\{')
LEX = re.compile(r'/\*[\s\S]*?\*/|//[^\n]*|"(?:\\[\s\S]|[^"\\])*"|\'(?:\\[\s\S]|[^\'\\])*\'')
ALIASES = re.compile(r'(?m)^\s*#\s*define\s+(MPI_\w+)\s+(P?MPI_\w+)\b')

def mask(text):
    return LEX.sub(lambda m: ''.join('\n' if c=='\n' else ' ' for c in m[0]),text)

def body_at(text, start):
    depth = 1
    for end in range(start,len(text)):
        depth += (text[end]=='{') - (text[end]=='}')
        if not depth:
            return text[start:end]
    raise ValueError('Unbalanced function body')

def canonical(name):
    return name[1:] if name.startswith('PMPI_') else name

def production(path, impl):
    parts = pathlib.PurePosixPath(path).parts
    if any(p.lower() in {'test','tests','testing','examples','example','benchmarks','mansrc'} for p in parts):
        return False
    if impl=='openmpi':
        return path.startswith(('ompi/','opal/')) and '/tools/' not in path
    if impl=='mpich':
        return path.startswith('src/') and not path.startswith(('src/pm/','src/mpl/'))
    return path.startswith('src/')

def stub_reason(body, name):
    # Input validation before a top-level failure marker does not implement the
    # API. Markers inside an optional branch need review of that branch instead.
    depth = 0
    for match in re.finditer(r'[{}]|\b(?:not_implemented|notimplemented|NOT_IMPLEMENTED|NOT_IMPLEMENTED_YET)\s*\(', body):
        if match[0]=='{': depth += 1
        elif match[0]=='}': depth -= 1
        elif depth==0 and '#' not in body:
            return 'Unconditional not-implemented marker in the API body.'
    # A failure under argument checking is not an unconditional stub.
    if re.search(r'\b(?:if|switch|for|while)\s*\(',body) or '#' in body:
        return None
    if re.search(r'\b(?:not_implemented|notimplemented|NOT_IMPLEMENTED|NOT_IMPLEMENTED_YET)\s*\(',body):
        return 'Unconditional not-implemented marker in the API body.'
    if name!='MPI_Abort' and re.search(r'\b(?:abort|exit|__builtin_trap|mpc_common_debug_abort)\s*\(',body):
        return 'Unconditional termination in the API body.'
    trivial = re.sub(r'\(void\)\s*\w+\s*;|\b(?:UNUSED|TODO)\s*\([^;]*\)\s*;', '',body).strip()
    if re.fullmatch(r'return\s+MPI_T_ERR_NOT_SUPPORTED\s*;',trivial):
        return 'Always returns MPI_T_ERR_NOT_SUPPORTED.'
    # MPI_Pcontrol and the predefined null callbacks may legitimately do nothing.
    legitimate = name=='MPI_Pcontrol' or 'NULL' in name or name.endswith('_DELETE_FN')
    if not legitimate and (not trivial or re.fullmatch(r'(?:return\s+(?:MPI_SUCCESS|0|MPI_ERR_[A-Z_]+)|MPI_ERROR_SUCCESS\(\))\s*;',trivial)):
        return 'Empty body or constant-only return; requires semantic review before deciding whether this is a valid no-op.'
    return None

def scan_archive(archive, impl, release, names):
    definitions = collections.defaultdict(list)
    mentions = collections.defaultdict(list)
    aliases = {}
    templates = {}
    files = 0
    with tarfile.open(archive) as tar:
        roots = {m.name.removeprefix('./').split('/')[0] for m in tar if m.name and m.isfile()}
        if roots != {release['archive_root']}:
            raise ValueError(f'{impl}: expected archive root {release["archive_root"]}, found {sorted(roots)}')
        for member in tar:
            if not member.isfile(): continue
            path = member.name.removeprefix('./').split('/',1)[-1]
            if not production(path,impl) or not path.endswith(('.c','.h','.h.in','.c.in','.cpp','.cc','.txt','.py','.json')):
                continue
            stream = tar.extractfile(member)
            raw = stream.read().decode('utf-8',errors='replace')
            code = mask(raw) if path.endswith(('.c','.h','.h.in','.c.in','.cpp','.cc')) else raw
            files += 1
            if impl=='mpich' and path.endswith('_api.txt'):
                for match in re.finditer(r'(?m)^(MPI_\w+):', raw):
                    templates[match[1]]={'path':path,'line':raw.count('\n',0,match.start())+1}
            for match in TOKEN.finditer(code):
                name = canonical(match[0])
                if name in names and len(mentions[name])<10:
                    mentions[name].append({'path':path,'line':code.count('\n',0,match.start())+1})
            for match in ALIASES.finditer(code):
                aliases[match[1]] = canonical(match[2])
            if not path.endswith(('.c','.h','.h.in','.c.in','.cpp','.cc')): continue
            for match in DEFINITION.finditer(code):
                name = canonical(match[1])
                if name not in names: continue
                body = body_at(code,match.end())
                definitions[name].append({'path':path,'line':code.count('\n',0,match.start(1))+1,
                                          'stub_candidate':stub_reason(body,name),
                                          'conditional':'#' in body})
    if files<100 or len(definitions)<100:
        raise ValueError(f'{impl}: incomplete/unrecognized source layout ({files} files, {len(definitions)} API definitions). No absence classifications emitted.')
    rows = {}
    review = []
    for name in sorted(names):
        bodies = definitions.get(name,definitions.get(aliases.get(name),[]))
        evidence = bodies[0] if bodies else (mentions[name][0] if mentions[name] else None)
        source = release['repository']+'/blob/'+release['tag']+'/'+urllib.parse.quote(evidence['path'])+f'#L{evidence["line"]}' if evidence else release['repository']+'/tree/'+release['tag']
        if bodies:
            candidates = [b for b in bodies if b['stub_candidate']]
            if candidates:
                status='unsupported' if all(b['stub_candidate'] and 'semantic review' not in b['stub_candidate'] for b in bodies) else 'unknown'
                reason=('Unimplemented release source body. ' if status=='unsupported' else 'Potential stub in release source; pending semantic review. ')+candidates[0]['stub_candidate']
                review.append({'name':name,'definitions':bodies})
            else:
                status='supported'
                reason='C API definition found in the released sources. Static inventory; backend behavior and runtime conformance have not been verified.'
        elif mentions[name]:
            # Do not mistake declarations, generated wrappers or build macros
            # for either a functioning implementation or proof of absence.
            status='unknown'
            reason='Referenced in release sources, but no literal C definition recognized. Check generated bindings, aliases and declarations before resolving support.'
            review.append({'name':name,'references':mentions[name]})
        else:
            status='unsupported'
            reason='No API definition, declaration or reference in the scanned production source tree of this release (including binding generators and MPI-I/O sources).'
        rows[name]={'status':status,'source':source,'reason':reason,'basis':'source inventory',
                    'locations':bodies or mentions[name], 'review_required':bool(bodies and candidates) or bool(not bodies and mentions[name])}
        if impl=='mpich' and bodies and evidence['path'].startswith('src/binding/'):
            template=templates.get(name.removesuffix('_c'))
            if template:
                rows[name]['source']=release['repository']+'/blob/'+release['tag']+'/'+template['path']+f'#L{template["line"]}'
                rows[name]['reason']+=' The linked binding template generates this API; the recorded C definition path/line refers to the official release archive.'
    return {'version':release['version'],'scan':'static inventory complete; semantic review pending',
            'archive':release['archive'],'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
            'files_scanned':files,'rows':rows,'review':review}

def download(impl, release):
    cache = ROOT/'data/downloads';cache.mkdir(parents=True,exist_ok=True)
    path = cache/f'{impl}-{release["version"]}.tar.gz'
    if not path.exists():
        request = urllib.request.Request(release['archive'],headers={'User-Agent':'MPI-API-Atlas/1.0'})
        with urllib.request.urlopen(request,timeout=60) as response:
            temporary=path.with_suffix('.tmp');temporary.write_bytes(response.read());temporary.replace(path)
    return path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--impl',choices=list(k for k in RELEASES if k!='checked'),action='append',help='Defaults to all three implementations')
    parser.add_argument('--archive',type=pathlib.Path,help='Use an existing official release archive (requires exactly one --impl)')
    args=parser.parse_args()
    selected=args.impl or ['openmpi','mpich','mpc']
    if args.archive and len(selected)!=1:parser.error('--archive requires exactly one --impl')
    names={r['name'] for r in json.loads((ROOT/'dist/apis.json').read_text())['rows']}
    output=ROOT/'data/source-audit.json'
    audit=json.loads(output.read_text()) if output.exists() else {'implementations':{}}
    overrides_path=ROOT/'data/source-overrides.json'
    overrides=json.loads(overrides_path.read_text()) if overrides_path.exists() else {}
    for impl in selected:
        release=RELEASES[impl]
        try:
            result=scan_archive(args.archive or download(impl,release),impl,release,names)
        except (urllib.error.URLError, OSError, ValueError, tarfile.TarError) as error:
            parser.exit(1,f'{impl} {release["version"]}: {error}\nExisting audit unchanged. Run on a network-enabled machine or supply the official archive with --archive.\n')
        for name, override in overrides.get(impl,{}).items():
            if override['version']!=release['version'] or override['status'] not in {'supported','unsupported','unknown'}:
                raise ValueError('Invalid or stale source override: '+name)
            if not override.get('source') or not override.get('reason'):
                raise ValueError('Source overrides require source URL and reason')
            result['rows'][name]={k:v for k,v in override.items() if k!='version'}
        unresolved=[name for name,row in result['rows'].items() if row['status']=='unknown']
        result['unresolved']=unresolved
        result['scan']=f'production source inventory and stub/alias review; {len(unresolved)} unresolved APIs'
        audit['implementations'][impl]=result
        print(impl,release['version'],dict(collections.Counter(r['status'] for r in result['rows'].values())),f'{len(result["review"])} review candidates')
    audit['checked']=datetime.date.today().isoformat()
    temporary=output.with_suffix('.tmp');temporary.write_text(json.dumps(audit,indent=2)+'\n');temporary.replace(output)
    print('Saved',output,'— inspect review candidates before claiming a complete implementation audit.')

if __name__=='__main__':main()
