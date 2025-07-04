#!/usr/bin/env python3
import os
import sys
import json
import argparse
import hashlib
import requests
from github import Github
import re

def fetch_update_json(url):
    """Fetch an update JSON file and return its parsed content.

    The update files published by the firmware repository contain a JSON
    metadata line followed by additional binary data.  Using ``response.json``
    directly fails because of this extra content.  Instead, read only the
    first line of the response and parse that as JSON.
    """

    response = requests.get(url)
    if response.status_code != 200:
        return None

    # splitlines handles both ``\n`` and ``\r\n`` newlines
    first_line = response.text.splitlines()[0]
    return json.loads(first_line)

def calculate_json_hash(json_data):
    """Return a deterministic SHA256 digest for a JSON object."""
    return hashlib.sha256(json.dumps(json_data, sort_keys=True).encode("utf-8")).hexdigest()


def parse_release_versions(text):
    """Return a mapping of product name to version from a release body."""
    if not text:
        return {}

    block_match = re.search(
        r"##\s*Versions\s*(.*?)<!--\s*END VERSIONS SECTION\s*-->",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if not block_match:
        return {}

    section = block_match.group(1)
    versions = {}
    for m in re.finditer(r"\*\*([^*]+)\*\*:\s*`([^`]+)`", section):
        product = m.group(1).strip().lower()
        versions[product] = m.group(2).strip()
    return versions

def main():
    p = argparse.ArgumentParser(
        description="Fetch releases from warped-pinball/vector and generate per-product JSON"
    )
    p.add_argument("--owner", required=True, help="GitHub org or user (e.g. warped-pinball)")
    p.add_argument("--repo", required=True, help="Repo name to scan (e.g. vector)")
    p.add_argument(
        "--out-dir",
        default="docs",
        help=(
            "Where to write JSON files (defaults to the 'docs' folder so GitHub Pages can serve them)"
        ),
    )
    args = p.parse_args()

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.stderr.write("ERROR: GITHUB_TOKEN not set\n")
        sys.exit(1)

    gh = Github(token)
    repository = gh.get_repo(f"{args.owner}/{args.repo}")

    # key = product -> dict of release lists by type
    releases_by_product = {
        "sys11": {"prod": [], "beta": [], "dev": [], "all": []},
        "wpc": {"prod": [], "beta": [], "dev": [], "all": []},
    }
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

        versions_in_body = parse_release_versions(release.body or "")

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

            product_version = versions_in_body.get(product, base_version)
            release_type = "production"
            if re.search(r"-dev\d+$", product_version):
                release_type = "dev"
            elif re.search(r"-beta-?\d+$", product_version):
                release_type = "beta"

            update_hash = calculate_json_hash(update_data)

            file_db.append({
                "product": product,
                "version": product_version,
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
                "version": product_version,
                "url": asset.browser_download_url,
                "notes": release.body or "No release notes provided",
                "published_at": release.published_at.isoformat(),
                "type": release_type,
                "download_count": asset.download_count,
            }
            releases_by_product[product]["all"].append(release_entry)
            releases_by_product[product][release_type if release_type != "production" else "prod"].append(release_entry)

    # Write out the JSON files for each product
    for product, groups in releases_by_product.items():
        if groups["all"]:
            # All firmware metadata now lives under docs/vector/<product>
            out_folder = os.path.join(args.out_dir, "vector", product)
            os.makedirs(out_folder, exist_ok=True)

            # write combined data for backward compatibility
            all_path = os.path.join(out_folder, "all.json")
            with open(all_path, "w") as f:
                json.dump(groups["all"], f, indent=2)
            print(f"✅ Wrote {all_path}")

            # write per-type JSON files
            for key, filename in [("prod", "prod.json"), ("beta", "beta.json"), ("dev", "dev.json")]:
                path = os.path.join(out_folder, filename)
                with open(path, "w") as f:
                    json.dump(groups[key], f, indent=2)
                print(f"✅ Wrote {path}")

            # Write the latest production release to a separate file (latest.json)
            prod_releases = groups["prod"]
            if prod_releases:
                latest_release = max(prod_releases, key=lambda r: r["published_at"])
            else:
                latest_release = max(groups["all"], key=lambda r: r["published_at"])
            latest_release_data = {
                "version": latest_release["version"],
                "url": latest_release["url"],  # This is the download link for update.json
                "release_page": f"https://github.com/{args.owner}/{args.repo}/releases/tag/{latest_release['version']}",  # Link to the release page
                "published_at": latest_release["published_at"]  # Just the date, no need for release notes
            }

            # Latest release metadata in the same folder
            # https://software.warpedpinball.com/vector/<product>/latest.json
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
