# Atlas assessment against the released MPI vaults

The atlas contains all **704 MPI-5.0 C-callable entries** found in the release
vault's binding inventory, with no missing or unexpected current names. Its
remaining ten entries are explicitly retained, removed MPI-1 interfaces.
Callback typedefs are excluded from callable-entry counts. A vault routine can
have several C bindings, so its 535 routine records are not directly comparable
to the atlas's 714 entries.

The review used the supplied local `mpi-md-vaults-release` checkout at revision
`f3a7e844d56b07a95dedd6af475778984c1b073e`, covering released versions MPI-1.3
through MPI-5.0. Input hashes, exact binding inventory, historical differences
and evidence links are recorded in `standard-vault-audit.json`. The vault
repository describes its content as derived renderings; the final MPI Forum
PDF remains normative.

## Metadata correction

`MPI_Status_set_elements_c` first appears in a ratified release in **MPI-4.1**.
The MPI-4.1 fixes-to-MPI-4.0-errata section explicitly identifies the addition of
this missing large-count interface. The atlas's previous MPI-4.0 introduction
label is corrected to MPI-4.1.

Other signature-history differences are retained as review evidence rather
than blindly rewriting introduction dates. In particular, MPI-2.0 is an
extensions volume rather than a cumulative standard, MPI-1.0/1.1 are absent
from the vault release, and some callback functions appeared in chapter prose
before their signatures entered the annexes. The addition of the
`MPI_CONVERSION_FN_NULL` signature to the MPI-3.1 annex does not establish that
the callback itself was introduced in MPI-3.1.

## Organization correction

MPI does not define the atlas's former `kind → family → variant` hierarchy.
The formal document has **chapters, sections, procedure specifications and
language bindings**. The interface now uses **Chapter / Section / Operation
form**, retaining the old storage keys for compatibility.

Exact API transclusions under chapter headings provide **639 binding locations**.
The remaining **75 entries** have explicitly marked fallbacks: 50 handle
conversion/serialization bindings, two predefined null conversion callbacks and
23 deprecated/removed interfaces. These use final C-binding-summary ownership
or explicit legacy functional mappings; their functional Section label is
distinguished from an exact API heading path. The grouping snapshot is
`standard-grouping.json`; its reproducible generator records input hashes and
the source revision. Each exact location links to a pinned chapter line.

Chapter ownership now follows the standard rather than prefixes. Examples:

| API group | Standard chapter |
| --- | --- |
| Neighborhood collectives | Virtual Topologies for MPI Processes |
| Reduction operator management and datatype value-index lookup | Collective Communication |
| Datatype/window/communicator attributes | Groups, Contexts, Communicators, and Caching |
| Communicator/window/file/session error handlers | MPI Environmental Management |
| Session-scoped buffer management | Point-to-Point Communication |
| Generalized requests | External Interfaces |
| Sessions initialization | Process Initialization, Creation, and Management |

Operation forms **blocking, nonblocking and persistent** are separate from
procedure blocking semantics. Both `MPI_Send_init` and `MPI_Bcast_init`
initialize persistent operations, but the standard classifies the former
procedure as nonblocking and the latter as blocking. Shared request completion
functions receive no single operation form. Communication mode, collective
scope and MPI-I/O positioning/coordination are separate facets. RMA Put/Get are
not labeled blocking; their completion relies on RMA synchronization.

See `standard-taxonomy-audit.md` for the detailed formal-structure analysis.

## Limits

This assessment verifies catalogue names and metadata against standard sources.
It does not establish semantic conformance of Open MPI, MPICH or MPC and performs
no runtime conformance tests. Existing implementation support columns continue
to report the separate release-source audit, including its limitations.

Sources: [release vault](https://github.com/tonyskjellum/mpi-md-vaults-release/tree/f3a7e844d56b07a95dedd6af475778984c1b073e),
[MPI-4.1 changes](https://github.com/tonyskjellum/mpi-md-vaults-release/blob/f3a7e844d56b07a95dedd6af475778984c1b073e/vaults/vault-mpi-41/sections/changes.md),
[MPI-5.0 semantic terms](https://github.com/tonyskjellum/mpi-md-vaults-release/blob/f3a7e844d56b07a95dedd6af475778984c1b073e/vaults/vault-mpi-50/sections/terms.md),
[final MPI-5.0 PDF](https://www.mpi-forum.org/docs/mpi-5.0/mpi50-report.pdf).

MPI: A Message-Passing Interface Standard, Version 5.0. © 1993–2025 University
of Tennessee, Knoxville, Tennessee. Standard heading extracts copied by
permission of the University of Tennessee; see the release repository NOTICE.md.
