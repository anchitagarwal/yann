"""
Support for the implementation from

Goodfellow, Ian, Jean Pouget-Abadie, Mehdi Mirza, Bing Xu, David Warde-Farley, Sherjil Ozair,
Aaron Courville, and Yoshua Bengio. "Generative adversarial nets." In Advances in Neural Information
Processing Systems, pp. 2672-2680. 2014.

TODO:

    There seems to be something wrong with the fine-tuning update. Code crashes after a call to
    _new_era. This needs debugging and fixing.
"""
import time
import numpy
import theano.tensor as T
import theano
from collections import OrderedDict
import imp
try:
    imp.find_module('progressbar')
    progressbar_installed = True
except ImportError:
    progressbar_installed = False
if progressbar_installed is True:
    import progressbar
from yann.network import network
from yann.core.operators import copy_params

class gan (network):
    """
    This class is inherited from the network class and has its own methods modified in support of gan
    networks.

    Todo:
        Sumith Chintala says that its better to seperate generator and dataset when training 
        discriminator. Do that. 

        in __init__ kwargs = kwargs is not a good option Check its working.
        
    Args:
        Same as the network class
    """
    def __init__ (self, verbose = 2 ,**kwargs):
        super(gan,self).__init__(verbose = verbose, kwargs = kwargs)

    def initialize_train(self, verbose = 2):
        """
        Internal function that creates a train methods for the GAN network

        Args:
            verbose: as always
        """
        if verbose >=3:
            print("... creating the classifier training theano function ")

        #D_c(x)
        index = T.lscalar('index')
        if self.softmax_head is True:
            if self.cooked_datastream.svm is False:
                self.mini_batch_train_softmax = theano.function(
                        inputs = [index, self.cooked_softmax_optimizer.epoch],
                        outputs = self.dropout_softmax_cost,
                        name = 'train',
                        givens={
                self.x: self.data_x[index * self.mini_batch_size:(index + 1) * self.mini_batch_size],
                self.y: self.data_y[index * self.mini_batch_size:(index + 1) * self.mini_batch_size]},
                        updates = self.cooked_softmax_optimizer.updates,
                        on_unused_input = 'ignore')
            else:
                self.mini_batch_train_softmax = theano.function(
                        inputs = [index, self.cooked_softmax_optimizer.epoch],
                        outputs = self.dropout_softmax_cost,
                        name = 'train',
                        givens={
                self.x: self.data_x[ index * self.mini_batch_size:(index + 1) * self.mini_batch_size],
                self.one_hot_y: self.data_one_hot_y[index * self.mini_batch_size:(index + 1) *
                                                                        self.mini_batch_size]},
                        updates = self.cooked_softmax_optimizer.updates,
                        on_unused_input = 'ignore')

        #-0.5* log ( D(x) ) - 0.5* log ( 1- D (G (z)))
        self.mini_batch_train_discriminator = theano.function(
                inputs = [index, self.cooked_discriminator_optimizer.epoch],
                outputs = self.dropout_D_cost,
                name = 'train',
                givens={
        self.x: self.data_x[ index * self.mini_batch_size:(index + 1) * self.mini_batch_size] },
                updates = self.cooked_discriminator_optimizer.updates,
                on_unused_input = 'ignore')

        # -0.5 * log (D(G(z)))        
        self.mini_batch_train_generator = theano.function(
                inputs = [index, self.cooked_generator_optimizer.epoch],
                outputs = self.dropout_G_cost,
                name = 'train',
                givens={
        self.x: self.data_x[ index * self.mini_batch_size:(index + 1) * self.mini_batch_size]},
                updates = self.cooked_generator_optimizer.updates,
                on_unused_input = 'ignore')

        self.mini_batch_discriminator_probability = theano.function(
                inputs = [index],
                outputs = self.discriminator_probability,
                name = 'discriminator_probability',
                givens={
        self.x: self.data_x[ index * self.mini_batch_size:(index + 1) * self.mini_batch_size] },
                on_unused_input = 'ignore')

        self.mini_batch_generator_probability = theano.function(
                inputs = [index],
                outputs = self.generator_probability,
                name = 'generator_probability',
                givens={
        self.x: self.data_x[ index * self.mini_batch_size:(index + 1) * self.mini_batch_size] },
                on_unused_input = 'ignore')

    def cook_softmax_optimizer ( self, optimizer_params, verbose = 2):
        """
        This method cooks the softmax optimizer.

        Args:
            verbose: as always
        """
        optimizer_params["id"] = 'softmax_optimizer'
        if verbose >=3 :
            print("... Building the softmax classifier backprop network.")
        self.add_module( type = 'optimizer', params = optimizer_params, verbose =verbose )
        self.cooked_softmax_optimizer = self.optimizer["softmax_optimizer"]

        self._cook_optimizer(params = self.classifier_active_params,
                             objective = self.dropout_softmax_cost,
                             optimizer = self.cooked_softmax_optimizer,
                             verbose = verbose )
        self.softmax_learning_rate = self.learning_rate
        self.softmax_decay_learning_rate = self.decay_learning_rate
        self.softmax_current_momentum = self.current_momentum

    def cook_discriminator ( self, optimizer_params, verbose = 2):
        """
        This method cooks the real optimizer.

        Args:
            verbose: as always
        """
        optimizer_params["id"] = 'discriminator_optimizer'
        if verbose >=3 :
            print("... Building the real classifier backprop network.")
        self.add_module( type = 'optimizer', params = optimizer_params, verbose =verbose )
        self.cooked_discriminator_optimizer = self.optimizer["discriminator_optimizer"]

        self._cook_optimizer(params = self.discriminator_active_params,
                             objective = self.dropout_D_cost,
                             optimizer = self.cooked_discriminator_optimizer,
                             verbose = verbose )
        self.discriminator_learning_rate = self.learning_rate
        self.discriminator_decay_learning_rate = self.decay_learning_rate
        self.discriminator_current_momentum = self.current_momentum

    def cook_generator ( self, optimizer_params, verbose = 2):
        """
        This method cooks the fake optimizer.

        Args:
            verbose: as always
        """
        optimizer_params["id"] = 'generator_optimizer'
        if verbose >=3 :
            print("... Building the fake classifier backprop network.")
        self.add_module( type = 'optimizer', params = optimizer_params, verbose =verbose )
        self.cooked_generator_optimizer = self.optimizer["generator_optimizer"]

        self._cook_optimizer(params = self.generator_active_params,
                             objective = self.dropout_G_cost,
                             optimizer = self.cooked_generator_optimizer,
                             verbose = verbose )
        self.generator_learning_rate = self.learning_rate
        self.generator_decay_learning_rate = self.decay_learning_rate
        self.generator_current_momentum = self.current_momentum

    def cook( self,
                objective_layers,
                discriminator_layers,
                generator_layers,
                game_layers,                
                softmax_layer = None,
                classifier_layers = None,
                optimizer_params = None,
                verbose = 2,
                **kwargs ):
        """
        This function builds the backprop network, and makes the trainer, tester and validator
        theano functions. The trainer builds the trainers for a particular objective layer and
        optimizer.

        Args:
            optimizer_params: Supply optimizer_params.
            datastream: Supply which datastream to use.
                            Default is the last datastream created.
            visualizer: Supply a visualizer to cook with.

            objective_layers: Supply a tuple of layer ids of layers that have the objective
                              functions (classification, discriminator, generator)

            classifier: supply the classifier layer of the discriminator.
            discriminator: supply the discriminator layer of the data stream.
            generator: supply the last generator layer.
            generator_layers: list or tuple of all generator layers
            discriminator_layers: list or tuple of all discriminator layers
            classifier_layers: list or tuple of all classifier layers
            game_layers: list or tuple of two layers. The first is D(G(z)) and the second is D(x)
            verbose: Similar to the rest of the toolbox.


        """
        if verbose >= 2:
            print(".. Cooking the network")
        if verbose >= 3:
            print("... Building the network's objectives, gradients and backprop network")

        if not 'optimizer' in kwargs.keys():
            optimizer = None
        else:
            optimizer = kwargs['optimizer']

        if self.last_visualizer_created is None:
            visualizer_init_args = { }
            self.add_module(type = 'visualizer', params=visualizer_init_args, verbose = verbose)

        if not 'visualizer' in kwargs.keys():
            visualizer = self.last_visualizer_created
        else:
            visualizer = kwargs['visualizer']

        if not 'datastream' in kwargs.keys():
            datastream = None
        else:
            datastream = kwargs['datastream']

        if not 'resultor' in kwargs.keys():
            resultor = None
        else:
            resultor = kwargs['resultor']

        if not 'params' in kwargs.keys():
            params = None
        else:
            params = params

        self.network_type = 'gan'

        if datastream is None:
            if self.last_datastream_created is None:
                raise Exception("Cannot build trainer without having an datastream initialized")

            if verbose >= 3:
                print("... datastream not provided, assuming " + self.last_datastream_created)
            datastream = self.last_datastream_created
        else:
            if not datastream in self.datastream.keys():
                raise Exception ("Datastream " + datastream + " not found.")
        self.cooked_datastream = self.datastream[datastream]

        if resultor is None:
            if self.last_resultor_created is None:
                if verbose >= 3:
                    print('... No resultor setup, creating a defualt one.')
                self.add_module( type = 'resultor', verbose =verbose )
            else:
                if verbose >= 3:
                    print("... resultor not provided, assuming " + self.last_resultor_created)
            resultor = self.last_resultor_created
        else:
            if not resultor in self.resultor.keys():
                raise Exception ("Resultor " + resultor + " not found.")
        self.cooked_resultor = self.resultor[resultor]
        
        self.generator_active_params = []
        self.discriminator_active_params = []

        if objective_layers[0] is None:
            self.softmax_head = False
        else:
            self.softmax_head = True

        if self.softmax_head is True:
            self.classifier_active_params = []

        for lyr in generator_layers:
            self.generator_active_params = self.generator_active_params + \
                                           self.dropout_layers[lyr].active_params

        for lyr in discriminator_layers:
            self.discriminator_active_params = self.discriminator_active_params + \
                                               self.dropout_layers[lyr].active_params
        if self.softmax_head is True:
            for lyr in classifier_layers:
                self.classifier_active_params = self.classifier_active_params + \
                                                self.dropout_layers[lyr].active_params

        if optimizer_params is None:
            optimizer_params =  {
                            "momentum_type"       : 'false',
                            "momentum_params"     : (0.9, 0.95, 30),
                            "regularization"      : (0.000, 0.000),
                            "optimizer_type"      : 'sgd',
                                }

        if datastream is None:
            if self.last_datastream_created is None:
                raise Exception("Cannot build trainer without having an datastream initialized")

            if verbose >= 3:
                print("... datastream not provided, assuming " + self.last_datastream_created)
            datastream = self.last_datastream_created
        else:
            if not datastream in self.datastream.keys():
                raise Exception ("Datastream " + datastream + " not found.")

        self.cooked_datastream = self.datastream[datastream]
        self._cook_datastream(verbose = verbose)

        if game_layers is None:
            raise Exception("Need game layers")
        else:
            generator_sigmoid, discriminator_sigmoid = game_layers
            self.generator_probability = self.dropout_layers[generator_sigmoid].output
            self.discriminator_probability = self.dropout_layers[discriminator_sigmoid].output

        if self.softmax_head is True:
            self.data_y = self.cooked_datastream.data_y
            if self.cooked_datastream.svm is True:
                self.data_one_hot_y = self.cooked_datastream.data_one_hot_y
            self.y = self.cooked_datastream.y
            self.one_hot_y = self.cooked_datastream.one_hot_y
        self.current_data_type = self.cooked_datastream.current_type

        if self.softmax_head is True:
            self.softmax_cost = self.layers[objective_layers[0]].output
            self.dropout_softmax_cost = self.dropout_layers[objective_layers[0]].output

        self.D_cost = self.layers[objective_layers[1]].output
        self.dropout_D_cost = self.dropout_layers[objective_layers[1]].output
        self.G_cost = self.layers[objective_layers[2]].output
        self.dropout_G_cost = self.dropout_layers[objective_layers[2]].output

        self._cook_datastream(verbose = verbose)
        if self.softmax_head is True:
            self.cook_softmax_optimizer(optimizer_params = optimizer_params,
                                        verbose = verbose)
        self.cook_discriminator(   optimizer_params = optimizer_params,
                                    verbose = verbose)
        self.cook_generator(   optimizer_params = optimizer_params,
                                    verbose = verbose)
                                
        if self.softmax_head is True:
            self._initialize_test (classifier = softmax_layer,
                                   verbose = verbose)
            self._initialize_predict ( classifier = softmax_layer,
                                     verbose = verbose)
            self._initialize_posterior (classifier = softmax_layer,
                                       verbose = verbose)            
            self._initialize_confusion (classifier = softmax_layer,
                                    verbose = verbose)

        self.initialize_train ( verbose = verbose )
        self.validation_accuracy = []
        self.best_validation_errors = numpy.inf
        self.best_training_errors = numpy.inf
        self.training_accuracy = []
        self.best_params = []

        # Let's bother only about learnable params. This avoids the problem when weights are
        # shared
        if self.softmax_head is True:
            self.active_params = self.classifier_active_params + self.discriminator_active_params+\
                                    self.generator_active_params
        else:
            self.active_params = self.discriminator_active_params + self.generator_active_params

        for param in self.active_params:
            self.best_params.append(theano.shared(param.get_value(borrow = self.borrow)))

        self.gen_cost = []
        self.disc_cost = []
        self.softmax_cost = []
        self.cooked_visualizer = self.visualizer[visualizer]
        self._cook_resultor(resultor = self.cooked_resultor, verbose = verbose)        
        self._cook_visualizer(verbose = verbose) # always cook visualizer last.
        self.visualize (epoch = 0, verbose = verbose)
        # Cook Resultor.


    def _new_era ( self, new_learning_rate = 0.01, verbose = 2):
        """
        This re-initializes the learning rate to the learning rate variable. This also reinitializes
        the parameters of the network to best_params.

        Args:
            new_learning_rate: rate at which you want fine tuning to begin.
            verbose: Just as the rest of the toolbox.
        """
        if verbose >= 3:
            print("... setting up new era")
        if self.softmax_head is True:
            self.softmax_learning_rate.set_value(numpy.asarray(new_learning_rate,
                                                        dtype = theano.config.floatX))
        self.generator_learning_rate.set_value(numpy.asarray(new_learning_rate,
                                                        dtype = theano.config.floatX))
        self.discriminator_learning_rate.set_value(numpy.asarray(new_learning_rate,
                                                        dtype = theano.config.floatX))
        # copying and removing only active_params. Is that a porblem ?
        copy_params ( source = self.best_params, destination = self.active_params ,
                                                                            borrow = self.borrow)
    def print_status (self, epoch , verbose = 2):
        """
        This function prints the costs of the current epoch, learning rate and momentum of the
        network at the moment.

        Todo:
            This needs to to go to visualizer.

        Args:
            verbose: Just as always.
            epoch: Which epoch are we at ?
        """

        discriminator_probability = self.mini_batch_discriminator_probability(0)
        generator_probability = self.mini_batch_generator_probability(0)
        
        if self.cooked_datastream is None:
            raise Exception(" Cook first then run this.")

        if len(discriminator_probability) < self.batches2train * self.mini_batches_per_batch[0]:
            print(".. Discriminator Sigmoid D(x)   : " + str(discriminator_probability[-1]))
        else:
            print(".. Discriminator Sigmoid D(x)   : " + str(numpy.mean(\
             discriminator_probability[-1 * self.batches2train * self.mini_batches_per_batch[0]:])))

        if len(generator_probability) < self.batches2train * self.mini_batches_per_batch[0]:
            print(".. Generator Sigmoid D(G(z))         : " + str(generator_probability[-1]))
        else:
            print(".. Generator Sigmoid D(G(z))         : " + str(numpy.mean(\
                 generator_probability[-1 * self.batches2train * self.mini_batches_per_batch[0]:])))
        
        if verbose >= 3:
            print("... Learning Rate       : " + str(self.learning_rate.get_value(borrow=\
                                                                                 self.borrow)))
            print("... Momentum            : " + str(self.current_momentum(epoch)))

    def _create_layer_activities(self, datastream = None, verbose = 2):
        """
        Use this function to create activities for  each layer.
        I don't know why this might be useful, but its fun to check this out I guess. This will only
        work after the dataset is initialized.

        Used internally by ``cook`` method. Use the layer_activity

        Args:
            datastream: id of the datastream, Default is latest.
            verbose: as usual

        """
        if verbose >=3:
            print("... creating the activities of all layers ")

        if self.cooked_datastream is None:
           raise Exception ("This needs to be run only after network is cooked")

        index = T.lscalar('index')
        self.layer_activities_created = True
        for id, _layer in self.inference_layers.iteritems():
            if verbose >=3 :
                print("... collecting the activities of layer " + id)             
            activity = _layer.output            

            out = True
            """ This would avoid printing the layer that has only one output
            if len(_layer.output_shape) == 2:
                if _layer.output_shape[1] == 1:
                    out = False
            elif _layer.output_shape == (1,):
                out = False
            """
            if self.softmax_head is True and out is True:
                self.layer_activities[id] = theano.function(
                            name = 'layer_activity_' + id,
                            inputs = [index],
                            outputs = activity,
                            givens={
                            self.x: self.cooked_datastream.data_x[index *
                                            self.cooked_datastream.mini_batch_size:(index + 1) *
                                                        self.cooked_datastream.mini_batch_size],
                            self.y: self.cooked_datastream.data_y[index *
                                            self.cooked_datastream.mini_batch_size:(index + 1) *
                                                        self.cooked_datastream.mini_batch_size]},
                                            on_unused_input = 'ignore')
            elif out is True:
                self.layer_activities[id] = theano.function(
                            name = 'layer_activity_' + id,
                            inputs = [index],
                            outputs = activity,
                            givens={
                            self.x: self.cooked_datastream.data_x[index *
                                            self.cooked_datastream.mini_batch_size:(index + 1) *
                                                        self.cooked_datastream.mini_batch_size]},
                                                        on_unused_input = 'ignore')

    def validate (self, epoch = 0, training_accuracy = False, show_progress = False, verbose = 2):
        """
        Method is use to run validation. It will also load the validation dataset.

        Args:
            verbose: Just as always
            show_progress: Display progressbar ?
            training_accuracy: Do you want to print accuracy on the training set as well ?
        """
        if self.softmax_head is True:
            self.network_type = 'classifier'
            best, better = super(gan,self).validate(epoch = epoch,
                                    training_accuracy = training_accuracy,
                                    show_progress = show_progress,
                                    verbose = verbose)
        else:
            best = True
            better = True
        return (best, better)
    def train ( self, verbose, **kwargs):
        """
        Training function of the network. Calling this will begin training.

        Args:
            epochs: ``(num_epochs for each learning rate... )`` to train Default is ``(20, 20)``
            validate_after_epochs: 1, after how many epochs do you want to validate ?
            show_progress: default is ``True``, will display a clean progressbar.
                                If ``verbose`` is ``3`` or more - False
            early_terminate: ``True`` will allow early termination.
            k : how many discriminator updates for every generator update.
            learning_rates: (annealing_rate, learning_rates ... ) length must be one more than
                            ``epochs`` Default is ``(0.05, 0.01, 0.001)``
            save_after_epochs: 1, Save network after that many epochs of training.
            pre_train_discriminator: If you want to pre-train the discriminator to make it stay
                                    ahead of the generator for making predictions. This will only
                                    train the softmax layer loss and not the fake or real loss.


        """
        start_time = time.clock()

        if verbose >= 1:
            print(". Training")

        if self.cooked_datastream is None:
            raise Exception ("Cannot train without cooking the network first")

        if not 'epochs' in kwargs.keys():
            epochs = (20, 20)
        else:
            epochs = kwargs["epochs"]

        if not 'k' in kwargs.keys():
            k = 1
        else:
            k = kwargs["k"]

        if not 'validate_after_epochs' in kwargs.keys():
            self.validate_after_epochs = 1
        else:
            self.validate_after_epochs = kwargs["validate_after_epochs"]

        if not 'visualize_after_epochs' in kwargs.keys():
            self.visualize_after_epochs = self.validate_after_epochs
        else:
            self.visualize_after_epochs = kwargs['visualize_after_epochs']

        if not 'save_after_epochs' in kwargs.keys():
            self.save_after_epochs = self.validate_after_epochs
        else:
            self.save_after_epochs = kwargs['save_after_epochs']

        if not 'show_progress' in kwargs.keys():
            show_progress = True
        else:
            show_progress = kwargs["show_progress"]

        if progressbar_installed is False:
            show_progress = False

        if verbose == 3:
            show_progress = False

        if not 'training_accuracy' in kwargs.keys():
            training_accuracy = False
        else:
            training_accuracy = kwargs["training_accuracy"]

        if not 'early_terminate' in kwargs.keys():
            patience = 5
        else:
            if kwargs["early_terminate"] is True:
                patience = numpy.inf
            else:
                patience = 5

        if not 'pre_train_discriminator' in kwargs.keys():
            pre_train_discriminator = 0
        else:
            pre_train_discriminator = kwargs['pre_train_discriminator']

        # (initial_learning_rate, fine_tuning_learning_rate, annealing)
        if not 'learning_rates' in kwargs.keys():
            learning_rates = (0.05, 0.01, 0.001)
        else:
            learning_rates = kwargs["learning_rates"]

        # Just save some backup parameters
        nan_insurance = []
        for param in self.active_params:
            nan_insurance.append(theano.shared(param.get_value(borrow = self.borrow)))

        if self.softmax_head is True:
            self.softmax_learning_rate.set_value(learning_rates[1])
            
        patience_increase = 2
        improvement_threshold = 0.995
        best_iteration = 0
        epoch_counter = 0
        early_termination = False
        iteration= 0
        era = 0

        while (epoch_counter < pre_train_discriminator) \
                            and (not early_termination) \
                            and (self.softmax_head is True):

            nan_flag = False
            # This printing below and the progressbar should move to visualizer ?
            if verbose >= 1:
                print(".")
                if  verbose >= 2:
                    print("\n")
                    print(".. Pre-Training Epoch: " + str(epoch_counter))

            if show_progress is True:
                total_mini_batches =  self.batches2train * self.mini_batches_per_batch[0]
                bar = progressbar.ProgressBar(maxval=total_mini_batches, \
                        widgets=[progressbar.AnimatedMarker(), \
                ' training ', ' ', progressbar.Percentage(), ' ',progressbar.ETA(), ]).start()

            # Go through all the large batches
            total_mini_batches_done = 0
            for batch in xrange (self.batches2train):

                if nan_flag is True:
                    # If NAN, restart the epoch, forget the current epoch.
                    break
                # do multiple cached mini-batches in one loaded batch
                if self.cache is True:
                    self._cache_data ( batch = batch , type = 'train', verbose = verbose )
                else:
                    # If dataset is not cached but need to be loaded all at once, check if trianing.
                    if not self.current_data_type == 'train':
                        # If cache is False, then there is only one batch to load.
                        self._cache_data(batch = 0, type = 'train', verbose = verbose )

                # run through all mini-batches in new batch of data that was loaded.
                for minibatch in xrange(self.mini_batches_per_batch[0]):
                    # All important part of the training function. Batch Train.
                    # This is the classifier for discriminator. I will run this later.
                    softmax_cost = self.mini_batch_train_softmax (minibatch, epoch_counter)

                    if  numpy.isnan(softmax_cost):
                        nan_flag = True
                        new_lr = self.softmax_learning_rate.get_value( borrow = self.borrow ) * 0.1
                        self._new_era(new_learning_rate = new_lr, verbose =verbose )
                        if verbose >= 2:
                            print(".. NAN! Slowing learning rate by 10 times and restarting epoch.")
                        break

                    self.softmax_cost = self.softmax_cost + [softmax_cost]
                    total_mini_batches_done = total_mini_batches_done + 1

                    if show_progress is False and verbose >= 3:
                        print(".. Mini batch: " + str(total_mini_batches_done))
                        self.print_status(  epoch = epoch_counter, verbose = verbose )

                    if show_progress is True:
                        bar.update(total_mini_batches_done)

            if show_progress is True:
                bar.finish()

            # post training items for one loop of batches.
            if nan_flag is False:
                if verbose >= 2:
                    if len(self.softmax_cost) < self.batches2train * self.mini_batches_per_batch[0]:
                        print(".. Discriminator Softmax Cost       : " + str(self.softmax_cost[-1]))
                    else:
                        print(".. Discriminator Softmax Cost       : " + str(numpy.mean(
                                                            self.softmax_cost[-1 *
                                            self.batches2train * self.mini_batches_per_batch[0]:])))

                    if verbose >= 3:
                        print("... Learning Rate       : " + str(self.learning_rate.get_value(
                                                                             borrow=  self.borrow)))
                        print("... Momentum            : " + str(self.current_momentum(epoch)))

                best, better = self.validate(   epoch = epoch_counter,
                                        training_accuracy = training_accuracy,
                                        show_progress = show_progress,
                                        verbose = verbose )
                self.visualize ( epoch = epoch_counter , verbose = verbose)

                if best is True:
                    copy_params(source = self.active_params, destination= nan_insurance ,
                                                                    borrow = self.borrow,
                                                                    verbose = verbose)
                    copy_params(source = self.active_params, destination= self.best_params,
                                                                    borrow = self.borrow,
                                                                    verbose = verbose)


                    self.softmax_decay_learning_rate(learning_rates[0])

                if patience < epoch_counter:
                    early_termination = True
                    if final_era is False:
                        if verbose >= 3:
                            print("... Patience ran out lowering learning rate.")
                        new_lr = self.generator_learning_rate.get_value( borrow = self.borrow )*0.1
                        self._new_era(new_learning_rate = new_lr, verbose =verbose )
                        early_termination = False
                    else:
                        if verbose >= 2:
                            print(".. Early stopping")
                        break
                epoch_counter = epoch_counter + 1

        end_time = time.clock()
        if verbose >=2 and self.softmax_head is True:
            print(".. Pre- Training complete.Took " +str((end_time - start_time)/60) + " minutes")

        # Reset training for the main loop

        self.discriminator_learning_rate.set_value(learning_rates[1])
        self.generator_learning_rate.set_value(learning_rates[1])
        if self.softmax_head is True:
            self.softmax_learning_rate.set_value(learning_rates[1])
        
        patience_increase = 2
        patience = numpy.inf
        improvement_threshold = 0.995
        best_iteration = 0
        epoch_counter = 0
        early_termination = False
        iteration= 0
        era = 0

        if isinstance(epochs, int):
            total_epochs = epochs
            change_era = epochs + 1
        elif len(epochs) > 1:
            total_epochs = sum(epochs)
            change_era = epochs[era]
        else:
            total_epochs = epochs
            change_era = epochs + 1

        final_era = False
        gen_cost = 0.
        # main loop
        while (epoch_counter < total_epochs) and (not early_termination):
            nan_flag = False
            # check if its time for a new era.

            if (epoch_counter == change_era):
            # if final_era, while loop would have terminated.
                era = era + 1
                if era == len(epochs) - 1:
                    final_era = True
                if verbose >= 3:
                    print("... Begin era " + str(era))
                change_era = epoch_counter + epochs[era]
                if self.learning_rate.get_value(borrow = self.borrow) < learning_rates[era+1]:
                    if verbose >= 2:
                        print(".. Learning rate was already lower than specified. Not changing it.")
                    new_lr = self.generator_learning_rate.get_value(borrow = self.borrow)
                else:
                    new_lr = learning_rates[era+1]
                self._new_era(new_learning_rate = new_lr, verbose = verbose)

            # This printing below and the progressbar should move to visualizer ?
            if verbose >= 1:
                print(".")
                if  verbose >= 2:
                    print("\n")
                    print(".. Epoch: " + str(epoch_counter) + " Era: " +str(era))

            if show_progress is True:
                total_mini_batches =  self.batches2train * self.mini_batches_per_batch[0]
                bar = progressbar.ProgressBar(maxval=total_mini_batches, \
                        widgets=[progressbar.AnimatedMarker(), \
                ' training ', ' ', progressbar.Percentage(), ' ',progressbar.ETA(), ]).start()

            # Go through all the large batches
            total_mini_batches_done = 0
            for batch in xrange (self.batches2train):

                if nan_flag is True:
                    # If NAN, restart the epoch, forget the current epoch.
                    break
                # do multiple cached mini-batches in one loaded batch
                if self.cache is True:
                    self._cache_data ( batch = batch , type = 'train', verbose = verbose )
                else:
                    # If dataset is not cached but need to be loaded all at once, check if trianing.
                    if not self.current_data_type == 'train':
                        # If cache is False, then there is only one batch to load.
                        self._cache_data(batch = 0, type = 'train', verbose = verbose )

                # run through all mini-batches in new batch of data that was loaded.
                for minibatch in xrange(self.mini_batches_per_batch[0]):
                    # All important part of the training function. Batch Train.
                    # This is the classifier for discriminator. I will run this later.
                    if self.softmax_head is True:
                        softmax_cost = self.mini_batch_train_softmax (minibatch, epoch_counter)
                    disc_cost = self.mini_batch_train_discriminator (minibatch, epoch_counter)
                    if (minibatch + 1) * (batch + 1 ) * (epoch_counter + 1) % k == 0:
                        gen_cost = self.mini_batch_train_generator (minibatch, epoch_counter)

                    if numpy.isnan(gen_cost) or \
                        numpy.isnan(disc_cost):
                        nan_flag = True
                        new_lr = self.generator_learning_rate.get_value( borrow = self.borrow )*0.1
                        self._new_era(new_learning_rate = new_lr, verbose =verbose )
                        if verbose >= 2:
                            print(".. NAN! Slowing learning rate by 10 times and restarting epoch.")
                        break

                    self.disc_cost = self.disc_cost + [disc_cost]
                    self.gen_cost = self.gen_cost + [gen_cost]

                    if self.softmax_head is True:
                        self.softmax_cost = self.softmax_cost + [softmax_cost]

                    total_mini_batches_done = total_mini_batches_done + 1

                    if show_progress is False and verbose >= 3:
                        print(".. Mini batch: " + str(total_mini_batches_done))
                        self.print_status(  epoch = epoch_counter, verbose = verbose )

                    if show_progress is True:
                        bar.update(total_mini_batches_done)

            if show_progress is True:
                bar.finish()

            # post training items for one loop of batches.
            if nan_flag is False:
                if verbose >= 2:
                    self.print_status ( epoch = epoch_counter, verbose = verbose )

                best, better = self.validate(   epoch = epoch_counter,
                                        training_accuracy = training_accuracy,
                                        show_progress = show_progress,
                                        verbose = verbose )
                self.save_params ( epoch = epoch_counter, verbose = verbose )
                self.visualize ( epoch = epoch_counter , verbose = verbose)

                if best is True:
                    copy_params(source = self.active_params, destination= nan_insurance ,
                                                                    borrow = self.borrow,
                                                                    verbose = verbose)
                    copy_params(source = self.active_params, destination= self.best_params,
                                                                    borrow = self.borrow,
                                                                    verbose = verbose)

                self.discriminator_decay_learning_rate(learning_rates[0])
                self.generator_decay_learning_rate(learning_rates[0])
                if self.softmax_head is True:
                    self.softmax_decay_learning_rate(learning_rates[0])

                if patience < epoch_counter:
                    early_termination = True
                    if final_era is False:
                        if verbose >= 3:
                            print("... Patience ran out lowering learning rate.")
                        new_lr = self.fake_learning_rate.get_value( borrow = self.borrow ) * 0.1
                        self._new_era(new_learning_rate = new_lr, verbose =verbose )
                        early_termination = False
                    else:
                        if verbose >= 2:
                            print(".. Early stopping")
                        break
                epoch_counter = epoch_counter + 1

        end_time = time.clock()
        if verbose >=2 :
            print(".. Training complete.Took " +str((end_time - start_time)/60) + " minutes")