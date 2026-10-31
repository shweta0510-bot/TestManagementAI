# Pending pipeline feature for the Zara platform.
# End-to-end creation is tagged @end-to-end and runs only when the Zara
# pipeline repository has no pipeline left in Pending Setup.
# While one exists, finish setup on that pipeline in Zara.

Feature: Pending pipeline on the Zara platform

  @reuse-pending
  Scenario: Reuse a pipeline that is already pending setup
    Given the Zara pipeline repository has a pipeline pending setup
    When the pending feature runs
    Then pipeline creation does not run end to end
    And the existing pending pipeline is kept for setup in Zara

  @end-to-end @seed-pipeline
  Scenario: Create a pipeline when none are pending setup
    Given the Zara pipeline repository has no pipeline pending setup
    When the pending feature runs
    Then pipeline creation runs end to end
    And the Zara pipeline repository has one pipeline pending setup
