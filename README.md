# Warped Pinball Software Website

This repo powers the public firmware-update endpoints for Warped Pinball.

## Generating release data

Use `scripts/generate.py` to pull release information from GitHub and build the
JSON files served in the `docs` folder. Before running the script, install the
Python dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Then execute the generator with a valid `GITHUB_TOKEN` environment variable:

```bash
GITHUB_TOKEN=<token> python3 scripts/generate.py --owner warped-pinball --repo vector --out-dir docs
```

