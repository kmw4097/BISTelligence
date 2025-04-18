# for model

import numpy as np
import seaborn as sns
import random
import os
from pyod.models.mcd import MCD
from sklearn.mixture import GaussianMixture
from pyod.models.lof import LOF
from pyod.models.ocsvm import OCSVM
from pyod.models.iforest import IForest
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, losses, models
from keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.models import load_model


class BaseModel:

    def GetMCD(contamination, random_state, support_fraction):
        model_mcd = MCD(contamination=contamination, random_state=random_state, support_fraction=support_fraction)

        return model_mcd

    def GetOCSVM(contamination, nu, kernel, degree):
        model_ocsvm = OCSVM(contamination=contamination, nu=nu, kernel=kernel, degree=degree)

        return model_ocsvm

    def GetLOF(contamination, novelty, n_neighbors):
        model_lof = LOF(contamination=contamination, novelty=novelty, n_neighbors=n_neighbors)

        return model_lof

    def GetIForest(contamination, n_estimators):
        model_iforest = IForest(contamination=contamination, n_estimators=n_estimators)

        return model_iforest

    def GetGMM(n_components, covariance_type):
        model_gmm = GaussianMixture(
            n_components=n_components,
            covariance_type=covariance_type
        )
        return model_gmm

    def GetAE(momentum, train_shape, random_state):
        def my_seed_everywhere(seed: int = 2):
            random.seed(seed)  # random
            np.random.seed(seed)  # np
            os.environ["PYTHONHASHSEED"] = str(seed)  # os
            tf.random.set_seed(seed)  # tensorflow

        my_seed = random_state
        my_seed_everywhere(my_seed)

        input_dim = train_shape[1]
        # tf.random.set_seed(2)
        initializer = tf.keras.initializers.HeNormal(seed=random_state)
        momentum = momentum

        encoder = models.Sequential([
            # input layer
            layers.InputLayer(input_shape=input_dim),

            layers.Dense(64, kernel_initializer=initializer),
            layers.BatchNormalization(momentum=momentum),
            layers.ReLU(),

            layers.Dense(32, kernel_initializer=initializer),
            layers.BatchNormalization(momentum=momentum),
            layers.ReLU(),

            layers.Dense(16, kernel_initializer=initializer),
            layers.BatchNormalization(momentum=momentum),
            layers.ReLU(),

            layers.Dense(8, kernel_initializer=initializer),
            layers.BatchNormalization(momentum=momentum),
            layers.ReLU(),

            layers.Dense(4, kernel_initializer=initializer),
            layers.BatchNormalization(momentum=momentum),
            layers.ReLU(),
        ])

        decoder = models.Sequential([

            layers.Dense(4, kernel_initializer=initializer),
            layers.BatchNormalization(momentum=momentum),
            layers.ReLU(),

            layers.Dense(8, kernel_initializer=initializer),
            layers.BatchNormalization(momentum=momentum),
            layers.ReLU(),

            layers.Dense(16, kernel_initializer=initializer),
            layers.BatchNormalization(momentum=momentum),
            layers.ReLU(),

            layers.Dense(32, kernel_initializer=initializer),
            layers.BatchNormalization(momentum=momentum),
            layers.ReLU(),

            layers.Dense(64, kernel_initializer=initializer),
            layers.BatchNormalization(momentum=momentum),
            layers.ReLU(),

            # output layer
            layers.Dense(input_dim, kernel_initializer=initializer),
        ])

        model_ae = models.Sequential([
            encoder, decoder
        ])

        return model_ae


class ModelTrain:

    def __init__(self):
        self.param_dict = {'contamination': 0.01,
                           'nu': 0.01,
                           'novelty': True,
                           'random_state': 42,
                           'n_components': 1,
                           'covariance_type': 'full',
                           'momentum': 0.9,
                           'learning_rate': 0.03,
                           'epochs': 100,
                           'patience': 10,
                           'n_neighbors': 20,
                           'kernel': 'rbf',
                           'degree': 3,
                           'n_estimators': 100,
                           'support_fraction': None}

    def SetTrainer(self, train_data):
        self.train_data = train_data

    def SetParam(self, param_dict):
        self.param_dict.update(param_dict)

    def GetTrainedModel(self, model_name="MCD"):
        model = 0
        if model_name == 'MCD':
            model = BaseModel.GetMCD(
                self.param_dict['contamination'],
                self.param_dict['random_state'],
                self.param_dict['support_fraction']
            )
            model.fit(self.train_data)

        elif model_name == 'OCSVM':
            model = BaseModel.GetOCSVM(
                self.param_dict['contamination'],
                self.param_dict['nu'],
                self.param_dict['kernel'],
                self.param_dict['degree']
            )
            model.fit(self.train_data)

        elif model_name == 'IForest':
            model = BaseModel.GetIForest(
                self.param_dict['contamination'],
                self.param_dict['n_estimators']
            )
            model.fit(self.train_data)

        elif model_name == 'LOF':
            model = BaseModel.GetLOF(
                self.param_dict['contamination'],
                self.param_dict['novelty'],
                self.param_dict['n_neighbors']
            )
            model.fit(self.train_data)

        elif model_name == 'GMM':
            model = BaseModel.GetGMM(
                self.param_dict['n_components'],
                self.param_dict['covariance_type']
            )
            model.fit(self.train_data)

        elif model_name == 'AE':
            model = BaseModel.GetAE(
                self.param_dict['momentum'],
                self.train_data.shape,
                self.param_dict['random_state']
            )

            checkpoint_path = 'model/saved_model/best_ae_model.h5'
            early_stopping = EarlyStopping(monitor='val_loss', mode='min', verbose=1,
                                           patience=self.param_dict['patience'])
            check_point = ModelCheckpoint(checkpoint_path, monitor='val_loss', mode='min', save_best_only=True)

            model.compile(optimizer=keras.optimizers.Adam(learning_rate=self.param_dict['learning_rate']),
                          loss=keras.losses.MeanSquaredError())

            history = model.fit(
                self.train_data, self.train_data,
                shuffle=True,
                epochs=self.param_dict['epochs'],
                batch_size=14,
                validation_split=0.3,
                callbacks=[early_stopping, check_point],
                verbose=0
            )
            model = load_model(checkpoint_path)
        else:
            raise 'you can choose in ["MCD", "IForest", "OCSVM", "LOF", "GMM", "AE"]'

        return model