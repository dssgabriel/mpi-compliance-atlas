"""Build section links from local copies of the MPI Forum HTML editions."""
import argparse
import collections
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
FORUM = 'https://www.mpi-forum.org/docs/'
HEADING = re.compile(r'<h[1-6]\b[^>]*>\s*<(?:span id|a name)="(Node\d+)"', re.I)
LITERAL = re.compile(r'<tt\b[^>]*>(.*?)</tt\s*>', re.I | re.S)
# Some pages put the name after the argument list (e.g. handle conversion).
BINDING = re.compile(r'^\s*(?:(?:int|void|double|MPI_\w+)\s+(MPI_\w+)\s*\(|\([^)]*\)\s*(MPI_\w+)\s*$)')

# These predefined names are defined in prose, not in separate binding blocks.
# Finalize also appears in a tool example; select its actual definition.
PREFERRED = {
    'node208.htm#Node208': ('MPI_COMM_DUP_FN', 'MPI_COMM_NULL_COPY_FN', 'MPI_COMM_NULL_DELETE_FN'),
    'node209.htm#Node209': ('MPI_WIN_DUP_FN', 'MPI_WIN_NULL_COPY_FN', 'MPI_WIN_NULL_DELETE_FN'),
    'node210.htm#Node210': ('MPI_TYPE_DUP_FN', 'MPI_TYPE_NULL_COPY_FN', 'MPI_TYPE_NULL_DELETE_FN'),
    'node270.htm#Node270': ('MPI_Finalize',),
    'node380.htm#Node382': ('MPI_CONVERSION_FN_NULL', 'MPI_CONVERSION_FN_NULL_C'),
    'node446.htm#Node446': ('MPI_DUP_FN', 'MPI_NULL_COPY_FN', 'MPI_NULL_DELETE_FN'),
}


def section_links(directory, names, appendix_start, preferred):
    candidates = collections.defaultdict(set)
    sections = {}
    for page in directory.glob('node*.htm*'):
        node = re.fullmatch(r'node(\d+)', page.stem)
        if not node or int(node[1]) >= appendix_start:
            continue
        source = page.read_text(encoding='latin-1')
        headings = list(HEADING.finditer(source))
        for i, heading in enumerate(headings):
            end = headings[i+1].start() if i+1 < len(headings) else len(source)
            section = source[heading.end():end]
            target = f'{page.name}#{heading[1]}'
            sections[target] = section
            for literal in LITERAL.findall(section):
                binding = BINDING.match(html.unescape(re.sub(r'<[^>]*>', ' ', literal)))
                if binding:
                    name = binding[1] or binding[2]
                    if name in names:
                        candidates[name].add(target)

    for target, apis in preferred.items():
        for name in apis:
            if not re.search(rf'\b{re.escape(name)}\b', sections.get(target, '')):
                raise ValueError(f'{name} not found at reviewed target {target}')
            candidates[name] = {target}

    unresolved = {name: sorted(candidates[name]) for name in sorted(names) if len(candidates[name]) != 1}
    if unresolved:
        raise ValueError(f'Expected one HTML definition per API, found {unresolved}')
    return {name: next(iter(candidates[name])) for name in names}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mpi50', type=pathlib.Path, help='Local mpi-5.0/mpi50-report directory')
    parser.add_argument('mpi11', type=pathlib.Path, help='Local mpi-1.1/mpi-11-html directory')
    args = parser.parse_args()
    audit = json.loads((ROOT / 'data/standard-vault-audit.json').read_text())
    modern = section_links(args.mpi50, set(audit['bindings']), 555, PREFERRED)
    legacy = section_links(args.mpi11, set(audit['coverage']['retained_removed_entries']), 167, {})
    links = {name: FORUM + 'mpi-5.0/mpi50-report/' + target for name, target in modern.items()}
    links.update({name: FORUM + 'mpi-1.1/mpi-11-html/' + target for name, target in legacy.items()})
    (ROOT / 'data/standard-html-links.json').write_text(json.dumps(links, indent=2, sort_keys=True) + '\n')
    print(f'{len(modern)} MPI 5.0 and {len(legacy)} MPI 1.1 HTML definitions')


if __name__ == '__main__':
    main()
