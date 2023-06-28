#!/usr/bin/env python
from gnuradio import gr, blocks
import mediatools
import numpy as np

class source_alphabet(gr.hier_block2):
    def __init__(self, dtype="discrete", limit=10000, randomize=False):
        if(dtype == "discrete"):
            gr.hier_block2.__init__(self, "source_alphabet",
                gr.io_signature(0,0,0),
                gr.io_signature(1,1,gr.sizeof_char))

            self.src = blocks.file_source(gr.sizeof_char, "source_material/gutenberg_shakespeare.txt")
            self.convert = blocks.packed_to_unpacked_bb(1, gr.GR_LSB_FIRST);
            #self.convert = blocks.packed_to_unpacked_bb(8, gr.GR_LSB_FIRST);
            self.limit = blocks.head(gr.sizeof_char, limit)
            self.connect(self.src,self.convert)
            last = self.convert

            # whiten our sequence with a random block scrambler (optionally)
            if(randomize):
                rand_len = 256
                rand_bits = np.random.randint(2, size=rand_len)
                self.randsrc = blocks.vector_source_b(rand_bits, True)
                self.xor = blocks.xor_bb()
                self.connect(self.randsrc,(self.xor,1))
                self.connect(last, self.xor)
                last = self.xor

        else:   # "type_continuous"
            gr.hier_block2.__init__(self, "source_alphabet",
                gr.io_signature(0,0,0),
                gr.io_signature(1,1,gr.sizeof_float))

            self.src = mediatools.audiosource_s(["source_material/serial-s01-e01.mp3"])
            self.convert2 = blocks.interleaved_short_to_complex()
            self.convert3 = blocks.multiply_const_cc(1.0/65535)
            self.convert = blocks.complex_to_float()
            self.limit = blocks.head(gr.sizeof_float, limit)
            self.connect(self.src,self.convert2,self.convert3, self.convert)
            last = self.convert

        # connect head or not, and connect to output
        if(limit==None):
            self.connect(last, self)
        else:
            self.connect(last, self.limit, self)


if __name__ == "__main__":
    print "QA..."

    # Test discrete source
    tb = gr.top_block()
    src = source_alphabet("discrete", 1000)
    snk = blocks.vector_sink_b()
    tb.run()

    # Test continuous source
    tb = gr.top_block()
    src = source_alphabet("continuous", 1000)
    snk = blocks.vector_sink_f()
    tb.run()
