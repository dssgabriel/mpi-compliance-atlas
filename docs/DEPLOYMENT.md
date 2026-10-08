# Build and deployment

Run commands from the root of this repository. The site sources are in `site/`;
the GitHub Pages workflow is in `.github/workflows/pages.yml`.

## Local preview

```sh
python3 site/scripts/build_data.py
python3 site/scripts/build_standalone.py
python3 -m http.server 8000 --directory site/dist
```

Open http://localhost:8000. The standalone page at `site/dist/standalone.html`
also works directly from disk. Builds require Python 3.10+ and use the checked-in
source extracts and audit snapshots.

## GitHub Pages

1. Push this root repository to GitHub with `main` as its default branch.
2. In **Settings → Pages → Build and deployment → Source**, select
   **GitHub Actions**.
3. Run **Deploy GitHub Pages** in the Actions tab or push a commit to `main`.

The workflow builds the catalogue, runs the audit tests and uploads only
`site/dist/`. GitHub supplies the deployment URL. Relative asset paths support
repository Pages URLs; no custom domain or external vault checkout is required.

## Checks

```sh
python3 -m unittest discover -s site/scripts -p 'test_*.py'
```
