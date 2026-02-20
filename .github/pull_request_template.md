## Summary

- Describe the change.

## Testing

- List commands/checks run for this PR.

---

## Release checklist (for website release PRs)

Use this checklist when publishing a new release from `vector` to this `website` repo.

- [ ] A new release tag has been created and published as **Latest** in `vector` (example: `1.10.2`).
- [ ] A branch exists in this repository named exactly after that release tag (example: `1.10.2`).
- [ ] The **Sync Releases** GitHub Action has been run successfully for this release.
- [ ] This PR is opened from the release-tag branch into the target branch (typically `main`).
- [ ] Tim has been notified in the VideoApron card workflow that we plan to push this update and should test it.
- [ ] After reviews/checks and Tim's testing confirmation, this PR is merged.
