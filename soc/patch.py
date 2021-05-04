from migen import Module


class Patch(Module):
    """Patches one pin through to another
    """

    def __init__(self, input_pin, output_pin):
        self.comb += output_pin.eq(input_pin)
