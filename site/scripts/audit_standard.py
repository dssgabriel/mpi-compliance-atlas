"""Compare exact C bindings with the released MPI Markdown vaults.

The vaults are a derived reference; the MPI Forum PDFs remain normative.
Run before build_data.py. The checked-in report makes offline rebuilds possible.
"""
import argparse
import collections
import hashlib
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY = 'https://github.com/tonyskjellum/mpi-md-vaults-release'
VERSIONS = ('13', '20', '21', '22', '30', '31', '40', '41', '50')
NAME = re.compile(r'\b(MPI_[A-Za-z0-9_]+)\s*\(')


def read_bindings(path):
    payload = json.loads(path.read_text())
    bindings, typedefs = {}, {}
    for function in payload['functions']:
        for prototype in function['c_bindings']:
            destination = typedefs if re.match(r'\s*typedef\b', prototype) else bindings
            for name in NAME.findall(prototype):
                record = {'prototype': prototype, 'procedure': function['lis_name'],
                          'vault_chapter': function['chapter']}
                if name in destination and destination[name] != record:
                    raise ValueError(f'Conflicting C binding: {path}: {name}')
                destination[name] = record
    return bindings, typedefs, len(payload['functions'])


def audit(vault_root, catalogue):
    inventory, sources = {}, {}
    for version in VERSIONS:
        relative = f'vaults/vault-mpi-{version}/signatures.json'
        path = vault_root / relative
        bindings, typedefs, procedures = read_bindings(path)
        inventory[version] = bindings
        sources[version] = {'path': relative, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                            'procedures': procedures, 'c_entries': len(bindings),
                            'excluded_callback_typedefs': sorted(typedefs)}
    commit = subprocess.run(['git', '-C', str(vault_root), 'rev-parse', 'HEAD'],
                            capture_output=True, text=True, check=True).stdout.strip()
    rows = {row['name']: row for row in catalogue['rows']}
    current = inventory['50']
    current_names = {name for name, row in rows.items() if row['lifecycle'] != 'removed'}
    missing, extra = sorted(current.keys() - current_names), sorted(current_names - current.keys())
    records = {}
    for name, binding in sorted(current.items()):
        present = [v for v in VERSIONS if name in inventory[v]]
        records[name] = dict(binding, releases=[v[0] + '.' + v[1] for v in present],
                             source=f'{REPOSITORY}/blob/{commit}/vaults/vault-mpi-50/API/{binding["procedure"]}.md')
    # Absence from a historical signature database is not evidence of absence
    # from the standard. MPI-2.0 is an extensions volume, and early callback
    # signatures are incomplete. Only explicit changes justify corrections.
    correction_source = f'{REPOSITORY}/blob/{commit}/vaults/vault-mpi-41/sections/changes.md'
    corrections = {
        'MPI_Status_set_elements_c': {
            'introduced': '4.1', 'source': correction_source,
            'reason': 'First ratified release containing this exact C binding is MPI-4.1. Its fixes-to-MPI-4.0-errata section explicitly says the missing large-count interface was added.'}
    }
    historical_discrepancies = []
    for name, row in rows.items():
        if name not in records:
            continue
        first = records[name]['releases'][0]
        if first != row['introduced'] and not (first == '1.3' and row['introduced'] in ('1.0', '1.2')):
            historical_discrepancies.append({'name': name, 'atlas_introduced': row['introduced'],
                                             'first_vault_signature': first,
                                             'resolution': 'explicit correction' if name in corrections else 'retain historical evidence; signature absence alone is inconclusive'})
    return {
        'reference': 'MPI 5.0', 'repository': REPOSITORY, 'commit': commit,
        'normative_source': 'https://www.mpi-forum.org/docs/mpi-5.0/mpi50-report.pdf',
        'scope': 'Catalogue C-binding coverage and metadata; no runtime implementation conformance tests.',
        'sources': sources,
        'coverage': {'atlas_entries': len(rows), 'standard_entries': len(current),
                     'matched_standard_entries': len(current_names & current.keys()),
                     'missing': missing, 'unexpected_current_entries': extra,
                     'retained_removed_entries': sorted(rows.keys() - current.keys())},
        'history_corrections': corrections, 'historical_discrepancies': historical_discrepancies,
        'limitations': ['Vaults are derived renderings, not normative publications.',
                        'MPI-1.0/1.1 are absent; MPI-1.3 cannot distinguish introductions in 1.0 and 1.2.',
                        'MPI-2.0 is an extensions volume, not a complete cumulative API inventory.',
                        'Callbacks may appear in prose before their signatures enter the appendices.',
                        'MPI_op_free is a known historical spelling inconsistency, not a missing atlas API.',
                        'A complete name inventory does not establish implementation semantic conformance.'],
        'bindings': records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vault-root', type=pathlib.Path, default=ROOT.parents[1] / 'mpi-md-vaults-release')
    parser.add_argument('--catalogue', type=pathlib.Path, default=ROOT / 'dist/apis.json')
    args = parser.parse_args()
    report = audit(args.vault_root.resolve(), json.loads(args.catalogue.read_text()))
    (ROOT / 'data/standard-vault-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['coverage'], indent=2))
    if report['coverage']['missing'] or report['coverage']['unexpected_current_entries']:
        raise SystemExit('Standard inventory mismatch; review the report before rebuilding.')


if __name__ == '__main__':
    main()
