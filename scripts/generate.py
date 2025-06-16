#!/usr/bin/env python3
import os
import sys
import json
import argparse
import hashlib
import requests
from github import Github

def fetch_asset_metadata(owner, repo, release_id, asset_name):
    """Fetch the metadata of an asset (such as SHA1 hash) using GitHub API."""
    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/{release_id}/assets"
    response = requests.get(api_url)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch assets for release {release_id}: {response.text}")
    
    assets = response.json()
    
    # Find the asset with the matching name
    for asset in assets:
        if asset["name"] == asset_name:
            return asset
    
    return None

def calculate_json_hash(json_data):
    """Calculate a hash for the given JSON data."""
    return hashlib.sha256(json.dumps(json_data, sort_keys=True).encode('utf-8')).hexdigest()

def main():
    p = argparse.ArgumentParser(
        description="Fetch releases from warped-pinball/vector and generate per-product JSON"
    )
    p.add_argument("--owner", required=True, help="GitHub org or user (e.g. warped-pinball)")
    p.add_argument("--repo", required=True, help="Repo name to scan (e.g. vector)")
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
    previous_update_hashes = {"sys11": None, "wpc": None}

    for release in repository.get_releases():
        if release.draft or release.prerelease:
            continue

        tag = release.tag_name
        # Determine the product (sys11 or wpc)
        if tag.startswith("wpc-"):
            product = "wpc"
            version = tag[len("wpc-"):]
        else:
            product = "sys11"
            if tag.startswith("sys11-"):
                version = tag[len("sys11-"):]
            else:
                version = tag

        # Get the asset metadata for update.json (instead of downloading the full file)
        asset = None
        try:
            asset = fetch_asset_metadata(args.owner, args.repo, release.id, "update.json")
        except Exception as e:
            print(f"⏭️ Skipping {tag}: {str(e)}", file=sys.stderr)
            continue

        if not asset:
            print(f"⏭️ Skipping {tag}: no update.json asset", file=sys.stderr)
            continue

        update_url = asset["browser_download_url"]
        # Use the SHA1 of the asset to compare files
        update_hash = asset["sha1"]

        # Skip this release if it's identical to the last release for this product
        if previous_update_hashes[product] == update_hash:
            print(f"⏭️ Skipping {tag}: identical to previous release")
            continue

        # Store the update hash to compare with the next release
        previous_update_hashes[product] = update_hash

        # Extract metadata for the release
        release_data = {
            "version": version,
            "url": update_url,  # This is the download link for update.json
            "notes": release.body or "No release notes provided",
            "published_at": release.published_at.isoformat()  # Add the release date for sorting
        }

        # Store the release data
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
