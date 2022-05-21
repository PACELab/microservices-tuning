import numpy as np
import sys
import pandas as pd
import math
import random
from collections import OrderedDict

import helper

class DDS:
    def __init__(self, args, parameter_csv, sequence_number, r=0.2, sampling_choice= "random"):
       self.args = args
       self.parameter_csv = parameter_csv
       self.r = r
       self.current_config_index = 1
       self.sampling_choice = sampling_choice
       self.parameters_meta = self.generate_parameters_meta()
       self.tunable_parameters = self.generate_tunable_parameters_list()
       self.sequence_number = sequence_number
       self.x_best, self.f_best = self.init_best_random_point(self.args.app, self.args.dimensionality_reduction)
       self.x_new = []

    def init_best_random_point(self, app, exp_type):
        """
        Runs a set of initial points and selects the best of them for the algorithm to start with. This can be done
        using different sampling schemes or static samples.
        """
        if self.args.init and self.args.approach != "hybrid":
            df = helper.get_init_points(app, exp_type, self.sequence_number)
            best = df.iloc[-1,:].astype(float).idxmin() # column corresponding to the minimum objective value
            config_values = df[best].values
            init_point = helper.process_init_point(self.parameter_csv, config_values, dds=True)
        else:
            print("getting default")
            # get the default
            init_point = get_init_points_default(app, exp_type)
            print(init_point)
            print(len(init_point[0]))
        return init_point 

    def generate_parameters_meta(self):
        """
        Create metadata that will help the algorithm
        format: [ categorical, discrete, float, lower_limit, upper_limit, step, [values] ]
        """
        parameters_meta = OrderedDict()
        with open(self.parameter_csv) as parameters_csv_f:
            next(parameters_csv_f) #skip header
            for i, line in enumerate(parameters_csv_f):
                row = [None] * 7
                contents = line.split(',')
                key = contents[0] + '_' + contents[2] if contents[2] else contents[0] + '_' + str(i)
                values_range = contents[6].strip().split(';')
                # categorical
                if contents[3].strip():
                    row[0] = 1
                    row[3] = 0 #lower limit
                    row[4] = len(values_range) - 1 #upper limit
                    row[6] = values_range
                # discrete
                elif contents[4].strip():
                    row[1] = 1
                    row[3] = int(values_range[0])
                    row[4] = int(values_range[1])
                    row[5] = int(contents[7].split('.')[0]) if contents[7] else 1
                #float
                elif contents[5].strip():
                    row[2] = 1
                    row[3] = float(values_range[0])
                    row[4] = float(values_range[1])
                parameters_meta[key] = row # all values will be None if the parameter is not being tuned.
        return parameters_meta

    def generate_tunable_parameters_list(self):
        """
        This creates a list containing a subset of those parameters that are requested to be tuned. The parameters_csv
        also has parameters that are placeholders because of how the interfaces have been designed.
        """
        tunable_parameters = []
        for key in self.parameters_meta:
            # if any of the fields are set, that parameter is being tuned
            if any(self.parameters_meta[key]):
                tunable_parameters.append(key)
        return tunable_parameters

    def stop_config_generation(self,stats_file):
        """
        Signals the end of optimization
        """
        return self.current_config_index > self.args.model_iterations

    def get_d_inclusion_mask(self, p):
        """
        Each dimension is included with probability "p"
        """
        return [True if random.uniform(0, 1) > p else False for _ in self.tunable_parameters]

    def find_next_x_helper(self,i, x_i_best):
        current_parameter_meta = self.parameters_meta[self.tunable_parameters[i]]
        # index 4 is max and 3 is min. So r * (max-min) * N(0,1). For categorical, it is 0 and len(values)-1
        lower_limit = current_parameter_meta[3]
        upper_limit = current_parameter_meta[4]
        perturbation = self.r * (upper_limit - lower_limit) * np.random.normal()
        x_i_new = x_i_best + perturbation
        
        # categorical or discrete. For categorical, only tuning the indices of the values list
        if not current_parameter_meta[2]:
            # randomly choose ceil and floor. Otherwise boundary values will not get selected.
            round_int_function = [math.ceil, math.floor][random.randint(0,1)]
            x_i_new = round_int_function(x_i_new)
    
        # mirroring the perturbation.
        if x_i_new < lower_limit:
            x_i_new = lower_limit + lower_limit - x_i_new
            if x_i_new > upper_limit:
                x_i_new = lower_limit
        if x_i_new > upper_limit:
            x_i_new = upper_limit - (x_i_new - upper_limit)
            if x_i_new < lower_limit:
                x_i_new = upper_limit
        return x_i_new
    
    def find_next_x(self,dimensions_inclusion_mask):
        x_new = []
        print(len(dimensions_inclusion_mask))
        for i, value in enumerate(dimensions_inclusion_mask):
            if value:
                x_new.append(self.find_next_x_helper(i, self.x_best[i]))
            else: # same as before as this dimension is not being tuned
                x_new.append(self.x_best[i])
        return x_new

    def format_config(self):
        """
        The config generated by the algorithm is converted to the format that is expected by the interfaces of the next
        stage. For example, for categorical values, we are just tuning the indices of the list of allowed values. That
        index has to be convered to the actual categorical value.
        """
        configs = []
        for i,key in enumerate(self.parameters_meta):
            if key in self.tunable_parameters:
                index = self.tunable_parameters.index(key)
                if self.parameters_meta[key][0]: #categorical
                    # for categorical, the value being tuned is the index in the list of allowed values
                    # index 6 of the meta data structure has the list of allowed values
                    configs.append(self.parameters_meta[key][6][self.x_new[index]])
                else:
                    configs.append(self.x_new[index])
            else: # these were not requested to be tuned
                configs.append(None)
        return configs

    def next_config(self):
        p = 1 - math.log(self.current_config_index)/math.log(self.args.model_iterations)
        dimensions_inclusion_mask = self.get_d_inclusion_mask(p)
        # choose a random dimension if all dimensions are excluded
        if not any(dimensions_inclusion_mask ):
            dimensions_inclusion_mask[random.randint(0,len(dimensions_inclusion_mask) - 1)] = True
        self.x_new = self.find_next_x(dimensions_inclusion_mask)
        return self.format_config()

    def analysis(self,f_new):
        if f_new < self.f_best:
            self.f_best = f_new
            self.x_best = self.x_new
        self.current_config_index += 1
        print("Best parameters: %s \nFunction value %f"%(self.x_best, self.f_best))


def test_f(configs):
    print(configs)
    return random.randint(1,100)


def get_init_points_default(app, exp_type):
    point_dict = {        "MM": 
                {
                "all": ([24, 512, 32, 65536, 64, 1024, 20, 24, 1.25, 64, 1024, 20, 24, 1.25, 64, 1024, 20, 24, 1.25, 64, 1024, 20, 24, 1.25, 64, 1024, 20, 24, 1.25, 64, 1024, 20, 24, 1.25, 64, 1024, 20, 24, 1.25, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128,     19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 10000, 7, 5, 10, 128, 10000, 7, 5, 10, 128, 10000, 7, 5, 10, 128, 7, 480, 7, 480, 7, 480, 7, 480, 7,     480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480], 37.7),
                "variability": ([24, 512, 32, 65536,64, 1024, 20, 24, 1.25,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,10000, 7, 5, 10, 128,7, 480,7, 480,7, 480,7, 480,7, 480,7, 480,7, 480,7, 480,],37.7),
                "bottleneck" : ([24, 512, 32, 65536,64, 1024, 20, 24, 1.25,64, 1024, 20, 24, 1.25,64, 1024, 20, 24, 1.25,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,10000, 7, 5, 10, 128,7, 480,7, 480,7, 480,7, 480,7, 480,7, 480,7, 480,7, 480,],37.7),
                "critical_path": ([ 24, 512, 32, 65536, 64, 1024, 20, 24, 1.25, 64, 1024, 20, 24, 1.25, 64, 1024, 20, 24, 1.25,19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 7, 480,7, 480,7, 480,7, 480,7, 480,7, 480,7, 480,], 37.7),
                "critical_path_variability": ([24, 512, 32, 65536,19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128,7, 480,7, 480],37.7)
                },
            "SN":
                {
                "all" : ([64, 1024,   20, 24, 1.25, 64, 1024,   20, 24, 1.25,64, 1024,   20, 24, 1.25,64, 1024,   20, 24, 1.25, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128, 24, 512, 32, 65536, 0, 24, 512, 32, 65536, 0, 10000, 7, 5, 10, 128,10000, 7, 5, 10, 128,10000, 7, 5, 10, 128,10000, 7, 5, 10, 128, 7, 480, 7, 480 ,7, 480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480,7, 480,7, 480,7, 480,24],50),
                "variability" : ([64, 1024,   20, 24, 1.25, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 24, 512, 32, 65536, 0, 10000, 7, 5, 10, 128,10000, 7, 5, 10, 128, 7, 480],50),
                "bottleneck" : ([64, 1024,   20, 24, 1.25, 19.5, 0, 1, 128, 128,4, 512, 32, 65536, 0,10000, 7, 5, 10, 128,10000, 7, 5, 10, 128, 7, 480, 7, 480,7, 480, 7, 480], 41.1),
                "critical_path" : ([64, 1024,   20, 24, 1.25, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 24, 512, 32, 65536, 0, 10000, 7, 5, 10, 128,10000, 7, 5, 10, 128,10000, 7, 5, 10, 128, 7, 480, 7, 480 ,7, 480, 7, 480, 24],41.1),
                "critical_path_variability":([64, 1024,   20, 24, 1.25, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128,24, 512, 32, 65536, 0,7, 480], 41.1),
                #"nginx: ([24, 512, 32, 65536,0],36.9),
                "redis": ([10000, 7, 5, 10, 128],31.9),
                "mongo" : ([19.5, 0, 1, 128, 128],31.87),
                "cherrypick" : ([4155,1164,73,10,1.4924712,9.322325557,1,3,174,190,4.171503672,0,1,127,116,20,1835,14,2260,0,14220,4,9,92,271,13400,4,5,68,205,13714,0,3,76,183,40,780,21,115,17,844,14,841,4],20.75)
                },
            "TT":
                {
                "all":([24, 512, 32, 65536, 0,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,10000, 7, 5, 10, 128,], 72.45),
                "critical_path":([19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128], 72.45),
                "variability": ([19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128],72.45),
                "bottleneck": ([19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,],72.45),
                "critical_path_variability": ([19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,19.5, 0, 1, 128, 128,],72.45),
                },
            }
    return point_dict[app][exp_type]

if __name__ == "__main__":
    """
    test_object = DDS('./configs/all/social_networking_parameters.csv')
    while( not test_object.stop_config_generation("/dev/null")):
        configs = test_object.next_config()
        f_new = test_f(configs)
        test_object.analysis(f_new)
    """

