# Warped Pinball Software Website

This repo powers the public firmware-update endpoints for Warped Pinball.

## Generating release data

Use `scripts/generate.py` to pull release information from GitHub and build the
JSON files served by GitHub Pages. Before running the script, install the
Python dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Then execute the generator with a valid `GITHUB_TOKEN` environment variable.  
The site is published from the `docs/` directory, so write all generated files
there:

```bash
GITHUB_TOKEN=<token> python3 scripts/generate.py --owner warped-pinball --repo vector --out-dir docs
```

All firmware metadata files are published under a `vector/` prefix. For example,
the System 11 metadata can be downloaded from:

```
https://software.warpedpinball.com/vector/sys11/latest.json
```
Additional files like `prod.json`, `beta.json`, and `dev.json` live in the same
`vector/<product>` directory.

GitHub Pages is configured to publish from the `docs/` directory. The
repository includes a `CNAME` file so the site is served at
`https://updates.warpedpinball.com` without extra path segments.

