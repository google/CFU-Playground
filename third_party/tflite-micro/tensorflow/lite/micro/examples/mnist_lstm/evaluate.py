# Copyright 2022 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================
"""LSTM model evaluation for MNIST recognition

Run:
bazel build tensorflow/lite/micro/examples/mnist_lstm:evaluate
bazel-bin/tensorflow/lite/micro/examples/mnist_lstm/evaluate
--model_path=".tflite file path" --img_path="MNIST image path"

"""
import os

from absl import app
from absl import flags
from absl import logging
import numpy as np
from PIL import Image

from tflite_micro.tensorflow.lite.micro.python.interpreter.src import tflm_runtime

FLAGS = flags.FLAGS

flags.DEFINE_string("model_path", "/tmp/lstm_trained_model/lstm.tflite",
                    "the trained model path.")
flags.DEFINE_string("img_path", "/tmp/samples/sample0.jpg",
                    "path for the image to be predicted.")
flags.DEFINE_bool("quantized", False, "if the model is quantized")


def read_img(img_path):
  """Read MNIST image

  Args:
      img_path (str): path to a MNIST image

  Returns:
      np.array : image in the correct np.array format
  """
  image = Image.open(img_path)
  data = np.asarray(image, dtype=np.float32)
  if data.shape not in [(28, 28), (28, 28, 1)]:
    raise ValueError(
        "Invalid input image shape (MNIST image should have shape 28*28 or 28*28*1)"
    )
  # Normalize the image if necessary
  if data.max() > 1:
    data = data / 255.0
  # Model inference requires batch size one
  data = data.reshape((1, 28, 28))
  return data


def predict_image(interpreter, img_path, quantized=False):
  """Use TFLM interpreter to predict a MNIST image

  Args:
      interpreter (tflm_runtime.Interpreter): the TFLM python interpreter
      img_path (str): path to the image that need to be predicted
      input_scale (float): quantization scale for the input tensor. Defaults to
        1 (no quantization)
      quantized (bool): if the model is quantized

  Returns:
      np.array : predicted probability for each class (digit 0-9)
  """
  data = read_img(img_path)
  # Quantize the input if necessary
  if quantized:
    # Get input quantization parameters (0 since input data has only one channel)
    input_quantization_parameters = interpreter.get_input_details(
        0)["quantization_parameters"]
    input_scale, input_zero_point = input_quantization_parameters["scales"][
        0], input_quantization_parameters["zero_points"][0]
    # quantize the input data
    data = data / input_scale + input_zero_point
    data = data.astype("int8")

  interpreter.set_input(data, 0)
  interpreter.invoke()
  tflm_output = interpreter.get_output(0)
  # LSTM is stateful, reset the state after the usage since each image is independent
  interpreter.reset()
  # One image per time (i.e., remove the batch dimention)
  # Note: quantized output (dtpe int8) is converted to float to avoid integer overflow during dequantization
  return tflm_output[0].astype("float")


def main(_):
  if not os.path.exists(FLAGS.model_path):
    raise ValueError(
        "Model file does not exist. Please check the .tflite model path.")
  if not os.path.exists(FLAGS.img_path):
    raise ValueError("Image file does not exist. Please check the image path.")

  tflm_interpreter = tflm_runtime.Interpreter.from_file(FLAGS.model_path)
  category_probabilities = predict_image(tflm_interpreter, FLAGS.img_path,
                                         FLAGS.quantized)
  predicted_category = np.argmax(category_probabilities)
  logging.info("Model predicts the image as %i with probability %.2f",
               predicted_category, category_probabilities[predicted_category])


if __name__ == "__main__":
  app.run(main)
