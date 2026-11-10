@tooling
Feature: Issue forms
  Bug reports are only useful when they carry the version, the interpreter, the
  target shell and the reproduction. GitHub Issue Forms ask for those fields, and
  the validator keeps the YAML honest offline, because a form with a mistyped
  element type fails silently on GitHub. Rendering the form in a browser is a
  manual step: `gh form preview`, which needs the GitHub CLI.

  Scenario: A well-formed form passes
    Given an issue form with a name, a description and a body
    When I validate the issue forms
    Then the issue forms are valid

  Scenario: A form without a description is reported
    Given an issue form without a description
    When I validate the issue forms
    Then form validation reports PSF-FORM-004

  Scenario: An unknown element type is reported
    Given an issue form with an element type of slider
    When I validate the issue forms
    Then form validation reports PSF-FORM-007

  Scenario: A dropdown without options is reported
    Given an issue form with a dropdown that has no options
    When I validate the issue forms
    Then form validation reports PSF-FORM-011

  Scenario: Two elements that share an id are reported
    Given an issue form with two elements that share an id
    When I validate the issue forms
    Then form validation reports PSF-FORM-008

  Scenario: A required checkbox that is not a boolean is reported
    Given an issue form with a checkbox whose required flag is not a boolean
    When I validate the issue forms
    Then form validation reports PSF-FORM-012

  Scenario: A config file that points outside the repository is reported
    Given a config file with a relative contact link
    When I validate the issue forms
    Then form validation reports PSF-FORM-015
