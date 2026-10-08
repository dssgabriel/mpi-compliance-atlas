"""MPI-5 chapter ownership and independent operation facets.

The standard does not define a kind/family/variant hierarchy. Those legacy
storage keys expose Chapter / Section / Operation form in the atlas. Chapter
ownership follows the final C binding summary, not name prefixes. Section
titles follow the MPI-5 contents. Operation form is not procedure blocking:
in particular Send_init and Bcast_init have different procedure semantics.
"""
import re
import json
import pathlib

BASE = 'https://www.mpi-forum.org/docs/mpi-5.0/mpi50-report/'
CHAPTERS = {
    'p2p': (3, 'Point-to-Point Communication'),
    'partitioned': (4, 'Partitioned Point-to-Point Communication'),
    'datatypes': (5, 'Datatypes'),
    'colls': (6, 'Collective Communication'),
    'communicator': (7, 'Groups, Contexts, Communicators, and Caching'),
    'topology': (8, 'Virtual Topologies for MPI Processes'),
    'environment': (9, 'MPI Environmental Management'),
    'info': (10, 'The Info Object'),
    'process': (11, 'Process Initialization, Creation, and Management'),
    'one-sided': (12, 'One-Sided Communications'),
    'external': (13, 'External Interfaces'),
    'io': (14, 'I/O'),
    'tools': (15, 'Tool Support'),
    'language': (19, 'Language Bindings'),
    'abi': (20, 'Application Binary Interface (ABI)'),
}
# Final PDF chapter numbers differ from the pre-final HTML numbering.
# The final PDF contents and A.3 summary are authoritative for ownership.
SUMMARY_CHAPTERS = dict(enumerate([
    'p2p', 'partitioned', 'datatypes', 'colls', 'communicator',
    'topology', 'environment', 'info', 'process', 'one-sided',
    'external', 'io', 'language', 'abi', 'tools', 'tools',
], 1))
TAXONOMY = {
    'version': 'MPI 5.0',
    'labels': {'kind': 'Chapter', 'family': 'Section', 'variant': 'Operation form'},
    'authority': 'https://www.mpi-forum.org/docs/mpi-5.0/mpi50-report.pdf',
    'basis': 'MPI-5.0 release-vault chapter API transclusions and heading paths; final PDF binding summary and explicit legacy mappings supply fallbacks',
    'note': 'Kind, family and variant are atlas storage keys, not MPI-defined taxonomy terms. Operation form is distinct from procedure blocking semantics. Sections use standard titles; orthogonal facets remain separate.',
    'vault_verified': True,
    'vault_note': 'Exact chapter and heading paths were read from the MPI-5.0 release vault, with the final PDF binding summary as fallback for appendix-only and legacy entries.',
    'references': {
        'organization': BASE + 'node25.htm',
        'naming': BASE + 'node28.htm',
        'operations': BASE + 'node31.htm',
        'vault_terms': 'https://github.com/tonyskjellum/mpi-md-vaults-release/blob/f3a7e844d56b07a95dedd6af475778984c1b073e/vaults/vault-mpi-50/sections/terms.md',
        'procedures': BASE + 'node32.htm',
        'contents': BASE + 'mpi50-report.htm',
    },
    'chapters': {key: {'number': number, 'title': title} for key, (number, title) in CHAPTERS.items()},
}


GROUPING = json.loads((pathlib.Path(__file__).resolve().parents[1] / 'data/standard-grouping.json').read_text())
TAXONOMY['vault_source'] = GROUPING['source']
TAXONOMY['vault_signatures_sha256'] = GROUPING['signatures_sha256']


def _chapter(name, section):
    if name in GROUPING['rows']:
        return GROUPING['rows'][name]['kind']
    match = re.match(r'A\.3\.(\d+)\b', section)
    if match and int(match[1]) in SUMMARY_CHAPTERS:
        return SUMMARY_CHAPTERS[int(match[1])]
    if section == 'Address arithmetic':
        return 'datatypes'
    if section == 'Timers and synchronization':
        return 'environment'
    # Deprecated/removed interfaces retain their functional chapter; lifecycle
    # is a separate facet. Every legacy name is explicitly accounted for.
    if name in {'MPI_Address', 'MPI_Get_elements_x', 'MPI_Type_extent',
                'MPI_Type_hindexed', 'MPI_Type_hvector', 'MPI_Type_lb',
                'MPI_Type_struct', 'MPI_Type_ub', 'MPI_Type_get_extent_x',
                'MPI_Type_get_true_extent_x', 'MPI_Type_size_x'}:
        return 'datatypes'
    if name in {'MPI_Errhandler_create', 'MPI_Errhandler_get', 'MPI_Errhandler_set'}:
        return 'environment'
    if name in {'MPI_Info_get', 'MPI_Info_get_valuelen'}:
        return 'info'
    if name == 'MPI_Status_set_elements_x':
        return 'external'
    if name in {'MPI_Attr_delete', 'MPI_Attr_get', 'MPI_Attr_put', 'MPI_DUP_FN',
                'MPI_Keyval_create', 'MPI_Keyval_free', 'MPI_NULL_COPY_FN',
                'MPI_NULL_DELETE_FN'}:
        return 'communicator'
    raise ValueError(f'No standard chapter evidence for {name}: {section!r}')


def classify(name, section):
    """Return chapter/section ownership and conservative semantic facets."""
    kind = _chapter(name, section)
    x = name.removesuffix('_c')[4:]
    lower = x.lower()
    family = CHAPTERS[kind][1]
    form = None
    facets = {}
    role = None
    if kind == 'p2p':
        if 'buffer' in lower:
            family = 'Buffer Allocation and Usage'
        elif x.startswith(('Wait', 'Test', 'Request_get_status')) and x != 'Test_cancelled':
            family = 'Nonblocking Communication'
            role = 'completion' if x.startswith(('Wait', 'Test')) else 'status inquiry'
        elif x.startswith(('Request_', 'Start')):
            family = 'Persistent Communication Requests' if x.startswith('Start') else 'Communication Request Objects'
            role = 'starting' if x.startswith('Start') else 'request management'
        elif x.startswith(('Cancel', 'Test_cancelled')):
            family = 'Probe and Cancel'
        elif 'probe' in lower or x.startswith(('Mrecv', 'Imrecv')):
            family = 'Probe and Cancel'
            if x.startswith(('Mrecv', 'Imrecv')):
                form = 'nonblocking' if x == 'Imrecv' else 'blocking'
            elif 'probe' in lower:
                role = 'message inquiry'
        elif x.endswith('_init'):
            family = 'Persistent Communication Requests'
            form, role = 'persistent', 'initialization'
        elif re.match(r'i?(?:[bsr]?send|recv)', lower):
            form = 'nonblocking' if lower.startswith('i') else 'blocking'
            family = 'Nonblocking Communication' if form == 'nonblocking' else 'Blocking Send and Receive Operations'
        if re.match(r'i?(?:[bsr]?send)', lower):
            facets['communication_mode'] = ('buffered' if 'bsend' in lower else
                'synchronous' if 'ssend' in lower else 'ready' if 'rsend' in lower else 'standard')
        if 'mprobe' in lower or 'mrecv' in lower:
            facets['message_matching'] = 'matched'
    elif kind == 'partitioned':
        family = 'Semantics of Partitioned Point-to-Point Communication'
        if x.endswith('_init'):
            form, role = 'persistent', 'initialization'
        elif x.startswith('Pready'):
            role = 'partition activation'
        else:
            role = 'partition arrival inquiry'
    elif kind == 'datatypes':
        family = 'Pack and Unpack' if x.startswith(('Pack', 'Unpack')) else 'Derived Datatypes'
    elif kind in {'colls', 'topology'}:
        neighbor = 'neighbor_' in lower
        if kind == 'colls' and (x.startswith('Op_') or x == 'Reduce_local'):
            family = 'Global Reduction Operations'
        elif neighbor or re.fullmatch(r'i?(?:allgather|allgatherv|allreduce|alltoall|alltoallv|alltoallw|barrier|bcast|exscan|gather|gatherv|reduce|reduce_scatter|reduce_scatter_block|scan|scatter|scatterv)(?:_init)?', lower):
            form = 'persistent' if x.endswith('_init') else 'nonblocking' if x.startswith('I') else 'blocking'
            facets['collective_scope'] = 'neighborhood' if neighbor else 'communicator'
            if neighbor:
                family = {'blocking': 'Neighborhood Collective Communication on Virtual Topologies',
                    'nonblocking': 'Nonblocking Neighborhood Communication on Process Topologies',
                    'persistent': 'Persistent Neighborhood Communication on Process Topologies'}[form]
            else:
                family = {'nonblocking': 'Nonblocking Collective Operations',
                    'persistent': 'Persistent Collective Operations'}.get(form, _collective_section(lower))
            if form == 'persistent':
                role = 'initialization'
        elif kind == 'topology':
            family = 'Topology Constructors' if x.endswith('create') or x == 'Dims_create' else 'Topology Inquiry Functions'
            if x.endswith('_map'):
                family = 'Low-Level Topology Functions'
            if x.startswith('Cart') or x == 'Dims_create':
                facets['topology_type'] = 'cartesian'
            elif x.startswith('Dist_graph'):
                facets['topology_type'] = 'distributed graph'
            elif x.startswith('Graph'):
                facets['topology_type'] = 'graph'
    elif kind == 'communicator':
        family = ('Group Management' if x.startswith('Group') else
            'Caching' if any(s in lower for s in ('keyval', '_attr', '_fn')) else
            'Naming Objects' if x.endswith(('_get_name', '_set_name')) else
            'Inter-Communication' if x.startswith('Intercomm') or '_remote_' in x else 'Communicator Management')
        if x.startswith('Comm_idup'):
            form = 'nonblocking'
    elif kind == 'environment':
        family = ('Timers and Synchronization' if x in {'Wtime', 'Wtick'} else
            'Memory Allocation' if x in {'Alloc_mem', 'Free_mem'} else
            'Error Handling' if 'err' in lower else 'Implementation Information')
    elif kind == 'process':
        family = ('The Sessions Model' if x.startswith('Session') else
            'MPI and Threads' if x in {'Init_thread', 'Query_thread', 'Is_thread_main'} else
            'The World Model' if x in {'Init', 'Finalize', 'Initialized', 'Finalized'} else
            'Common Elements of Both Process Models' if x == 'Abort' else
            'The Dynamic Process Model' if x.startswith('Comm_spawn') else 'Establishing Communication')
    elif kind == 'one-sided':
        family = ('Synchronization Calls' if x.startswith(('Win_fence', 'Win_lock', 'Win_unlock', 'Win_flush', 'Win_sync', 'Win_post', 'Win_start', 'Win_complete', 'Win_wait', 'Win_test')) else
            'Initialization' if x.startswith('Win') else 'Communication Calls')
        if x.startswith(('Rput', 'Rget', 'Raccumulate')):
            family = 'Request-based RMA Communication Operations'
            facets['rma_completion'] = 'request-based local completion'
        elif family == 'Communication Calls':
            facets['rma_completion'] = 'RMA synchronization'
        # RMA operation completion is governed by local/remote completion and
        # synchronization semantics; Put/Get are not labeled blocking here.
    elif kind == 'external':
        family = 'Generalized Requests' if x.startswith('Grequest') else 'Associating Information with Status'
    elif kind == 'io':
        if re.match(r'File_i?(?:read|write)', x):
            family = 'Split Collective Data Access Routines' if x.endswith(('_begin', '_end')) else 'Data Access'
            form = 'split collective' if x.endswith(('_begin', '_end')) else 'nonblocking' if x.startswith(('File_iread', 'File_iwrite')) else 'blocking'
            facets['io_positioning'] = 'explicit offset' if '_at' in x else 'shared file pointer' if '_shared' in x or '_ordered' in x else 'individual file pointer'
            facets['io_coordination'] = 'collective' if '_all' in x or '_ordered' in x else 'noncollective'
            if x.endswith(('_begin', '_end')):
                role = 'initiation' if x.endswith('_begin') else 'completion'
        elif x in {'Register_datarep', 'CONVERSION_FN_NULL', 'CONVERSION_FN_NULL_C'}:
            family = 'File Interoperability'
        elif x.endswith(('_get_view', '_set_view')):
            family = 'File Views'
        elif x in {'File_sync', 'File_get_atomicity', 'File_set_atomicity'}:
            family = 'Consistency and Semantics'
        else:
            family = 'File Manipulation'
    elif kind == 'tools':
        family = ('Profiling Interface' if x == 'Pcontrol' else
            'Control Variables' if x.startswith('T_cvar') else
            'Performance Variables' if x.startswith('T_pvar') else
            'Events' if x.startswith(('T_event', 'T_source')) else
            'Variable Categorization' if x.startswith('T_category') else 'Initialization and Finalization')
    elif kind == 'language':
        family = 'Language Interoperability'
    result = {
        'kind': kind, 'family': family, 'variant': form or 'not applicable',
        'chapter': {'number': CHAPTERS[kind][0], 'title': CHAPTERS[kind][1]},
        'operation_form': form,
        'taxonomy_source': TAXONOMY['authority'],
        'classification_basis': 'C binding summary ' + section,
    }
    evidence = GROUPING['rows'].get(name)
    if evidence:
        path = evidence['section_path']
        result['family'] = path[0] if path else CHAPTERS[kind][1]
        result['section_path'] = path
        result['taxonomy_source'] = GROUPING['source'] + '/blob/' + GROUPING['revision'] + '/' + evidence['vault_file'] + '#L' + str(evidence['line'])
        result['classification_basis'] = 'MPI-5.0 vault chapter API transclusion and heading path'
        result['classification_method'] = 'exact vault heading path'
    else:
        result['section_path'] = [family]
        result['classification_method'] = 'legacy functional mapping' if section == 'Removed MPI-1 APIs' or section.startswith('A.3.17 ') else 'binding-summary fallback'
        result['classification_basis'] += '; Section is a functional fallback, not an exact API heading path'
    if role:
        result['procedure_role'] = role
    # Explicit examples in Semantic Terms / MPI Procedures. These describe
    # the procedure, independently of the associated operation form.
    if x in {'Send_init', 'Recv_init', 'Isend', 'Irecv', 'Ibcast', 'Improbe'}:
        result['procedure_blocking'] = 'nonblocking'
    elif x in {'Send', 'Recv', 'Bcast', 'Mprobe', 'Bcast_init', 'Bsend', 'Rsend', 'Mrecv'} or re.fullmatch(r'File_(?:read|write)_(?:at_all|all|ordered)_begin', x):
        result['procedure_blocking'] = 'blocking'
    result.update(facets)
    return result


def _collective_section(lower):
    if lower == 'barrier':
        return 'Barrier Synchronization'
    if lower == 'bcast':
        return 'Broadcast'
    if lower.startswith('allgather'):
        return 'All-Gather'
    if lower.startswith('alltoall'):
        return 'All-to-All Scatter/Gather'
    if lower.startswith('gather'):
        return 'Gather'
    if lower.startswith('scatter'):
        return 'Scatter'
    if lower.startswith('reduce_scatter'):
        return 'Reduce-Scatter'
    if lower in {'scan', 'exscan'}:
        return 'Scan'
    return 'Global Reduction Operations'
