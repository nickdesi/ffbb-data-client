---
name: pypi-immutable-release-workflow
description: Workflow procedure for PyPI package releases and post-release patch handling
triggers:
  - "pypi release"
  - "publish to pypi"
  - "HTTP 400 File already exists"
  - "release tag failed"
---

# PyPI Immutable Release Workflow

## The Insight
The Python Package Index (PyPI) enforces strict immutability: once any artifact (`.whl` or `.tar.gz`) is uploaded for version `X.Y.Z`, PyPI permanently rejects any subsequent upload for the same version with HTTP 400 `File already exists`.
Never attempt to force-push an existing git tag or re-run a publish workflow on the same tag after applying a fix.

## Why This Matters
If a CI check or build step fails after a partial publish or if a linter/security issue is discovered post-release, pushing to the existing tag will fail the GitHub Actions publish job.

## Recognition Pattern
- `Publish to PyPI` workflow fails with `HTTPError: 400 Bad Request from https://upload.pypi.org/legacy/`
- "File already exists" error during twine/flit/uv publish

## The Approach
1. **Never reuse or overwrite an existing release tag**.
2. When applying any code, linter, typings, or security fix post-release:
   - Increment the patch version in `CHANGELOG.md` and `RELEASE_NOTES.md` (`2.4.0` -> `2.4.1` -> `...`).
   - Commit changes to `master` / `main`.
   - Create a brand new git annotated tag: `git tag -a vX.Y.Z+1 -m "Release vX.Y.Z+1"`.
   - Push both the branch and the new tag: `git push origin master && git push origin vX.Y.Z+1`.
   - Monitor the GitHub Actions `Publish to PyPI` and `tests` workflows until completion.
