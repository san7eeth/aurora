Feature: Aurora service health
  Aurora exposes a health endpoint for CI and deployment smoke checks.

  Scenario: The local API is reachable and the database is ready
    Given the Aurora API is configured
    When I request the health endpoint
    Then the health endpoint responds successfully
    And the database reports ready
