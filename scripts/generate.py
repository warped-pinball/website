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

    # key = (product, channel) → list of releases
    releases_by_product = {"sys11": {"main": [], "beta": []}, "wpc": {"main": [], "beta": []}}

    for release in repository.get_releases():
        if release.draft:
            continue

        tag = release.tag_name

        # Determine product & version
        if tag.startswith("wpc-"):
            product = "wpc"
            version = tag[len("wpc-"):]
        else:
            product = "sys11"
            if tag.startswith("sys11-"):
                version = tag[len("sys11-"):]
            else:
                version = tag

        # Channel: prerelease → beta, else main
        channel = "beta" if release.prerelease else "main"

        # Extract metadata from release info
        release_data = {
            "version": version,
            "url": f"https://github.com/{args.owner}/{args.repo}/releases/download/{tag}/{tag}.uf2",  # assuming firmware is named like tag.uf2
            "notes": release.body or "No release notes provided",
            "published_at": release.published_at.isoformat()  # Add the release date for sorting
        }

        # Store release data
        releases_by_product[product][channel].append(release_data)

    # Write out the JSON files
    for product, channels in releases_by_product.items():
        for channel, releases in channels.items():
            out_folder = os.path.join(args.out_dir, product)
            os.makedirs(out_folder, exist_ok=True)
            out_path = os.path.join(out_folder, f"{channel}.json")
            with open(out_path, "w") as f:
                json.dump(releases, f, indent=2)
            print(f"✅ Wrote {out_path}")

    print("✅ Generated release data for all products and channels.")


if __name__ == "__main__":
    main()
