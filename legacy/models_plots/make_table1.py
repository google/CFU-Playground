from make_plots import update_results
import os
import json
from pprint import pprint
import tensorflow as tf
import numpy as np
from natsort import natsorted, ns

# RESULTS_PATH = "CNN_radio_ML"
RESULTS_PATH = "encoder_radio_ML"


def calculate_parameters(model_path: str):
    model = tf.keras.models.load_model(model_path)

    trainableParams = np.sum([np.prod(v.get_shape()) for v in model.trainable_weights])
    nonTrainableParams = np.sum([np.prod(v.get_shape()) for v in model.non_trainable_weights])
    totalParams = trainableParams + nonTrainableParams
    return totalParams


resultss = []
experiments = natsorted([f for f in os.listdir(RESULTS_PATH) if "experiment" in f]) 
for i, experiment in enumerate(experiments):
    # print(">>>>>>>>>>>>>>>>>>>>>>>")
    # print(experiment)
    results_filepath = os.path.join(RESULTS_PATH, experiment, "results.json")
    with open(results_filepath, "r") as res_file:
        results = json.load(res_file)

    model_path = os.path.join(RESULTS_PATH, experiment, "model")
    n_parameters = calculate_parameters(model_path)

    update_results(results)

    # pprint(results["model_configuration"])
    resultss.append(results)
    print(
        # f"CNN_{(i+1) % 10} & "
        f"ENC_{(i+1) % 11} & "
        f"{'%.1f' % (results['Accuracy Average'] * 100)}% & "
        f"{'%.1f' % (results['Accuracy Maximum'] * 100)}% & "
        f"{'%.1f' % (results['Accuracy snr 0+ Average'] * 100)}% & "
        f"{n_parameters//1000}K \\\\ [1ex]".replace("%", "\\%").replace("_", "\\_")
    )

for i, results in enumerate(resultss):
    print(experiments[i])
    pprint(results["model_configuration"])