@tooling
Feature: Clean Code linting
  The CC rules of rude-clean-code cap the size, the parameter count, the scope, the
  nesting, the operand count, the branch count and the class size of the code.
  `python -m automation.clean_code` runs them over both distributions and the
  repository automation, and fails the build when one of them reports. The rules
  are warnings to rude, which exits 0 when it reports only warnings, so the exit
  status is this module's own.

  Scenario: A clean tree passes the gate
    Given the linter answers with no findings
    When I run the clean code gate
    Then the gate succeeds
    And the output reports the trees are clean

  Scenario: A finding fails the gate
    Given the linter reports a function with too many parameters
    When I run the clean code gate
    Then the gate fails
    And the output names the rule that reported

  Scenario: A broken linter fails the gate
    Given the linter cannot be started
    When I run the clean code gate
    Then the gate fails with a tool error
    And the output explains that the linter failed

  Scenario: JSON output carries the findings
    Given the linter reports a function with too many parameters
    When I run the clean code gate with JSON output
    Then the gate fails
    And the output is a list of findings
