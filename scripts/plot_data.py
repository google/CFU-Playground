import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("pgf")
matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    'font.family': 'serif',
    'text.usetex': True,
    'pgf.rcfonts': False,
})

snr_to_acc = {
    -20: 0.09226713532513181,
    -18: 0.09279279279279279,
    -16: 0.09366130558183539,
    -14: 0.1417979610750695,
    -12: 0.18673647469458987,
    -10: 0.2810516772438803,
    -8: 0.41843971631205673,
    -6: 0.492151431209603,
    -4: 0.6538821328344246,
    -2: 0.7926391382405745,
    0: 0.8435185185185186,
    2: 0.8739800543970988,
    4: 0.8887867647058824,
    6: 0.8891891891891892,
    8: 0.8955895589558955,
    10: 0.8927000879507476,
    12: 0.9014869888475836,
    14: 0.8969917958067457,
    16: 0.9024163568773235,
    18: 0.8931506849315068,
}

y = list(snr_to_acc.values())
x = list(snr_to_acc.keys())
default_x_ticks = range(len(x))

plt.plot(x, y)
# plt.xticks(default_x_ticks, x)

plt.ylabel("Accuracy")
plt.xlabel("SNR")

# plt.show()
plt.savefig("snr_example.pgf")