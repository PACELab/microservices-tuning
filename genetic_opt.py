import nevergrad as ng 
import numpy as np
import helper
from timeit import default_timer as timer

#for concurrent execution to arrive at result faster
from concurrent import futures

class GeneticOpt:
    # Initialize all the private variables.
    def __init__(self, args, sequence_number):
        self.args = args
        self.sequence_number = sequence_number
        self.current_model_iteration = -1 # index of the current configuration. -1 before the method starts.
        self.current_sequence_folder = self.args.main_version +"-%d"%sequence_number
        self.domain_space = helper.ng_domain_space(self.current_sequence_folder, self.args.app)
        self.total_time = 0
        self.start_time = 0
        self.end_time = 0
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
        # get the instrumentation to be passed as parameterization
        instrum = self.domain_space[2]
        # mutation -> gaussian 
        # crossover -> false 
        # tested on relatively smaller imput of similar types as in the perf-analysis config files.
        """
			The budget defines the number of iterations that can be performed by the optimizer 
			large budget corresponds to better results but more cost in terms of computation, as 
			the optimizer runs longer. 
			 
			The 'num_workers' parameter takes into the number of parallel processes that can be 
			taken up by the optimizer(i.e., the number of separate experiments in parallel)
			
			futures.ThreadPoolExecutor is used to utilize multithreading to make use of the num_workers 
			assigned to the optimizer, so that the number of experiments can be conducted in parallel. 
			
			the domain space is passed as parameters to the optimizer.
        """
        optimizer = ng.optimizers.OnePlusOne(parametrization=instrum, budget = self.args.model_iterations, num_workers = 1)
        self.start_time = timer()
        with futures.ThreadPoolExecutor(max_workers=optimizer.num_workers) as executor:
            recommendation = optimizer.minimize(self.objective, executor=executor, batch_mode=False)
        time_file = "./results/%s/time.txt"%(self.current_sequence_folder)
        with open(time_file,"w") as f:
             f.write(str(self.total_time/self.args.model_iterations))
        print("Optimization time per iteration %f" % (self.total_time/self.args.model_iterations))

        # extract values using recommendation.value
        return recommendation

    def objective(self,*unorderedparams, **hyperparameters):
        """
        config will be an array like [12,256,"on",....]. So from hyperparameters, we would have to create an array. If hyperparameters is a dictionary, we would have to create an ordered list by comparing it with the parameter_csv file. 
        """
        # creating config with ordered parameters
        # use the ordered parameters passed ny Nevergrad and map them with the parameter names that we have in paramOrder list.
        self.end_time = timer()
        self.total_time += self.end_time - self.start_time
        config = []
        paramOrder = self.domain_space[1]
        for param in paramOrder:
            if param not in hyperparameters:
                config.append(None)
            else:
                config.append(hyperparameters[param])
        
        self.current_model_iteration += 1 # a new config has been created by the optimization method

        objective_function_value = helper.optimizer_helper(self.args, self.sequence_number, self.current_model_iteration, config)
        # we can take a weighted mixture or some other combination of metrics of different rps. Fow now, it will be only one RPS. So the first element in the rps_list
        #objective_function_value = test(config)

        #We only need the object fn. value ~latency for optimizing using Genetic algo/PSO etc. 
        self.start_time = timer()
        return objective_function_value 

