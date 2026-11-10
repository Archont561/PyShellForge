@tooling
Feature: Automation CLI
  Repository automation is registered in `dodo.py` and driven by doit through
  `pixi run automation <task>`. The registry is the only place that knows what
  exists and what the gate is, so adding a task means touching one file and
  nothing else. The modules under `automation/` stay ordinary Python, which is
  what lets doit import the registry without running any automation.

  Scenario: Every gate is a registered task
    Given the task registry
    When I read every task
    Then every task name is kebab-case
    And the check task depends on every gate in the graph

  Scenario: The aggregate task only wires dependencies
    Given the task registry
    When I read every task
    Then the check task declares no actions of its own

  Scenario: A module that succeeds passes its task
    Given a module whose entry point returns zero
    When the registry adapter runs it
    Then the task succeeds

  Scenario: A module that reports a failure stops the task
    Given a module whose entry point returns a failure status
    When the registry adapter runs it
    Then the task fails with a message naming the status

  Scenario: Importing the registry runs nothing
    Given a module whose entry point raises when called
    When the registry is imported
    Then the import completes without running anything

  Scenario: The parameterised tasks declare their parameters
    Given the task registry
    When I read every task
    Then the release-build task offers a ref and a tag-check switch
    And the detect-changes task offers a base, a head and an event
