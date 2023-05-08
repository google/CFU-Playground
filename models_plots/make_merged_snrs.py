import json
import matplotlib.pyplot as plt
import os
import matplotlib
import numpy as np

from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes 
from mpl_toolkits.axes_grid1.inset_locator import mark_inset
matplotlib.use("pgf")
matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    'font.family': 'serif',
    'text.usetex': True,
    'pgf.rcfonts': False,
})


experiments = [
    "CNN_radio_ML/experiment_0/",
    "CNN_radio_ML/experiment_8/",
    "encoder_radio_ML/experiment_2/",
    "encoder_radio_ML/experiment_8/",
]

labels = [
    "CNN_1:radioML_2016.10a",
    "CNN_9:radioML_2016.10a",
    "ENC_3:radioML_2016.10a",
    "ENC_9:radioML_2016.10a",
]

# fig = plt.figure(figsize=(20,20))
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

snr_to_accs = []
for i, experiment in enumerate(experiments):
    result_filepath = os.path.join(experiment, "results.json")
    with open(result_filepath, 'r') as result_filepath:
        results = json.load(result_filepath)   
    snr_to_acc = results["snr_to_acc_test"]
    snr_to_accs.append(snr_to_acc)


    ax.plot(list(snr_to_acc.keys()), list(snr_to_acc.values()), label=labels[i])
plt.ylim([0, 1])
ax.set_xlabel("SNR")
ax.set_ylabel("Accuracy")
ax.legend()
ax.grid()
plt.setp(ax.get_xticklabels()[::2], visible=False)
plt.yticks(np.arange(0, 1, 0.1).tolist() )

# x1, x2 = -2, 12
x1, x2 = 7, 13
y1, y2 = 0.65, 0.95

axins = zoomed_inset_axes(ax, 1.7, loc=4) # zoom = 2
for snr_to_acc in snr_to_accs:
    axins.plot(list(snr_to_acc.keys()), list(snr_to_acc.values()))

axins.set_xlim(x1, x2)
axins.set_ylim(y1, y2)
plt.xticks(visible=False)
plt.yticks(visible=False)
mark_inset(ax, axins, loc1=3, loc2=1, fc="0.9", ec="0.5")


plt.draw()

# plt.show()
plt.savefig("snr_to_acc_top_4.pdf")

