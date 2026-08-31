# Release process for `kaleido` package

1. Create release branch titled `release-vX.Y.Z`
  - We try to follow [semantic versioning guidelines](https://semver.org) as much as possible
2. Update the changelog:
    - Review the items in `CHANGELOG.md` under the "Unreleased" header
    - Ensure all items follow this format: 
        - `- Description of change [[#XXXX](https://github.com/plotly/Kaleido/pull/XXXX)]`
      - ...followed by `with thanks to @username for the contribution!` if the PR is from a community contributor
    - Add any missing items (PRs which were merged since the last release)
      - PRs which don't change the contents of the built package (e.g. changes to the README, etc.) and minor dependency upgrades don't need to be mentioned
    - Add a header `## vX.Y.Z` above the unreleased items, under `## Unreleased`
    - Commit and push the `CHANGELOG.md` updates
      - Note: In most cases, no other files need to be updated for the release. This is because the build process determines the package version from git tags, so the version number itself doesn't need to be updated anywhere besides the changelog.
5. Open a PR into `main`, wait for tests to pass, get approval, and then merge into `main`
6. On your local machine, tag the release branch merge commit with the version number:

        git checkout main
        git pull
        git tag vX.Y.Z
        git push origin vX.Y.Z

5. Build the release artifacts:
    - Ensure your git environment inside the `Kaleido/` directory is totally clean, i.e. `git status` returns the following:

            On branch main
            Your branch is up to date with 'origin/main'.

            nothing to commit, working tree clean

    - If needed, stash or delete/move files to get to a clean environment. This is important because `setuptools-git-versioning` will not generate the correct version number if you have untracked or changed files presesnt.
    - Build the package:

            cd src/py/
            python -m build
    
    - Two artifacts will be added to `src/py/dist`. Ensure that they have the correct filenames:
      - `kaleido-X.Y.Z-py3-none-any.whl`
      - `kaleido-X.Y.Z.tar.gz`
7. Release on GitHub:
    - Go to https://github.com/plotly/Kaleido/releases and click "Draft a new release"
    - Select the `vX.Y.Z` tag you created previously
    - Copy and paste the relevant changelog section into the release notes
    - Upload the `.whl` and `.tar.gz` build artifacts
8. Release on PyPI:
    - Install the `twine` Python package if not already installed (`pip install twine`)
    - `cd` into the `dist/` directory
    - Use `twine` to upload the artifacts to PyPI:

            twine upload `kaleido-X.Y.Z*`
    - You will need to enter an API token proving you have permission to publish

