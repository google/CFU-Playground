import matlab
from matlab import engine
import numpy as np
import random


def generate_data(eng, SNR=30, max_offset=5, fc=902e6, fs=200e3, seed=123456):
    eng.rng(seed)

    # Random bits
    d = eng.randi(matlab.int64([0, 3]), 1024, 1)

    # PAM4 modulation
    syms = eng.pammod(d, 4.0)

    # Square-root raised cosine filter
    filterCoeffs = eng.rcosdesign(0.35, 4.0, 8.0)
    tx = eng.filter(filterCoeffs, 1, eng.upsample(syms, 8))

    # Channel
    multipathChannel = eng.comm.RicianChannel(
        "SampleRate",
        fs,
        "PathDelays",
        matlab.double([0.0, 1.8 / 200e3, 3.4 / 200e3]),
        "AveragePathGains",
        matlab.double([0, -2, -10]),
        "KFactor",
        4.0,
        "MaximumDopplerShift",
        4.0,
    )

    # % Apply an independent multipath channel
    eng.workspace["multipathChannel"] = multipathChannel
    eng.workspace["tx"] = tx
    # eng.eval("reset(multipathChannel)")
    # outMultipathChan = multipathChannel(tx)
    outMultipathChan = eng.eval("multipathChannel(tx)")
    eng.workspace["outMultipathChan"] = outMultipathChan

    # Determine clock offset factor
    clockOffset = (eng.rand() * 2 * max_offset) - max_offset
    C = 1 + clockOffset / 1e6

    # Add frequency offset
    frequencyShifter = eng.comm.PhaseFrequencyOffset(
        "SampleRate", fs, "FrequencyOffset", -(C - 1) * fc
    )
    eng.workspace["frequencyShifter"] = frequencyShifter
    # frequencyShifter.FrequencyOffset = -(C-1)*fc
    outFreqShifter = eng.eval("frequencyShifter(outMultipathChan)")
    # outFreqShifter = frequencyShifter(outMultipathChan)

    # Add sampling time drift
    # t = (0:length(tx)-1) / fs;
    t = np.arange(len(tx)) / fs
    newFs = fs * C
    # tp = (0:length(tx)-1)' / newFs;
    tp = np.arange(len(tx)) / newFs
    outTimeDrift = eng.interp1(t, outFreqShifter, tp)

    # Add noise
    rx = eng.awgn(outTimeDrift, float(SNR), 0.0)
    return rx


if __name__ == "__main__":
    eng = engine.start_matlab()
    eng.cd(r"matlab", nargout=0)

    data = generate_data(eng)
    print(data)

    # eng.helperModClassGetNNFrames([1, 2, 3])
