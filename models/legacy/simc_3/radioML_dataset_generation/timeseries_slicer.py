import numpy as np
import analyze_stats
import matplotlib.pyplot as plt

def slice_timeseries(x, l=128, d=64, max_k = None):
    k = (len(x) - l + 1) / d
    if not max_k == None:
        k = min(k, max_k)
    X = np.zeros([k,2,l], dtype=np.float32)
    for i in range(0,k):
        # Rect Window
        w = np.ones([l])
        # Sin Window
        #w = np.sin(np.arange(0,np.pi,np.pi/l))
        x_i =      x[i*d:i*d+l] * w
        X[i,0,:] = np.real(x_i)
        X[i,1,:] = np.imag(x_i)
        energy = analyze_stats.calc_vec_energy(X[i])
        X[i,0,:] /= energy
        X[i,1,:] /= energy
    return X

def slice_timeseries_dict(td, l=128, d=64, max_k = None):
    nd = {}
    for k,v in td.iteritems():
        nd[k] = slice_timeseries(v,l,d,max_k)
    return nd

def slice_timeseries_real(x, l=128, d=64, max_k = None):
    k = (len(x) - l + 1) / d
    if not max_k == None:
        k = max(k, max_k)
    X = np.zeros([k,1,l], dtype=np.float32)
    for i in range(0,k):
        x_i =      x[i*d:i*d+l]
        X[i,0,:] = x_i
    return X


def slice_timeseries_real_dict(td, l=128, d=64, max_k = None):
    nd = {}
    for k,v in td.iteritems():
        nd[k] = slice_timeseries_real(v,l,d,max_k)
    return nd
