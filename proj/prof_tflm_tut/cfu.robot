*** Settings ***
Library                       Process
Suite Setup                   Setup
Suite Teardown                Teardown
Test Setup                    Reset Emulation
Test Teardown                 Test Teardown
Resource                      ${RENODEKEYWORDS}


*** Variables ***
${USER_INPUT}                  1 2 3
${PLATFORM}                    platform.repl
${BINARY}                      binary.elf
${UART}                        sysbus.uart


*** Keyword ***
Create Machine
    Execute Command    mach create
    Execute Command    machine LoadPlatformDescription    ${PLATFORM}
    Execute Command    sysbus LoadELF                     ${BINARY}
    Execute Command    Create Terminal Tester             ${UART}
    

Wait For CPU Prompt
    Wait For Line On Uart      ====
    Wait For Prompt            >
    

*** Test Cases ***
Run Test
    @{choices}=    Split String    ${USER_INPUT}

    Create Machine
    Start Simulation

    Wait For Line On Uart         CFU Playground
    
    FOR  ${choice}  IN  @{choices}
        Wait For CFU Prompt
        Write To Uart            ${choice}
    END

    Wait For CFU Prompt
