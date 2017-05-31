from yann.network import network

def mlp ( dataset, verbose = 1 ):            
    """
    This method is a tutorial on building a two layer multi-layer neural network. The built
    network is mnist->800->800->10 .It optimizes with polyak momentum and rmsprop. 

    Args:
        dataset: an already created dataset.
    """
    optimizer_params =  {        
                "momentum_type"       : 'polyak',             
                "momentum_params"     : (0.65, 0.9, 30),      
                "regularization"      : (0.0001, 0.0001),       
                "optimizer_type"      : 'adagrad',                
                "id"                  : "main"
                        }

    dataset_params  = {
                            "dataset"   :  dataset,
                            "svm"       :  False, 
                            "n_classes" : 10,
                            "id"        : 'data'
                    }

    net = network(   borrow = True,
                     verbose = verbose )                       
    
    net.add_module ( type = 'optimizer',
                     params = optimizer_params, 
                     verbose = verbose )

    net.add_module ( type = 'datastream', 
                     params = dataset_params,
                     verbose = verbose )

    net.add_layer ( type = "input",
                    id = "input",
                    verbose = verbose, 
                    datastream_origin = 'data')
    
    net.add_layer ( type = "dot_product",
                    origin = "input",
                    id = "dot_product_1",
                    num_neurons = 800,
                    activation = 'relu',
                    verbose = verbose
                    )

    net.add_layer ( type = "dot_product",
                    origin = "dot_product_1",
                    id = "dot_product_2",
                    num_neurons = 800,                    
                    activation = 'relu',
                    verbose = verbose
                    ) 
    
    net.add_layer ( type = "classifier",
                    id = "softmax",
                    origin = "dot_product_2",
                    num_classes = 10,
                    activation = 'softmax',
                    verbose = verbose
                    )

    net.add_layer ( type = "objective",
                    id = "obj",
                    origin = "softmax",
                    verbose = verbose
                    )

    learning_rates = (0.05, 0.01, 0.001)  

    net.cook( optimizer = 'main',
              datastream = 'data',
              classifier = 'softmax',
              verbose = verbose
              )
    # from yann.utils.graph import draw_network
    # draw_network(net.graph, filename = 'mlp.png')    
    net.pretty_print()
    net.train( epochs = (20, 20), 
               validate_after_epochs = 1,
               training_accuracy = True,
               show_progress = True,
               early_terminate = True,
               learning_rates = learning_rates,               
               verbose = verbose)

    net.test(verbose = verbose)


## Boiler Plate ## 
if __name__ == '__main__':
    import sys
    dataset = None  
    if len(sys.argv) > 1:
        if sys.argv[1] == 'create_dataset':
            from yann.special.datasets import cook_mnist  
            data = cook_mnist (verbose = 3)
            dataset = data.dataset_location()
        else:
            dataset = sys.argv[1]
    else:
        print "provide dataset"
    
    if dataset is None:
        print " creating a new dataset to run through"
        from yann.special.datasets import cook_mnist  
        data = cook_mnist (verbose = 3)
        dataset = data.dataset_location()

    mlp ( dataset, verbose = 2 ) 

