
import numpy as np
import lightgbm as lgb

from hyperopt import hp, tpe, anneal, Trials, fmin, STATUS_OK
from hyperopt.pyll.stochastic import sample

import helper

class SimulatedAnnealing:
    # Initialize all the private variables.
    def __init__(self, n_iter, argv, cluster_number):
        # A Trials object stores the dictionary returned from the objective function
        self.simAnneal_trials = Trials()
        self.n_iter = n_iter
        self.argv = argv
        self.config_idx = -1
        self.domain_space = helper.hyperopt_space(argv[2])
        self.cluster_number = cluster_number
        # All the parameters that are required for the new objective function can be initialized using argv
        # See find_optimal_config.py to know how they are being created. Some are directly from the user arguments and some are being created using the user arguments.

    # Returns false when the BO execution has to stop. This could be
    # as simple as stopping after trying "n" samples
    def stop_config_generation(self):
        pass

    # Returns the next config from the list of configurations that BO picks
    def next_config(self):
        pass

    # Based on the result of the previously sampled point,
    # this method can be the one that checks the activation function,
    # updates posterior etc. Basically, the method that is called
    # after the sample configuration is run.
    def analysis(self):
        pass


    def optimize(self):
        # get the domain space for the hyperparameters
        space = self.domain_space[0]
        # Run optimization self.n_iter number of times
        # The best object that is returned from fmin contains the hyperparameters 
        # that yielded the lowest loss on the objective function
        # anneal.suggest uses simulated annealing algorithm to find the optimum parameters
        best = fmin(fn=self.objective, space=space, algo=anneal.suggest,
                    max_evals=self.n_iter, trials=self.simAnneal_trials, rstate=np.random.RandomState(50))
        #store the simAnneal_trials in the version folder.
        # TODO: return the simAnneal_trials object to find_optimal_config and access the results using .results attribute
        # which gives a list of dictionaries (can sort it on basis of loss to find optimum parameters)
        # TODO: can return "best" itself instead of simAnneal_trials
        
        # return best
        return self.simAnneal_trials
    
    def objective(self,hyperparameters):
        """
        config will be an array like [12,256,"on",....]. So from hyperparameters, we would have to create an array. If hyperparameters is a dictionary, we would have to create an ordered list by comparing it with the parameter_csv file. 
        """
        # creating config with ordered parameters
        config = []
        paramOrder = self.domain_space[1]
        for param in paramOrder:
            config.append(hyperparameters[param])
        
        self.config_idx += 1
        app_file_suffix = {"SN": "social_networking"}
        config_dir = self.argv[1]
        version = self.argv[2]
        app = self.argv[3]
        client = self.argv[4]
        rps_list = self.argv[5].split(',')
        iterations = int(self.argv[6])
        approach = self.argv[7]
        parameter_csv_file = app_file_suffix[app] + "_parameters.csv"
        configuration_csv_file = app_file_suffix[app] + "_config.csv"
        result_folder = "/home/ubuntu/uservices/uservices-perf-analysis/results"

        app_config_dir = config_dir + "/" + version
        parameter_csv_path = app_config_dir + "/" + parameter_csv_file  # list of parameters, their ranges, etc.
        configuration_csv_path = app_config_dir + "/" + configuration_csv_file  # a template of the app deployment config
        cluster_config_dir = "../DeathStarBench/socialNetwork/cluster_setups"
        helper.write_app_config_csv(parameter_csv_path, configuration_csv_path, self.config_idx, config, app_config_dir, app)
        objective_function_value = helper.run_config(result_folder, app_config_dir, self.config_idx, cluster_config_dir, version, app, client, rps_list, iterations, self.cluster_number)
        # we can take a weighted mixture or some other combination of metrics of different rps. Fow now, it will be only one RPS. So the first element in the rps_list
        #objective_function_value = test(config)
        return { 'loss': objective_function_value, 'params': hyperparameters, 'status': STATUS_OK}

    
