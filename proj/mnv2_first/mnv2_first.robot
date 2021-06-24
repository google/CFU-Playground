*** Settings ***
Suite Setup                   Setup
Suite Teardown                Teardown
Test Setup                    Reset Emulation
Test Teardown                 Test Teardown
Resource                      ${RENODEKEYWORDS}

*** Keywords ***
Create Machine
    Execute Command          include @${CURDIR}/TARGET.resc
    Create Terminal Tester   sysbus.uart

    Start Emulation

*** Test Cases ***
Should Run Mobile Net V2 Golden Tests
    Create Machine

    Wait For Line On Uart    CFU Playground
    Wait For Prompt On Uart  main>
    Write Line To Uart       1
    Wait For Prompt On Uart  models>
    Write Line To Uart       2
    Wait For Prompt On Uart  mnv2>
    Write Line To Uart       g
    Wait For Line On Uart    Golden tests passed  120
    Wait For Prompt On Uart  mnv2>


Should Run TFLite Unit Tests
    Create Machine

    Write Line To Uart       5
    Wait For Line On Uart    CONV TEST:
    Wait For Line On Uart    ~~~ALL TESTS PASSED~~~
    Wait For Line On Uart    DEPTHWISE_CONV TEST:
    Wait For Line On Uart    ~~~ALL TESTS PASSED~~~
    Wait For Prompt On Uart  main>


Should Run 1x1 Conv2D Golden Tests
    Create Machine

    Write Line To Uart       3
    Wait For Prompt On Uart  mnv2_first>
    Write Line To Uart       1
    Wait For Line On Uart    OK - output tensor matches
    Wait For Prompt On Uart  mnv2_first>
