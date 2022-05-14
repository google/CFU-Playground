*** Settings ***
Library                       Process
Suite Setup                   Setup
Suite Teardown                Teardown
Test Setup                    Reset Emulation
Test Teardown                 Test Teardown
Resource                      ${RENODEKEYWORDS}


*** Variables ***
${USER_INPUT}                 1 2 3
${SCRIPT}                     script.resc
${UART}                       sysbus.uart


*** Keyword ***
Create Machine
    Execute Command           include @${SCRIPT}
    Create Terminal Tester    ${UART}
    

Wait For CFU Prompt
    Wait For Line On Uart      ====
    Wait For Prompt On Uart    >
    

*** Test Cases ***
Run Test
    @{choices}=    Split String    ${USER_INPUT}

    Create Machine
    Start Emulation

    Wait For Line On Uart         CFU Playground
    
    FOR  ${choice}  IN  @{choices}
        Wait For CFU Prompt
        Write To Uart            ${choice}
    END

    Wait For CFU Prompt