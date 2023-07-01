import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")


from datasets.fabric import make_sigmod_ds
from models.fabric import (
    make_sigmod_model,
    EncoderLayerConfiguration,
    EncoderTransformerConfiguration,
)
from tools.utils import set_seed
from evaluation.metric_evaluation import metric_evaluation, snr_to_metric_evaluation
from evaluation.vizualization import plot_train

import tensorflow as tf


def main():
    set_seed(1234)

    # Load dataset
    radioml = make_sigmod_ds("radioml_2016")
    radioml.load("data/radioml_2016/RML2016.10a_dict.pkl")
    splitted_radioml_ds = radioml.split_train_val_test(0.8, 0.1)

    enc_v1_configuration = EncoderTransformerConfiguration(
        input_shape=(128, 2),
        n_classes=len(radioml.get_modulations()),
        cnn_output_channels=[32],
        cnn_kernel_sizes=[8],
        cnn_paddings=["same"],
        encoder_layer=EncoderLayerConfiguration(
            h=4,
            d_k=32,
            d_v=32,
            d_model=32,
            d_ff=128,
            n=4,
        ),
        avg_size=32,
        dense_sizes=[128],
    )

    model = make_sigmod_model("encoder_transformer_1d_v1", enc_v1_configuration)

    # Train model
    def step_decay(epoch):
        lrate = 0.001
        factor = epoch // 8
        lrate /= 10**factor
        return lrate

    lrate = tf.keras.callbacks.LearningRateScheduler(step_decay)

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.0),
        # optimizer=tf.keras.optimizers.Adam(),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(),
        metrics=["accuracy"],
    )

    # N_EPOCHS = 16
    N_EPOCHS = 2
    BATCH_SIZE = 256

    h = model.fit(
        splitted_radioml_ds.train.data,
        splitted_radioml_ds.train.labels,
        epochs=N_EPOCHS,
        batch_size=BATCH_SIZE,
        validation_data=(splitted_radioml_ds.val.data, splitted_radioml_ds.val.labels),
        callbacks=[lrate],
    )

    plot_train(h.history)

    metric_evaluation(
        model,
        splitted_radioml_ds.test.data,
        splitted_radioml_ds.test.labels,
        radioml.get_modulations(),
    )

    snr_to_metric_evaluation(
        model,
        splitted_radioml_ds.test.data,
        splitted_radioml_ds.test.labels,
        radioml.get_snrs()[radioml.get_split_indecies().test],
    )


if __name__ == "__main__":
    main()
