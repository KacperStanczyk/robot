*** Settings ***
Documentation     Sample test demonstrating Validation Framework keywords.
Library           validation_framework.keywords

*** Test Cases ***
Activate Wipers
    [Documentation]    Ensure the wipers activate when requested.
    PRECOND.Ensure Standby
    WIPERS.Set Mode =    AUTO
    WIPERS.Spray
    VERIFY.Wipers State ==    ACTIVE
    CAPTURE.Start    BodyCAN
    CAPTURE.Stop     BodyCAN
