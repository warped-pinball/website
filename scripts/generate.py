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
    p.add_argument("--out-dir", default="docs", help="Where to write JSON files")
    args = p.parse_args()

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.stderr.write("ERROR: GITHUB_TOKEN not set\n")
        sys.exit(1)

    gh = Github(token)
    repository = gh.get_repo(f"{args.owner}/{args.repo}")

    # key = (product) → list of full releases
    releases_by_product = {"sys11": [], "wpc": []}

    for release in repository.get_releases():
        if release.draft or release.prerelease:
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

        # Exclude releases with no update.json file
        asset = next((a for a in release.get_assets() if a.name == "update.json"), None)
        if not asset:
            print(f"⏭️ Skipping {tag}: no update.json asset", file=sys.stderr)
            continue

        # Extract metadata from release info
        release_data = {
            "version": version,
            "url": f"https://github.com/{args.owner}/{args.repo}/releases/download/{tag}/update.json",  # Fixed URL
            "notes": release.body or "No release notes provided",
            "published_at": release.published_at.isoformat()  # Add the release date for sorting
        }

        # Store release data
        releases_by_product[product].append(release_data)

    # Write out the JSON files for each product
    for product, releases in releases_by_product.items():
        if releases:
            out_folder = os.path.join(args.out_dir, product)
            os.makedirs(out_folder, exist_ok=True)
            out_path = os.path.join(out_folder, "main.json")
            with open(out_path, "w") as f:
                json.dump(releases, f, indent=2)
            print(f"✅ Wrote {out_path}")

            # Write the latest release to a separate file (latest.json)
            latest_release = max(releases, key=lambda r: r["published_at"])  # Get the latest release
            latest_release_data = {
                "version": latest_release["version"],
                "url": latest_release["url"],  # This is the download link for update.json
                "release_page": f"https://github.com/{args.owner}/{args.repo}/releases/tag/{latest_release['version']}",  # Link to the release page
                "published_at": latest_release["published_at"]  # Just the date, no need for release notes
            }

            latest_path = os.path.join(out_folder, "latest.json")
            with open(latest_path, "w") as f:
                json.dump(latest_release_data, f, indent=2)
            print(f"✅ Wrote {latest_path} for {product}")

    print("✅ Generated release data for all products.")


if __name__ == "__main__":
    main()
