# Release Process

This document covers the standard flow for publishing a new `vector` release and updating the website metadata.

## Prerequisites

- Access to create releases in the `vector` repository.
- Access to create branches and PRs in this `website` repository.
- Permission to run GitHub Actions in this repository.
- Access to notify Tim using the VideoApron card system.

## Steps

1. **Create the latest release in `vector`.**
   - In the `vector` repository, create and publish the new release tag (for example, `1.10.2`).
   - Confirm the release is marked as the latest release.

2. **Create a release branch in `website`.**
   - In this repository, create a new branch named exactly after the release tag.
   - Example: if the release is `1.10.2`, create branch `1.10.2`.

3. **Run the version-sync GitHub Action.**
   - Trigger the GitHub Action used to sync versions (for example, the "Sync Versions" workflow).
   - Verify the workflow updates release metadata as expected.

4. **Open a pull request for the release branch.**
   - Create a PR from the release branch (e.g., `1.10.2`) into the target branch (typically `main`).
   - Include a short summary of the new release and any notable metadata changes.

5. **Notify Tim through VideoApron before merge.**
   - Create/update the VideoApron card to notify Tim that a new update is rolling out.
   - Ask Tim to test against the pending website release data.

6. **Merge the PR.**
   - After Tim’s confirmation/testing and normal review checks, merge the PR.
   - Confirm the website-published metadata reflects the new release.

## Quick checklist

- [ ] `vector` latest release created.
- [ ] `website` branch created with matching tag name.
- [ ] Version-sync GitHub Action run successfully.
- [ ] PR opened from release branch.
- [ ] Tim notified via VideoApron and asked to test.
- [ ] PR merged.
