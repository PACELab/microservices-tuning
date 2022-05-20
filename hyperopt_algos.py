#! /usr/bin/python3
"""
pip install lightgbm
pip install hyperopt
"""
import os
import numpy as np
import sys

from hyperopt import hp, anneal, tpe, Trials, fmin, STATUS_OK
from hyperopt.fmin import generate_trials_to_calculate
from hyperopt.pyll.stochastic import sample
from timeit import default_timer as timer 

import helper

class HyperOptAlgos:
    # Initialize all the private variables.
    def __init__(self, args, sequence_number):
        # A Trials object stores the dictionary returned from the objective function
        self.args = args
        self.sequence_number = sequence_number
        self.current_sequence_folder = self.args.main_version +"-%d"%sequence_number
        self.algorithm = {"sa": anneal.suggest, "tpe": tpe.suggest}[self.args.approach]
        self.current_model_iteration = -1 # index of the current configuration. -1 before the method starts.
        self.domain_space = helper.hyperopt_space(self.current_sequence_folder, self.args.app)
        self.total_time = 0
        self.start_time = None
        self.end_time = None
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
       print(space)
       # Run optimization self.num_iterations number of times
       # The best object that is returned from fmin contains the hyperparameters 
       # that yielded the lowest loss on the objective function
       
       # Start of the first iteration
       self.start_time = timer()
       if self.args.init:
           init_vals = []
           paramOrder = self.domain_space[1]
           app_file_suffix = {"SN": "social_networking", "MM": "media_microservices", "HR": "hotel_reservation", "TT": "train_ticket"}
           parameter_csv_file = app_file_suffix[self.args.app] + "_parameters.csv"
           start_time = timer()
           if self.args.init:
               parameter_csv_path = os.path.join(self.args.config_folder, self.current_sequence_folder, parameter_csv_file)
               df = helper.get_init_points(self.args.app, self.args.dimensionality_reduction, self.sequence_number)
               for column in df:
                   x, y = helper.process_init_point(parameter_csv_path, df[column].values)
                   i=0
                   init_dict = {}
                   for param in paramOrder:
                       if param.endswith('_'):
                           pass
                           #init_dict[param] = "" # a feature to cover for a bug has lead many other features that cover that bug. Mummy :(((
                       else:
                           init_dict[param] = x[i]
                           i += 1
                   init_vals.append(init_dict)
           trials = generate_trials_to_calculate(init_vals)
       else:
           trials = Trials()
       best = fmin(fn=self.objective, space=space, algo= self.algorithm,
                   max_evals=self.args.model_iterations, trials= trials, rstate=np.random.RandomState(50) )
       #store the bayes_trials in the version folder.
       # TODO: return the bayes_trials object to find_optimal_config and access the results using .results attribute
       # which gives a list of dictionaries (can sort it on basis of loss to find optimum parameters)
       # TODO: can return "best" itself instead of bayes_trials
       
       # return best
       time_file = "/home/ubuntu/uservices/uservices-perf-analysis/results/%s/time.txt"%(self.current_sequence_folder)
       with open(time_file,"w") as f:
           f.write(str(self.total_time/self.args.model_iterations))
       print("Optimization time per iteration %f" % (self.total_time/self.args.model_iterations))
    

    def objective(self,hyperparameters):
        """
        config will be an array like [12,256,"on",....]. So from hyperparameters, we would have to create an array. If hyperparameters is a dictionary, we would have to create an ordered list by comparing it with the parameter_csv file. 
        """
        # end of the first iteration approx
        self.end_time = timer()
        self.total_time += self.end_time - self.start_time 

        # creating config with ordered parameters
        config = []
        paramOrder = self.domain_space[1]
        for param in paramOrder:
            config.append(hyperparameters[param])
        self.current_model_iteration += 1 # a new config has been created by the optimization method
        objective_function_value = helper.optimizer_helper(self.args, self.sequence_number, self.current_model_iteration, config)
        # we can take a weighted mixture or some other combination of metrics of different rps. Fow now, it will be only one RPS. So the first element in the rps_list
        #objective_function_value = test(config)

        # approx beginning of the next iteration
        self.start_time = timer()
        return { 'loss': objective_function_value, 'params': hyperparameters, 'status': STATUS_OK} 
