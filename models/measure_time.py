import os
# os.environ['CUDA_VISIBLE_DEVICES'] = ''
import tensorflow as tf
import time
import numpy as np
from tools.deployment_tools import predict_tflite
from tools.deployment_tools import to_tf_lite


# tf.config.set_visible_devices([], 'GPU')

model_cnn_path = "final_models_evaluation/CNN_mixed_v2_0-30_quant/experiment_0/model"
model_encoder_path = "final_models_evaluation/encoder_mixed_v2_0-30_0/experiment_0/model/"

# model_path = model_encoder_path
model_path = model_cnn_path

if model_path == model_cnn_path:
    data = np.load("final_models_evaluation/data_mixed_V2_0_30_30k.npy")
else:
    data = np.squeeze(np.load("final_models_evaluation/data_mixed_V2_0_30_30k.npy"))

print(">>>>>", data.shape)

# model = tf.keras.models.load_model(model_path)
model = to_tf_lite(model_path)

open(model_path + "_tf_lite_no_quant", "wb").write(model)
# open(model_path, "wb").write(model)

# data = data[:40_000]
data = data[:1_000]

warm_up = 5
n_iterations = 10
batch_size = 1

for i in range(warm_up):
    print(f"Warm up: {i}")
    # pred = model.predict(data, batch_size=batch_size, verbose=False)
    for k in range(len(data)):
        # pred = model.predict(np.expand_dims(data[k], 1), 1, verbose=False)
        pred = predict_tflite(model, np.expand_dims(data[k], 0))
        # pred = predict_tflite(model, data[k])

start = time.time()
for i in range(n_iterations):
    print(f"Run: {i}")
    # pred = model.predict(data, batch_size=batch_size, verbose=False)
    for k in range(len(data)):
        # pred = model.predict(np.expand_dims(data[k], 1), 1, verbose=False)
        pred = predict_tflite(model, np.expand_dims(data[k], 0))
        # pred = predict_tflite(model, data[k])

end = time.time()

elapsed = end - start
print(f"Time elapsed: {elapsed}s")
print(f"Time per frame: {(elapsed / (len(data) * n_iterations)) * 1000}ms")

