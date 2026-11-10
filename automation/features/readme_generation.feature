@tooling
Feature: README generation
  The README is a generated artefact. Maintainers regenerate it from the ejs
  template through readme-md-generator, and CI fails when the committed file
  drifts from a fresh generation.

  Background:
    Given a repository with the pinned generator and a README template

  Scenario: A current README passes the freshness check
    Given the generator produces a README identical to the committed one
    When I check the README
    Then the command succeeds
    And the output reports that the README is up to date

  Scenario: A stale README fails the freshness check
    Given the generator produces a README that differs from the committed one
    When I check the README
    Then the command fails
    And the output reports that the README is out of date

  Scenario: Regenerating rewrites the README
    Given the generator produces a README that differs from the committed one
    When I regenerate the README
    Then the command succeeds
    And the README contains the generated content

  Scenario: The banner is rendered into the template marker
    Given a template that marks where the banner belongs
    When I regenerate the README
    Then the README carries the rendered wordmark

  Scenario: Output without the generator attribution is rejected
    Given the generator produces a README without the attribution footer
    When I regenerate the README
    Then the command fails

  Scenario: A missing template is reported as a usage error
    Given the README template does not exist
    When I regenerate the README
    Then the command fails with a usage error

  Scenario: A failing generator is reported without touching the README
    Given the generator exits with a failure
    When I regenerate the README
    Then the command fails
    And the README is unchanged
