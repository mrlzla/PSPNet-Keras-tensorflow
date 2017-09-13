from os import path
from os.path import join
from scipy.misc import imresize
from python_utils.preprocessing import data_generator_s31
from python_utils.callbacks import callbacks
from keras.models import load_model
import layers_builder as layers
import numpy as np
import argparse
import os

def set_npy_weights(weights_path, model):
        npy_weights_path = join("weights", "npy", weights_path + ".npy")
        json_path = join("weights", "keras", weights_path + ".json")
        h5_path = join("weights", "keras", weights_path + ".h5")

        print("Importing weights from %s" % npy_weights_path)
        weights = np.load(npy_weights_path).item()

        for layer in model.layers:
            print(layer.name)
            if layer.name[:4] == 'conv' and layer.name[-2:] == 'bn':
                mean = weights[layer.name]['mean'].reshape(-1)
                variance = weights[layer.name]['variance'].reshape(-1)
                scale = weights[layer.name]['scale'].reshape(-1)
                offset = weights[layer.name]['offset'].reshape(-1)

                model.get_layer(layer.name).set_weights([mean, variance,
                                                             scale, offset])

            elif layer.name[:4] == 'conv' and not layer.name[-4:] == 'relu':
                try:
                    weight = weights[layer.name]['weights']
                    model.get_layer(layer.name).set_weights([weight])
                except Exception as err:
                    try:
	                biases = weights[layer.name]['biases']
                        model.get_layer(layer.name).set_weights([weight,
                                                                 biases])
		    except Exception as err2:
			print(err2)

            if layer.name == 'activation_52':
                break

def train(datadir, logdir, input_size, nb_classes, resnet_layers, batchsize, weights, initial_epoch, pre_trained):
    if args.weights:
    	model = load_model(weights)
    else:
        model = layers.build_pspnet(nb_classes=nb_classes,
                         resnet_layers=resnet_layers,
                         input_shape=input_size)
        set_npy_weights(pre_trained, model)
    model.fit_generator(
        data_generator_s31(datadir=datadir, batch_size=batchsize, input_size=input_size, nb_classes=nb_classes),
        epochs=100000, verbose=True, steps_per_epoch=50, callbacks=callbacks(logdir), initial_epoch=initial_epoch)

class PSPNet(object):
    """Pyramid Scene Parsing Network by Hengshuang Zhao et al 2017"""

    def __init__(self, nb_classes, resnet_layers, input_shape):
        self.input_shape = input_shape
        self.model = layers.build_pspnet(nb_classes=nb_classes,
                           layers=resnet_layers,
                           input_shape=self.input_shape)
        print("Load pre-trained weights")
        self.model.load_weights("weights/keras/pspnet101_voc2012.h5")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dim', type=int, default=473)
    parser.add_argument('--classes', type=int, default=32)
    parser.add_argument('--resnet_layers', type=int, default=50)
    parser.add_argument('--batch', type=int, default=4)
    parser.add_argument('--datadir', type=str, required=True)
    parser.add_argument('--logdir', type=str)
    parser.add_argument('--weights', type=str, default=None)
    parser.add_argument('--initial_epoch', type=int, default=0)
    parser.add_argument('-m', '--model', type=str, default='pspnet50_ade20k',
                        help='Model/Weights to use',
                        choices=['pspnet50_ade20k',
                                 'pspnet101_cityscapes',
                                 'pspnet101_voc2012'])
    parser.add_argument('--gpu', type=int, default=0)
    args = parser.parse_args()

    os.environ['CUDA_VISIBLE_DEVICES'] = str(args.gpu)

    train(args.datadir, args.logdir, (args.input_dim, args.input_dim), args.classes, args.resnet_layers, args.batch, args.weights, args.initial_epoch, args.model)
