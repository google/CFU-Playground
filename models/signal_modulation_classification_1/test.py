from trainedNet1 import load_model, classes
from data import saven_pam4_data
from data import load_test_data
import numpy as np
import random


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
    print(f"## Predict 10 of each class (random from train)")
    for cl in classes:
        print(f"    ### class = {cl}")
        indecies = random.sample(range(len(test_data[cl])), 10)
        for i in indecies:
            data = test_data[cl][i].reshape((1, 1, 1024, 2))
            model_pred = classes[np.argmax(model.predict(data))]
            print(f"         pred = {model_pred}, actual = {cl}")


    