CHANGELOG
=========

1.0.3rc:
--------

* bug fix: decorators now can intelligently cast ints and floats
* bug fix: fixed misplaced decorators
* Brand new awesome learning encapsulation paradygm, that is way more flexible and powerfull. Arbitrary infos such as weights means, maxes etc... can now be logged and saved on any type of device.
* Layers can have multiple types (INPUT, HIDDEN, OUTPUT)
* Embedding layares can now be hidden layers as well as inputs
* Null cost redefined as a function of outputs and targets
* GeometricalEarlyStopping can now work descending (default) or ascending
* Better abstraction of saving criteria
* Minor refactoring of GGPlot2 recorder
* Added SavePeriod to periodically save the model
* Embedding has now a paramater that allows the masking of inputs by using the label 0 
* Scale in softmax
* Mandatory setCreationArgument() is gone for good
* New saving method allows for Layers to be passed as constructor arguments
* Parameter initializations/updates now go through layer functions initParameter and updateParameter
* bug fix: Loading a saved model will no longer trigger parameter reinitialisations
* bug fix: Precition accuracy used to be the same as the classification accuracy
* Added HeWeights and ScaledVarianceWeights initializations
* bug fix: GeometricEarlyStopping's patience is now truly reset when a better score is achieved
* refact: Output layers no longer need to have weights/bias
* feature: Outputlayer can now track the parameters of all layers in a network. Not only those that belong to branches that directly lead to them.
* feature: Layers now perform basic sanity checks.
* added test for Autoencode layer
* bug fix: _setShape() now gives a last chance to set the layers shape before initialization. Fixes a bug where weight matrices could be wrongly initiliazed when the input was a Composite layer
* bug fix: Added missing test outputs to Composite
* bug fix: Ensure that composite layers are always concatenanted in the same order
* Addded fcuntion for getting a layer inner and outer connections sorted in alphabetical order

1.0.2rc:
--------

* Fixed multiple inputs and added test
* Minor doc updates and cleaning
* printLog() of network works even in the model does not compile, and shows the exception message at the end

1.0.1rc:
--------
* Theano functions can now have several outputs. Model function no longer return an array, but an ordered dict where each key conrrespond to a given output
* Theano function wrapper will now need more arguments, such as the names given to each output
* Added accuracy functions such as: testAndAccuracy, and trainAndAccuracy that return both the score and the accuracy
* Updated trainer/recorder/stopCriteria to support function multiple outputs. They now have more parameters
* trainer now lets you define which function to use for train, test and validation 
* Added SavingRules (children of SavingRule_ABC) to decide when the model should be saved by the recorder. SavingRules are passed through the argument whenToSave
* Created SaveMin and SaveMax SavingRules
* EndOfTraining exceptions are now handeled independently from other exceptionin trainer.

1.0.0rc:
--------

* The begining of a new era for Mariana.
* There is as new abstraction type: initalialization (initializations.py).
* Added batch normalization layer.
* New Layer_ABC functions: getParameter, getParameterDict, getParameterNames, getParameterShape. The last one must be definded for initializations to work.
* GlorotTanhInit is now an initialization.
* Most abstractions now have a common interface.
* More consistent and sane layer implementation.
* All layers now have: activation, regularizations, initializations, learningScenario, decorators and name.
* Layer types have been moved to Network.
* Classifier_ABC is no more.
* New abstract class WeightBias_ABC.
* Networks now have a log, that can be pretty printed using printLog().
* saveOutputs argument is no more
* All layers now have propagate() model function that returns their outputs.
* Output layers can now also serve as hidden layers.
* ToHidden() and toOutput() are no more.
* SoftmaxClassifier() now has an accuracy function.
* AutoEncoder layer now takes a layer name as argument.
* Functions to save parameters of a network in npy or HDF5 formats.
* Save() is now based on clone()  and can now handle many layers and still uses pickle (Yeah I said that I am going to do something using HDF5 and JSON, but it is not worth the trouble).
* CloneBare() is no more.
* Clone() can now clone any layer based on the constructor arguments but you need to call the introspective self._setCreationArguments() at the end of the constructor. 
* Network.load() to load models saved by save().
* Embedding for Conv nets.
* Added example for hierarchical softmax.
* Many other things and little adjustements that make the code more beautiful.
