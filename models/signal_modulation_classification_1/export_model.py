from trainedNet1 import load_model, classes
from data import saven_pam4_data
from data import load_test_data
import numpy as np
import random
from tqdm import tqdm


def test_model(model, data):
    print("[debug] Stat model test")
    n_overall_correct = 0
    n_tests = 0
    n_cl_correct = {}
    for cl in tqdm(classes):
        n_cl_correct[cl] = 0
        # indecies = random.sample(range(len(test_data[cl])), 10)
        indecies = range(len(test_data[cl]))
        for i in indecies:
            data = test_data[cl][i].reshape((1, 1, 1024, 2))
            model_pred = classes[np.argmax(model.predict(data))]
            n_tests += 1
            if model_pred == cl:
                n_cl_correct[cl] += 1
                n_overall_correct += 1
    print(f"Overall accuracy: {n_overall_correct / n_tests}")
    for cl in n_cl_correct:
        print(f"{cl} accuracy: {n_cl_correct[cl] / len(test_data[cl])}")
        
def export_test(model, data, tests_per_class=1):
    print("[debug] Export test")
    for cl in tqdm(classes):
        indecies = random.sample(range(len(test_data[cl])), tests_per_class)
        for i in indecies:
            data = test_data[cl][i].reshape((1, 1, 1024, 2))
            pred = model.predict(data)

if __name__ == "__main__":
    random.seed(1)
    model = load_model()
    # model.summary()


    test_data = load_test_data()
    test_model(model, test_data)

    