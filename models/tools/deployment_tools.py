import tensorflow as tf
from typing import Optional, List, Union
import numpy as np
from tqdm import tqdm
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import shutil


def to_tf_lite(
    tf_model_path: str,
    apply_quantization=False,
    representative_ds: Optional[np.ndarray] = None,
    optimizations: Optional[List[tf.lite.Optimize]] = None,
    supported_ops: Optional[List[tf.lite.OpsSet]] = None,
    input_output_types=[tf.int8, tf.int8],
):
    if optimizations is None:
        optimizations = [tf.lite.Optimize.DEFAULT]

    if supported_ops is None:
        supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]

    converter = tf.lite.TFLiteConverter.from_saved_model(tf_model_path)
    if not apply_quantization:
        model_no_quant_tflite = converter.convert()
        return model_no_quant_tflite

    if representative_ds is None:
        raise ValueError(f"Representative ds is None")

    def representative_dataset():
        for i in range(len(representative_ds)):
            yield [np.expand_dims(representative_ds[i], axis=0)]

    converter.optimizations = optimizations
    converter.target_spec.supported_ops = supported_ops

    converter.inference_input_type = input_output_types[0]
    converter.inference_output_type = input_output_types[1]

    converter.representative_dataset = representative_dataset
    model_tflite = converter.convert()
    return model_tflite


def predict_tflite(tflite_model, x_test):
    # Prepare the test data
    x_test_ = x_test.copy()
    x_test_ = x_test_.astype(np.float32)

    # Initialize the TFLite interpreter
    interpreter = tf.lite.Interpreter(model_content=tflite_model)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()[0]
    output_details = interpreter.get_output_details()[0]

    # If required, quantize the input layer (from float to integer)
    input_scale, input_zero_point = input_details["quantization"]
    if (input_scale, input_zero_point) != (0.0, 0):
        x_test_ = x_test_ / input_scale + input_zero_point
        x_test_ = x_test_.astype(input_details["dtype"])

    # Invoke the interpreter
    y_pred = np.empty((x_test_.shape[0], *output_details["shape"]), dtype=output_details["dtype"])
    for i in range(len(x_test_)):
        interpreter.set_tensor(input_details["index"], [x_test_[i]])
        interpreter.invoke()
        y_pred[i] = interpreter.get_tensor(output_details["index"])[0]

    # If required, dequantized the output layer (from integer to float)
    output_scale, output_zero_point = output_details["quantization"]
    if (output_scale, output_zero_point) != (0.0, 0):
        y_pred = y_pred.astype(np.float32)
        y_pred = (y_pred - output_zero_point) * output_scale

    return y_pred


def export_tf_lite_micto_model_form(
    tf_lite_model: Union[str, bytes], tflm_model_path: str, model_name=None
):
    if isinstance(tf_lite_model, bytes):
        tf_lite_model_path = f"temp_{model_name}.tflite"
        open(tf_lite_model_path, "wb").write(tf_lite_model)

    elif isinstance(tf_lite_model, str):
        tf_lite_model_path = tf_lite_model
    else:
        raise RuntimeError("tf_lite_model should be string-path of tflite model (bytes)")

    if model_name is None:
        model_name = tflm_model_path.replace("/", "_").replace(".", "_")
    os.system(f"/development/RISC-V-SIMD-extension-for-the-AI-workload/custom_bin/xxd -i -n {model_name}_model {tf_lite_model_path} > {tflm_model_path}")

    if isinstance(tf_lite_model, bytes):
        os.remove(tf_lite_model_path)


def export_test_data(
    model,
    test_data: np.ndarray,
    test_labels: np.ndarray,
    classes: List[str],
    file: str,
    # tests_per_class=1,
    predict=lambda model, data: model.predict(data),
    model_name="MODEL_1",
    apply_quantization=False,
):
    print("[debug] Export test data")
    if apply_quantization:
        interpreter = tf.lite.Interpreter(model_content=model)
        interpreter.allocate_tensors()
        input_details = interpreter.get_input_details()[0]
        output_details = interpreter.get_output_details()[0]

    define_name = model_name.upper() + "_TEST_DATA"
    with open(file, "w") as res_file:
        res_file.write(f"#ifndef {define_name}\n")
        res_file.write(f"#define {define_name}\n\n")
        for ci, cl in tqdm(enumerate(classes)):
            # indecies = random.sample(range(len(test_data[cl])), tests_per_class)
            indecies = [np.where(test_labels == ci)[0][0]]
            for i in indecies:
                data = np.array([test_data[i]])
                pred = predict(model, data)

                if apply_quantization:
                    input_scale, input_zero_point = input_details["quantization"]
                    if (input_scale, input_zero_point) != (0.0, 0):
                        data = data / input_scale + input_zero_point
                        data = data.astype(input_details["dtype"])
                    output_scale, output_zero_point = output_details["quantization"]
                    if (output_scale, output_zero_point) != (0.0, 0):
                        pred = pred / output_scale + output_zero_point
                        pred = pred.astype(output_details["dtype"])


                data_str = _Tools.np_to_c_array(
                    data, arr_name=f"test_data_{model_name}_{cl}".replace("-", "_")
                )
                pred_str = _Tools.np_to_c_array(
                    pred, arr_name=f"pred_{model_name}_{cl}".replace("-", "_")
                )
                res_file.write(data_str + "\n")
                res_file.write(pred_str + "\n")
                res_file.write("\n\n")
        res_file.write(f"#endif // {define_name}\n")


class _Tools:
    TEMPLATES_PATH = Path(__file__).resolve().parent / "templates"
    CFU_SRC_PATH = Path(__file__).resolve().parent.parent.parent / "common" / "src"
    CFU_ROOT = Path(__file__).resolve().parent.parent.parent
    ANCHOR = "// My_models_anchor"

    @staticmethod
    def np_to_c_array(arr: np.ndarray, arr_name="arr") -> str:
        if arr.dtype == np.float32:
            type_specifier = "float"
        elif arr.dtype == np.float64:
            type_specifier = "float"
        elif arr.dtype == np.uint8:
            type_specifier = "unsigned char"
        elif arr.dtype == np.int8:
            type_specifier = "signed char"
        else:
            raise NotImplementedError(f"Type {arr.dtype} is not supported")

        res = f"{type_specifier} {arr_name}[] = "

        # TODO: very ineffective
        res += "{"
        for v in arr.flatten():
            res += str(v) + ","
        res = res[:-1]
        res += "};"

        return res

    @staticmethod
    def add_after_line(file_path: Path, line: str, add_what: str, res_path=None):
        updated_file_content = ""
        for fline in open(file_path, "r"):
            updated_file_content += fline
            if fline.strip() == line:
                updated_file_content += add_what
        if res_path is None:
            res_path = file_path
        with open(res_path, "w") as f:
            f.write(updated_file_content)
    
    class _TestData:
        def __init__(self, y, pred) -> None:
            self.y = y
            self.pred = pred


def deploy_model_tflite(
    tf_lite_model: bytes,
    test_data: np.ndarray,
    test_labels: np.ndarray,
    model_name: str,
    classes: List[str],
    epsilon=0.0005,
    apply_quantization=False,
    arena_size=110_000,
    create_cfu_playground_proj=False,
    proj_template="proj_template",
):
    # Output files
    model_header = f"{model_name}_model.h"
    test_data_header = f"{model_name}_test_data.h"
    model_test_header = f"{model_name}.h"
    model_test_src = f"{model_name}.cc"

    # Export model to model file
    export_tf_lite_micto_model_form(tf_lite_model, model_header, model_name=model_name)

    # Export test data and outputs to file
    export_test_data(
        tf_lite_model,
        test_data,
        test_labels,
        classes,
        test_data_header,
        model_name=model_name,
        predict=predict_tflite,
        apply_quantization=apply_quantization,
    )

    # Load templates for tests, and fill context
    environment = Environment(loader=FileSystemLoader(_Tools.TEMPLATES_PATH))

    model_h_template = environment.get_template("model.h.j2")
    model_cc_template = environment.get_template("model.cc.j2")

    num_classes = len(classes)

    test_data_names = [
        _Tools._TestData(
            f"test_data_{model_name}_{cls}".replace("-", "_"),
            f"pred_{model_name}_{cls}".replace("-", "_"),
        )
        for cls in classes
    ]

    context = {
        "model_name": model_name,
        "model_name_upper": model_name.upper(),
        "apply_quantization": apply_quantization,
        "num_classes": str(num_classes),
        "epsilon": str(epsilon), #if not apply_quantization else "0",
        "test_data": test_data_names,
        "output_type": "int8_t" if apply_quantization else "float",
        "input_type": "int8_t" if apply_quantization else "float",
    }

    # Save model tests
    with open(model_test_header, mode="w", encoding="utf-8") as model_h_file:
        model_h_file.write(model_h_template.render(context))

    with open(model_test_src, mode="w", encoding="utf-8") as model_cc_file:
        model_cc_file.write(model_cc_template.render(context))

    # Move model files to sources
    model_path = _Tools.CFU_SRC_PATH / "models" / model_name
    if not model_path.exists():
        model_path.mkdir()

    shutil.move(model_header, model_path / model_header)
    shutil.move(test_data_header, model_path / test_data_header)
    shutil.move(model_test_header, model_path / model_test_header)
    shutil.move(model_test_src, model_path / model_test_src)

    # Update tflite.cc file
    add_arena_size_str = f"""\
#ifdef INCLUDE_MODEL_{model_name.upper()}
    {arena_size},
#endif
"""
    tflite_cc_file = _Tools.CFU_SRC_PATH / "tflite.cc"
    tflite_cc_file_bak = _Tools.CFU_SRC_PATH / "tflite.cc.bak"
    _Tools.add_after_line(
        tflite_cc_file_bak,
        line=_Tools.ANCHOR,
        add_what=add_arena_size_str,
        res_path=tflite_cc_file,
    )

    # Update models.c file
    add_model_menu_str = f"""\
#if defined(INCLUDE_MODEL_{model_name.upper()}) || defined(INCLUDE_ALL_TFLM_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "{model_name}", {model_name}_menu),
#endif        
"""
    models_file = _Tools.CFU_SRC_PATH / "models" / "models.c"
    models_file_bak = _Tools.CFU_SRC_PATH / "models" / "models.c.bak"
    _Tools.add_after_line(
        models_file_bak,
        line=_Tools.ANCHOR,
        add_what=add_model_menu_str,
        res_path=models_file,
    )

    models_file = _Tools.CFU_SRC_PATH / "models" / "models.c"
    models_file_bak = _Tools.CFU_SRC_PATH / "models" / "models.c"
    _Tools.add_after_line(
        models_file_bak,
        line="// My models include anchor",
        add_what=f"#include \"models/{model_name}/{model_name}.h\"\n",
        res_path=models_file,
    )

    if create_cfu_playground_proj:
        proj_dir = _Tools.CFU_ROOT / "proj" / model_name
        template_dir = _Tools.CFU_ROOT / "proj" / proj_template
        if not proj_dir.exists():
            shutil.copytree(template_dir, proj_dir)
            _Tools.add_after_line(
                template_dir / "Makefile",
                line="DEFINES += INCLUDE_MODEL_PDTI8",
                add_what=f"DEFINES += INCLUDE_MODEL_{model_name.upper()}\n",
                res_path=proj_dir / "Makefile",
            )

        else:
            print(f"[Warning] proj directory already exists: {proj_dir}")
