@tooling
Feature: Documentation validation
  Documentation is a product surface, so the repository checks it. The docs
  validator enforces the required sections, the navigation index, internal links
  and anchors before Markdown, prose and link linters run in CI. The required
  sections are `docs/concepts/`, `docs/guides/`, `docs/reference/` and
  `docs/development/`, and the validator reads that list from its own
  configuration.

  Background:
    Given a documentation tree with every required section

  Scenario: A well-formed documentation tree passes
    Given the documentation tree is complete
    When I validate the documentation
    Then the documentation is valid

  Scenario: A page that is missing from the index is reported
    Given a page that the index does not link to
    When I validate the documentation
    Then validation reports PSF-DOC-003

  Scenario: A broken relative link is reported
    Given a page that links to a file that does not exist
    When I validate the documentation
    Then validation reports PSF-DOC-004

  Scenario: A link to a missing anchor is reported
    Given a page that links to an anchor that does not exist
    When I validate the documentation
    Then validation reports PSF-DOC-005

  Scenario: A missing required section is reported
    Given the development section is removed
    When I validate the documentation
    Then validation reports PSF-DOC-001

  Scenario: A fenced code block without a language is reported
    Given a page with a fenced code block without a language
    When I validate the documentation
    Then validation reports PSF-DOC-006

  Scenario: An unclosed fenced code block is reported
    Given a page with an unclosed fenced code block
    When I validate the documentation
    Then validation reports PSF-DOC-009
