#!/usr/bin/env python3
import os
import sys
import json
import argparse
from github import Github
import requests

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
        if tag.startswith("sys11-"):
            product = "sys11"
            version = tag[len("sys11-"):]
        elif tag.startswith("wpc-"):
            product = "wpc"
            version = tag[len("wpc-"):]
        else:
            continue

        channel = "beta" if release.prerelease else "main"

        # find the update.json asset
        asset = next((a for a in release.get_assets() if a.name == "update.json"), None)
        if not asset:
            print(f"⏭️ Skipping {tag}: no update.json asset", file=sys.stderr)
            continue

        # fetch and parse its JSON
        resp = requests.get(
            asset.browser_download_url,
            headers={"Authorization": f"token {token}"}
        )
        data = resp.json()

        key = (product, channel)
        prev = latest.get(key)
        if not prev or release.published_at > prev[0].published_at:
            latest[key] = (release, data)

    # write out the JSON files
    for (product, channel), (_, data) in latest.items():
        out_folder = os.path.join(args.out_dir, product)
        os.makedirs(out_folder, exist_ok=True)
        out_path = os.path.join(out_folder, f"{channel}.json")
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)

    prods = [f"{k[0]}/{k[1]}" for k in latest]
    print("✅ Generated updates for:", ", ".join(prods))


if __name__ == "__main__":
    main()
