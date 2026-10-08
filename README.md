# MPI Compliance Atlas

MPI Compliance Atlas is an interactive reference for comparing MPI C API availability across [**Open MPI**](https://github.com/open-mpi/ompi), [**MPICH**](https://github.com/pmodels/mpich) and [**MPC**](https://github.com/cea-hpc/mpc), using **MPI 5.0** as the standard reference.

The atlas contains **714 entries**: all 704 standard C entries plus ten removed MPI-1 interfaces retained for historical comparison.
It includes MPI Tools, large-count bindings and predefined callbacks.

Our standard introduction reference draws on the [MPI standard vaults](https://github.com/tonyskjellum/mpi-md-vaults-release); we thank Anthony Skjellum and Nicole Avans for making them available.

Readers can search APIs, browse standard chapters and sections, and filter by introduction revision, lifecycle and count binding.
Each entry links to standard and implementation evidence; the source inspector shows the reasoning behind its support classification.

- **Supported:** positive implementation or exact documentation evidence.
- **Unsupported:** absent from the reviewed release sources or a reviewed stub.
- **Unknown:** unresolved source or linkage evidence.

The comparison uses specific release snapshots.
These labels describe API availability and source evidence; they do not certify complete semantic or runtime MPI conformance.

See the [methodology](docs/METHODOLOGY.md), [standard assessment](site/data/standard-assessment.md) and [source attribution](site/NOTICE.md) for the evidence and review limits.

## AI disclosure

AI assistance was used to develop the site, organize and assess API evidence, and write documentation.
The atlas links to the underlying standard and implementation sources so readers can review its claims; AI-assisted analysis does not establish runtime MPI conformance.
