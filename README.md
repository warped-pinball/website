# Warped Pinball Software Website

This repo powers the public firmware-update endpoints for Warped Pinball.

## Generating release data

Use `scripts/generate.py` to pull release information from GitHub and build the
JSON files served by GitHub Pages. Before running the script, install the
Python dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Then execute the generator with a valid `GITHUB_TOKEN` environment variable:

```bash
GITHUB_TOKEN=<token> python3 scripts/generate.py --owner warped-pinball --repo vector --out-dir .
```

Latest production builds are published under a `vector/` prefix. For example,
the System 11 firmware can be downloaded from:

```
https://software.warpedpinball.com/vector/sys11/latest.json
```

The repository includes a `CNAME` file so GitHub Pages serves the site at
`https://updates.warpedpinball.com` without extra path segments.

