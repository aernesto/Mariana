#Personal tribute to nomad soul
OMICRON_SIGNATURE = ">|\/| /-\ |-> | /-\ |\| /-\>"

VERBOSE = False
SAVE_MESSAGE_LOG = True
SAVE_MESSAGE_LOG_FILE = "Mariana_logs.txt"

#The seed used for generating random stuff
RANDOM_SEED = None

import numpy
numpy.random.seed(RANDOM_SEED)

TYPE_INPUT_LAYER = "input"
TYPE_OUTPUT_LAYER = "output"
TYPE_HIDDEN_LAYER = "hidden"

import theano
DEVICE_IS_GPU = (theano.config.device.find("gpu") > -1)
INTX="int32"
FLOATX=theano.config.floatX
