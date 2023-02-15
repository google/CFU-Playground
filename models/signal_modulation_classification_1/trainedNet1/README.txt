This Python package was created by
MATLAB Deep Learning Toolbox Converter for TensorFlow Models.
14-Feb-2023 23:39:08

This package contains a TensorFlow model exported from MATLAB.


ISSUES ENCOUNTERED DURING EXPORT FROM MATLAB
--------------------------------------------
There were no issues.


USAGE
-----

* To load the model with weights:

    import trainedNet1
    model = trainedNet1.load_model()


* To load the model without weights:

    import trainedNet1
    model = trainedNet1.load_model(load_weights=False)


* To save a loaded model into TensorFlow SavedModel format:

    model.save(<fileName>)


* To save a loaded model into TensorFlow HDF5 format:

    model.save(<fileName>, save_format='h5')


PACKAGE FILES
-------------

model.py
	Defines the untrained model. Modifying this file before calling load_model 
	might cause load_model to give unexpected results.

weights.h5
	Contains the model weights in HDF5 format. Warning: This file is not 
	compatible with the tensorflow.keras.models.load_model() function. See the 
	USAGE section above for instructions on how to load the model and re-save 
	it in standard TensorFlow SavedModel or HDF5 formats.

__init__.py
	Defines the load_model function.
