#!/usr/bin/env python3
import os
import sys
import json
import argparse
from github import Github
import requests
import re

def main():
    p = argparse.ArgumentParser(
        description="Fetch releases from warped-pinball/vector and generate per-product JSON"
    )
    p.add_argument("--owner",   required=True, help="GitHub org or user (e.g. warped-pinball)")
    p.add_argument("--repo",    required=True, help="Repo name to scan (e.g. vector)")
    p.add_argument("--out-dir", default="content", help="Where to write JSON files")
    args = p.parse_args()

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.stderr.write("ERROR: GITHUB_TOKEN not set\n")
        sys.exit(1)

    gh = Github(token)
    repository = gh.get_repo(f"{args.owner}/{args.repo}")

    # key = (product, channel) → (latest_release_obj, parsed_json)
    latest = {}

    for release in repository.get_releases():
        if release.draft:
            continue

        tag = release.tag_name

        # Determine product & version
        if tag.startswith("wpc-"):
            product = "wpc"
            version = tag[len("wpc-"):]
        else:
            # Everything else is sys11
            product = "sys11"
            # strip a leading "sys11-" if present, else keep full tag
            if tag.startswith("sys11-"):
                version = tag[len("sys11-"):]
            else:
                version = tag

        # Channel: prerelease → beta, else main
        channel = "beta" if release.prerelease else "main"

        # Find the update.json asset
        asset = next((a for a in release.get_assets() if a.name == "update.json"), None)
        if not asset:
            print(f"⏭️ Skipping {tag}: no update.json asset", file=sys.stderr)
            continue

        # Fetch and parse its JSON
        resp = requests.get(
            asset.browser_download_url,
            headers={"Authorization": f"token {token}"}
        )
        try:
            data = resp.json()
        except ValueError:
            print(f"❌ Invalid JSON at {asset.browser_download_url}", file=sys.stderr)
            continue

        # Ensure the JSON has the correct version/url (override if needed)
        # (Optional) Uncomment to enforce our convention:
        # data = {
        #   "version": version,
        #   "url": f"https://github.com/{args.owner}/{args.repo}/releases/download/{tag}/{tag}.uf2",
        #   **{k: v for k,v in data.items() if k not in ("version","url")}
        # }

        key = (product, channel)
        prev = latest.get(key)
        if not prev or release.published_at > prev[0].published_at:
            latest[key] = (release, data)

    # Write out the JSON files
    for (product, channel), (_, data) in latest.items():
        out_folder = os.path.join(args.out_dir, product)
        os.makedirs(out_folder, exist_ok=True)
        out_path = os.path.join(out_folder, f"{channel}.json")
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"✅ Wrote {out_path}")

    if not latest:
        print("⚠️  No matching releases found.")
    else:
        prods = ", ".join(f"{p}/{c}" for p,c in latest)
        print(f"✅ Generated updates for: {prods}")


if __name__ == "__main__":
    main()
