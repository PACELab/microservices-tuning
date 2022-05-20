#! /usr/bin/python

import sys,subprocess,copy
import time

def runComposeInHosts(allHosts,hostToConfig):
    runCmdTemplate = "ssh -i ~/compass.key ubuntu@${cluster_hosts[0]} \"cd $social_network_home;${docker_compose_template/filename/$host_1_file}\""
    destFolder = "/home/ubuntu/uservices/DeathStarBenchMirror/mediaMicroservices/"; destFilename = "/home/ubuntu/uservices/DeathStarBenchMirror/mediaMicroservices/touse.yaml"
    #destFolder = "/home/ubuntu/"; destFilename = "/home/ubuntu/touse.yaml"

    for curHost in allHosts:

        scpPrefix = "scp -i ~/compass.key "+str(hostToConfig[curHost])
        scpSuffix = "ubuntu@"+str(curHost)+":"+str(destFilename)
        scpCmd = str(scpPrefix)+" "+str(scpSuffix)

        scpPre2 = "scp -i ~/compass.key "+str(hostToConfig["config"])
        scpSuffix2 = "ubuntu@"+str(curHost)+":"+str(destFolder)
        scpCmd2 = str(scpPre2)+" "+str(scpSuffix2)
        
        print ("\n\t scpCmd: %s \n scpCmd2: %s "%(scpCmd,scpCmd2))

        try:
            subprocess.check_output(scpCmd,shell=True,universal_newlines=True)
            #subprocess.check_output(scpCmd2,shell=True,universal_newlines=True)
            
        except Exception as err:
            print ("\t Exception: %s happened while copying file: %s to host: %s "%(err,hostToConfig[curHost],curHost))
            sys.exit()

        runCmdPrefix = "ssh -i ~/compass.key ubuntu@"+str(curHost)
        runCmdSuffix="\"cd "+str(destFolder)+"; docker-compose -f touse.yaml up -d \" "
        runCmd = str(runCmdPrefix)+" "+str(runCmdSuffix)
        print ("\t runCmd: %s "%(runCmd))
        try:
            subprocess.check_output(runCmd,shell=True,universal_newlines=True)
        except Exception as err:
            print ("\t Exception: %s happened while copying file: %s to host: %s "%(err,hostToConfig[curHost],curHost))
            sys.exit()        
        #return

def beginDocker(allHosts):

    beginDockerSuffix = "sudo dockerd -H tcp://0.0.0.0:2375 -H unix:///var/run/docker.sock --cluster-advertise ens3:2375 --cluster-store consul://"+str(consulHost)+":8500 > dockerd.log 2>&1 &"
    hostsToStart = allHosts

    for curHost in hostsToStart:
        loginPrefix = "ssh -i ~/compass.key ubuntu@"+str(curHost)
        beginDockerCmd = str(loginPrefix)+" "+str(beginDockerSuffix)
        print ("\t beginDockerCmd: %s "%(beginDockerCmd))
        try:
            subprocess.check_output(beginDockerCmd,shell=True,universal_newlines=True)
        except Exception as err:
            print ("\t Exception: %s happened while bringing up docker in host: %s "%(err,curHost))
            sys.exit()

def beginConsul(consulHost):
    beginDockerCmd = "sudo service docker start"
    try:
        subprocess.check_output(beginDockerCmd,shell=True,universal_newlines=True)
    except Exception as err:
        print ("\t Exception: %s happened while bringing up docker in consulHost: %s "%(err,consulHost))
        sys.exit()

    consulCmd = "sudo docker run -d -p 8500:8500 -h consul --name consul progrium/consul -server -bootstrap"
    print ("consulCmd: %s "%(consulCmd))
    try:
        subprocess.check_output(consulCmd,shell=True,universal_newlines=True)
    except Exception as err:
        print ("\t Exception: %s happened while bringing up consul in host"%(err))
        sys.exit()

def beginOverlayNW(hostToUse):
    loginPrefix = "ssh -i ~/compass.key ubuntu@"+str(hostToUse)
    overlayCmd=str(loginPrefix)+" sudo docker network create -d overlay --subnet=192.168.143.0/24 media-overlay"

    print ("overlayCmd: %s "%(overlayCmd))
    try:
        subprocess.check_output(overlayCmd,shell=True,universal_newlines=True)
    except Exception as err:
        print ("\t Exception: %s happened while bringing up overlay-network"%(err))
        sys.exit()

def getHostname():
    hostname = subprocess.check_output('hostname',shell=True,universal_newlines=True)
    return hostname.strip()

numArgs = 2

if(len(sys.argv)<=numArgs):
    print ("\t Usage: <mainConfigDir> <frontEndHost>")
    sys.exit()

mainConfigDir = sys.argv[1]
frontEndHost = sys.argv[2]
consulHost = getHostname()

mapHostToConfigFilename = str(mainConfigDir)+"/hostToConfig.log"

hostToConfig = {}
allHosts = []

configJsonFile = str(mainConfigDir)+"/config.json"
hostToConfig["config"] = configJsonFile

for curLine in open(mapHostToConfigFilename,'r').readlines():
    curLine = curLine.strip().split(",")
    host = curLine[0]
    file = str(mainConfigDir)+"/"+str(curLine[1])
    print ("\t host: %s file: %s "%(host,file))

    hostToConfig[host] = file
    allHosts.append(host)

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

##### py script... 

beginConsul(consulHost)
time.sleep(10)

beginDocker(allHosts)
time.sleep(20)

beginOverlayNW(allHosts[0])
time.sleep(10)

runComposeInHosts(allHosts,hostToConfig)
