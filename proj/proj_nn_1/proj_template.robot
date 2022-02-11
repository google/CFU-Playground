*** Settings ***
Suite Setup                   Setup
Suite Teardown                Teardown
Test Setup                    Reset Emulation
Test Teardown                 Test Teardown
Resource                      ${RENODEKEYWORDS}

*** Test Cases ***
Should Walk The Menu
    Execute Command          include @${CURDIR}/TARGET.resc
    Create Terminal Tester   sysbus.uart

    Start Emulation

    Wait For Line On Uart    CFU Playground
    Wait For Prompt On Uart  main>
    Write Line To Uart       3
    Wait For Line On Uart    Project Menu
    Write Line To Uart       h
    Wait For Line On Uart    Hello, World!
