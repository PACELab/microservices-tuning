#! /usr/bin/python3

import sys,subprocess,time,copy,datetime
import pickle

### Global constants
defContainerLife = 60 # seconds
interJobWaitTime = 0.75 #seconds
graceSleep = defContainerLife + (4*60)
colocateJob = "nn"

machinesToBeUsed = []
#otherVMs = ["userv5","userv6","userv7","userv8"];runningFrom = ["userv1"] # SN
#otherVMs = ["serverless-4","serverless-6","serverless-7"]; runningFrom = ["serverless-3"] # HR
#otherVMs = ["serverless-dev1","serverless-dev2","serverless-dev3","serverless-dev4","serverless-dev5"];runningFrom = ["serverless-controller"] # MM

#otherVMs = ["userv-large-1","serverless-2","serverless-3","serverless-4"];runningFrom = ["serverless-controller"] # SN
#otherVMs = ["userv-larger-1","serverless-2","serverless-3","serverless-4"];runningFrom = ["serverless-controller"] # SN
#otherVMs = ["userv-largest-1","serverless-2","serverless-3","serverless-4"];runningFrom = ["serverless-controller"] # SN

#otherVMs = ["serverless-9","serverless-10","serverless-11","serverless-12","serverless-13","serverless-14"];runningFrom = ["serverless-8"] # MM


#versionName = "script_testing" #"temp_should_autogenerate_it"
###

class AccumulateStats():

    def __init__(self,exptConfigs): #functionsToMonitor,opVersionName,iterations=5):
        self.machinesToBeUsed = exptConfigs['machinesToBeUsed']
        self.versionName = exptConfigs['versionName']

        self.folderPrefix="."
        self.outputDir = str(self.folderPrefix)+"/"+exptConfigs['outputDir']
        self.dockStatsDir = str(self.outputDir)+"/docker_stats/"
        self.dockStatsFilePrefix = exptConfigs['filePrefix']

        
        self.sshCommandPrefix = ['ssh', '-i','./compass.key']
        self.scp_command_prefix = ['scp', '-i','./compass.key']
        self.mpstatLogFilename = str(self.outputDir)+'/mpstats_'+str(self.versionName)+'.log'


        self.cmdsToUse = {
            'mpStatMonitoring' : ['mpstat','-P','ALL','1','>',self.mpstatLogFilename,'&'],
            'createDirs'  : ["mkdir","-p",self.dockStatsDir],
            'grepDockerProcs' : ['ps','-aux','|','grep docker','| grep stats','| grep ubuntu'], 
            'checkStatus' : ["ls","-ltr",self.outputDir,"| wc -l"],
            'consolidateLogs' : [str(self.dockStatsDir)+"/*",str(self.dockStatsDir)],
            'copyLatencyLogs' : [str(self.outputDir)+"/*.log",str(self.outputDir)],
        }

        self.checkStatus()
        print ("\t <AccumulateStats(AS)> <init> Actions: VersionName: %s "%(self.versionName))
        #print ("\t <AccumulateStats(AS)> <init> Actions: --%s-- VersionName: %s "%(self.functionsToMonitor,self.versionName))


    def analyseLogs(self):
        logsOutputDir = self.dockStatsDir
        filePrefix = self.dockStatsFilePrefix
        folderPrefix=self.folderPrefix
        print ("\t logsOutputDir: %s filePrefix: %s "%(logsOutputDir,filePrefix))
        #listOfFiles = subprocess.check_output("ls "+str(logsOutputDir)+"/media*",shell=True,universal_newlines=True)

        listOfFiles = subprocess.check_output("ls "+str(logsOutputDir)+"/"+str(filePrefix)+"*",shell=True,universal_newlines=True)
        listOfFiles = listOfFiles.split("\n")
        foundActions = {}

        print ("\t List of files.. \n")
        for curFilePath in listOfFiles:
            print ("\t%s"%(curFilePath))

        for curFilePath in listOfFiles:
            curFilePath = curFilePath.strip()
            if(len(curFilePath)<2):
                continue;

            splitPath = curFilePath.split('/')
            curFile = ""
            if(len(splitPath)>=1):
                curFile = splitPath[len(splitPath)-1]
            else:
                continue;
            containerName = curFile.split('.')[0]

            toAnalyzeFile = str(logsOutputDir)+"/"+str(curFile)
            
            parseCmd = [str(folderPrefix)+"/parseDockerStats.py",str(logsOutputDir),curFile]
            print ("\t curFile: %s containerName: %s parseCmd: %s "%(curFile,containerName,parseCmd))
            #return
            try:
                parseProcObj = subprocess.Popen(parseCmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
                time.sleep(1) # is this necessary?
                out,err = parseProcObj.communicate()
                print ("\t out: %s "%(out))
            except Exception as err:
                print ("\t Some error: %s happened during analysing file: %s "%(err,curFile))
            #break

    def copyLatencyLogs(self):
        """
        On the client, the wrk2 logs and the mpstats log are collected. On the other hosts, only mpstats are collected. Basically any version/*.log file is collected and copied to client in the result folder.
        """
        for host in self.machinesToBeUsed :
            command = copy.deepcopy(self.scp_command_prefix)
            command.append("ubuntu@"+str(host)+":"+str(self.cmdsToUse["copyLatencyLogs"][0]))
            for idx,curCmdTerm in enumerate(self.cmdsToUse["copyLatencyLogs"]):
                if(idx==0):
                    continue;
                command.append(curCmdTerm)
            print ("\t <copyLatencyLogs> host: %s command: %s "%(host,command))
            tempProcObj = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE) # should check success 

            if(tempProcObj.poll() !=0): # if retCode is 0, implies cmd ran successfully.
                continue;
            else:
                print ("\t <AS><copyLatencyLogs> Error in launchMonitoring for machine: %s "%(host))

    def consolidateLogs(self):
        """
        Copies *.log files from docker_stats folder on all the hosts to the client's docker_stats/ folder
        """
        for host in self.machinesToBeUsed:
            command = copy.deepcopy(self.scp_command_prefix)
            command.append("ubuntu@"+str(host)+":"+str(self.cmdsToUse["consolidateLogs"][0]))
            for idx,curCmdTerm in enumerate(self.cmdsToUse["consolidateLogs"]):
                if(idx==0):
                    continue;
                command.append(curCmdTerm)
            print ("\t <consolidateLogs> host: %s command: %s "%(host,command))
            tempProcObj = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE) # should check success 

            if(tempProcObj.poll() !=0): # if retCode is 0, implies cmd ran successfully.
                continue;
            else:
                print ("\t <AS><consolidateLogs> Error in launchMonitoring for machine: %s "%(host))
        self.copyLatencyLogs()

    def checkStatus(self):
        for host in self.machinesToBeUsed:
            command = copy.deepcopy(self.sshCommandPrefix)
            command.append("ubuntu@"+str(host))

            for curCmdTerm in self.cmdsToUse["checkStatus"]:
                command.append(curCmdTerm)
            print ("\t <checkStatus> host: %s command: %s "%(host,command))

            lsObj = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE) # should check success 
            out,err = lsObj.communicate()
            print ("\t <AS><checkStatus> Machine: %s lsOutput: --%s--"%(host,out))

        self.consolidateLogs()

############################ Reading inputs

# test is the client machine and train refers to other hosts. Why were they named like this? Probably we will never know
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
appTodockStatsMap = {
    
    "SN" : "ubuntu_",
    "MM" : "ubuntu_",
    "HR" : "ubuntu_",
    "TT" : "ubuntu_",

}

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

if(not appCode in listOfApps):
    print ("\t appCode: %s is not found in list of apps.. "%(appCode,listOfApps))
    sys.exit()
app_folder = {"SN": "socialNetwork", "MM": "mediaMicroservices", "HR":"hotelReservation","TT":"trainTicket"}
cluster_config_dir = "./%s/cluster_setups/"%app_folder[appCode]

#versionName is of the form v_default_0_rps500. So split on '_' and get the second element in the list.
with open(cluster_config_dir + versionName.split('_')[1] + "/host_roles.pkl","rb") as host_roles_f:
    host_mapping = pickle.load(host_roles_f)
otherVMs = host_mapping["all_hosts"]
runningFrom = [host_mapping["client"]]

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
    'feNode' : feNode,
    "filePrefix" : appTodockStatsMap[appCode]
}

statsObj = AccumulateStats(exptConfigs); 
time.sleep(5)
statsObj.analyseLogs()
