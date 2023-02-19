from trainedNet1 import load_model, classes
from data import saven_pam4_data
from data import load_test_data
from tqdm import tqdm
import numpy as np
import random


def test_model(model, test_data, predict=lambda model, data: model.predict(data)):
    print("[debug] Start model test")
    n_overall_correct = 0
    n_tests = 0
    n_cl_correct = {}
    for cl in tqdm(classes):
        n_cl_correct[cl] = 0
        # indecies = random.sample(range(len(test_data[cl])), 10)
        indecies = range(len(test_data[cl]))
        for i in indecies:
            data = test_data[cl][i].reshape((1, 1, 1024, 2))
            pred = predict(model, data)
            model_pred = classes[np.argmax(pred)]
            n_tests += 1
            if model_pred == cl:
                n_cl_correct[cl] += 1
                n_overall_correct += 1
    print(f"Overall accuracy: {n_overall_correct / n_tests}")
    for cl in n_cl_correct:
        print(f"{cl} accuracy: {n_cl_correct[cl] / len(test_data[cl])}")

if __name__ == "__main__":
    random.seed(1)
    model = load_model()
    # model.summary()

    print("## Predict 7_pam4 test data")
    for i in range(saven_pam4_data.shape[-1]):
        print(f"    i = {i}")
        data = saven_pam4_data[:, :, :, i]
        data = data.reshape((1, 1, 1024, 2))

        pred = model.predict(data)
        print(f"    [info] pred: {pred}")
        print(f"    [info] pred modulation: {classes[np.argmax(pred)]}")
        print("\n")

    
    # train_data = load_train_data(classes)
    # print(f"## Predict 10 of each class (random from train)")
    # for cl in classes:
    #     print(f"    ### class = {cl}")
    #     indecies = random.sample(range(len(train_data[cl])), 10)
    #     for i in indecies:
    #         print(train_data[cl][i].shape)
    #         model_pred = classes[np.argmax(model.predict(train_data[cl][i]))]
    #         print(f"         pred = {model_pred}, actual = {cl}")


    test_data = load_test_data()
    test_model(model, test_data)




    