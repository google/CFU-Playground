from migen import Module, Signal, Record, FSM, NextState, If

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
    """
    A module that controls clocks between CFU and CPU so that power usage is
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
