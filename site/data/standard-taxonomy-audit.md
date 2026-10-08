# MPI standard organization audit

The MPI standard does not prescribe a universal `kind → family → variant`
hierarchy. Its formal organization is chapters, sections and procedure
specifications, with language-independent specifications and language bindings.
The atlas now exposes **Chapter / Section / Operation form**, retaining the old
field names internally for compatibility.

Source: `mpi-md-vaults-release` revision
`f3a7e844d56b07a95dedd6af475778984c1b073e`, MPI-5.0 vault. The release repository
states that the Forum PDF remains normative. Final PDF chapter numbering is
used; the pre-final HTML contents differ in numbering.

## Evidence and mapping

`standard-grouping.json` records exact C binding names, the containing chapter,
the complete heading path and the line of the API transclusion in chapter prose.
It contains 639 exact callable binding locations; callback typedefs are excluded.
The remaining 75 atlas entries have an explicitly marked fallback: 50 handle
conversion/serialization bindings, two predefined null conversion callbacks,
and 23 deprecated/removed entries. The final C binding summary supplies
ownership for appendix-only bindings; explicit legacy mappings preserve the
functional chapter of deprecated and removed interfaces. Every catalogue entry
must resolve; the classifier raises an error rather than using a utility bucket.

Reproduce the grouping evidence with:

```sh
python3 site/scripts/build_standard_grouping.py ../mpi-md-vaults-release
python3 site/scripts/test_standard_taxonomy.py
```

The broad Section column uses the first heading beneath the chapter. The source
inspector can also show the complete `section_path` for more specific ownership.
This respects the standard's uneven heading depth without inventing a uniform
family taxonomy. Lifecycle and large-count bindings remain independent facets.

Representative corrections:

| API | Chapter | Section |
| --- | --- | --- |
| `MPI_Type_get_value_index` | Collective Communication | Global Reduction Operations → MINLOC and MAXLOC |
| `MPI_Op_create` | Collective Communication | Global Reduction Operations → User-Defined Reduction Operations |
| `MPI_Neighbor_allgather` | Virtual Topologies for MPI Processes | Neighborhood Collective Communication on Virtual Topologies |
| `MPI_Type_create_keyval` | Groups, Contexts, Communicators, and Caching | Caching → Datatypes |
| `MPI_Comm_create_errhandler` | MPI Environmental Management | Error Handling → Error Handlers for Communicators |
| `MPI_Session_attach_buffer` | Point-to-Point Communication | Buffer Allocation and Usage |
| `MPI_Grequest_start` | External Interfaces | Generalized Requests |
| `MPI_Session_init` | Process Initialization, Creation, and Management | The Sessions Model |

## Formal semantic dimensions

Semantic Terms / MPI Operations defines operation forms **blocking,
nonblocking and persistent** and stages **initialization, starting, completion
and freeing**. Semantic Terms / MPI Procedures distinguishes the procedure's
locality and completeness; its blocking classification is a separate concept.

For example, `MPI_Send_init` and `MPI_Bcast_init` initialize persistent
operations. The former is a nonblocking procedure, while the latter is a
blocking procedure. The atlas records this distinction explicitly. Shared
completion routines such as `MPI_Wait` serve multiple operation forms and do
not receive a single inferred form. `MPI_Probe` and `MPI_Iprobe` are examples
of procedures that are not operation-related.

Communication mode (**standard, buffered, synchronous, ready**) is separate
from operation form. Neighborhood scope is separate from form. MPI-I/O
positioning (**explicit offset, individual file pointer, shared file pointer**)
and coordination (**collective, noncollective**) are independent. Split
collective I/O has separate initiation and completion procedures.

RMA Put/Get are not labeled blocking from their names. Their local and remote
completion semantics involve RMA synchronization. Request-based RMA supplies
request-based local completion, recorded as `rma_completion`, without implying
remote completion.

Naming Conventions describes `MPI_Class_action_subset`, with legacy exceptions.
This naming rule is useful as a facet but cannot determine chapter ownership:
datatype attribute routines appear in Caching and datatype value-index lookup
appears in collective reduction operations.

## Sources

- [MPI-5.0 vault organization](https://github.com/tonyskjellum/mpi-md-vaults-release/blob/f3a7e844d56b07a95dedd6af475778984c1b073e/vaults/vault-mpi-50/sections/intro.md)
- [MPI-5.0 vault terms and conventions](https://github.com/tonyskjellum/mpi-md-vaults-release/blob/f3a7e844d56b07a95dedd6af475778984c1b073e/vaults/vault-mpi-50/sections/terms.md)
- [MPI-5.0 final normative PDF](https://www.mpi-forum.org/docs/mpi-5.0/mpi50-report.pdf)

MPI: A Message-Passing Interface Standard, Version 5.0. © 1993–2025 University
of Tennessee, Knoxville, Tennessee. Standard heading extracts copied by
permission of the University of Tennessee; see the release repository NOTICE.md.
