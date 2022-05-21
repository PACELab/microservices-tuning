from timeit import default_timer
from subprocess import Popen, PIPE
import pandas as pd
import numpy as np
import os
import time
import datetime
import pickle
import sys
import subprocess
import random
import threading

import stats
import config_to_docker_compose
import deploy_application
import generate_commands
import online_config_updater

from hyperopt import hp
from skopt.space import Integer, Real, Categorical
import nevergrad as ng


def run_online_config(result_folder, app_config_dir, app_config_iteration, cluster_config_dir, version, app, client, rps_list, iterations, cluster_number, collect_jaeger=False, online=False):
    """
    Returns the objective value for the current time window.
    """


def run_workload(duration):
    cmd = "./wrk2online/wrk -t 1 -c 4 -d 5400 -p 300 -L -s ./wrk2/scripts/social-network/compose-post.lua http://130.245.127.209:8080/wrk2-api//post/compose -R 150"
    p = Popen(cmd, stdout=PIPE, bufsize=1, universal_newlines=True, shell=True)
    i = 5
    while True:
        line = p.stdout.readline()
        if "0.950000" in line:
            reward = line.split()[0]
            with open(f"./{i}.latency", "w") as f:
                f.write(reward)
            i += 5

def run_config(result_folder, app_config_dir, app_config_iteration, cluster_config_dir, version, app, client, rps_list, iterations, cluster_number, collect_jaeger=False, online=False):
    """
    Runs each experiment 'iter' number of times at requests per second equal to each element in 'rps'
    Returns a csv file with statistics averaged across different iterations.
    """
    config_to_docker_compose.create_docker_compose_files(app_config_dir+"/"+str(
        app_config_iteration)+"_cluster.csv", cluster_config_dir, version, app, client, app_config_iteration, cluster_number)
    experiment_duration = 300
    starting_iteration = 0
    pause_time_seconds = 5
    app_folder_dict = {"SN": "socialNetwork", "MM": "mediaMicroservices",
                       "HR": "hotelReservation", "TT": "trainTicket"}
    host_mapping = {}
    with open(cluster_config_dir+"/" + version + "/host_roles.pkl", "rb") as host_roles_f:
        host_mapping = pickle.load(host_roles_f)
    # for default method, the same methods as carver can be implemented but they return nothing or the template csv file.
    for rps in rps_list:
        for retry_count in range(3):
            try:
                clean_and_deploy_app(
                    cluster_config_dir, version, app, cluster_number, host_mapping)
                break
            except Exception as e:
                print(e)
                print("Error deploying application. Retry count %d" %
                      retry_count)
                continue

        time.sleep(pause_time_seconds)
        os.chdir("./%s" %
                 app_folder_dict[app])
        # init_train_ticket()
        #init_social_networking(pause_time_seconds, host_mapping)
        os.chdir(".")
        print("Experiment: start %s" % datetime.datetime.now())
        # run 3+1 iteration of the experiment starting from "experiment_iteration"
        command_script = "generated_cmds_%s.sh" % str(cluster_number)
        # iterations +1 for the first dummy iteration
        generate_commands.generate_commands("results", version, "v_%s_%s" % (version, app_config_iteration), starting_iteration, iterations + 1,
                                            experiment_duration, [rps], command_script, app, host_mapping["monitor"], host_mapping["frontend"], "gsomashekar", collect_jaeger)
        #os.system("./genCmds.py results %s v_%s_%s %s %s %s %s %s %s %s %s gsomashekar %s" %(version, version, app_config_iteration, starting_iteration, iterations + 1, experiment_duration, rps,command_script, app, host_mapping["monitor"], host_mapping["frontend"], collect_jaeger))
        os.system("./%s" % command_script)
        print("Experiment: end %s" % datetime.datetime.now())
    try:
        stats.collect_stats(result_folder, version,
                            app_config_iteration, app, rps_list, iterations)
        stats.collect_stats_individual_requests(
            result_folder, version, app_config_iteration, app, rps_list, iterations)
    except:
        print("Error creating stats file. Did the experiment fail?")
    # can only run one experiment at an RPS
    # return get_objective_value(version, app_config_iteration, rps_list[0], "P_95" , 2)
    return get_objective_value(version, app_config_iteration, rps_list[0], 2, 95)


def init_train_ticket():
    os.system("./wrk2/wrk -t 1 -c 1 -d 2 -R 1 -L -s ./wrk2/scripts/train-ticket/auth.lua http://130.245.127.237:8080")
    with open("./admin_token.txt") as f:
        token = f.read()
        print(token)
    print("./wrk2/wrk -t 1 -c 1 -d 20 -R 3 -L -s ./wrk2/scripts/train-ticket/trains.lua http://130.245.127.237:8080 %s 100" % (token))
    os.system("./wrk2/wrk -t 1 -c 1 -d 20 -R 3 -L -s ./wrk2/scripts/train-ticket/trains.lua http://130.245.127.237:8080 %s 100" % (token))
    os.system("./wrk2/wrk -t 1 -c 1 -d 20 -R 3 -L -s ./wrk2/scripts/train-ticket/routes.lua http://130.245.127.237:8080 %s 100" % (token))
    os.system("./wrk2/wrk -t 1 -c 1 -d 20 -R 3 -L -s ./wrk2/scripts/train-ticket/travel.lua http://130.245.127.237:8080 %s 100" % (token))


def init_social_networking(pause_time_seconds, host_mapping):
    print("Init social graph: start %s" % datetime.datetime.now())
    os.system("python3 scripts/init_social_graph.py %s" %
              (host_mapping["frontend"]))
    print("Init social graph: end %s" % datetime.datetime.now())
    time.sleep(pause_time_seconds)
    print("Generating posts: start %s" % datetime.datetime.now())
    os.system("./scripts/genPosts.py %s 100 100 1 962" %
              (host_mapping["frontend"]))
    print("Generating posts: end %s" % datetime.datetime.now())
    time.sleep(pause_time_seconds)


def clean_and_deploy_app(cluster_config_dir, version, app, cluster_number, host_mapping):
    print("./clean_up.sh %s %s %s" % (cluster_config_dir + "/"+version+"/hostToConfig.log", str(cluster_number), app))
    print("Cleaning: start %s" % datetime.datetime.now())
    os.system("./clean_up.sh %s %s %s" % (cluster_config_dir +
                                          "/"+version+"/hostToConfig.log", str(cluster_number), app))
    print("Cleaning: end %s" % datetime.datetime.now())
    print("Deploying: start %s" % datetime.datetime.now())
    # The client IP of the current machine can be used instead of passing it from find_optimal....py but the client can be a different machine than the one where the script is running.
    deploy_application.deploy_app(
        cluster_config_dir+"/"+version, host_mapping["frontend"], host_mapping["client"], host_mapping["backend"], app, cluster_number)
    print("Deploying: end %s" % datetime.datetime.now())


def clean_config(config):
    """
    Optimizers can send config in different formats/types. This method converts types and formats to the ones expected by the downstream methods
    Example:
    1240.0 to 1240 (i.e floats that have 0 as decimal are converted to integers.)
    """
    for i, value in enumerate(config):
        # None is also NOT float
        if value is not None and isinstance(value, float) and value.is_integer():
            config[i] = int(config[i])
    return config

def online_apply_config(parameters_csv, config_template, current_config_index, config, app_config_dir, app):
    """
    """
    app_source_map = {"SN": "socialNetwork", "MM": "mediaMicroservices",
                      "HR": "hotelReservation", "TT": "trainTicket"}
    app_destination_map = {"SN": "social-network-microservices",
                           "MM": "media_microservices", "HR": "hotelReservation", "TT": "trainTicket"}

    try:
        critical_path_filename = app_config_dir + "/critical_path.txt"
        with open(critical_path_filename) as f:
            critical_path = f.read().splitlines()
    except Exception as e:
        print("Failed to read the critical path file %s" % e)
        sys.exit()
    parameters_df = pd.read_csv(parameters_csv)
    config_template_df = pd.read_csv(config_template)

    # config is chosen by an optimization module. Types have to be converted to the expected form
    config = clean_config(config)
    # Each column corresponds to one set of configuration
    parameters_df[current_config_index] = pd.Series(config, dtype=str)
    for index, row in config_template_df.iterrows():
        if row["microservice"] in critical_path:
            current_microservice_df = parameters_df[parameters_df.microservice ==
                                                    row.microservice]
            # sorry, this is too messy. But the goal is to get the formats shown in the method doc string
            if row["type"] == "mongo":
                pass
            else:
                # map the parameters config file in the volumes. The file is not present by default. So, the default
                # values will be used.
                if row["type"] == "service":
                    row["volumes"] = "~/uservices/DeathStarBench/%s/config/parameters-config.txt:/%s/config/parameters-config.txt" % (
                        app_source_map[app], app_destination_map[app])
                param_value = ["%s%s%s%s%s" % (current_helper_dict["param_prefix"], param, current_helper_dict["param_value_separator"], value, current_helper_dict["value_suffix"].get(
                    param, "")) for param, value in zip(current_microservice_df.parameter.values, current_microservice_df[current_config_index].values)]
                row["command"] = current_helper_dict["param_separator"].join(
                    param_value)
            config_template_df.loc[index, "command"] = row["command"]
    config_template_df.to_csv(
        app_config_dir+"/"+str(current_config_index)+"_cluster.csv")
    # Rewrite the new dataframe with an extra config column
    parameters_df.to_csv(parameters_csv, index=False)

def write_app_config_csv(parameters_csv, config_template, current_config_index, config, app_config_dir, app):
    """
    The values of the parameters are being written in the format expected by the subsystem for which the config is being applied.
    Except for nginx, which needs a modified .conf, the rest are written to the "command" column in the format they are expected 
    in the docker-compose file (the value written in the command tag of the docker-compose are the arguments passed to entry_point.sh 
    of different subsystems and this pattern is different across subsystems).
    Eg: The parameters for memcached:  "-m 1024 -c 20"
        The parameters for nginx:    "worker_process 10;worker_connections 1024"
        The parameters for redis: "--maxmemory 1024mb"
    """
    app_source_map = {"SN": "socialNetwork", "MM": "mediaMicroservices",
                      "HR": "hotelReservation", "TT": "trainTicket"}
    app_destination_map = {"SN": "social-network-microservices",
                           "MM": "media_microservices", "HR": "hotelReservation", "TT": "trainTicket"}
    helper_dict = {
        "frontend":
        {"param_prefix": "",
         "param_value_separator": " ",
         "value_suffix": {},
         "param_separator": ";"
         },
            "memcached":
                {"param_prefix": "-",
                 "param_value_separator": " ",
                 "value_suffix": {},
                 "param_separator": " "
                 },
            "mongo":
            {"param_prefix": {"wiredTigerConcurrentWriteTransactions": "--setParameter ", "wiredTigerConcurrentReadTransactions": "--setParameter "},  # default is "--"
                # default is " "
                "param_value_separator": {"wiredTigerConcurrentWriteTransactions": "=", "wiredTigerConcurrentReadTransactions": "="},
                "value_suffix": {},
                "param_separator": " "
             },
            "redis":
                {"param_prefix": "--",
                 "param_value_separator": " ",
                 "value_suffix": {"maxmemory": "mb"},
                 "param_separator": " "
                 },
            "mysql":
                {"param_prefix": "--",
                 "param_value_separator": "=",
                 "value_suffix": {},
                 "param_separator": " "
                 },
        "service":
        {"param_prefix": "",
         "param_value_separator": ",",
         "value_suffix": {},
         "param_separator": " "
         }
    }

    try:
        critical_path_filename = app_config_dir + "/critical_path.txt"
        with open(critical_path_filename) as f:
            critical_path = f.read().splitlines()
    except Exception as e:
        print("Failed to read the critical path file %s" % e)
        sys.exit()
    parameters_df = pd.read_csv(parameters_csv)
    config_template_df = pd.read_csv(config_template)

    # config is chosen by an optimization module. Types have to be converted to the expected form
    config = clean_config(config)
    # Each column corresponds to one set of configuration
    parameters_df[current_config_index] = pd.Series(config, dtype=str)
    for index, row in config_template_df.iterrows():
        if row["microservice"] in critical_path:
            current_helper_dict = helper_dict[row["type"]]
            current_microservice_df = parameters_df[parameters_df.microservice ==
                                                    row.microservice]
            # sorry, this is too messy. But the goal is to get the formats shown in the method doc string
            if row["type"] == "mongo":
                param_value = ["%s%s%s%s%s" % (current_helper_dict["param_prefix"].get(param, "--"), param, current_helper_dict["param_value_separator"].get(param, " "), value,
                                               current_helper_dict["value_suffix"].get(param, "")) for param, value in zip(current_microservice_df.parameter.values, current_microservice_df[current_config_index].values)]
                row["command"] = current_helper_dict["param_separator"].join(
                    param_value)
            else:
                # map the parameters config file in the volumes. The file is not present by default. So, the default
                # values will be used.
                if row["type"] == "service":
                    row["volumes"] = "~/uservices/DeathStarBench/%s/config/parameters-config.txt:/%s/config/parameters-config.txt" % (
                        app_source_map[app], app_destination_map[app])
                param_value = ["%s%s%s%s%s" % (current_helper_dict["param_prefix"], param, current_helper_dict["param_value_separator"], value, current_helper_dict["value_suffix"].get(
                    param, "")) for param, value in zip(current_microservice_df.parameter.values, current_microservice_df[current_config_index].values)]
                row["command"] = current_helper_dict["param_separator"].join(
                    param_value)
            config_template_df.loc[index, "command"] = row["command"]
    config_template_df.to_csv(
        app_config_dir+"/"+str(current_config_index)+"_cluster.csv")
    # Rewrite the new dataframe with an extra config column
    parameters_df.to_csv(parameters_csv, index=False)


# Specify the hyperopt domain space for all hyperparameters
def hyperopt_space(version, app):
    # The file ./configs/first_exp/social_networking_parameters.csv has all the parameters, their ranges, whether they are discrete, or continous etc. This can be used to build the create the space. The assumption should be that there is a csv file with a list of parameters, their ranges, etc and the below has to be created from it.
    # Does space have to a dictionary? -- Yes
    space = dict()
    paramOrder = []
    header = True
    app_dict = {"SN": "social_networking", "MM": "media_microservices",
                "HR": "hotel_reservation", "TT": "train_ticket"}
    file = open('./configs/%s/%s_parameters.csv' %
                (version, app_dict[app]))

    # code to create domain space by reading all the hyperparameters and their ranges from csv file
    for line in file:
        # skip the header
        if header:
            header = False
            continue

        contents = line.split(',')
        # microservice name and parameter concatenated using '-'
        param = contents[0] + '_' + contents[2]
        # 1. If categorical
        if contents[3].strip():
            prange = contents[6].strip().split(';')
            space[param] = hp.choice(param, [el for el in prange])
            paramOrder.append(param)
        # 2. If discrete
        elif contents[4].strip():
            prange = contents[6].strip().split(';')
            step = int(contents[7].split('.')[0]) if contents[7] else 1
            #space[param] = hp.quniform(param, int(prange[0]), int(prange[1]), step)
            space[param] = hp.randint(param, int(prange[0]), int(prange[1]))
            paramOrder.append(param)
        # 3. If float
        elif contents[5].strip():
            prange = contents[6].strip().split(';')
            space[param] = hp.uniform(
                param, float(prange[0]), float(prange[1]))
            paramOrder.append(param)
        # 4. If none of the above (no parameter values provided)
        else:
            space[param] = None
            paramOrder.append(param)
    return [space, paramOrder]


# Specify the skopt domain space for all hyperparameters
def skopt_space(version, app):
    # The file ./configs/first_exp/social_networking_parameters.csv has all the parameters, their ranges, whether they are discrete, or continous etc. This can be used to build the create the space. The assumption should be that there is a csv file with a list of parameters, their ranges, etc and the below has to be created from it.
    # Does space have to a dictionary? -- Yes
    space = []
    paramOrder = []
    header = True
    app_dict = {"SN": "social_networking", "MM": "media_microservices",
                "HR": "hotel_reservation", "TT": "train_ticket"}
    file = open('./configs/%s/%s_parameters.csv' %
                (version, app_dict[app]))

    # code to create domain space by reading all the hyperparameters and their ranges from csv file
    for line in file:
        # skip the header
        if header:
            header = False
            continue

        contents = line.split(',')
        # microservice name and parameter concatenated using '-'
        param = contents[0] + '_' + contents[2]
        # 1. If categorical
        if contents[3].strip():
            catgs = contents[6].strip().split(';')
            hyper = Categorical(catgs, name=param)
            space.append(hyper)
        # 2. If discrete
        elif contents[4].strip():
            prange = contents[6].strip().split(';')
            hyper = Integer(int(prange[0]), int(prange[1]), name=param)
            space.append(hyper)
        # 3. If float
        elif contents[5].strip():
            prange = contents[6].strip().split(';')
            hyper = Real(float(prange[0]), float(prange[1]), name=param)
            space.append(hyper)
        paramOrder.append(param)
    return [space, paramOrder]

# Helper method that forms the domain space for Nevergrad based optimizers.


def ng_domain_space(version, app):
    # The file ./configs/first_exp/social_networking_parameters.csv has all the parameters, their ranges, whether they are discrete, or continous etc. This can be used to build the create the space. The assumption should be that there is a csv file with a list of parameters, their ranges, etc and the below has to be created from it.
    # Does space have to a dictionary? -- Yes
    space = dict()
    paramOrder = []
    header = True
    app_dict = {"SN": "social_networking", "MM": "media_microservices",
                "HR": "hotel_reservation", "TT": "train_ticket"}
    file = open('./configs/%s/%s_parameters.csv' %
                (version, app_dict[app]))

    # code to create domain space by reading all the hyperparameters and their ranges from csv file
    for line in file:
        # skip the header
        if header:
            header = False
            continue

        contents = line.split(',')
        # microservice name and parameter concatenated using '-'
        param = contents[0] + '_' + contents[2]
        # 1. If categorical
        if contents[3].strip():
            prange = contents[6].strip().split(';')
            space[param] = ng.p.Choice(el for el in prange)
            paramOrder.append(param)
        # 2. If discrete
        elif contents[4].strip():
            prange = contents[6].strip().split(';')
            step = float(contents[7]) if contents[7] else 1
            choice_array = np.arange(int(prange[0]), int(prange[1]), step)
            space[param] = ng.p.Choice(choice for choice in choice_array)
            paramOrder.append(param)
        # 2. If float
        elif contents[5].strip():
            prange = contents[6].strip().split(';')
            step = float(contents[7])
            choice_array = np.arange(float(prange[0]), float(prange[1]), step)
            space[param] = ng.p.Choice(choice for choice in choice_array)
            paramOrder.append(param)
        # 3. If none of the above (no parameter values provided)
        else:
            space[param] = None
            paramOrder.append(param)

    instrum = ng.p.Instrumentation(**space)
    return [space, paramOrder, instrum]


def get_objective_value(version, config_iteration, rps, experiment_iteration, metric=95, online=False):
    result_folder = "./results/"
    if online:
        pass
    else:
        experiment_folder = result_folder + version + \
            "/v_%s_%d_rps%s/i1/" % (version, config_iteration, rps)
        result = subprocess.run(" cat %s/*_latencies.txt | datamash perc:%d 1 > %s/objective_value" %
                                (experiment_folder, metric, experiment_folder), stdout=subprocess.PIPE, shell=True)
        result = subprocess.run(" cat %s/*_latencies.txt | datamash perc:%d 1" %
                            (experiment_folder, metric), stdout=subprocess.PIPE, shell=True)
    try:
        # microseconds to milliseconds
        objective_value = float(result.stdout)/1000
    except Exception as e:
        print(e)
        print("result.stdout: %s" % result.stdout)
        objective_value = 10000.0
    return objective_value


def get_objective_value_old(version, config_iteration, rps, metric, experiment_iteration):
    """
    experiemnt iteration = 0 => summary across iterations
    1,2,3 correspond to indificual iterations in the summary stats file. 
    Since the first line has headers, experiment_iteration is the "index" of the line where the stats for iteration
    experiment_iteration is located (0 indexing XP) 
    This is crude but is efficient than using csv/pandas?? Check.
    """
    percentile_index_map = {'P_95': -2}
    result_folder = "./results/"
    summary_stats_file = result_folder + version + \
        "/v_%s_%d_rps%s/summary_merged_stats.csv" % (
            version, config_iteration, rps)
    with open(summary_stats_file) as f:
        value = f.readlines()[experiment_iteration].split(',')[
            percentile_index_map[metric]]
    return float(value)


def get_init_points(app, exp_type, sequence_number):
    config_folder = './configs'
    df = pd.read_csv("%s/%s_%s_random_samples.csv" %
                     (config_folder, app.lower(), exp_type), header=None)
    slice_columns = list(range((sequence_number - 1) * 3, sequence_number*3))
    return df[slice_columns]


def process_init_point(parameters_csv_file, config_values, dds=False):
    """
    Format the input for custom written algorithms like DDS.
    Off-the-shelf libraries have their own such modules.
    Convert categorical to list of indices, change data type.  
    """
    y = float(config_values[-1])
    x = []  # final x that will be passed back
    with open(parameters_csv_file) as parameters_csv_f:
        next(parameters_csv_f)
        for line, element in zip(parameters_csv_f, config_values[:-1]):
            contents = line.split(',')
            values_range = contents[6].strip().split(';')
            # categorical
            if contents[3].strip():
                if dds:
                    x.append(values_range.index(element))
                else:
                    x.append(str(element))
            # discrete
            elif contents[4].strip():
                x.append(int(element))
            # float
            elif contents[5].strip():
                x.append(float(element))
            else:
                pass  # the case where the parameter is not being tuned for this run

    return [x, y]

def online_optimizer_helper(args, sequence_number, current_model_iteration, config):
    app_file_suffix = {"SN": "social_networking", "MM": "media_microservices",
                       "HR": "hotel_reservation", "TT": "train_ticket"}
    app_folder_dict = {"SN": "socialNetwork", "MM": "mediaMicroservices",
                       "HR": "hotelReservation", "TT": "trainTicket"}
    version = args.main_version + "-%d" % sequence_number
    app_config_dir = os.path.join(args.config_folder, version)

    parameter_csv_file = app_file_suffix[args.app] + "_parameters.csv"
    configuration_csv_file = app_file_suffix[args.app] + "_config.csv"
    result_folder = "./results"

    # list of parameters, their ranges, etc.
    parameter_csv_path = os.path.join(app_config_dir, parameter_csv_file)
    # a template of the app deployment config
    configuration_csv_path = os.path.join(
        app_config_dir, configuration_csv_file)
    cluster_config_dir = "../DeathStarBench/%s/cluster_setups" % (
        app_folder_dict[args.app])    
    write_app_config_csv(parameter_csv_path, configuration_csv_path,
                         current_model_iteration, config, app_config_dir, args.app) 

def optimizer_helper(args, sequence_number, current_model_iteration, config):
    app_file_suffix = {"SN": "social_networking", "MM": "media_microservices",
                       "HR": "hotel_reservation", "TT": "train_ticket"}
    app_folder_dict = {"SN": "socialNetwork", "MM": "mediaMicroservices",
                       "HR": "hotelReservation", "TT": "trainTicket"}
    version = args.main_version + "-%d" % sequence_number
    app_config_dir = os.path.join(args.config_folder, version)

    parameter_csv_file = app_file_suffix[args.app] + "_parameters.csv"
    configuration_csv_file = app_file_suffix[args.app] + "_config.csv"
    result_folder = "./results"

    # list of parameters, their ranges, etc.
    parameter_csv_path = os.path.join(app_config_dir, parameter_csv_file)
    # a template of the app deployment config
    configuration_csv_path = os.path.join(
        app_config_dir, configuration_csv_file)
    cluster_config_dir = "../DeathStarBench/%s/cluster_setups" % (
        app_folder_dict[args.app])
    write_app_config_csv(parameter_csv_path, configuration_csv_path,
                         current_model_iteration, config, app_config_dir, args.app)
    return run_config(result_folder, app_config_dir, current_model_iteration, cluster_config_dir, version, args.app, args.client, args.rps_list, args.experiment_iterations, args.cluster_number)


def hybrid_helper(sequence_folder, app, n_samples, parameter_csv_path):
    # God will not forgive you for all these hardcodings
    """
    Get the points explored by DDS
    """
    rps_dict = {"SN": 700, "MM": 500, "TT": 50}
    result_folder = "./results/"
    perf = []
    for j in range(1, n_samples+1):
        objective_value_file = result_folder + sequence_folder + \
            "/v_%s_%d_rps%d" % (sequence_folder, j,
                                rps_dict[app]) + "/i1/objective_value"
        with open(objective_value_file) as f:
            perf.append(float(f.read())/1000)
    df = pd.read_csv(parameter_csv_path)
    config_file_indices = list(
        [str(i) for i in range(1, n_samples+1)])  # DDS so starts from 1
    result = df[config_file_indices]
    result.loc[len(result)] = perf
    return result


def test_objective(config):
    """
    test function to verify that the optimization works as expected before integrating
    """
    print(config)
    return random.randint(1, 100)


if __name__ == "__main__":
    # Unit tests for functions (move them to test scripts)
    print(get_objective_value("sn-default", 0, 700, 1, metric=95))
    # write_app_config_csv(parameters_csv,config_template,current_config_index,config,app_config_dir)
