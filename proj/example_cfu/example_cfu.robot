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
    Write Line To Uart       2
    Wait For Prompt On Uart  functional>
    Write Line To Uart       f
    Wait For Line On Uart    0x00040818, 0x0004f7e7: 0x00000206, 0x18080400, 0x18102000
    Wait For Line On Uart    0x0004891b, 0x000476e4: 0x00000206, 0x1b890400, 0xd8912000
    Wait For Prompt On Uart  functional>
    Write Line To Uart       c
    Wait For Line On Uart    Ran 481474 comparisons.
    Wait For Prompt On Uart  functional>
