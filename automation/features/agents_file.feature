@tooling
Feature: AGENTS.md generation and maintenance
  AGENTS.md is generated and maintained with the agents-md CLI. The CLI refreshes
  only the sections wrapped in its HTML-comment markers and preserves everything
  outside them, so the repository validates that contract before the file can rot:
  every generated section stays present, in order, headed as the CLI expects, and
  free of the unfinished stubs a fresh scan leaves behind.

  Scenario: A curated AGENTS.md passes the contract check
    Given an AGENTS.md that carries every generated section
    When I check the agent instructions
    Then the agent instructions are valid

  Scenario: A section that lost its markers is reported
    Given an AGENTS.md where the commands section lost its markers
    When I check the agent instructions
    Then the agent instructions report PSF-AGENT-002

  Scenario: A section left as an unfinished stub is reported
    Given an AGENTS.md with an unfinished agents-md stub
    When I check the agent instructions
    Then the agent instructions report PSF-AGENT-005

  Scenario: A stale sidecar file is reported
    Given an AGENTS.generated.md sidecar next to AGENTS.md
    When I check the agent instructions
    Then the agent instructions report PSF-AGENT-006

  Scenario: Creating the skeleton is refused once markers exist
    Given an AGENTS.md that carries every generated section
    When I bootstrap the agent instructions
    Then the bootstrap is refused without running the generator
