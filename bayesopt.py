#! /usr/bin/python3
"""
pip install scikit-optimize
"""
from skopt.utils import use_named_args
from skopt import gp_minimize, gbrt_minimize, forest_minimize
from timeit import default_timer as timer
import os

import helper


class BayesianOptimization:
    # Initialize all the private variables.
    def __init__(self, args, sequence_number, online=False, current_model_iteration=-1):
        self.args = args
        self.sequence_number = sequence_number
        # index of the current configuration. -1 before the method starts.
        self.current_model_iteration = current_model_iteration
        self.online = online
        self.current_sequence_folder = self.args.main_version + "-%d" % sequence_number
        # domain space for BO using skopt library. verison and app code are the input
        self.domain_space = helper.skopt_space(
            self.current_sequence_folder, self.args.app)
        if args.approach == "hybrid":
            self.surrogate_model = gp_minimize
        else:
            self.surrogate_model = {"gp": gp_minimize, "gbrt": gbrt_minimize,
                                    "forest": forest_minimize}[args.approach.split('-')[1]]
        self.total_time = 0

    def optimize(self):
        # get the domain space for the hyperparameters
        space = self.domain_space[0]
        start_time = None
        end_time = None

        # objective function as a nested function
        # use this decorator to correctly receive the parameters as a list

        @use_named_args(space)
        def objective(**hyperparameters):
            # uses the variable of the nesting function
            nonlocal start_time
            # roughly the end of the previous iteration
            end_time = timer()
            self.total_time = end_time - start_time
            config = []
            paramOrder = self.domain_space[1]
            # creating config with ordered parameters
            for param in paramOrder:
                if param not in hyperparameters:
                    config.append(None)
                else:
                    config.append(hyperparameters[param])

            # a new config has been created by the optimization method
            self.current_model_iteration += 1

            if self.online:
                objective_function_value = helper.online_optimizer_helper(
                    self.args, self.sequence_number, self.current_model_iteration, config)
            else:
                objective_function_value = helper.optimizer_helper(
                    self.args, self.sequence_number, self.current_model_iteration, config)
            # we can take a weighted mixture or some other combination of metrics of different rps. Fow now, it will be only one RPS. So the first element in the rps_list
            #objective_function_value = test(config)
            # The metric to be minimized is to be returned

            # roughly the beginning of the next iteration
            start_time = timer()
            return objective_function_value

        bad_configs = [[2, 1, 1, 1, 1.1], [
            64, 1, 1, 1, 1.1], [64, 1, 999, 1, 2]]
        # Run optimization self.iterations number of times
        #result = gp_minimize(objective, space, n_calls=self.args.iterations, n_initial_points=3, x0=bad_configs)

        # Beginning of the first iteration
        app_file_suffix = {"SN": "social_networking", "MM": "media_microservices",
                           "HR": "hotel_reservation", "TT": "train_ticket"}
        parameter_csv_file = app_file_suffix[self.args.app] + "_parameters.csv"
        start_time = timer()
        x_0 = []
        y_0 = []
        if self.args.init:
            parameter_csv_path = os.path.join(
                self.args.config_folder, self.current_sequence_folder, parameter_csv_file)

            if self.args.approach == "hybrid":
                # DDS has completed self.current_model_iteration number of iterations
                df = helper.hybrid_helper(
                    self.current_sequence_folder, self.args.app, self.current_model_iteration, parameter_csv_path)
            else:
                df = helper.get_init_points(
                    self.args.app, self.args.dimensionality_reduction, self.sequence_number)
            for column in df:
                x, y = helper.process_init_point(
                    parameter_csv_path, df[column].values)
                x_0.append(x)
                y_0.append(y)
            result = self.surrogate_model(objective, space, n_calls=(
                self.args.model_iterations-self.current_model_iteration + 1), n_initial_points=len(x_0), x0=x_0, y0=y_0, acq_func=self.args.acq_func)
        else:
            if self.args.test:
                #x, y = get_init_points_default(
                #     self.args.app, self.args.dimensionality_reduction)
                #x_0.append(x)
                #y_0.append(y)
                #result = self.surrogate_model(objective, space, n_calls=self.args.model_iterations-1,
                #                              n_initial_points=1, x0=x_0, y0=y_0, acq_func=self.args.acq_func)
                pass
            else:
                result = self.surrogate_model(
                    objective, space, n_calls=self.args.model_iterations, n_initial_points=3, acq_func=self.args.acq_func)

        # CherryPick
        #result = gp_minimize(objective, space, n_calls=self.model_iterations, n_initial_points = 3 , acq_func = "EI")
        # result contains the best parameters, min value, as well as all the
        # parameters and function value at those points

        time_file = "/home/ubuntu/uservices/uservices-perf-analysis/results/%s/time.txt" % (
            self.current_sequence_folder)
        with open(time_file, "w") as f:
            f.write(str(self.total_time/self.args.model_iterations))
        print("Optimization time per iteration %f" %
              (self.total_time/self.args.model_iterations))
        return result


def get_init_points_default(app, exp_type):
    point_dict = {"MM":
                  {
                      "all": ([24, 512, 32, 65536, 64, 1024, 20, 24, 1.25, 64, 1024, 20, 24, 1.25, 64, 1024, 20, 24, 1.25, 64, 1024, 20, 24, 1.25, 64, 1024, 20, 24, 1.25, 64, 1024, 20, 24, 1.25, 64, 1024, 20, 24, 1.25, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128,     19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 10000, 7, 5, 10, 128, 10000, 7, 5, 10, 128, 10000, 7, 5, 10, 128, 7, 480, 7, 480, 7, 480, 7, 480, 7,     480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480], 37.7),
                      "variability": ([24, 512, 32, 65536, 64, 1024, 20, 24, 1.25, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 10000, 7, 5, 10, 128, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, ], 37.7),
                      "bottleneck": ([24, 512, 32, 65536, 64, 1024, 20, 24, 1.25, 64, 1024, 20, 24, 1.25, 64, 1024, 20, 24, 1.25, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 10000, 7, 5, 10, 128, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, ], 37.7),
                      "critical_path": ([24, 512, 32, 65536, 64, 1024, 20, 24, 1.25, 64, 1024, 20, 24, 1.25, 64, 1024, 20, 24, 1.25, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, ], 37.7),
                      "critical_path_variability": ([24, 512, 32, 65536, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 7, 480, 7, 480], 37.7)
                  },
                  "SN":
                  {
                      "all": ([64, 1024,   20, 24, 1.25, 64, 1024,   20, 24, 1.25, 64, 1024,   20, 24, 1.25, 64, 1024,   20, 24, 1.25, 19.5, 128, 128, 19.5, 128, 128, 19.5, 128, 128, 19.5, 128, 128, 19.5, 128, 128, 19.5, 128, 128, 24, 512, 32, 65536, 24, 512, 32, 65536, 10000, 5, 10, 128, 10000, 5, 10, 128, 10000, 5, 10, 128, 10000, 5, 10, 128, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, 7, 480, 24], 30.1),
                      "variability": ([64, 1024,   20, 24, 1.25, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 24, 512, 32, 65536, 0, 10000, 7, 5, 10, 128, 10000, 7, 5, 10, 128, 7, 480], 50),
                      "bottleneck": ([64, 1024,   20, 24, 1.25, 19.5, 0, 1, 128, 128, 4, 512, 32, 65536, 0, 10000, 7, 5, 10, 128, 10000, 7, 5, 10, 128, 7, 480, 7, 480, 7, 480, 7, 480], 41.1),
                      "critical_path": ([64, 1024,   20, 24, 1.25, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 24, 512, 32, 65536, 0, 10000, 7, 5, 10, 128, 10000, 7, 5, 10, 128, 10000, 7, 5, 10, 128, 7, 480, 7, 480, 7, 480, 7, 480, 24], 41.1),
                      "critical_path_variability": ([64, 1024,   20, 24, 1.25, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 24, 512, 32, 65536, 0, 7, 480], 41.1),
                      # "nginx: ([24, 512, 32, 65536,0],36.9),
                      "redis": ([10000, 7, 5, 10, 128], 31.9),
                      "mongo": ([19.5, 0, 1, 128, 128], 31.87),
                      "cherrypick": ([4155, 1164, 73, 10, 1.4924712, 9.322325557, 1, 3, 174, 190, 4.171503672, 0, 1, 127, 116, 20, 1835, 14, 2260, 0, 14220, 4, 9, 92, 271, 13400, 4, 5, 68, 205, 13714, 0, 3, 76, 183, 40, 780, 21, 115, 17, 844, 14, 841, 4], 20.75)
                  },
                  "TT":
                  {
                      "all": ([24, 512, 32, 65536, 0, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 10000, 7, 5, 10, 128, ], 72.45),
                      "critical_path": ([19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128], 72.45),
                      "variability": ([19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128], 72.45),
                      "bottleneck": ([19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, ], 72.45),
                      "critical_path_variability": ([19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, 19.5, 0, 1, 128, 128, ], 72.45),
                  },
                  }
    return point_dict[app][exp_type]
