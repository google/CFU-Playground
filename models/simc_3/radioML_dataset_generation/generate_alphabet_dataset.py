#!/usr/bin/env python
from transmitters import transmitters
from source_alphabet import source_alphabet
import timeseries_slicer
from gnuradio import channels, gr, blocks
#import matplotlib.pyplot as plt
import numpy as np
import numpy.fft, cPickle, gzip


apply_channel = True

output = {}
#snr_vals = [-10,-8,-6,-4,-2,0,2,4,6,8,10,12,14,16,18,20]
blks={"continuous":{ "size":gr.sizeof_float,
                     "sink":blocks.vector_sink_f },
      "discrete"  :{ "size":gr.sizeof_char,
                     "sink":blocks.vector_sink_b }}
for alphabet_type in transmitters.keys():
    


    print "running test", alphabet_type
    tx_len = int(1000e3)
    src = source_alphabet(alphabet_type, tx_len, True)
    head = blocks.head(blks[alphabet_type]["size"], tx_len)
    snk = blks[alphabet_type]["sink"]()
    tb = gr.top_block()
    tb.connect(src,head,snk)
    tb.run()
    print "finished: ", len(snk.data())
    output[alphabet_type] = np.array(snk.data(), dtype=np.float32)

print output
X = timeseries_slicer.slice_timeseries_real_dict(output, 128, 64, 1000)
cPickle.dump( X, file("alphabet_dict.dat", "wb" ) )

