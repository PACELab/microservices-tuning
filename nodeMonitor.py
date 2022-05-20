#! /usr/bin/python3

import sys,subprocess,time,copy,datetime
import csv
import pickle

### Global constants
defContainerLife = 60 # seconds
interJobWaitTime = 0.75 #seconds
graceSleep = defContainerLife + (4*60)
colocateJob = "nn"

machinesToBeUsed = []
#otherVMs = ["userv5","userv6","userv7","userv8"];runningFrom = ["userv2"] # SN
#otherVMs = ["serverless-dev1","serverless-dev2","serverless-dev3","serverless-dev4","serverless-dev5"];runningFrom = ["serverless-controller"] # MM

#otherVMs = ["userv-large-1","serverless-2","serverless-3","serverless-4"];runningFrom = ["serverless-controller"] # SN
#otherVMs = ["serverless-9","serverless-10","serverless-11","serverless-12"];runningFrom = ["serverless-8"] # MM


#otherVMs = ["userv-larger-1","serverless-2","serverless-3","serverless-4"];runningFrom = ["serverless-controller"] # SN
#otherVMs = ["userv-largest-1","serverless-2","serverless-3","serverless-4"];runningFrom = ["serverless-controller"] # SN
 
#versionName = "script_testing" #"temp_should_autogenerate_it"
###

class AccumulateStats():

    # Intialize command prefixes.
    def __init__(self,exptConfigs): #functionsToMonitor,opVersionName,iterations=5):

        self.machinesToBeUsed = exptConfigs['machinesToBeUsed']
        self.versionName = exptConfigs['versionName']

        self.outputDirPrefix = '/home/ubuntu/logs/'
        self.folderPrefix="/home/ubuntu/uservices/uservices-perf-analysis"
        self.outputDir = str(self.folderPrefix)+"/"+exptConfigs['outputDir']
        self.dockStatsDir = str(self.outputDir)+"/docker_stats/"

        self.localContLogsFilename = exptConfigs['outputDir']+"/controller0_logs.log"
        self.dummyProcNum = 7234 
        
        #self.funcContainerSuffix = str(self.versionName)+"_out.log"
        self.sshCommandPrefix = ['ssh', '-i','/home/ubuntu/compass.key']
        #self.sshCommandPrefix = ['ssh']
        self.scpCommandPrefix = ['scp', '-i','/home/ubuntu/compass.key']
        #self.scpCommandPrefix = ['scp']
        self.dockerLogFilename = str(self.outputDir)+'/dockstats_'+str(self.versionName)+'.log'
        self.mpstatLogFilename = str(self.outputDir)+'/mpstats_'+str(self.versionName)+'_%s.log'
        self.dummyProcNum = 7234

        # commands prefix.
        self.cmdsToUse = {
            'dockerMonitoring' : ['docker','stats','>',self.dockerLogFilename,'&'],
            'mpStatMonitoring' : ['mpstat','-P','ALL','1','%s'%exptConfigs['durtnSeconds'],'>',self.mpstatLogFilename,'&'],
            'createDirs'  : ["mkdir","-p",self.dockStatsDir],
            'copyInvokerLogs'  : ["cp","/tmp/wsklogs/invoker*/*.log",self.outputDir],
            'copyControllerLogs'  : ["cp","/tmp/wsklogs/controller*/*.log",self.outputDir],
            'bringControllerLogs' : [self.outputDir+"/controller0_logs.log",self.localContLogsFilename],
            'grepDockerProcs' : ['ps','-aux','|','grep docker','| grep stats','| grep ubuntu'], 
            'grepMpstatProcs' : ['ps','-aux','|','grep mpstat'], 
            'searchFuncContainer' : ['grep','-i','',self.dockerLogFilename,' >',''] , # 1st empty param: actionName, 2nd: actionName"_out.log"
            'uniqFunctions' : ["awk","'{print $1}'","","| uniq"], # 1st empt param: actionName"_out.log"
            'findDockerStats' : [],
            'stopMonitoring' : ["kill","-9",""],
            'checkStatus' : ["ls","-ltr",self.outputDir,"| wc -l"],
            'consolidateLogs' : [str(self.dockStatsDir)+"/*",str(self.dockStatsDir)],
            'copyLatencyLogs' : [str(self.outputDir)+"/*.log",str(self.outputDir)],
            'overwriteInvokerLog' : ["sudo","sh","-c ' ","echo 0",">","/home/ubuntu/invoker.log","'"], #"/tmp/wsklogs/invoker0/invoker0_logs.log","'"],
            'overwriteControllerLog' : ["sudo","sh","-c ' ","echo 0",">","/tmp/wsklogs/controller0/controller0_logs.log","'"] #/tmp/wsklogs/controller0/controller0_logs.log
        }
        """
        runUservApplnCmd script starts the wrk2 commands to generate the load, runs the dockerStatsStream.py script too.
        So, calling it monitoringCmds is not right but life is not fair.
        """
        runUservApplnCmd = [str(self.folderPrefix)+"/runUservAppln.py","",str(exptConfigs['numThreads']),str(exptConfigs['numConns']),
                            str(exptConfigs['durtnSeconds']),str(exptConfigs['rps']),str(exptConfigs['numContsToTrack']),
                            str(exptConfigs['outputDir']),str(exptConfigs['appCode']),str(exptConfigs['feNode']), str(iterNum)]

        self.cmdsToUse["monitoringCmds"] = [runUservApplnCmd] + [self.cmdsToUse['mpStatMonitoring']] # The experiment is also being run. Not just monitoring.
        self.cmdsToUse['grepProcs'] =  [ (self.cmdsToUse['grepDockerProcs'],'stats'),(self.cmdsToUse['grepMpstatProcs'],'1')   ]  # : ['ps','-aux','|','grep docker','| grep stats','| grep ubuntu'], 

        self.monitoringProcs = {} # per-machine used to kill it, eventually. 
        self.launchMonitoring()
        print ("\t <AccumulateStats(AS)> <init> Actions: VersionName: %s "%(self.versionName))
        #print ("\t <AccumulateStats(AS)> <init> Actions: --%s-- VersionName: %s "%(self.functionsToMonitor,self.versionName))

    def createDirs(self):
        allDirs = [self.machinesToBeUsed,runningFrom] 
        for curDir in allDirs:
            for curMachine in curDir: #self.machinesToBeUsed:
                curLaunchCmd = copy.deepcopy(self.sshCommandPrefix)
                curLaunchCmd.append("ubuntu@"+str(curMachine))
                for curCmdTerm in self.cmdsToUse["createDirs"]:
                    curLaunchCmd.append(curCmdTerm)
                print ("\t <createDirs> curMachine: %s curLaunchCmd: %s "%(curMachine,curLaunchCmd))
                tempProcObj = subprocess.Popen(curLaunchCmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE) # should check success 

                if(tempProcObj.poll() and (tempProcObj.poll() < 0)): # if retCode is less than 0, the process exited with error. If it is None, it is still running.
                    print ("\t <AS><createDirs> Error in launchMonitoring for machine: %s "%(curMachine))

    def copyLatencyLogs(self):
        for curMachine in runningFrom:
            curLaunchCmd = copy.deepcopy(self.scpCommandPrefix)
            curLaunchCmd.append("ubuntu@"+str(curMachine)+":"+str(self.cmdsToUse["copyLatencyLogs"][0]))
            for idx,curCmdTerm in enumerate(self.cmdsToUse["copyLatencyLogs"]):
                if(idx==0):
                    continue;
                curLaunchCmd.append(curCmdTerm)
            print ("\t <copyLatencyLogs> curMachine: %s curLaunchCmd: %s "%(curMachine,curLaunchCmd))
            tempProcObj = subprocess.Popen(curLaunchCmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE) # should check success 

            if(tempProcObj.poll() and (tempProcObj.poll() < 0)): # if retCode is 0, implies cmd ran successfully.
                continue;
            else:
                print ("\t <AS><copyLatencyLogs> Error in launchMonitoring for machine: %s "%(curMachine))

    # Bringing log files (docker stats) from remote machines to client machine. 
    def consolidateLogs(self):
        for curMachine in self.machinesToBeUsed:
            curLaunchCmd = copy.deepcopy(self.scpCommandPrefix)
            curLaunchCmd.append("ubuntu@"+str(curMachine)+":"+str(self.cmdsToUse["consolidateLogs"][0]))
            for idx,curCmdTerm in enumerate(self.cmdsToUse["consolidateLogs"]):
                if(idx==0):
                    continue;
                curLaunchCmd.append(curCmdTerm)
            print ("\t <consolidateLogs> curMachine: %s curLaunchCmd: %s "%(curMachine,curLaunchCmd))
            tempProcObj = subprocess.Popen(curLaunchCmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE) # should check success 

            if(tempProcObj.poll() and (tempProcObj.poll() < 0)): # if retCode is 0, implies cmd ran successfully.
                continue;
            else:
                print ("\t <AS><consolidateLogs> Error in launchMonitoring for machine: %s "%(curMachine))
        self.copyLatencyLogs()

    # Checking whether log files are generated.
    def checkStatus(self):
        for curMachine in self.machinesToBeUsed:
            curLaunchCmd = copy.deepcopy(self.sshCommandPrefix)
            curLaunchCmd.append("ubuntu@"+str(curMachine))

            for curCmdTerm in self.cmdsToUse["checkStatus"]:
                curLaunchCmd.append(curCmdTerm)
            print ("\t <checkStatus> curMachine: %s curLaunchCmd: %s "%(curMachine,curLaunchCmd))

            lsObj = subprocess.Popen(curLaunchCmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE) # should check success 
            out,err = lsObj.communicate()
            print ("\t <AS><checkStatus> Machine: %s lsOutput: --%s--"%(curMachine,out))

        self.consolidateLogs()


    # Start the monitoring here. 
    def launchMonitoring(self):
        self.createDirs(); time.sleep(2)
        for curMachine in self.machinesToBeUsed:
            for curMonitoringSet in self.cmdsToUse["monitoringCmds"]:
                curLaunchCmd = copy.deepcopy(self.sshCommandPrefix)
                curLaunchCmd.append("ubuntu@"+str(curMachine))                

                for curCmdTerm in curMonitoringSet:
                    if(curCmdTerm == ""):
                        if(curMachine in runningFrom):
                            curLaunchCmd.append(str(1))
                        else:
                            curLaunchCmd.append(str(0))
                    elif (curCmdTerm == self.mpstatLogFilename):
                        print(self.mpstatLogFilename%curMachine)
                        curLaunchCmd.append(self.mpstatLogFilename%curMachine)
                    else:
                        curLaunchCmd.append(curCmdTerm)

                print ("\n\t <AS><launchMonitoring> curMachine: %s curLaunchCmd: %s "%(curMachine,curLaunchCmd))
                tempProcObj = subprocess.Popen(curLaunchCmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE) # should check success 
                if(tempProcObj.poll() and (tempProcObj.poll() < 0)): # if retCode is 0, implies cmd ran successfully.
                    print ("\t <AS><launchMonitoring> Error in launchMonitoring for machine: %s "%(curMachine))


def get_host_dict(app_code):
    app_code_folder_map = {"SN":"socialNetwork","HR":"hotelReservation","MM":"mediaMicroservices", "TT":"trainTicket"}
    host_dict_file = "/home/ubuntu/uservices/DeathStarBench/%s/cluster_setups/v11/hostToConfig.log"%(app_code_folder_map[app_code])
    with open(host_dict_file) as csv_file:
        reader = csv.reader(csv_file)
        host_dict = dict(reader)
    return host_dict

def get_current_host():
    hostname = subprocess.check_output('hostname',shell=True,universal_newlines=True)
    return hostname.strip()

############################ Reading inputs


numArgs = 4
typeOfSet = {
    'test' : 1,
    'train' : 0
}

#if(len(sys.argv)<(numArgs+1)):
if(1):
    print ("\t Usage: <workloadSet 0: training 1: test> <outputDir> <versionName> ..")
    print ("\t Train:  0 <outputDir> <versionName> <app1-(et)file1> <app2-(mp)-file2> ")
    print ("\t Test:  1 <outputDir> <versionName> <parameters-file> \n")
    #sys.exit()

# ./nodeMonitor.py 1 results/v0.70//i4 v0.70_4_A0 4 results/v0.70//cmd_0.log
# ./nodeMonitor.py 1 results/v0.70//i1 v0.70_1_A0 1 results/v0.70//cmd_0.log &
# 1 v0.70 5 300 4 1 4

# ./commonDriver.py 1  1 v0.11 5 300 4 1 4
# ./commonDriver.py 4  1 v0.70 5 300 4 1 4 



listOfApps = ["SN","HR","MM", "TT"]
baseOutputDir = sys.argv[1]
versionName = sys.argv[2] 
iterNum = int(sys.argv[3])

numThreads = int(sys.argv[4])
numConns = int(sys.argv[5])
runTime = int(sys.argv[6]) # in seconds.
rps = int(sys.argv[7])
numContsToTrack = int(sys.argv[8])
appCode = sys.argv[9]
emailRecipient = sys.argv[10]
feNode = sys.argv[11]

app_folder = {"SN": "socialNetwork", "MM": "mediaMicroservices", "HR":"hotelReservation","TT":"trainTicket"}
cluster_config_dir = "/home/ubuntu/uservices/DeathStarBench/%s/cluster_setups/"%app_folder[appCode]

#versionName is of the form v_default_0_rps500. So split on '_' and get the second element in the list.
with open(cluster_config_dir + versionName.split('_')[1] + "/host_roles.pkl","rb") as host_roles_f:
        host_mapping = pickle.load(host_roles_f)
otherVMs = host_mapping["all_hosts"]
runningFrom = [host_mapping["client"]]

"""
host_dict = get_host_dict(appcode)
otherVMs = host_dict["all_hosts"] 
runningFrom = get_current_host()
"""
if(not appCode in listOfApps):
    print ("\t appCode: %s is not found in list of apps.. "%(appCode,listOfApps))
    sys.exit()

scriptCmd = ""

start =time.time()

outputDir = str(baseOutputDir)+"/"+str(versionName)+"/i"+str(iterNum)
exptVersion = str(baseOutputDir)+"_"+str(versionName)+"_i"+str(iterNum)

content = "echo \" FYI... \" "
mailHeading = " \"Beginning of expt version "+str(exptVersion)+" at `date` \" %s@cs.stonybrook.edu "%(emailRecipient)
emailCmd = str(content)+"  | mail -s "+str(mailHeading)

# To launch accumulate stats on the cluster machines and to clean them up once done..
exptConfigs = {
    'machinesToBeUsed' : runningFrom+otherVMs,
    'versionName' : versionName,
    'outputDir' : outputDir,

    'numThreads' : numThreads,
    'numConns' : numConns,
    'durtnSeconds' : runTime,
    'rps' : rps,
    'numContsToTrack' : numContsToTrack,
    'appCode' : appCode,
    'feNode' : feNode
}

statsObj = AccumulateStats(exptConfigs); 
time.sleep(5)

try:
    subprocess.check_output(emailCmd,shell=True,universal_newlines=True)
except Exception as err:
    print ("\t Error in issuing email! %s "%(err))

bufferWaitTime = 60
time.sleep(runTime+bufferWaitTime)

statsObj.checkStatus()
