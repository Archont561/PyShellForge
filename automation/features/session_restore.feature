@tooling
Feature: Session restore
  A fresh checkout or a short-lived sandbox has the source but neither Pixi nor a
  solved environment. `python -m automation.restore` is the command that gets it to a
  working repository, and it reports what it skipped instead of pretending.

  Scenario: A missing Pixi installation is installed before the environment is solved
    Given a repository without Pixi
    When I restore the session
    Then Pixi is installed from the official installer
    And the environment is solved with the lock file

  Scenario: An existing Pixi installation is reused
    Given a repository with Pixi on the PATH
    When I restore the session
    Then the installer is not run
    And the environment is solved with the lock file

  Scenario: Git hooks are installed in a checkout
    Given a repository with Pixi on the PATH inside a git checkout
    When I restore the session
    Then the Lefthook hooks are installed

  Scenario: Git hooks are skipped outside a checkout
    Given a repository with Pixi on the PATH and no git checkout
    When I restore the session
    Then the hooks are reported as skipped

  Scenario: An unsolvable environment is reported
    Given a repository whose environment cannot be solved
    When I restore the session
    Then the session restore reports a failure
