from trainedNet1 import load_model, classes
import tensorflow as tf
from data import load_test_data, load_train_data, saven_pam4_data
import numpy as np
import random
from tqdm import tqdm
from test import test_model
import os

MODELS_DIR = "models/"
if not os.path.exists(MODELS_DIR):
    os.mkdir(MODELS_DIR)

MODEL_TF = MODELS_DIR + "model"
MODEL_NO_QUANT_TFLITE = MODELS_DIR + "model_no_quant.tflite"
MODEL_TFLITE = MODELS_DIR + "model.tflite"
MODEL_TFLITE_MICRO = MODELS_DIR + "model.cc"


def predict_tflite(tflite_model, x_test):
    # Prepare the test data
    x_test_ = x_test.copy()
    # x_test_ = x_test_.reshape((x_test.size, 1))
    x_test_ = x_test_.astype(np.float32)

    # Initialize the TFLite interpreter
    interpreter = tf.lite.Interpreter(model_content=tflite_model)
    # experimental_op_resolver_type=tf.lite.experimental.OpResolverType.BUILTIN_REF)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()[0]
    output_details = interpreter.get_output_details()[0]

    # If required, quantize the input layer (from float to integer)
    input_scale, input_zero_point = input_details["quantization"]
    if (input_scale, input_zero_point) != (0.0, 0):
        x_test_ = x_test_ / input_scale + input_zero_point
        x_test_ = x_test_.astype(input_details["dtype"])

    # Invoke the interpreter
    y_pred = np.empty(x_test_.size, dtype=output_details["dtype"])
    # for i in range(len(x_test_)):
    #     interpreter.set_tensor(input_details["index"], [x_test_[i]])
    #     interpreter.invoke()
    #     y_pred[i] = interpreter.get_tensor(output_details["index"])[0]
    interpreter.set_tensor(input_details["index"], x_test_)
    interpreter.invoke()
    y_pred = interpreter.get_tensor(output_details["index"])[0]

    # If required, dequantized the output layer (from integer to float)
    output_scale, output_zero_point = output_details["quantization"]
    if (output_scale, output_zero_point) != (0.0, 0):
        y_pred = y_pred.astype(np.float32)
        y_pred = (y_pred - output_zero_point) * output_scale

    return y_pred


def np_to_c_array(arr: np.ndarray, arr_name="arr") -> str:
    if arr.dtype == np.float32:
        type_specifier = "float"
    elif arr.dtype == np.uint8:
        type_specifier = "unsigned char"
    elif arr.dtype == np.int8:
        type_specifier = "char"
    else:
        raise NotImplementedError(f"Type {arr.dtype} is not supported")
    res = f"{type_specifier} {arr_name}[] = "   
    
    # res += np.array2string(arr.flatten(), separator=",").replace("[", "{").replace("]", "}")
    # res += ";"

    # very ineffective
    res += "{"
    for v in arr.flatten():
        res += str(v) + ","
    res = res[:-1]
    res += "};"

    return res


def export_test_data(
    model, data, file: str, tests_per_class=1, predict=lambda model, data: model.predict(data), model_name="MODEL_1"
):
    print("[debug] Export test")
    with open(file, "w") as res_file:
        res_file.write(f"#ifndef {model_name}\n")
        res_file.write(f"#define {model_name}\n\n")
        for cl in tqdm(classes):
            # indecies = random.sample(range(len(test_data[cl])), tests_per_class)
            indecies = [0]
            for i in indecies:
                data = test_data[cl][i].reshape((1, 1, 1024, 2))
                pred = predict(model, data)
                data_str = np_to_c_array(data, arr_name=f"test_data_{cl}_{i}".replace('-', ''))
                pred_str = np_to_c_array(pred, arr_name=f"pred_{cl}_{i}".replace('-', ''))
                res_file.write(data_str + "\n")
                res_file.write(pred_str + "\n")
                res_file.write("\n\n")
        res_file.write(f"#endif // {model_name}\n")


def save_models(model, repr_data):
    model.save(MODEL_TF)

    converter = tf.lite.TFLiteConverter.from_saved_model(MODEL_TF)
    model_no_quant_tflite = converter.convert()

    # Save the model to disk
    open(MODEL_NO_QUANT_TFLITE, "wb").write(model_no_quant_tflite)

    # Convert the model to the TensorFlow Lite format with quantization
    def representative_dataset():
        for cl in classes:
            for d in repr_data[cl]:
                yield [d.reshape((1, 1, 1024, 2))]

    # Set the optimization flag.
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    # Enforce integer only quantization
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8
    # Provide a representative dataset to ensure we quantize correctly.
    converter.representative_dataset = representative_dataset
    try:
        model_tflite = converter.convert()
    except Exception as exc:
        print(exc)
        return model, model_no_quant_tflite, None

    # Save the model to disk
    open(MODEL_TFLITE, "wb").write(model_tflite),
    return model, model_no_quant_tflite, model_tflite


def export_model_micro(tflite_model_path):
    os.system(f"xxd -i {tflite_model_path} > {MODEL_TFLITE_MICRO}")
    # Update variable names
    REPLACE_TEXT = MODEL_TFLITE.replace("/", "_").replace(".", "_")
    os.system(f"sed -i 's/'{REPLACE_TEXT}'/g_model/g' {MODEL_TFLITE_MICRO}``")


if __name__ == "__main__":
    random.seed(1)
    model = load_model()
    # model.summary()

    # load data
    test_data = load_test_data()
    # train_data = load_train_data(classes)

    # save all models (regular, tf lite, tf lite with quantization, tf lite micro (with quantization))
    model, model_no_quant_tflite, model_tflite = save_models(model, test_data)
    # if model is not None:
    #     print(f"## Test original model")
    #     test_model(model, test_data)

    if model_no_quant_tflite is not None:
        print(f"## Test tf lite no quant model")
        test_model(model_no_quant_tflite, test_data, predict=predict_tflite)

    if model_tflite is not None:
        print(f"## Test tf lite model")
        test_model(model_tflite, test_data, predict=predict_tflite)

    model_name = "signal_modulation_1"
    test_data_file = "test_data.h"

    if model_tflite is not None:
        export_model_micro(MODEL_TFLITE)
        export_test_data(model_tflite, test_data, file=test_data_file, predict=predict_tflite, model_name=model_name)
    else:
        export_model_micro(MODEL_NO_QUANT_TFLITE)
        export_test_data(model_no_quant_tflite, test_data, file=test_data_file, predict=predict_tflite, model_name=model_name)
