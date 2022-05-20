#! /usr/bin/python3
import os
import sys,subprocess,copy
import time

def runComposeInHosts(allHosts,hostToConfig):
    runCmdTemplate = "ssh -i ~/compass.key ubuntu@${cluster_hosts[0]} \"cd $social_network_home;${docker_compose_template/filename/$host_1_file}\""
    destFilename = "/home/ubuntu/touse.yaml"

    for curHost in allHosts:
        scpPrefix = "scp -i ~/compass.key "+str(hostToConfig[curHost])
        scpSuffix = "ubuntu@"+str(curHost)+":"+str(destFilename)
        scpCmd = str(scpPrefix)+" "+str(scpSuffix)
        print ("\n\t scpCmd: %s "%(scpCmd))

        try:
            subprocess.check_output(scpCmd,shell=True,universal_newlines=True)
        except Exception as err:
            print ("\t Exception: %s happened while copying file: %s to host: %s "%(err,hostToConfig[curHost],curHost))
            raise err

        runCmdPrefix = "ssh -i ~/compass.key ubuntu@"+str(curHost)
        runCmdSuffix=" sudo docker-compose -f "+str(destFilename)+" up -d"
        runCmd = str(runCmdPrefix)+" "+str(runCmdSuffix)
        print ("\t runCmd: %s "%(runCmd))
        try:
            subprocess.check_output(runCmd,shell=True,universal_newlines=True)
        except Exception as err:
            print ("\t Exception: %s happened while executing %s on  %s "%(err, runCmd, curHost))
            raise err
        #return

def beginDocker(allHosts,client,consulHost, consul_port):
    #Docker can be started on the client machine too
    #beginDockerSuffix = "sudo dockerd -H tcp://0.0.0.0:2375 -H unix:///var/run/docker.sock --cluster-advertise ens3:2375 --cluster-store consul://"+str(consulHost)+":8500 > dockerd.log 2>&1 &"
    # consul advertises on a interface that has private IP. Public IP is tricky. So choose an interface of the consul host that has private IP  in the below command.
    # https://stackoverflow.com/questions/34365604/how-to-create-docker-overlay-network-between-multi-hosts
    beginDockerSuffix = "sudo dockerd -H tcp://0.0.0.0:2375 -H unix:///var/run/docker.sock --cluster-advertise enp2s0f0:2375 --cluster-store consul://%s:%s > dockerd.log 2>&1 &"%(consulHost, consul_port)
    hostsToStart = allHosts

    for curHost in hostsToStart:
        loginPrefix = "ssh -i ~/compass.key ubuntu@"+str(curHost)
        if curHost in  []:
            #TODO: Connect the ethernet cable to np2s0f0 the next time you go to the lab and remove this
            beginDockerCmd = str(loginPrefix)+" "+str(beginDockerSuffix.replace("enp2s0f0","enp2s0f1"))
        else:
            beginDockerCmd = str(loginPrefix)+" "+str(beginDockerSuffix)
        print ("\t beginDockerCmd: %s "%(beginDockerCmd))
        try:
            subprocess.check_output(beginDockerCmd,shell=True,universal_newlines=True)
        except Exception as err:
            print ("\t Exception: %s happened while bringing up docker in host: %s "%(err,curHost))
            raise err
            

def create_loadgenerator(client_host, overlay_network):
    #TODO: remove hardcoding
    loadgenerator_container = "loadgenerator"
    os.system("ssh -i ~/compass.key ubuntu@%s sudo docker run --name %s -v /home/ubuntu/uservices/uservices-perf-analysis/:/home/ubuntu/uservices/uservices-perf-analysis/ -v /home/ubuntu/uservices/DeathStarBench/:/home/ubuntu/uservices/DeathStarBench/ -td gaganso/loadgenerator:v1"%(client_host,loadgenerator_container))
    os.system("ssh -i ~/compass.key ubuntu@%s sudo docker network connect %s %s"%(client_host,overlay_network,loadgenerator_container))

def beginConsul(consulHost, consul_name, consul_port):
    beginDockerCmd = "sudo service docker start"
    try:
        subprocess.check_output(beginDockerCmd,shell=True,universal_newlines=True)
    except Exception as err:
        print ("\t Exception: %s happened while bringing up docker in consulHost: %s "%(err,consulHost))
        raise err

    consulCmd = "sudo docker run -d -p %s:8500 -h %s --name %s progrium/consul -server -bootstrap"%(consul_port, consul_name, consul_name)
    print ("consulCmd: %s "%(consulCmd))
    try:
        subprocess.check_output(consulCmd,shell=True,universal_newlines=True)
    except Exception as err:
        print ("\t Exception: %s happened while bringing up consul in host"%(err))
        raise err

def consul_attributes(cluster_number):
    potential_ports = [8500,8501,8502]
    consul_name = "consul_" + str(cluster_number)
    host_port = potential_ports[int(cluster_number) - 1]
    return consul_name, host_port

def beginOverlayNW(hostToUse,overlay_name):
    loginPrefix = "ssh -i ~/compass.key ubuntu@"+str(hostToUse)

    # overlay_name is of the form social-network-overlay-2. So, get the cluster number and use it in the IP to get different subnets
    overlayCmd=str(loginPrefix)+" sudo docker network create -d overlay --subnet=192.168.%s.0/24 %s"%(overlay_name.split('-')[-1], overlay_name)

    print ("overlayCmd: %s "%(overlayCmd))
    try:
        subprocess.check_output(overlayCmd,shell=True,universal_newlines=True)
    except Exception as err:
        print ("\t Exception: %s happened while bringing up overlay-network"%(err))
        raise err

def getHostname():
    hostname = subprocess.check_output('hostname',shell=True,universal_newlines=True)
    return hostname.strip()

def create_volumes(backend, app):
    app_dict = {"SN" : "socialNetwork","MM" : "mediaMicroservices", "HR":"hotelReservation","TT":"trainTicket"}
    volume_parent_directory = "/home/ubuntu/uservices/DeathStarBench/%s"%app_dict[app]
    volume_source = volume_parent_directory + "/volumes"
    volume_destination = volume_parent_directory + "/tmp"
    ssh_command = "ssh ubuntu@%s "%backend
    os.system(ssh_command + "sudo rm -rf %s"%(volume_destination))
    os.system(ssh_command + "mkdir -p %s"%(volume_destination))
    os.system(ssh_command + "sudo cp -r %s/* %s"%(volume_source, volume_destination))

def deploy_app(mainConfigDir, front_end_host, client, backend, app,  cluster_number):
    overlay_name_dict = {"SN":"social-network-overlay", "MM" : "media-microservices-overlay", "HR":"hotel-reservation-overlay","TT":"train-ticket-overlay"}
    mapHostToConfigFilename = str(mainConfigDir)+"/hostToConfig.log" 
    hostToConfig = {}
    allHosts = []

    consulHost = client

    for curLine in open(mapHostToConfigFilename,'r').readlines():
        curLine = curLine.strip().split(",")
        host = curLine[0]
        file = str(mainConfigDir)+"/"+str(curLine[1])
        print ("\t host: %s file: %s "%(host,file))
        
        hostToConfig[host] = file
        allHosts.append(host)

    create_volumes(backend, app)
    consul_name, host_port = consul_attributes(cluster_number)
    beginConsul(consulHost, consul_name, host_port)
    time.sleep(10)
    
    beginDocker(allHosts,client,consulHost, host_port)
    time.sleep(20)
   
    overlay_name = overlay_name_dict[app] + "-%s"%cluster_number
    beginOverlayNW(allHosts[0],overlay_name)
    time.sleep(10)

    #create_loadgenerator(client,overlay_name_dict[app])
    runComposeInHosts(allHosts,hostToConfig)



if __name__ == "__main__":
    numArgs = 6

    if(len(sys.argv)<=numArgs):
        print ("\t Usage: <mainConfigDir> <frontEndHost> <client> <backend> <app> <cluster number>")
        sys.exit()
    
    mainConfigDir = sys.argv[1] # cluster_config/<version> folder where the host to yaml mapping and all the docker compose files are stored.
    frontEndHost = sys.argv[2] # The VM on which the frontend is running
    client = sys.argv[3] # The VM which is acting as the client or the VM on which the client container is brought up
    backend = sys.argv[4]
    app = sys.argv[5] #The code for the application being deployed
    cluster_number = sys.argv[6]

    deploy_app(mainConfigDir, frontEndHost, client, backend, app, cluster_number)
    
    # common_cmds="sudo dockerd -H tcp://0.0.0.0:2375 -H unix:///var/run/docker.sock --cluster-advertise ens3:2375 --cluster-store consul://usec-var-1:8500 > dockerd.log 2>&1 &"
    
    # overlay_cmd="sudo docker network create -d overlay --subnet=192.168.0.0/24 social-network-overlay"
    # docker_compose_template="sudo docker-compose -f filename up -d"
    # sudo docker run -d -p 8500:8500 -h consul --name consul progrium/consul -server -bootstrap
    
    # for host in ${cluster_hosts[*]}
    # do
    #     ssh -i ~/compass.key ubuntu@$host "$common_cmds"
    # done
    
    # ssh -i ~/compass.key ubuntu@$host "$overlay_cmd"
    
    # echo "${docker_compose_template/filename/$host_1_file}"
    
    ## py script... 
