*** Settings ***
Documentation     Sample test demonstrating Validation Framework keywords.
Library           validation_framework.keywords

*** Test Cases ***
Activate Wipers
    [Documentation]    Ensure the wipers activate when requested.
    Set Vehicle State    VehicleAtRest
    Activate Wipers     INTERMITTENT
