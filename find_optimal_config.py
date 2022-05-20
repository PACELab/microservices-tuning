import os
import sys
import argparse
from timeit import default_timer as timer
import pickle
import threading

import carver
import helper
import bayesopt
import hyperopt_algos
import pso
import dds
import pbr
import ucb
import genetic_opt
import cb
import config_to_docker_compose


def generic_method(approach_instance, parameter_csv_path, configuration_csv_path, app_config_dir, app, result_folder, cluster_config_dir, client, rps_list, iterations, cluster_number):
    total_time = 0
    number_iterations = 0
    while(not approach_instance.stop_config_generation("dummy")):
        
        start = timer()
        config = approach_instance.next_config()
        total_time += timer() - start
        number_iterations += 1
        helper.write_app_config_csv(parameter_csv_path, configuration_csv_path,
                                    approach_instance.current_config_index, config, app_config_dir, app)
        objective_function_value = helper.run_config(result_folder, app_config_dir, approach_instance.current_config_index,
                                                     cluster_config_dir, version, app, client, rps_list, iterations, cluster_number)
        approach_instance.analysis(objective_function_value)
    print("Execution per iteration %f" % (total_time/number_iterations))

def online_generic_method(approach_instance, parameter_csv_path, configuration_csv_path, app_config_dir, app, result_folder, cluster_config_dir, client, rps_list, iterations, cluster_number):
    total_time = 0
    number_iterations = 0
    while(not approach_instance.stop_config_generation("dummy")):
        
        start = timer()
        config = approach_instance.next_config()
        total_time += timer() - start
        number_iterations += 1
        helper.write_app_config_csv(parameter_csv_path, configuration_csv_path,
                                    approach_instance.current_config_index, config, app_config_dir, app)
        objective_function_value = helper.run_config(result_folder, app_config_dir, approach_instance.current_config_index,
                                                     cluster_config_dir, version, app, client, rps_list, iterations, cluster_number)
        approach_instance.analysis(objective_function_value)
    print("Execution per iteration %f" % (total_time/number_iterations))

def create_config_directory(config_dir, app, app_config_dir, dim_red):
    template_dict = {"SN": "sn-%s-temp", "HR": "hr-%s-temp",
                     "MM": "mm-%s-temp", "TT": "tt-%s-temp"}
    os.system("mkdir %s" % app_config_dir)
    os.system("cp -r %s/* %s/" % (os.path.join(config_dir,
              template_dict[app] % dim_red), app_config_dir))


def argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "config_folder", help="The folder where the details of the application are present")
    parser.add_argument(
        "main_version", help="The name for this round of experiments")
    parser.add_argument("app", help="The application being used", choices=[
                        "SN", "MM", "HR", "TT"])
    parser.add_argument(
        "cluster_number", help="The cluster on which the experiments are to be run.", choices=[1, 2], type=int)
    parser.add_argument(
        "approach", help="The optimization algorithm to be used")
    parser.add_argument(
        "--client", help="The IP of the client machine", default="130.245.127.132")
    parser.add_argument("--rps_list", "-r", "-R",
                        help="The rps list at which experiments are to be run", nargs="+", type=int)
    parser.add_argument("--experiment_iterations", "-ei",
                        help="The number of times the experiment is repeated for a given algorithm and config (0th iteration is run for cache warm-up", default=1, type=int)
    parser.add_argument("--model_iterations", "-mi",
                        help="The number of iterations the algorithm is run in each sequence", default=12, type=int)
    parser.add_argument("--sequence_count", "-sc",
                        help="The number of times the algorithm is rerun", default=2, type=int)
    parser.add_argument("--start_sequence", "-ss",
                        help="Starting sequence number", default=1, type=int)
    parser.add_argument("--dimensionality_reduction", "-d",
                        help="The dimensionality reduction method used", default="critical_path")
    parser.add_argument(
        "--acq_func", "-a", help="The acquisition function to be used with Bayesian methods", default="EI")
    parser.add_argument("--experiment_duration", "-ed",
                        help="The duration of the online experiment in minutes", default="60")
    parser.add_argument("--warmup_duration", "-wd",
                        help="The duration of the warump in minutes", default="30")
    parser.add_argument("--init", action="store_true",
                        help="Initialize the algorithm with user supplied points instead of library generated random samples.")
    parser.add_argument("--test", action="store_true",
                        help="Temporary flags that is used to test a feature conditionally.")
    parser.add_argument("--online", action="store_true",
                        help="If passed, the experiment is run online")
    parser.add_argument("--monitoring_interval",
                        help="The interval at which the config is changed", default="3")
    return parser.parse_args()


def online_deploy_app(args, result_folder, app_config_dir, app_config_iteration, cluster_config_dir, version):
    """
    """
    duration = 5400
    config_to_docker_compose.create_docker_compose_files(app_config_dir+"/"+str(
        app_config_iteration)+"_cluster.csv", cluster_config_dir, version, args.app, args.client, app_config_iteration, args.cluster_number)
    host_mapping = {}
    iterations = float(
        args.experiment_duration)//float(args.monitoring_interval)

    with open(cluster_config_dir+"/" + version + "/host_roles.pkl", "rb") as host_roles_f:
        host_mapping = pickle.load(host_roles_f)
    helper.clean_and_deploy_app(cluster_config_dir, version, args.app,
                                args.cluster_number, host_mapping)
    x = threading.Thread(target = helper.run_workload, args=(duration,))
    x.start()
    os.sleep("sleep 1800")


if __name__ == "__main__":
    # percentile_across_requests("/home/ubuntu/uservices/uservices-perf-analysis/results/first_exp/v0_rps100/i0","SN")
    # collect_stats("/home/ubuntu/uservices/uservices-perf-analysis/results","v11",0,"SN",[400],3)
    #analysis("/home/ubuntu/uservices/uservices-perf-analysis/results", "configs/first_exp", 15, "first_exp", "SN", [450,500])
    args = argument_parser()
    app_file_suffix = {"SN": "social_networking", "MM": "media_microservices",
                       "HR": "hotel_reservation", "TT": "train_ticket"}
    app_folder_dict = {"SN": "socialNetwork", "MM": "mediaMicroservices",
                       "HR": "hotelReservation", "TT": "trainTicket"}
    parameter_csv_file = app_file_suffix[args.app]+"_parameters.csv"
    configuration_csv_file = app_file_suffix[args.app] + "_config.csv"
    result_folder = "/home/ubuntu/uservices/uservices-perf-analysis/results"

    cluster_config_dir = "../DeathStarBench/%s/cluster_setups" % app_folder_dict[args.app]

    for sequence_number in range(args.start_sequence, args.sequence_count+1):
        version = args.main_version + "-%d" % (sequence_number)
        app_config_dir = os.path.join(args.config_folder, version)
        create_config_directory(
            args.config_folder, args.app, app_config_dir, args.dimensionality_reduction)
        # list of parameters, their ranges, etc
        parameter_csv_path = os.path.join(app_config_dir, parameter_csv_file)
        # a template of the app deployment config
        configuration_csv_path = os.path.join(
            app_config_dir, configuration_csv_file)
        if args.online:
            online_deploy_app(args, result_folder, app_config_dir,
                              0, cluster_config_dir, version)

            if args.approach == "default":
                helper.run_online_config(result_folder, app_config_dir, 0, cluster_config_dir, version, args.app, args.client, args.rps_list,
                              args.experiment_iterations, args.cluster_number, collect_jaeger=True)
            elif args.approach.startswith("bayesopt"):
                approach_instance = bayesopt.BayesianOptimization(
                    args, sequence_number, online=True)
                approach_instance.optimize()

        elif args.approach == "default":
            helper.run_config(result_folder, app_config_dir, 0, cluster_config_dir, version, args.app, args.client, args.rps_list,
                              args.experiment_iterations, args.cluster_number, collect_jaeger=True)  # run the config without any changes.

        elif args.approach == "default-dsb":
            helper.run_config(result_folder, app_config_dir, 0, cluster_config_dir, version, args.app, args.client, args.rps_list,
                              args.experiment_iterations, args.cluster_number, collect_jaeger=True)  # run the config without any changes.

        elif args.approach == "carver":
            approach_instance = carver.Carver(
                parameter_csv_path, args.rps_list, args.iterations, current_config_index=-1, num_samples=8, num_buckets=8)
            generic_method(approach_instance, parameter_csv_path, configuration_csv_path, app_config_dir, args.app,
                           result_folder, cluster_config_dir, args.client, args.rps_list, args.experiment_iterations, args.cluster_number)

        elif args.approach == "dds":
            approach_instance = dds.DDS(
                args, parameter_csv_path, sequence_number, r=0.2)
            generic_method(approach_instance, parameter_csv_path, configuration_csv_path, app_config_dir, args.app,
                           result_folder, cluster_config_dir, args.client, args.rps_list, args.experiment_iterations, args.cluster_number)

        elif args.approach.startswith("bayesopt"):
            approach_instance = bayesopt.BayesianOptimization(
                args, sequence_number)
            approach_instance.optimize()

        elif args.approach == "tpe":
            approach_instance = hyperopt_algos.HyperOptAlgos(
                args, sequence_number)
            approach_instance.optimize()

        elif args.approach == "sa":
            approach_instance = hyperopt_algos.HyperOptAlgos(
                args, sequence_number)
            approach_instance.optimize()
        elif args.approach == "pso":
            approach_instance = pso.Pso(args, sequence_number)
            approach_instance.optimize()
        elif args.approach == "genetic":
            approach_instance = genetic_opt.GeneticOpt(args, sequence_number)
            approach_instance.optimize()
        elif args.approach == "hybrid":
            dds_iter = 6
            args.model_iterations = dds_iter
            approach_instance = dds.DDS(
                args, parameter_csv_path, sequence_number, r=0.2)
            generic_method(approach_instance, parameter_csv_path, configuration_csv_path, app_config_dir, args.app,
                           result_folder, cluster_config_dir, args.client, args.rps_list, args.experiment_iterations, args.cluster_number)
            bo_iter = 15
            args.model_iterations = bo_iter
            approach_instance = bayesopt.BayesianOptimization(
                args, sequence_number, current_model_iteration=dds_iter)
            approach_instance.optimize()
        elif args.approach == "pbr":
            approach_instance = pbr.PBR(args, parameter_csv_path, configuration_csv_path,
                                        app_config_dir, result_folder, cluster_config_dir, version, sequence_number)
            generic_method(approach_instance, parameter_csv_path, configuration_csv_path, app_config_dir, args.app,
                           result_folder, cluster_config_dir, args.client, args.rps_list, args.experiment_iterations, args.cluster_number)
        elif args.approach == "ucb":
            approach_instance = ucb.UCB_MAB(args, parameter_csv_path, )
            generic_method(approach_instance, parameter_csv_path, configuration_csv_path, app_config_dir, args.app,
                           result_folder, cluster_config_dir, args.client, args.rps_list, args.experiment_iterations, args.cluster_number)
        elif args.approach == "cb":
            approach_instance = cb.CBZO(args, parameter_csv_path, )
            generic_method(approach_instance, parameter_csv_path, configuration_csv_path, app_config_dir, args.app,
                           result_folder, cluster_config_dir, args.client, args.rps_list, args.experiment_iterations, args.cluster_number)
        else:
            print("Invalid approach")
            sys.exit(0)
        try:
            os.mkdir(app_config_dir)
        except FileExistsError as e:
            print("Error %s occured while trying to create the version directory %s" % (
                e, app_config_dir))
