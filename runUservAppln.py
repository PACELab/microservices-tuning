#!/usr/bin/python3
import os
import sys,subprocess,time,math
import socket

numArgs = 6 

folderPrefix="."
client_container_name = "loadgenerator"
def launchMediaMicroservicesCmd(numThreads,numConns,runTime,rps,feNode,outputFolder):
    # Prepare wrk command

    wrkFolder = str(folderPrefix)+"/wrk2"

    composeReviewPct = 25
    readReviewPct = 70
    readPlotPct = 5
   
    hostname = feNode

    composeReviewRps = int(rps*composeReviewPct/100)
    readReviewRps = int(rps*readReviewPct/100)
    readPlotRps = int(rps*readPlotPct/100)
    composeNumThreads = int(math.ceil(numThreads/4))
    composeNumConns = int(math.ceil(numConns/2))
    print ("\t numThreads: %d composeNumThreads: %d "%(numThreads,composeNumThreads))

    commonUrl = "http://"+str(hostname)+":8080/wrk2-api/"

    composeReviewPrefix = str(wrkFolder)+"/wrk -D exp -t "+str(composeNumThreads)+" -c "+str(composeNumConns)+" -d "+str(runTime) + " -P " + str(outputFolder) +"/review_compose_latencies.txt" 
    composeReviewCmd = str(composeReviewPrefix)+" -L -s "+str(wrkFolder)+"/scripts/media-microservices/compose-review.lua "+str(commonUrl)+"/review/compose -R "+str(composeReviewRps)+" > "+str(outputFolder)+"/review_compose.log 2>&1 &"

    readReviewPrefix = str(wrkFolder)+"/wrk -D exp -t "+str(numThreads)+" -c "+str(numConns)+" -d "+str(runTime)+ " -P " + str(outputFolder) +"/review_read_latencies.txt"
    readReviewCmd = str(readReviewPrefix)+" -L -s "+str(wrkFolder)+"/scripts/media-microservices/read-review.lua "+str(commonUrl)+"/review/read -R "+str(readReviewRps)+" > "+str(outputFolder)+"/review_read.log 2>&1 &"


    readPlotPrefix = str(wrkFolder)+"/wrk -D exp -t "+str(composeNumThreads)+" -c "+str(numConns)+" -d "+str(runTime) + " -P " + str(outputFolder) +"/plot_read_latencies.txt"
    readPlotCmd = str(readPlotPrefix)+" -L -s "+str(wrkFolder)+"/scripts/media-microservices/read-plot.lua "+str(commonUrl)+"/plot/read -R "+str(readPlotRps)+" > "+str(outputFolder)+"/plot_read.log 2>&1 &"

    wrkScriptFilename = "./tempExptRun.sh"
    wrkScriptFile = open(wrkScriptFilename,"w")

    scriptCmds = ["#! /bin/bash"]
    scriptCmds.append("\n")
    scriptCmds.append("cp "+str(wrkScriptFilename)+" "+str(outputFolder))
    #scriptCmds.append("cd "+str(wrkFolder))#scriptCmds.append(wrkCmd)

    scriptCmds.append(composeReviewCmd+"\n")
    scriptCmds.append(readReviewCmd+"\n")
    scriptCmds.append(readPlotCmd+"\n")
    
    scriptCmds.append("wait;"+"\n")

    for curLine in scriptCmds:
        wrkScriptFile.write(str(curLine)+"\n")
    wrkScriptFile.close()

    runWrkScriptCmd = ["bash","./"+str(wrkScriptFilename)]
    try:
        wrkProcObj = subprocess.Popen(runWrkScriptCmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
        return wrkProcObj
    except Exception as err:
        print ("\t ABORT! err: %s while running wrkCmd monitoring process! "%(err))
        sys.exit()    

def launchHotelReservationCmd(numThreads,numConns,runTime,rps,feNode,outputFolder):
    # Prepare wrk command
    wrkFolder = str(folderPrefix)+"/wrk2"
    feHostName = feNode  

    # toUseHostname = "usec-var-7";
    # print ("\t extractedHostName: %s toUseHostname: %s "%(hostname,toUseHostname)); 
    hostname = feHostName
    commonUrl = "http://"+str(feHostName)+":5000"

    wrkPrefix = str(wrkFolder)+"/wrk -D exp -t "+str(numThreads)+" -c "+str(numConns)+" -d "+str(runTime)  + " -P " + str(outputFolder) +"/hotel_reservation_latencies.txt"
    wrkCmd = str(wrkPrefix)+" -L -s "+str(wrkFolder)+"/scripts/hotel-reservation/mixed-workload_type_1.lua "+str(commonUrl)+" -R "+str(rps)+" > "+str(outputFolder)+"/latency.log 2>&1 &"

    wrkScriptFilename = "./tempExptRun.sh"
    wrkScriptFile = open(wrkScriptFilename,"w")

    scriptCmds = ["#! /bin/bash"]
    scriptCmds.append("\n")
    scriptCmds.append("cp "+str(wrkScriptFilename)+" "+str(outputFolder))
    #scriptCmds.append("cd "+str(wrkFolder))#scriptCmds.append(wrkCmd)

    scriptCmds.append(wrkCmd+"\n")
    scriptCmds.append("wait;"+"\n")

    for curLine in scriptCmds:
        wrkScriptFile.write(str(curLine)+"\n")
    wrkScriptFile.close()

    runWrkScriptCmd = ["bash","./"+str(wrkScriptFilename)]
    print ("\t wrkCmd: %s "%(wrkCmd))
    try:
        wrkProcObj = subprocess.Popen(runWrkScriptCmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
        return wrkProcObj
    except Exception as err:
        print ("\t ABORT! err: %s while running wrkCmd monitoring process! "%(err))
        sys.exit()    

def launchSocialNetworkCmd(numThreads,numConns,runTime,rps,feNode,outputFolder,is_client_container=False):
    # Prepare wrk command

    wrkFolder = str(folderPrefix)+"/wrk2"

    composePct = 10
    userTimelinePct = 20
    newsFeedPct = 70
    feHostName = feNode  
    
    #wrkCmd = "./wrk -D exp -t "+str(numThreads)+" -c "+str(numConns)+" -d "+str(runTime)+" -L -s ./scripts/social-network/compose-post.lua http://localhost:8080/wrk2-api/post/compose -R "+str(rps)
    wrkCmd = "./wrk -D exp -t "+str(numThreads)+" -c "+str(numConns)+" -d "+str(runTime)+" -L -s ./scripts/social-network/compose-post.lua http://localhost:8080/wrk2-api/post/compose -R "+str(rps)    

    hostname = subprocess.check_output('hostname',shell=True,universal_newlines=True)
    hostname = hostname.strip()

    # toUseHostname = "usec-var-7";
    # print ("\t extractedHostName: %s toUseHostname: %s "%(hostname,toUseHostname)); 
    hostname = feHostName

    composeRps = int(rps*composePct/100)
    userTimelineRps = int(rps*userTimelinePct/100)
    newsFeedRps = int(rps*newsFeedPct/100)

    wrkCmd = "./socialNetwork/runReqMix.sh "+str(numThreads)+" "+str(numConns)+" "+str(runTime)+" "+str(composeRps)+" "+str(userTimelineRps)+" "+str(newsFeedRps)+" "+str(hostname)

    wrkCmdPrefix = str(wrkFolder)+"/wrk -D exp -t "+str(numThreads)+" -c "+str(numConns)+" -d "+str(runTime)

    # If the client is a container, the way the command is run will be different and the url will also be different. So have a flag for this.
    commonUrl = "http://"+str(hostname)+":8080/wrk2-api/"
    if is_client_container:
        commonUrl = "http://nginx-thrift:8080/wrk2-api/"

    composeNumThreads = int(math.ceil(numThreads/4))
    composeNumConns = int(math.ceil(numConns/2))
    print ("\t numThreads: %d composeNumThreads: %d "%(numThreads,composeNumThreads))
    composePrefix = str(wrkFolder)+"/wrk -D exp -t "+str(composeNumThreads)+" -c "+str(composeNumConns)+" -d "+str(runTime) + " -P " + str(outputFolder) +"/compose_latencies.txt"
    composeCmd = str(composePrefix)+" -L -s "+str(wrkFolder)+"/scripts/social-network/compose-post.lua "+str(commonUrl)+"/post/compose -R "+str(composeRps)+" > "+str(outputFolder)+"/compose.log 2>&1 &"

    userTimelinePrefix = str(wrkFolder)+"/wrk -D exp -t "+str(composeNumThreads)+" -c "+str(composeNumConns)+" -d "+str(runTime)+ " -P " + str(outputFolder) +"/user_latencies.txt"
    userTimelineCmd = str(userTimelinePrefix)+" -L -s "+str(wrkFolder)+"/scripts/social-network/read-user-timeline.lua "+str(commonUrl)+"/user-timeline/read -R "+str(userTimelineRps)+" > "+str(outputFolder)+"/user.log 2>&1 &"

    newsFeedPrefix = str(wrkFolder)+"/wrk -D exp -t "+str(numThreads)+" -c "+str(numConns)+" -d "+str(runTime)  + " -P " + str(outputFolder) +"/home_latencies.txt"
    newsFeedCmd = str(newsFeedPrefix)+" -L -s "+str(wrkFolder)+"/scripts/social-network/read-home-timeline.lua "+str(commonUrl)+"/home-timeline/read -R "+str(newsFeedRps)+" > "+str(outputFolder)+"/home.log 2>&1 &"

    wrkScriptFilename = "tempExptRun.sh"
    wrkScriptFile = open(wrkScriptFilename,"w")

    scriptCmds = ["#! /bin/bash"]
    scriptCmds.append("\n")
    scriptCmds.append("cp "+str(wrkScriptFilename)+" "+str(outputFolder))
    #scriptCmds.append("cd "+str(wrkFolder))#scriptCmds.append(wrkCmd)

    scriptCmds.append(composeCmd+"\n")
    scriptCmds.append(userTimelineCmd+"\n")
    scriptCmds.append(newsFeedCmd+"\n")
    
    scriptCmds.append("wait;"+"\n")

    for curLine in scriptCmds:
        wrkScriptFile.write(str(curLine)+"\n")
    wrkScriptFile.close()
    runWrkScriptCmd = ["bash","./"+str(wrkScriptFilename)]

    if is_client_container:
        script_destination = "./"
        script_path = script_destination+"/tempExptRun.sh"
        os.system("docker cp %s %s:%s"%(wrkScriptFilename,client_container_name,script_path))
        os.system("docker exec %s chmod +x %s"%(client_container_name,script_path))
        runWrkScriptCmd = "docker exec -d %s ./tempExptRun.sh"%(client_container_name)
    print ("\t wrkCmd: %s "%(wrkCmd))
    try:
        if is_client_container:
            wrkProcObj = "" 
            os.system(runWrkScriptCmd)
            #wrkProcObj = subprocess.Popen(runWrkScriptCmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
        else:
            wrkProcObj = subprocess.Popen(runWrkScriptCmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
        return wrkProcObj
    except Exception as err:
        print ("\t ABORT! err: %s while running wrkCmd monitoring process! "%(err))
        sys.exit()    

def launchTrainTicketCmd(numThreads,numConns,runTime,rps,feNode,outputFolder):
     # Prepare wrk command
     wrkFolder = str(folderPrefix)+"/wrk2"
     feHostName = feNode
 
     # toUseHostname = "usec-var-7";
     # print ("\t extractedHostName: %s toUseHostname: %s "%(hostname,toUseHostname)); 
     hostname = feHostName
     commonUrl = "http://"+str(feHostName)+":8080"
     os.system("./wrk2/wrk -t 1 -c 1 -d 2 -R 1 -L -s ./wrk2/scripts/train-ticket/userauth.lua http://%s:8080"%feNode)
     with open("./user_token.txt") as f:
         token = f.read()
         print(token)
 
     wrkPrefix = str(wrkFolder)+"/wrk -D exp -t "+str(numThreads)+" -c "+str(numConns)+" -d "+str(runTime)  + " -P " + str(outputFolder) +"/train_ticket_latencies.txt"
     wrkCmd = str(wrkPrefix)+" -L -s "+str(wrkFolder)+"/scripts/train-ticket/mixedload.lua "+str(commonUrl)+" -R "+str(rps)+" > "+str(outputFolder)+"/latency.log 2>&1 &"
     wrkCmd = "./wrk2/wrk -t 2 -c 4 -d " + str(runTime) + " -P " + str(outputFolder) +"/train_ticket_latencies.txt" + " -R " + str(rps) + " -L -s ./wrk2/scripts/train-ticket/mixedload.lua http://%s:8080 %s 6000 > %s/latency.log 2>&1 &"%(feNode, token, str(outputFolder))
     print(wrkCmd)
 
     wrkScriptFilename = "./tempExptRun.sh"
     wrkScriptFile = open(wrkScriptFilename,"w")
 
     scriptCmds = ["#! /bin/bash"]
     scriptCmds.append("\n")
     scriptCmds.append("cp "+str(wrkScriptFilename)+" "+str(outputFolder))
     #scriptCmds.append("cd "+str(wrkFolder))#scriptCmds.append(wrkCmd)
 
     scriptCmds.append(wrkCmd+"\n")
     scriptCmds.append("wait;"+"\n")
 
     for curLine in scriptCmds:
         wrkScriptFile.write(str(curLine)+"\n")
     wrkScriptFile.close()
 
     runWrkScriptCmd = ["bash","./"+str(wrkScriptFilename)]
     print ("\t wrkCmd: %s "%(wrkCmd))
     try:
         wrkProcObj = subprocess.Popen(runWrkScriptCmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
         return wrkProcObj
     except Exception as err:
         print ("\t ABORT! err: %s while running wrkCmd monitoring process! "%(err))
         sys.exit()


def launchMonitoringCmd(numContsToTrack,monitorTime,logsOutputDir, iter_num):
    """ Start docker stats monitoring """
    startMonitoringCmd = [str(folderPrefix)+"/dockerStatsStream.py", str(numContsToTrack), str(monitorTime),str(logsOutputDir), str(iter_num)]
    print ("\t startMonitoringCmd: %s \n"%(startMonitoringCmd))
    try:
        monProcObj = subprocess.Popen(startMonitoringCmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
        print(monProcObj)
        return monProcObj
    except Exception as err:
        print ("\t ABORT! err: %s while launching monitoring process! "%(err))
        sys.exit()

def analyseLogs(logsOutputDir):
    print ("\t logsOutputDir: %s "%(logsOutputDir))
    #listOfFiles = subprocess.check_output("ls "+str(logsOutputDir)+"/media*",shell=True,universal_newlines=True)
    listOfFiles = subprocess.check_output("ls "+str(logsOutputDir),shell=True,universal_newlines=True)
    listOfFiles = listOfFiles.split("\n")
    foundActions = {}

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

def createDirs(fullOutputDirPath,logsOutputDir):

    try:
        subprocess.check_output("mkdir -p "+str(fullOutputDirPath),shell=True,universal_newlines=True)
    except Exception as err:
        print ("\t Likely folder: %s already exists err: %s "%(fullOutputDirPath,err))    

    try:
        subprocess.check_output("mkdir -p "+str(logsOutputDir),shell=True,universal_newlines=True)
    except Exception as err:
        print ("\t Likely folder: %s already exists err: %s "%(logsOutputDir,err))  

if(len(sys.argv)<=numArgs):
    print ("\t Usage: <threads> <connections> <exp-duration> <req-per-second> <numContsToTrack> <outputFolder>")
    sys.exit()

shouldLaunchWrk = int(sys.argv[1])
numThreads = int(sys.argv[2])
numConns = int(sys.argv[3])
runTime = int(sys.argv[4]) # in seconds.
rps = int(sys.argv[5])
numContsToTrack = int(sys.argv[6])
outputFolder = sys.argv[7]
applnName = sys.argv[8]
feNode = sys.argv[9]
iter_number = int(sys.argv[10])

extraMonitorTime = 30
monitorTime = runTime+extraMonitorTime

fullOutputDirPath = str(folderPrefix)+"/"+str(outputFolder)
logsOutputDir = str(fullOutputDirPath)+"/docker_stats"

createDirs(fullOutputDirPath,logsOutputDir)
monProcObj = launchMonitoringCmd(numContsToTrack,monitorTime,logsOutputDir, iter_number)
time.sleep(5)

if(shouldLaunchWrk):
    wrkProcObj = ""
    feNodeIP = socket.gethostbyname(feNode)
    if(applnName=="SN"):
        wrkProcObj = launchSocialNetworkCmd(numThreads,numConns,runTime,rps,feNodeIP,fullOutputDirPath)
        print ("\t Done launching monitoring and wrk scripts for socialNetwork! Will sleep for %d seconds "%(runTime))

    elif(applnName=="HR"):
        wrkProcObj = launchHotelReservationCmd(numThreads,numConns,runTime,rps,feNodeIP,fullOutputDirPath)
        print ("\t Done launching monitoring and wrk scripts for hotelReservation! Will sleep for %d seconds "%(runTime))
    elif(applnName=="MM"):
        wrkProcObj =  launchMediaMicroservicesCmd(numThreads,numConns,runTime,rps,feNodeIP,fullOutputDirPath)
        print ("\t Done launching monitoring and wrk scripts for mediaMicroservices! Will sleep for %d seconds "%(runTime))
    elif(applnName == "TT"):
        wrkProcObj = launchTrainTicketCmd(numThreads,numConns,runTime,rps,feNodeIP,fullOutputDirPath)
    else:
        print ("\t App: %s is not one of the currently supported application, exitting.."%(applnName))
        sys.exit()

    time.sleep(runTime)
    try:
        wrkProcOut,wrkProcErr = wrkProcObj.communicate()
        print ("\t wrkCmdOut: %s \n wrkCmdErr: %s "%(wrkProcOut,wrkProcErr))
    except Exception as err:
        print("Err %s"%err)
    time.sleep(extraMonitorTime)
else:
    time.sleep(monitorTime)

monOut,monErr = monProcObj.communicate()
print ("\t monProcOut: %s \n monProcErr: %s "%(monOut,monErr)) 

#should add analyse commands.
analyseLogs(logsOutputDir)



