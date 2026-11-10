@tooling
Feature: Release build
  A version number can be spent once: PyPI refuses a duplicate, so a build made
  from the wrong commit burns it for good. The release script therefore compares
  the tag with `[project].version` before it builds anything, empties `dist/` so a
  stale artifact cannot ride along, and checks both distributions with twine.

  Scenario: A tag that matches the version builds the release
    Given a package version of 1.2.3 and the tag v1.2.3
    When I build the release
    Then the distributions are built and checked

  Scenario: A tag that disagrees with the version is refused
    Given a package version of 1.2.3 and the tag v1.2.4
    When I build the release
    Then the release is refused before anything is built

  Scenario: A local run without a tag skips the guard
    Given a package version of 1.2.3 and no tag
    When I build the release
    Then the tag guard reports that it was skipped

  Scenario: A stale artifact never reaches the upload
    Given a stale artifact in the distribution directory
    When I build the release
    Then the stale artifact is gone from the distribution directory

  Scenario: A check run writes nothing
    Given a package version of 1.2.3 and the tag v1.2.3
    When I check the release tag only
    Then no distribution directory exists
