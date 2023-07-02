import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict
import seaborn as sn


def metric_evaluation(
    model,
    data: np.ndarray,
    labels: np.ndarray,
    modulations: List[str],
    verbose=True,
    metric=accuracy_score,
) -> Tuple[np.ndarray, Dict[str, float]]:
    """
    Evaluates model with given metric

    Returns:
        Tuple[np.ndarray, Dict[str, float]]: confusions matrix and dict with modulation -> accuracy
    """
    preds = model.predict(data)
    pred_labels = np.argmax(preds, axis=1)

    cls_to_acc = {"Overall": metric(labels, pred_labels)}

    verbose and print(f"Overall test accuracy: {cls_to_acc}")

    for ci, cl in enumerate(modulations):
        class_indecies = np.where(labels == ci)[0]
        cur_true_labels = labels[class_indecies]
        cur_pred_labels = pred_labels[class_indecies]
        cls_to_acc[cl] = accuracy_score(cur_true_labels, cur_pred_labels)
        verbose and print(f"{cl} test accuracy: {cls_to_acc[cl]}")

    cm = confusion_matrix(y_true=labels, y_pred=pred_labels)
    verbose and print(f"Confusion matrix:\n{cm}")
    df_cm = pd.DataFrame(cm, index=modulations, columns=modulations)
    if verbose:
        plt.figure(figsize=(10, 7))
        sn.heatmap(df_cm, annot=True)
        plt.show()
    return cm, cls_to_acc


def snr_to_metric_evaluation(
    model,
    data: np.ndarray,
    labels: np.ndarray,
    snrs: np.ndarray,
    verbose=True,
    metric=accuracy_score,
) -> Dict[float, float]:
    """
    Evaluates model on different snrs

    Returns:
        Dict[str]: Dict snr -> accuracy
    """
    snr_to_acc = {}
    # for snr in range(min(snrs), max(snrs) + 2, 2):
    for snr in sorted(np.unique(snrs)):
        cur_indecies = np.where(snrs == snr)[0]
        cur_data = data[cur_indecies]
        cur_labels = labels[cur_indecies]
        cur_pred = model.predict(cur_data, verbose=0)

        cur_pred_labels = np.argmax(cur_pred, axis=1)
        acc = metric(cur_labels, cur_pred_labels)
        verbose and print(f"SNR: {snr} -- Overall test accuracy: {acc}")
        snr_to_acc[float(snr)] = float(acc)
    return snr_to_acc
