#! /usr/bin/python3
# This module converts a configuration chosen by the previous step into docker-compose.yaml and .conf files 
# that help in deploying the application with the required configuration. Since the assumption is that only the 
# configuration is available in the csv format, this module also creates the version folder with necessart files 
# in the cluster_setups folder.
import sys
import re
import platform
import yaml
import pandas as pd
import subprocess
import os
import json
import pickle

def create_cluster_config(config,cluster_setup_folder,version,app_config_iteration):
    """
    Creates a mapping between the host and the docker compose file that should be deployed on the host.
    This mapping file and all the docker-compose files are moved to application's cluster_config folder.
    """
    unique_hosts = config.host.unique()
    host_config_file = cluster_setup_folder + "/" + version + "/hostToConfig.log"
    try:
        os.mkdir(cluster_setup_folder + "/" + version)
    except FileExistsError as e:
        print("Error %s while creating cluster config folder"%e)
    with open(host_config_file,"w") as host_config_f:
        for host in unique_hosts:
            host_config_f.write("%s,docker-compose-%s-%s.yaml\n"%(host,host,app_config_iteration))

def create_and_return_host_roles(config,cluster_setup_folder,version,client):
    """
        Saves a pickle file in the cluster config folder that maps the VMs with the roles they play.
        Eg: muserv1:frontend
        muserv2:monitor
        muserv3:client/load generator
    """
    host_mapping = {}
    host_roles_file = cluster_setup_folder + "/" + version + "/host_roles.pkl" 
    with open(host_roles_file,"wb") as host_roles_f:
       host_mapping["frontend"] = config[config.type=="frontend"]["host"].iloc[0]
       host_mapping["monitor"] = config[config.type=="monitor"]["host"].iloc[0]
       host_mapping["services"] = config[config.type=="service"]["host"].iloc[0]
       host_mapping["backend"] = config[config.type=="mongo"]["host"].iloc[0]
       host_mapping["client"] = client
       host_mapping["all_hosts"] = config.host.unique().tolist() 
       pickle.dump(host_mapping,host_roles_f)
    return host_mapping

def init_nginx_conf(app,frontend_host):
    """
    create_frontend_configfile(...) is not called unless the command field has any input. For "default", this is the case. In future, there coudl be more such cases.
    This method ensures the nginx.temp of the previous run is replaced by the template file as that has the default config for nginx.
    """
    app_folder_dict = {"SN":"socialNetwork", "MM": "mediaMicroservices", "HR":"hotelReservation","TT":"trainTicket"}
    config_template_file = "/home/ubuntu/uservices/uservices-perf-analysis/nginx_config/%s_nginx_frontend.template"%app_folder_dict[app];
    remote_destination_folder ="/home/ubuntu/uservices/DeathStarBench/%s/nginx-web-server/conf/"%app_folder_dict[app];
    subprocess.run("scp -i ~/compass.key %s ubuntu@%s:%s/nginx.temp"%(config_template_file, frontend_host, remote_destination_folder ),shell=True)
     
    config_template_file = "/home/ubuntu/uservices/uservices-perf-analysis/nginx_config/%s_nginx_media.template"%app_folder_dict[app];
    remote_destination_folder ="/home/ubuntu/uservices/DeathStarBench/%s/media-frontend/conf/"%app_folder_dict[app];
    subprocess.run("scp -i ~/compass.key %s ubuntu@%s:%s/nginx.temp"%(config_template_file, frontend_host, remote_destination_folder ),shell=True)
    
    config_template_file = "/home/ubuntu/uservices/uservices-perf-analysis/nginx_config/%s_nginx_frontend.template"%app_folder_dict[app];
    remote_destination_folder ="/home/ubuntu/uservices/DeathStarBench/%s/ts-ui-dashboard/"%app_folder_dict[app];
    subprocess.run("scp -i ~/compass.key %s ubuntu@%s:%s/nginx.temp"%(config_template_file, frontend_host, remote_destination_folder ),shell=True)

def create_frontend_configfile(frontend_name,frontend_host,config_options,version,app, output_folder):
    """
    The docker-compose.yml file mounts the config file nginx.temp
    nginx.temp is created in this method by modifying the template config in nginx.template
    """
    # Create a dictionary of parameter and value. TODO: have the param,value pair in the csv in dictionary format. eval() can be used to parse it directly.
    param_dict = {}
    for config in config_options.split(';'):
        parameter,value = config.split(' ')
        param_dict[parameter] = value

    # check if nginx parameters are set. worker_processes will always be set.
    if "worker_processes" not in param_dict:
        return

    app_folder_dict = {"SN":"socialNetwork", "MM": "mediaMicroservices","HR":"hotelReservation","TT":"trainTicket"}
    config_template_file = "/home/ubuntu/uservices/uservices-perf-analysis/nginx_config/%s_nginx_frontend.template"%app_folder_dict[app];
    remote_destination_folder ="/home/ubuntu/uservices/DeathStarBench/%s/nginx-web-server/conf/"%app_folder_dict[app];

    json_config_events_block_index = 1 # The media-frontend and the nginx frontend have different configs. The events block is the first element in media-frontend and the second element in the nginx frontend.
    if frontend_name == "media-frontend":
        config_template_file = "/home/ubuntu/uservices/uservices-perf-analysis/nginx_config/%s_nginx_media.template"%app_folder_dict[app];
        remote_destination_folder ="/home/ubuntu/uservices/DeathStarBench/%s/media-frontend/conf/"%app_folder_dict[app];
        json_config_events_block_index = 0

    config_directory = os.path.dirname(config_template_file)
    #config_json_file = config_file.replace('template','json')
    config_json_file = output_folder + "/" + config_template_file.split('/')[-1].replace("template", "json")
   
    #pip install crossplane. Check https://github.com/nginxinc/crossplane
    try:
        subprocess.run("crossplane parse %s -o %s"%(config_template_file, config_json_file),shell=True)#create a json file from the nginx config template 
    except:
        print("Check if crossplace is installed: pip3 install crossplace")
        sys.exit()

    with open(config_json_file) as config_json_f:
        config_json = json.loads(config_json_f.read())
    config_json["config"][0]["file"] = "nginx.temp" 


    #Event related configs. In nginx.template, index 1 in the parsed list of configs is events config. This is because the events block is the second parameter in nginx.template file.
    # Changing the order in that file will change the parameter order. Similarly for the other parameters.
    # TODO: If media_frontend or other apps are used, the below for loop approach is better. 
    
    offset = json_config_events_block_index
    config_json_parsed= config_json["config"][0]["parsed"]
    config_json_parsed[0 + offset]["block"][0]["args"] = [param_dict["worker_connections"]]
    config_json_parsed[1 + offset]["args"] = [param_dict["worker_processes"]]
    if "threads" in param_dict and "max_queue" in param_dict:
        config_json_parsed[2 + offset]["args"] = ["thread1","threads=%s"%param_dict["threads"],"max_queue=%s"%param_dict["max_queue"]]

    #if  not ("mm" in version or "100" in version or "init" in version):
    #    config_json_parsed[3 + offset]["block"][6 + offset]["args"] = [param_dict["tcp_nodelay"]] # just made tcpnodelay as the 6th arg in nginx_config/socialNetwork_nginx_media.template

    """
    EVENT_PARAM_INDEX = 1
    for config in config_options.split(';'):
        parameter,value = config.split(' ')
        for event_config_item in config_json["config"][0]["parsed"][EVENT_PARAM_INDEX]["block"]: #block key contains all the configs in the context of events
            if event_config_item ["directive"] == parameter:
                event_config_item ["args"] = [value]

    # Other parameters in the "main" context of the nginx.conf file
    for config in config_options.split(';'):
        parameter,value = config.split(' ')
        for config_item in config_json["config"][0]["parsed"]:
            if config_item["directive"] == parameter:
                config_item["args"] = [value]

    """
    with open(config_json_file,"w") as config_json_f:
        json.dump(config_json,config_json_f)
    try:
        subprocess.run("crossplane build -f --indent 4 --dir %s %s"%(output_folder, config_json_file),shell=True)
    except:
        print("Check if crossplace is installed: pip3 install crossplace")
    subprocess.run("scp -i ~/compass.key %s/nginx.temp ubuntu@%s:%s"%(output_folder, frontend_host, remote_destination_folder ),shell=True)

def create_services_config(config, services_host, app, local_destination_folder):
    """
    Writes config related to services i.e. worker threads and io_threads to a file.
    """
    app_folder_dict = {"SN":"socialNetwork", "MM":"mediaMicroservices", "HR":"hotelReservation","TT":"trainTicket"}
    remote_destination_folder = "/home/ubuntu/uservices/DeathStarBench/%s/config"%app_folder_dict[app]
    config_file_path = local_destination_folder + "/parameters-config.txt"
    with open(config_file_path, "w") as config_file_f:
        config_file_f.write("\n".join(config))
    subprocess.run("scp -i ~/compass.key %s ubuntu@%s:%s"%(config_file_path, services_host, remote_destination_folder),shell=True)


def create_docker_compose_files(config_csv,cluster_setup_folder,version,app,client,app_config_iteration, cluster_number):
    """
    The application configuration is created here. This includes:
    1) Create hostToConfig file in cluster_setup folder
    2) Create host to role mapping pickle file
    3) Overwrite the nging.temp files from the previous experiments
    4) Creation of the nginx.temp file with the required configs.
    5) Creation of docker-compose files with the required configs.
    6) Creation of parameters-config.txt file with values for io_threads and worker_threads which will be read by the
    services and set during runtime.
    """
    app_specific_data = {"SN":{"overlay_name":"social-network-overlay-%s"%cluster_number}, "MM":{"overlay_name":"media-microservices-overlay-%s"%cluster_number}, "HR":{"overlay_name":"hotel-reservation-overlay-%s"%cluster_number},"TT":{"overlay_name":"train-ticket-overlay-%s"%cluster_number}}
    config = pd.read_csv(config_csv)
    yaml_dict = {}
    yaml_dict["version"] = "3"
    host_mapping = {}

    output_folder = cluster_setup_folder + "/" + version

    create_cluster_config(config,cluster_setup_folder,version,app_config_iteration)
    host_mapping = create_and_return_host_roles(config,cluster_setup_folder,version,client)

    # replace the nginx.temp from the previous experiments (should actually be done in the clearn up step)
    init_nginx_conf(app,host_mapping["frontend"])

    hosts_counts = config.host.value_counts()  

    services_params = []
    # create one docker-compose file for each host
    for host, count in hosts_counts.iteritems():
        yaml_dict = {}
        yaml_dict["version"] = "3"
        yaml_dict["networks"]={"default":{"external":{"name":app_specific_data[app]["overlay_name"]}}}
        service_dict = {}
        is_service_config_changed = False
        current_host_services = config[config.host == host]
        # for all the services in the current host
        for index, row in current_host_services.iterrows():
            per_service_dict = {}
            per_service_dict["hostname"] = row["hostname"]
            per_service_dict["image"] = row["image"]
            if per_service_dict["image"] == "mongo":
                per_service_dict["image"] = "mongo:4.4"
                 
            per_service_dict["restart"] = row["restart"]
            if pd.notnull(row["entrypoint"]):
                per_service_dict["entrypoint"] = row["entrypoint"]
            if pd.notnull(row["ports"]):
                per_service_dict["ports"] = row["ports"].split(';')
            if pd.notnull(row["depends_on"]):
                per_service_dict["depends_on"] = row["depends_on"].split(';')
            if pd.notnull(row["environment"]):
                environ_dict = {}
                for item in row["environment"].split(';'):
                    key,value = item.split('=')
                    environ_dict[key] = value
                per_service_dict["environment"] = environ_dict
            if pd.notnull(row["volumes"]):
                per_service_dict["volumes"] = row["volumes"].split(';')
            if pd.notnull(row["command"]):
                # create nginx.conf
                if row["type"] ==  "frontend":
                    create_frontend_configfile(row["hostname"],row["host"],row["command"],version,app, output_folder)
                # set the io_threads and worker_threads.
                elif row["type"] == "service":
                    is_service_config_changed = True
                    services_params.extend(row["command"].split(' '))
                # for the rest of the microservices, the "command" column has the value for the "command" column in the
                # docker-compose file.
                else:
                    per_service_dict["command"] = row["command"] 
            service_dict[row["microservice"]] = per_service_dict
        if is_service_config_changed:
            # host will be the services host
            create_services_config(services_params, host, app, output_folder)

        yaml_dict["services"] = service_dict
        compose_file = open(output_folder+'/docker-compose-%s-%s.yaml'%(host,app_config_iteration), 'w')
        #write to the cluser config folder
        yaml.dump(yaml_dict, compose_file)



if __name__ == "__main__":
    app_config_csv = sys.argv[1]
    cluster_setup_folder = sys.argv[2]
    version = sys.argv[3]
    app = sys.argv[4]
    client = sys.argv[5]
    app_config_iteration = sys.argv[6]
    cluster_number = sys.argv[7]
    create_docker_compose_files(app_config_csv,cluster_setup_folder,version,app,client,app_config_iteration, cluster_number)
