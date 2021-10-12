"""
keras.py

functions to run and train autopilots using keras

"""
from typing import Optional
import numpy as np
from tensorflow import keras
from tensorflow.keras.layers import Input,Dense
from tensorflow.keras.layers import Convolution2D,MaxPooling2D,BatchNormalization
from tensorflow.keras.layers import Activation,Dropout,Flatten,Cropping2D,Lambda
from tensorflow.keras.models import Model,Sequential,load_model
from tensorflow.python.keras.callbacks import EarlyStopping,ModelCheckpoint


class KerasPilot:
    def __init__(self) -> None:
        self.model: Optional[Model] = None
        self.optimizer = "adam"

    def load(self, model_path: str) -> None:
        self.model = load_model(model_path)

    def _get_train_model(self) -> Model:
        """ Model used for training, could be just a sub part of the model"""
        return self.model

    def shutdown(self):
            pass

    def compile(self) -> None:
        pass

    def train(self,train_gen,val_gen,saved_model_path,epochs=100,steps=100,train_split=0.8,verbose=1, min_delta=.0005, patience=5, use_early_stop=True):
        """
        train_gen: generator that yields an array of images an array of

        """

        self.compile()

        # checkpoint to save model after each epoch
        save_best = keras.callbacks.ModelCheckpoint(saved_model_path,
                                                    monitor='val_loss',
                                                    verbose=verbose,
                                                    save_best_only=True,
                                                    mode='min')
        # stop training if the validation error stops improving.
        early_stop = keras.callbacks.EarlyStopping(monitor='val_loss',
                                                   min_delta=min_delta,
                                                   patience = patience,
                                                   verbose=verbose,
                                                   mode='auto')

        callbacks_list = [save_best]

        if use_early_stop:
            callbacks_list.append(early_stop)

        hist = self.model.fit_generator(
            train_gen,
            steps_per_epoch=steps,
            epochs=epochs,
            verbose=1,
            validation_data=val_gen,
            callbacks=callbacks_list,
            validation_steps=steps*(1.0-train_split)/train_split)

        return hist



class KerasLinear(KerasPilot):
    def __init__(self):
        super().__init__()
        self.model = default_linear()

    def compile(self) -> None:
        self.model.compile(optimizer=self.optimizer,loss='mse')

    def run(self,img_arr):
        img_arr = img_arr.reshape((1,) + img_arr.shape)
        outputs = self.model.predict(img_arr)
        # print(len(outputs),outputs)
        steering = outputs[0]
        throttle = outputs[1]
        return steering[0][0], throttle[0][0]



def conv2d(filters, kernel, strides, layer_num, activation='relu'):
    """
    Helper function to create a standard valid-padded convolutional layer
    with square kernel and strides and unified naming convention

    :param filters:     channel dimension of the layer
    :param kernel:      creates (kernel, kernel) kernel matrix dimension
    :param strides:     creates (strides, strides) stride
    :param layer_num:   used in labelling the layer
    :param activation:  activation, defaults to relu
    :return:            tf.keras Convolution2D layer
    """
    return Convolution2D(filters=filters,
                         kernel_size=(kernel, kernel),
                         padding='same',
                         strides=(strides, strides),
                         activation=activation,
                         name='conv2d_' + str(layer_num))


def core_cnn_layers(img_in, drop, l4_stride=1):
    """
    Returns the core CNN layers that are shared among the different models,
    like linear, imu, behavioural

    :param img_in:          input layer of network
    :param drop:            dropout rate
    :param l4_stride:       4-th layer stride, default 1
    :return:                stack of CNN layers
    """
    x = img_in
    x = conv2d(24, 5, 2, 1)(x)
    x = Dropout(drop)(x)
    x = conv2d(32, 5, 2, 2)(x)
    x = Dropout(drop)(x)
    x = conv2d(64, 5, 2, 3)(x)
    x = Dropout(drop)(x)
    x = conv2d(64, 3, 1, 4)(x)
    x = Dropout(drop)(x)
    x = conv2d(64, 3, 1, 5)(x)
    x = Dropout(drop)(x)
    x = Flatten(name='flattened')(x)
    return x

def default_linear():
    drop = 0.2
    img_in = Input(shape=(120,160,3),name='img_in')
    x = img_in
    x = Cropping2D(cropping=((60, 0), (0, 0)))(x)  # trim 60 pixels off top
    x = Lambda(lambda x: x / 127.5 - 1.)(x)  # normalize and re-center
    x = core_cnn_layers(x,drop)

    x = Dense(100,activation='relu',name='dense_1')(x)
    x = Dropout(.1)(x)
    x = Dense(50,activation='relu',name='dense_2')(x)
    x = Dropout(.1)(x)

    # categorical output of the angle
    angle_out = Dense(units=1,activation='linear',name='angle_out')(x)

    # continous output of throttle
    throttle_out = Dense(units=1,activation='linear',name='throttle_out')(x)

    model = Model(inputs=[img_in],outputs =[angle_out,throttle_out])

    return model