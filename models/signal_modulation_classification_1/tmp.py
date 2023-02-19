from data import load_train_data
from trainedNet1 import load_model, classes
from scipy import io


if __name__ == "__main__":
    frame_pam40 = io.loadmat("frame_pam4_0.mat")['frame']
    print(frame_pam40[:10])
    # train_data = load_train_data(classes)
    # print(len(train_data["PAM4"]))
    # print(train_data["PAM4"][0].shape)
    # print(train_data["PAM4"][0][:10])