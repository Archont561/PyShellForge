@product
Feature: Render a Bash script
  A script is a sequence of shell-neutral nodes. The Bash renderer quotes literal
  values and expands only variables declared earlier in the script.

  Scenario: Render and run a greeting
    Given a script that assigns a greeting name
    When the script is rendered as Bash
    Then the generated Bash matches the greeting golden file
    And the generated Bash prints the greeting
