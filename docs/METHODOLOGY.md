# MPI Compliance Atlas

A static page comparing MPI C APIs across the standard, Open MPI, MPICH and MPC.
The checked-in snapshot contains 714 C-callable entries in a flat register,
ordered by **chapter → section → operation form**, with explicit classification columns,
search, introduction revision, lifecycle and count binding filters. Every entry links to its C binding summary, chapter/section evidence and support evidence.

The interface uses square corners, compact monospaced typography and ruled
tables. Filter state and filtered support totals are explicit. A persistent
source inspector replaces the modal; selected records remain inspectable when
filters hide their row. The release ledger exposes source archive URLs, scanned
file counts, unresolved API counts and SHA-256 checksums. No external fonts,
framework or animated transitions are required.

## Run locally

Open `site/dist/standalone.html` directly in your browser; it needs no server.
The header and favicon use a transparent SVG recreation in
`site/assets/mpi-forum-logo.svg`, based on the downloaded official
[MPI Forum icon](https://github.com/mpi-forum/mpi-forum.github.io/blob/master/images/mpi-forum-icon.jpg).
The build copies the SVG into `site/dist/assets` and embeds it in the standalone
page, so the logo also works offline.
Rebuild this self-contained file after updating the catalogue:

```sh
python3 site/scripts/build_standalone.py
```

Alternatively, serve the normal multi-file page.

From the repository root:

```sh
python3 -m http.server 8000 --directory site/dist
```

Open http://localhost:8000. Serve the directory over HTTP; opening index.html
directly may block the JSON fetch.

## Sources and confidence

- The final [MPI 5.0 PDF](https://www.mpi-forum.org/docs/mpi-5.0/mpi50-report.pdf)
  supplies the complete C binding summary. The earlier HTML is missing final ABI
  serialization functions, so the final PDF is authoritative.
- Historical MPI 1.1, 2.2 and 3.1 binding summaries and explicit change logs supply
  introduction revisions. The MPI-1 baseline maps to 1.0 using the 1.1 archive;
  introduction is about the name, not all later semantic changes. Two address
  arithmetic helpers, two timer functions and ten removed MPI-1 functions augment
  the current summary.
- [Open MPI 5.0.10](https://docs.open-mpi.org/en/v5.0.10/man-openmpi/man3/index.html)
  and [MPICH 5.0.2](https://www.mpich.org/static/docs/v5.0.2/) manual indexes supply
  per-name documentation evidence.
- [MPC 4.3.1](https://github.com/cea-hpc/mpc/releases/tag/MPC_4.3.1) is the latest
  release checked. Its general conformance statement is not used as per-function
  evidence. Its release sources are now included in the source review.

**Supported** means a C implementation or exact API documentation is available;
its evidence panel distinguishes source and documentation evidence.
**Unsupported** means absent from the checked release source tree or a reviewed
stub. Source contradictions take precedence over documentation. **Unknown** is
reserved for unavailable sources or unresolved generated/conditional code.
A missing API in an inspected source tree is unsupported. Declarations and
library symbols alone do not prove implementation. Valid no-op APIs and null
callbacks must be distinguished from broken stubs.

The current snapshot uses **the exact released source archives**, with review
of candidate stubs, implementing macros and predefined callback aliases:

| Release | Supported | Unsupported | Unknown |
| --- | ---: | ---: | ---: |
| Open MPI 5.0.10 | 482 | 232 | 0 |
| MPICH 5.0.2 | 714 | 0 | 0 |
| MPC 4.3.1 | 441 | 272 | 1 |

MPC's `MPI_Register_datarep` is the single unresolved case: a core aborting stub
conflicts with a bundled ROMIO implementation. Resolving which symbol is exposed
requires a built-library/linkage check. MPC status conversions documented in its
manpages but lacking C implementations are unsupported. Error registration and
MPI_T routines returning success without writing outputs are unsupported too.

Supported is positive source evidence, **not a guarantee of complete MPI
conformance or absence of runtime bugs**. This review detects missing APIs and
identified stubs; it does not exhaustively verify every backend, platform,
algorithm, argument combination or build configuration. MPI-I/O requires the
implementation's I/O component. Open MPI's removed MPI-1 declarations require
`--enable-mpi1-compatibility`. No runtime conformance tests were performed.

Grouping follows MPI 5.0 chapters and section paths extracted from the released
vault. Sessions belong to Process Initialization, Creation, and Management;
request completion belongs to Point-to-Point Communication; neighborhood
collectives belong to Virtual Topologies. Datatypes, Info, External Interfaces,
Language Bindings and ABI retain their standard chapters. Operation form,
communication mode, collective scope and I/O positioning are separate attributes.
The legacy JSON keys `kind`, `family`, `variant` now mean Chapter, Section and
Operation form; these are atlas field names, not normative MPI taxonomy terms.

Includes built-in callback functions, MPI_T and large-count variants. Excludes
constants, callback typedefs, Fortran-specific bindings, MPIX extensions and
duplicate PMPI profiling aliases.

## Standard vault assessment

The [released MPI standard vaults](https://github.com/tonyskjellum/mpi-md-vaults-release)
independently confirm **704 of 704 MPI 5.0 C entries**, with no missing or
unexpected current entries. The ten removed MPI-1 entries are retained as history.
The vault has 535 procedure records; expanding their C bindings (including `_c`)
and excluding 20 callback typedefs gives 704 catalogue entries. Procedure and
binding counts describe different things.

`site/data/standard-vault-audit.json` records the repository commit, per-release
signature SHA-256, exact prototypes, coverage and historical discrepancies.
`site/data/standard-grouping.json` records chapter/heading evidence, and
`site/data/standard-assessment.md` explains the result and limitations.
The MPI Forum PDF remains normative; the vaults are derived renderings.

One introduction correction follows explicit standard errata: the exact
`MPI_Status_set_elements_c` binding first appears in the ratified MPI 4.1 text,
which adds the missing large-count interface as a fix to MPI 4.0. The atlas now
records 4.1 and exposes this qualification. Historical signature absence alone
is not used to change introductions: MPI 2.0 is an extensions volume and some
callbacks appear in prose before entering binding appendices.

Regenerate the vault comparison from a local checkout, then rebuild:

```sh
python3 site/scripts/audit_standard.py --vault-root ../mpi-md-vaults-release
python3 site/scripts/build_standard_grouping.py --vault-root ../mpi-md-vaults-release
python3 site/scripts/build_data.py
python3 site/scripts/test_standard_audit.py
python3 site/scripts/test_standard_taxonomy.py
python3 site/scripts/build_standalone.py
```

This establishes catalogue coverage and improves classification. It does not
establish semantic or runtime conformance of Open MPI, MPICH or MPC; their
existing release-source evidence and unresolved linkage case remain applicable.

## Rebuild / refresh

Rebuild the page's JSON from the checked-in source extracts, offline:

```sh
python3 site/scripts/build_data.py
```

Re-download the official PDF documents, manual indexes and MPC release notes on
a machine with network access, then rebuild:

```sh
python3 site/scripts/scrape.py --refresh
python3 site/scripts/build_data.py
```

The standards scraper requires Python 3 and Poppler's `pdftotext`. It caches
sources and fails on missing/incomplete documents rather than discarding APIs.
The shell cannot resolve download hosts in this environment; the documentation
snapshot was retrieved through the web reader and the user downloaded the
release archives. The complete cached-source inventory now runs successfully.

Inventory the exact release source archives on a network-enabled machine:

```sh
python3 site/scripts/audit_sources.py
python3 site/scripts/build_data.py
python3 site/scripts/build_standalone.py
```

`site/data/releases.json` pins versions, archive URLs, tags and release evidence.
The auditor scans production C sources/headers and binding generators, excluding
tests and examples. It records source paths, line numbers and archive SHA-256;
rejects mismatched archive roots and unrecognized/incomplete source layouts;
and preserves the existing audit if any selected download fails. A declaration
or reference without a recognized body remains a review candidate until aliases,
macros, binding generators and build files have been inspected. No mention
anywhere in the scanned production tree is unsupported. Literal C definitions
are positive static evidence, not a guarantee about backend/runtime behavior.

Potential stubs are put in the JSON `review` list. Unconditional failure markers
or termination bodies are unsupported; empty/constant-return bodies require
semantic review to avoid rejecting legitimate no-ops. Generated bindings,
conditional code, wrapper backends and build availability must also be reviewed
before claiming a full implementation audit. Place reviewed per-API results in
`site/data/source-overrides.json` with implementation keys and API-name keys;
each override requires `version`, `status`, `source` and `reason`. Source results
override docs, including documented APIs that are missing or unimplemented.
MPICH generated C binding locations refer to the official release archive;
evidence links point to their versioned generator templates when available.

For an already downloaded official archive:

```sh
python3 site/scripts/audit_sources.py --impl mpc --archive /path/to/mpc-MPC_4.3.1.tar.gz
```

The scanner and reviewed snapshot are verified by:

```sh
python3 site/scripts/test_audit_sources.py
```

Checks cover continued strings, declarations, calls, guarded error paths,
unconditional failure markers, legitimate no-ops, missing APIs, test-only
symbols, incomplete source layouts and wrong release versions. Older locally
cached archives were used only to verify the scanner and were excluded from
the release columns. UI filters and versioned evidence panels were checked too.

The page has no framework or backend. GitHub Pages publishes `site/dist` through
the repository workflow; see docs/DEPLOYMENT.md for deployment setup.

## Attribution

MPI: A Message-Passing Interface Standard. ©1993–2025 University of Tennessee,
Knoxville, Tennessee. MPI standard extracts copied by permission under the
notice included in the standard. Implementation documentation belongs to the
respective projects. Saved extracts are research inputs; the UI uses structured
API names and evidence classifications rather than republishing manual prose.
