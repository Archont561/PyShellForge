@tooling
Feature: Gherkin linting
  Scenarios describe user-visible behaviour and bind to pytest-bdd step
  definitions. The feature linter keeps scenarios well-formed and keeps the
  feature files and the step definitions in sync.

  Background:
    Given a feature file describing a shell rendering behaviour

  Scenario: A bound scenario passes
    Given a step definition for every step in the feature file
    When I lint the features
    Then linting is clean

  Scenario: An undefined step is reported
    Given no step definitions
    When I lint the features
    Then linting reports PSF-FEAT-006

  Scenario: An unused step definition is reported
    Given a step definition that no scenario uses
    When I lint the features
    Then linting reports PSF-FEAT-007

  Scenario: Steps in the wrong order are reported
    Given a scenario whose Given step follows its When step
    When I lint the features
    Then linting reports PSF-FEAT-005

  Scenario: A feature file without scenarios is reported
    Given a feature file with a Feature statement but no scenarios
    When I lint the features
    Then linting reports PSF-FEAT-002
