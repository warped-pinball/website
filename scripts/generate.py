#!/usr/bin/env python3
import os
import sys
import json
import argparse
import hashlib
import requests
from github import Github

def fetch_update_json(url):
    """Fetch an update JSON file and return its parsed content."""
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def calculate_json_hash(json_data):
    """Return a deterministic SHA256 digest for a JSON object."""
    return hashlib.sha256(json.dumps(json_data, sort_keys=True).encode("utf-8")).hexdigest()

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

    # key = product -> list of unique releases
    releases_by_product = {"sys11": [], "wpc": []}
    # track last update hash for each product so we can skip identical builds
    previous_update_hashes = {"sys11": None, "wpc": None}
    file_db = []  # collect metadata for all update files

    releases = list(repository.get_releases())
    # sort oldest -> newest so we only skip later duplicates
    releases.sort(key=lambda r: r.created_at)

    for release in releases:
        tag = release.tag_name
        if tag.startswith("wpc-"):
            base_version = tag[len("wpc-") :]
        elif tag.startswith("sys11-"):
            base_version = tag[len("sys11-") :]
        else:
            base_version = tag

        release_type = "production"
        if release.draft:
            release_type = "dev"
        elif release.prerelease:
            release_type = "beta"

        # gather assets by name
        assets = {a.name: a for a in release.get_assets()}
        for asset_name, product in [("update.json", "sys11"), ("update_wpc.json", "wpc")]:
            asset = assets.get(asset_name)
            if not asset:
                continue

            update_data = fetch_update_json(asset.browser_download_url)
            if update_data is None:
                print(f"⏭️ Skipping {tag} {asset_name}: failed to fetch", file=sys.stderr)
                continue

            update_hash = calculate_json_hash(update_data)

            file_db.append({
                "product": product,
                "version": base_version,
                "type": release_type,
                "url": asset.browser_download_url,
                "sha256": update_hash,
                "download_count": asset.download_count,
            })

            # Only skip if this is a production build identical to previous production
            if release_type == "production" and previous_update_hashes[product] == update_hash:
                continue

            if release_type == "production":
                previous_update_hashes[product] = update_hash

            release_entry = {
                "version": base_version,
                "url": asset.browser_download_url,
                "notes": release.body or "No release notes provided",
                "published_at": release.published_at.isoformat(),
                "type": release_type,
            }
            releases_by_product[product].append(release_entry)

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

    # write mini database of all update files
    if file_db:
        build_db_path = os.path.join(args.out_dir, "builds.json")
        with open(build_db_path, "w") as f:
            json.dump(file_db, f, indent=2)
        print(f"✅ Wrote {build_db_path}")

    print("✅ Generated release data for all products.")

if __name__ == "__main__":
    main()
