"""Refresh official PDF/API-index snapshots on a network-enabled machine.

Uses only Python's standard library plus the pdftotext executable. Downloads are
cached locally. A failed source aborts the refresh instead of erasing evidence.
The output is consumed by build_data.py; per-API source evidence is supplied by audit_sources.py.
"""
import argparse
import concurrent.futures
import datetime
import hashlib
import html
import json
import pathlib
import re
import subprocess
import tempfile
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
CACHE = ROOT / 'data/downloads'
PDFS = {
    '11': 'https://www.mpi-forum.org/docs/mpi-1.1/mpi1-report.pdf',
    '22': 'https://www.mpi-forum.org/docs/mpi-2.2/mpi22-report.pdf',
    '31': 'https://www.mpi-forum.org/docs/mpi-3.1/mpi31-report.pdf',
    '5': 'https://www.mpi-forum.org/docs/mpi-5.0/mpi50-report.pdf',
}
INDEXES = {
    'openmpi': 'https://docs.open-mpi.org/en/v5.0.10/man-openmpi/man3/index.html',
    'mpich': 'https://www.mpich.org/static/docs/v5.0.2/',
}
MPC = 'https://github.com/cea-hpc/mpc'
NAME = re.compile(r'\bMPI_[A-Za-z][A-Za-z0-9_]*(?=\s*\()')

def download(url, refresh):
    target = CACHE / hashlib.sha256(url.encode()).hexdigest()
    if refresh or not target.exists():
        request = urllib.request.Request(url, headers={'User-Agent':'MPI-API-Atlas/1.0 (documentation research)'})
        with urllib.request.urlopen(request, timeout=90) as response:
            body = response.read()
        if not body:
            raise RuntimeError('Empty source: ' + url)
        temporary = target.with_suffix('.tmp')
        temporary.write_bytes(body)
        temporary.replace(target)
    return target

def extract_pdf(path, version, url):
    with tempfile.TemporaryDirectory() as directory:
        out = pathlib.Path(directory)/'standard.txt'
        subprocess.run(['pdftotext','-layout',str(path),str(out)],check=True)
        pages = out.read_text().split('\f')
    records = {}; active = False; section = ''
    # Headings have differing appendix numbering in older revisions.
    begin = re.compile(r'^\s*(?:A\.\d+(?:\.\d+)?|\d+(?:\.\d+)*)\s+C [Bb]indings (?:for |of )?(?:Point.to.Point|POINT.TO.POINT)|^\s*(?:A\.\d+(?:\.\d+)?|\d+(?:\.\d+)*)\s+Point.to.Point Communication C Bindings')
    end = re.compile(r'^\s*(?:A\.\d+(?:\.\d+)?|\d+(?:\.\d+)*)\s+(?:Fortran|FORTRAN|C\+\+)')
    for page_number, page in enumerate(pages, 1):
        for line in page.splitlines():
            if begin.search(line) and not re.search(r'\.{3,}',line): active=True
            if active and end.search(line) and not re.search(r'\.{3,}',line): active=False
            if not active: continue
            if re.search(r'C [Bb]indings', line): section=line.strip()
            for name in NAME.findall(line):
                records[name]={'name':name,'standard':url+f'#page={page_number}','section':section}
    if len(records)<100:
        raise RuntimeError(f'Could not extract complete C summary for MPI {version}: {len(records)} entries')
    return records

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh',action='store_true',help='Download again instead of using cached sources')
    args=parser.parse_args(); CACHE.mkdir(parents=True,exist_ok=True)
    urls=[*PDFS.values(),*INDEXES.values(),MPC,MPC+'/blob/main/CHANGELOG.md']
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        downloads=dict(zip(urls,pool.map(lambda u:download(u,args.refresh),urls)))
    standards={v:extract_pdf(downloads[u],v,u) for v,u in PDFS.items()}
    indexes={k:sorted(set(re.findall(r'\bMPI_[A-Za-z0-9_]+\b',html.unescape(downloads[u].read_text())))) for k,u in INDEXES.items()}
    payload={'checked':datetime.date.today().isoformat(),'standards':standards,'indexes':indexes,'source_urls':urls,'implementations':{'openmpi':'5.0.10','mpich':'5.0.2'}}
    target=ROOT/'data/refreshed-snapshots.json';temporary=target.with_suffix('.tmp')
    temporary.write_text(json.dumps(payload,indent=2)+'\n');temporary.replace(target)
    print('Saved',target)
    print('MPC release notes downloaded. Run audit_sources.py to inventory the selected release sources.')

if __name__=='__main__':main()
