import matplotlib.pyplot as plt
from typing import Dict, Optional, List, Tuple


def plot_train(
    history: Dict,
    plot_keys: Optional[List[Tuple[str, ...]]] = None,
    plot_titles: Optional[List[str]] = None,
    plot_labels: Optional[List[Tuple[str, ...]]] = None,
):
    if plot_keys is None:
        plot_keys = [("accuracy", "val_accuracy"), ("loss", "val_loss")]
        plot_titles = ["Training and Validation Accuracy", "Training and Validation Loss"]
        plot_labels = [
            ("Training Accuracy", "Validation Accuracy"),
            ("Training Loss", "Validation Loss"),
        ]
    n_epochs = len(history[plot_keys[0][0]])
    n_plots = len(plot_keys)
    epochs_range = range(n_epochs)
    
    fig, axs = plt.subplots(n_plots)
    fig.set_size_inches(8, 8, forward=True)
    for i in range(n_plots):
        for j, subkey in enumerate(plot_keys[i]):
            axs[i].plot(epochs_range, history[subkey], label=plot_labels[i][j])
        axs[i].legend(loc="best")
        axs[i].set_title(plot_titles[i])


    plt.show()


def plot_snr_to_acc(snr_to_acc: Dict[int, float]):
    xs = sorted(list(snr_to_acc.keys()))
    ys = list(snr_to_acc.values())
    ys = sorted(ys, key=lambda y: xs[ys.index(y)])
    plt.plot(xs, ys)
    plt.title("SNR to accuracy plot")
    plt.ylabel("Accuracy")
    plt.xlabel("Signal-to-Noise")
    plt.show()
    
    