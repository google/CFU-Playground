from migen import Module, Signal, Record, FSM, NextState, NextValue, If

# CFU:CPU bus layout but just handshake signals
cfu_bus_minimized_layout = [
    ("cmd", [
        ("valid", 1),
        ("ready", 1),
    ]),
    ("rsp", [
        ("valid", 1),
        ("ready", 1),
    ]),
]

class CfuCpuClockCtrl(Module):
    """A module that controls clocks between CFU and CPU so that power usage is
    optimized.

    Attributes
    ----------

    cfu_bus: Record(cfu_bus_layout), in
        Bus connecting CFU and CPU.

    cfu_cen: Signal(1), out
        Clock enable signal for CFU.

    cpu_cen: Signal(1), out
        Clock enable signal for CPU.
    """

    def __init__(self):
        self.cfu_bus = Record(cfu_bus_minimized_layout)
        self.cfu_cen = Signal()
        self.cpu_cen = Signal()

        self.submodules.fsm = fsm = FSM(reset_state="CPU_ENABLED")

        fsm.act("CPU_ENABLED",
            self.cpu_cen.eq(1),
            self.cfu_cen.eq(0),

            # If CPU has prepared a command, enable CFU
            If(self.cfu_bus.cmd.valid,
                self.cfu_cen.eq(1),
                NextState("CFU_ENABLED"),
            )
        )

        fsm.act("CFU_ENABLED",
            self.cfu_cen.eq(1),
            self.cpu_cen.eq(1),

            # Disable CPU if CFU is calculating response
            If(~self.cfu_bus.rsp.valid & ~self.cfu_bus.cmd.valid,
                self.cpu_cen.eq(0),

                # Enable CPU and disable CFU if CPU received a response and has no next command
                If(self.cfu_bus.cmd.ready,
                    self.cpu_cen.eq(1),
                    NextState("CPU_ENABLED"),
                )
            )
        )

class StartStopEnableCtl(Module):
    """This module takes two input signals and returns an enable output signal
    based on them.

    Output signal `enable` is asserted between each `start` and `stop` signal.
    Additionaly it may stay asserted for `stop_cycles` number of cycles after
    asserting `stop` signal. It will not catch `start` signal during additional
    cycles if it occurs.

    Parameters
    ----------

    stop_cycles: int, optional
        A number of cycles that clock should stay enabled after receiving stop signal.

    Attributes
    ----------

    start: Signal(1), in
        Start signal, asserted when clock should be enabled.

    stop: Signal(1), in
        Stop signal, asserted when clock should be disabled.

    enable: Signal(1), out
        Enable signal, asserted from (`start`) to (`stop` + `stop_cycles`).
    """

    def __init__(self, stop_cycles=0):
        self.start  = start  = Signal()
        self.stop   = stop   = Signal()
        self.enable = enable = Signal()

        self.submodules.fsm = fsm = FSM(reset_state="WAIT_FOR_START")

        fsm.act("WAIT_FOR_START",
            enable.eq(0),
            If(start,
                enable.eq(1),
                NextState("WAIT_FOR_STOP")
            )
        )

        if stop_cycles > 0:
            delay = Signal(max=stop_cycles+1)

            fsm.act("WAIT_FOR_STOP",
                enable.eq(1),
                If(stop,
                    delay.eq(1),
                    NextState("DELAY_STOP")
                ),
            )

            fsm.act("DELAY_STOP",
                enable.eq(1),
                NextValue(delay, delay + 1),
                If(delay == stop_cycles,
                    enable.eq(0),
                    NextState("WAIT_FOR_START")
                )
            )
        else:
            fsm.act("WAIT_FOR_STOP",
                enable.eq(1),
                If(stop,
                    enable.eq(0),
                    NextState("WAIT_FOR_START")
                ),
            )
