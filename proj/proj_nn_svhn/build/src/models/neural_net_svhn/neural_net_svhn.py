

import os
import itertools
import numpy as np
import tensorflow as tf
import scipy.io
#import pandas as pd
#import seaborn as sns

import keras
from keras.models import Sequential
from keras.utils import np_utils
from keras.layers import Dense, Dropout, Activation, BatchNormalization,Flatten,Conv2D
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from tensorflow.keras.optimizers import SGD, Adadelta, Adagrad

from sklearn import datasets
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
from keras.callbacks import EarlyStopping
import matplotlib.pyplot as plt

#matplotlib inline
#plt.rcParams['figure.figsize'] = (12.0, 8.0)



#load image dataset
train_dataset = scipy.io.loadmat('train_32x32.mat') 
#train_extra_dataset = scipy.io.loadmat('extra_32x32.mat')
test_dataset = scipy.io.loadmat('test_32x32.mat')

X_train = train_dataset['X']
y_train = train_dataset['y']
#X_extra_train = train_extra_dataset['X']
#y_extra_train = train_extra_dataset['y']
X_test = test_dataset['X']
y_test = test_dataset['y']


print('Training set: ', X_train.shape, y_train.shape)
#print('Training extra set: ', X_extra_train.shape, X_extra_train.shape)
print('Testing set: ', X_test.shape, y_test.shape)

# Encode target column
X_train = X_train.astype('float32')

#X_extra_train = X_extra_train.astype('float32')
print('Training set type', type(X_train))

X_test = X_test.astype('float32')

# Scale data instance values between 0 to 1, before feeding to the neural network model
X_train /= 255
#X_extra_train /= 255
X_test /= 255

X_train = X_train[np.newaxis,...]
X_train = np.swapaxes(X_train,0,4).squeeze()

#X_extra_train = X_extra_train[np.newaxis,...]
#X_extra_train = np.swapaxes(X_extra_train,0,4).squeeze()

X_test = X_test[np.newaxis,...]
X_test = np.swapaxes(X_test,0,4).squeeze()


np.place(y_train,y_train == 10,0)
#np.place(y_extra_train,y_extra_train == 10,0)
np.place(y_test,y_test == 10,0)

y_train = tf.keras.utils.to_categorical(y_train, 10)
#y_extra_train = keras.utils.to_categorical(y_extra_train, 10)
y_test = tf.keras.utils.to_categorical(y_test, 10)

batch_size = 128
nb_classes = 10
nb_epoch = 20

# create Sequential model object
model = Sequential()

#input layer with 32 nodes **
model.add(Conv2D(32,(3, 3), activation='relu',input_shape=(32, 32, 3))) 
model.add(BatchNormalization())

# first hidden layer with 32 nodes
model.add(Conv2D(32,(3, 3),activation='relu'))
model.add(BatchNormalization())
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

# second hidden layer with 64 nodes **
model.add(Conv2D(64,(3, 3), activation='relu'))
model.add(BatchNormalization())

# third hidden layer with 64 nodes
model.add(Conv2D(64,(3, 3),activation='relu')) 
model.add(BatchNormalization())
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

# Flatten layer, Flatten serves as a connection between the convolution and dense layers
# transforms the format of the images from a 2d-array to a 1d-array
model.add(Flatten())
model.add(BatchNormalization())

# Dense is the layer to perform classification
model.add(Dense(512,activation='relu'))
model.add(BatchNormalization())
model.add(Dropout(0.5))

# Final Dense layer to map target class
model.add(Dense(nb_classes,activation='softmax'))

# stpes to compile model, using SGD as learning rate
sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(
    loss='categorical_crossentropy', 
    optimizer=sgd,
    metrics=['accuracy']
)

# model summary
model.summary()

model_history = model.fit(X_train, y_train, batch_size=batch_size, epochs=nb_epoch, verbose=1,
          shuffle=True,validation_split=0.25,
          callbacks=[EarlyStopping(monitor='val_loss', patience=5)])
          
          # Performance matrix 
#hist = pd.DataFrame(model_history.history)
#hist['epoch'] = model_history.epoch
#hist

#Evaluate model performance on Test dataset

test_loss, test_accuracy= model.evaluate(X_test, y_test)
print('Test Loss:', test_loss)
print('Test Accuracy:',test_accuracy)

prediction_array = model.predict(X_test)
predicted_class = np.argmax(prediction_array, axis=1)

# Plot function 
def plot_predicted_label(images, nrows, ncols, cls_true, cls_pred,prediction_array):
    fig, axes = plt.subplots(nrows, ncols,figsize=(20, 10))
    
    rs = np.random.choice(images.shape[0], nrows*ncols)
    
    for i, ax in zip(rs, axes.flat):
        prob = round(prediction_array[i][cls_pred[i]],2)
        title = 'True: %s, Pred: %s , Prob:%0.2f' % (np.argmax(cls_true[i]),cls_pred[i],prob)
        ax.imshow(images[i,:,:,0], cmap='binary')
        ax.set_title(title)
         
        ax.set_xticks([])
        ax.set_yticks([])


# ploat image with predicted and actual value
num_rows = 3
num_cols = 6
plot_predicted_label(X_test,num_rows, num_cols, y_test,predicted_class,prediction_array);

""" Converting to TFlite"""
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

with open('model.tflite', 'wb') as f:
  f.write(tflite_model)

