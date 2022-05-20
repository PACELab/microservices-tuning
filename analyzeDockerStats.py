#! /usr/bin/python3

import sys,subprocess
import pandas as pd
import operator

def getSvcName(curFile,applnName):
    #splitSvcName = curFile.split('socialnetwork_')
    splitSvcName = ""
    if(applnName=="SN"):
        splitTerm = "ubuntu_"
        #splitTerm = "socialnetwork_"
    elif(applnName=="MM"):
        splitTerm = "ubuntu_"
    elif(applnName=="HR"):
        splitTerm = "ubuntu_"
    elif(applnName=="TT"):
        splitTerm = "ubuntu_"

    splitSvcName = curFile.split(splitTerm)
    if(len(splitSvcName)==1):
        print ("\t Error with filename: %s provided, was expecting to have 2 fields (at least), but found only one field after spliting by splitTerm: %s  "%(curFile,splitTerm))
        sys.exit()

    #print ("\t splitSvcName: %s "%(str(splitSvcName)))
    logSvcName = splitSvcName[1].split('.log')
    #print ("\t logSvcName: %s "%(str(logSvcName)))
    likelySvcName = logSvcName[0]

    return likelySvcName


allRps = [100,200,300,400,500,550,600,650,700,750] #,800,850,900]
numIters = 2

ipFolderBase = sys.argv[1]
outputFolder = sys.argv[2]
exptVersion = sys.argv[3]

listOfApps = ["SN","HR","MM"]
applnName = sys.argv[4]
if(not applnName in listOfApps):
    print ("\t appCode: %s is not found in list of apps.. "%(applnName,listOfApps))
    sys.exit()

#curIter = sys.argv[4]
#rps = int(sys.argv[5])

mmAllServices = ['mediamicroservices_dns-media_1.log','mediamicroservices_nginx-web-server_1.log','mediamicroservices_cast-info-memcached_1.log','mediamicroservices_cast-info-mongodb_1.log','mediamicroservices_compose-review-memcached_1.log','mediamicroservices_movie-id-memcached_1.log','mediamicroservices_movie-id-mongodb_1.log','mediamicroservices_movie-info-memcached_1.log','mediamicroservices_elastic-search_1.log','mediamicroservices_movie-info-mongodb_1.log','mediamicroservices_jaeger_1.log','mediamicroservices_cast-info-service_1.log','mediamicroservices_compose-review-service_1.log','mediamicroservices_movie-review-mongodb_1.log','mediamicroservices_movie-id-service_1.log','mediamicroservices_movie-review-redis_1.log','mediamicroservices_movie-info-service_1.log','mediamicroservices_movie-review-service_1.log','mediamicroservices_plot-service_1.log','mediamicroservices_plot-memcached_1.log','mediamicroservices_rating-service_1.log','mediamicroservices_plot-mongodb_1.log','mediamicroservices_review-storage-service_1.log','mediamicroservices_rating-redis_1.log','mediamicroservices_text-service_1.log','mediamicroservices_unique-id-service_1.log','mediamicroservices_review-storage-memcached_1.log','mediamicroservices_user-review-service_1.log','mediamicroservices_review-storage-mongodb_1.log','mediamicroservices_user-service_1.log','mediamicroservices_user-memcached_1.log','mediamicroservices_user-mongodb_1.log','mediamicroservices_user-review-mongodb_1.log','mediamicroservices_user-review-redis_1.log']
snAllSvcFiles = ['ubuntu_write-home-timeline-service_1.log','ubuntu_write-home-timeline-rabbitmq_1.log','ubuntu_user-timeline-service_1.log','ubuntu_user-timeline-redis_1.log','ubuntu_user-timeline-mongodb_1.log','ubuntu_user-service_1.log','ubuntu_user-mongodb_1.log','ubuntu_user-mention-service_1.log','ubuntu_user-memcached_1.log','ubuntu_url-shorten-service_1.log','ubuntu_url-shorten-mongodb_1.log','ubuntu_url-shorten-memcached_1.log','ubuntu_unique-id-service_1.log','ubuntu_text-service_1.log','ubuntu_social-graph-service_1.log','ubuntu_social-graph-redis_1.log','ubuntu_social-graph-mongodb_1.log','ubuntu_post-storage-service_1.log','ubuntu_post-storage-mongodb_1.log','ubuntu_post-storage-memcached_1.log','ubuntu_nginx-thrift_1.log','ubuntu_media-service_1.log','ubuntu_media-mongodb_1.log','ubuntu_media-memcached_1.log','ubuntu_media-frontend_1.log','ubuntu_jaeger_1.log','ubuntu_home-timeline-service_1.log','ubuntu_home-timeline-redis_1.log','ubuntu_elastic-search_1.log','ubuntu_compose-post-service_1.log','ubuntu_compose-post-redis_1.log']

toProcFiles = []
if(applnName == "SN"):
    toProcFiles = snAllSvcFiles
elif(applnName == "MM"):
    toProcFiles = mmAllServices 


consolidatedResults = {}

for curRps in allRps:
    for curIter in range(1,numIters+1):
        ipFolder = str(ipFolderBase)+str(curRps)+"/i"+str(curIter)
        rpsIter = str(curRps)+"_i"+str(curIter)
        outFilename = str(outputFolder)+"/cpuPct_"+str(exptVersion)+"_rps"+str(curRps)+"_i"+str(curIter)+".log"

        print ("\t curRps: %s curIter: %s outFilename: %s "%(curRps,curIter,outFilename))
        legendArr = []
        globalParams = { 'bar_width' : 0.3, 'xlabel_size' : 12, 'ylabel_size' : 12, 'legend_size' : 12, 'saveFiletype' : "png"}

        allData = {}
        allTerms = [ 'cpuPct', 'memPct','netRx', 'netTx']
        perTermOpFolder = []
        yLabels = [ "CPU utilization (%)", "Memory utilization (%)", "Net Rx KBps", "Net Tx KBps" ]

        allData['svcName'] = []
        allData['cpuPct'] = []
        allData['memPct'] = []
        allData['netRx'] = []
        allData['netTx'] = []

        curOpFolder = str(outputFolder)
        try:
            subprocess.check_output("mkdir -p "+str(curOpFolder),shell=True,universal_newlines=True)
        except Exception as err:
            print ("\t Likely folder: %s exists. Anyway the error was: %s "%(outputFolder,err))

        cpuAvg = {}
        for curFileSuffix in toProcFiles:
            curFile = str(ipFolder)+"/docker_stats/proc_"+str(curFileSuffix)

            curSvcName = getSvcName(curFile,applnName)

            curData = pd.read_csv(curFile,sep=",",header=0)
            #print ("\t curFile: %s , curSvcName: %s len: %d "%(curFile,curSvcName,len(curData)))
            cpuMean = curData['cpu_pct'].mean()
            print ("\t curSvcName: %s len: %d cpu_mean: %.3f "%(curSvcName,len(curData),cpuMean))

            allData['svcName'].append(curSvcName)
            allData['cpuPct'].append(curData['cpu_pct'].tolist())
            allData['memPct'].append(curData['mem_pct'])
            allData['netRx'].append(curData['net_rx_kbytes'])
            allData['netTx'].append(curData['net_tx_kbytes'])

            cpuAvg[curSvcName] = cpuMean

        print ("\n")
        sorted_d = sorted(cpuAvg.items(), key=operator.itemgetter(1),reverse=True)

        outFile = open(outFilename,'w')
        for curKey,curVal in sorted_d:
            print ("\t svc: %s\t%.3f"%(curKey,curVal))

            fmtStr = str(curKey)+"\t"+str('%.3f'%(curVal))+"\n"
            outFile.write(fmtStr)
        outFile.close()

        consolidatedResults[rpsIter] = sorted_d

        print ("\t outFilename: %s "%(outFilename))


summaryFilename = str(outputFolder)+"/summary_cpuPct.log"
summaryFile = open(summaryFilename,'w')
for curRps in allRps:
    rpsLine = "\n\t *********************** curRps: %d ********************** \n"%(curRps)
    print (rpsLine)
    summaryFile.write(str(rpsLine)+"\n")

    curRpsData = []
    for curIter in range(1,numIters+1):

        curIterData = []
        rpsIter = str(curRps)+"_i"+str(curIter)
        for curSvc,curSvcCpu in consolidatedResults[rpsIter]:
            curIterData.append([curSvc,curSvcCpu])

        curRpsData.append(curIterData)

    minLineNum = (10000*10000)
    numArr = len(curRpsData)
    for idx,curArr in enumerate(curRpsData):
        print ("\t idx: %d len(curArr): %d "%(idx,len(curArr)))
        if(minLineNum>len(curArr)):
            minLineNum = len(curArr)

    for curLineNum in range(minLineNum):
        printLine = ""
        svcNameLine = "" 
        cpuPctLine = ""
        for curArrIdx in range(numArr):
            curSvc,curSvcCpu = curRpsData[curArrIdx][curLineNum]
            if(svcNameLine==""):
                #printLine = str(curSvc)+"\t"+str('%.3f'%(curSvcCpu))    
                svcNameLine = str(curSvc)
                cpuPctLine = str('%.3f'%(curSvcCpu))
            else:
                #printLine = str(printLine)+"\t\t\t"+str(curSvc)+" "+str('%.3f'%(curSvcCpu))
                svcNameLine = str(svcNameLine)+"\t\t\t"+str(curSvc)
                cpuPctLine = str(cpuPctLine)+"\t"+str('%.3f'%(curSvcCpu))

        printLine = str(svcNameLine)+"\t\t\t"+str(cpuPctLine)
        print ("%s"%(printLine))
        summaryFile.write(str(printLine)+"\n")
summaryFile.close()
print ("\t summaryFilename: %s "%(summaryFilename))
