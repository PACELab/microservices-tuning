#! /usr/bin/python3

import sys,json,time,subprocess,copy
import requests
import random

listOfApps = ["SN","HR","MM", "TT"]
endToStartInUsecs = (2*24*60*60*1000*1000)
numTracesToLookupPerIter = 1500

servNameLookup = {
    # SN app
    'compose': 'nginx-web-server',
    'home' :  'nginx-web-server',
    'user' : 'nginx-web-server' ,


    # MM app
    'reviewCompose' : 'nginx',
    'reviewRead' : 'nginx',
    'plot' : 'nginx',

    # TT app
    'book': 'ts-preserve-other-service',
    'search': 'ts-travel-service',
}

operation_name_lookup = {
        #SN app
        'compose' : '/wrk2-api/post/compose',
        'home' : '/wrk2-api/home-timeline/read',
        'user' : '/wrk2-api/user-timeline/read',
        #MM app
    'reviewCompose' : '/wrk2-api/review/compose',
    'reviewRead' : '/wrk2-api/review/read',
    'plot' : '/wrk2-api/plot/read',
    #TT app
    'search': 'queryInfo', 
    'book': 'preserve',
        }

def getTraceIDs(exptEndTime,storeDataFilename,reqType,monMachine,numReqsToQuery):
    # Get all the data Jaeger has collected for the latest 'numReqs' request before endTime. 
    # e.g.: EndTime is 10000 and before that there were say 200 requests of 'user' type. This experiment has only 100 requests. What we want is just the 100 latest requests.
    
    url = "http://"+str(monMachine)+":16686/api/traces?end=1576459171157000&limit=1000&maxDuration&minDuration&service=compose-post-service&start=1580917722975000"
    #http://172.24.204.24:16686/search?end=1598802620763000&limit=15&lookback=6h&maxDuration&minDuration&operation=%2Fwrk2-api%2Fpost%2Fcompose&service=nginx-web-server&start=1598781020763000
    serviceToQuery = servNameLookup[reqType] #"home-timeline-service"

    curEndTime = exptEndTime
    curStartTime = exptEndTime - endToStartInUsecs
    #curStartTime = exptEndTime - (7*60*1000*1000)   # TODO: just look at a 7 minute window as the experiments are being run for 5 minuts. Temp fix
    #numReqsToQuery = 2 * numTracesToLookupPerIter
    numProcReqs = 0
    allReqsData = []    
    try:
        traceFile = open(storeDataFilename)
        tracesJsonObj = json.load(traceFile)
        allReqsData = tracesJsonObj['data'] 
        numProcReqs = len(allReqsData)

        if(numProcReqs>0):

            curTrace = allReqsData[numProcReqs-1]
            nextSetEndTime = curEndTime

            for curTrace in allReqsData:
                interestedIdx = 0 #len(curTrace['spans'])-1
                curTraceStartTime = curTrace['spans'][interestedIdx]['startTime']
                if(curTraceStartTime < nextSetEndTime ):
                    nextSetEndTime = curTraceStartTime

            curEndTime = nextSetEndTime
            curStartTime = curEndTime - endToStartInUsecs

    except Exception as err:
        print ("\t Error: %s happened while trying to read file: %s "%(err,storeDataFilename))

    print ("\t numProcReqs: %d curStartTime: %s curEndTime: %s "%(numProcReqs,curStartTime,curEndTime))
    
    while(numProcReqs<numReqsToQuery):

        remainReqs = (numReqsToQuery - numProcReqs)
        remainReqs = numTracesToLookupPerIter if(remainReqs > numTracesToLookupPerIter) else remainReqs

        urlPrefix = "http://"+str(monMachine)+":16686/api/traces?end="+str(curEndTime)+"&limit="+str(remainReqs)
        urlSuffix = "&operation="+operation_name_lookup[reqType] + "&service="+str(serviceToQuery)+"&start="+str(curStartTime)
        url = str(urlPrefix)+str(urlSuffix)

        print ("\t url: %s "%(url))
        res = requests.get(url)

        traceIDs = []
        jdata = json.loads(res.content.decode('utf-8'))
        traces = jdata['data']
        print ("\t len(traces): %d "%(len(traces)))
        if len(traces) == 0:
            print("Stopping as the number of traces is 0")
            break
        nextSetEndTime = curEndTime
        for curTrace in traces:
            interestedIdx = 0 #len(curTrace['spans'])-1
            curTraceStartTime = curTrace['spans'][interestedIdx]['startTime']

            traceIDs.append(curTrace['traceID']) 
            if(curTraceStartTime < nextSetEndTime ):
                nextSetEndTime = curTraceStartTime

            allReqsData.append(curTrace)
            numProcReqs+=1
            diffFromStartTime = (curTraceStartTime - curStartTime)/(1000*1000)
            print ("\t req-num: %d traceID: %s curTraceStartTime: %s nextSetEndTime: %s diffFromStartTime: %.3f "%(numProcReqs,curTrace['traceID'],curTraceStartTime,nextSetEndTime,diffFromStartTime))

        curEndTime = nextSetEndTime
        curStartTime = curEndTime - endToStartInUsecs
        time.sleep(0.1)

        deltaTS = curEndTime - curStartTime 
        deltaTS/=(1000*1000)
        diff = (curEndTime - curStartTime)/(1000*1000)
        print ("\t New startTime: %d endTime: %d diff: %.3f deltaTS: %.3f "%(curStartTime,curEndTime,diff,deltaTS))

    data = {"data":allReqsData}
    with open(storeDataFilename, "w") as storeDataFile:
        json.dump(data, storeDataFile)

    print ("\t Data stored in file: %s "%(storeDataFilename))

egSpanInfo1 = {
    'traceID': '4badea6998304b91',
    'spanID': '4a932ecd93a3bdeb',
    'flags': 1, 'operationName': 'ReadHomeTimeline',
    'references': [{'refType': 'CHILD_OF','traceID': '4badea6998304b91','spanID': '33a4e8ef8c625135'}], 
    'startTime': 1581210100874261, 
    'duration': 6019, 
    'tags': [{'key': 'internal.span.format','type': 'string','value': 'proto'}],
    'logs': [],
    'processID': 'p2',
    'warnings': None
}

egSpanInfo2 = {
        'traceID': '4badea6998304b91',
        'spanID': '88bba3953bce014d',
        'flags': 1,
        'operationName': '/wrk2-api/home-timeline/read',
        'references': [{'refType': 'CHILD_OF', 'traceID': '4badea6998304b91', 'spanID': '4badea6998304b91'}],
        'startTime': 1581210100873601,
        'duration': 20056,
        'tags': [
            {'key': 'component', 'type': 'string', 'value': 'nginx'},
            {'key': 'nginx.worker_pid', 'type': 'string', 'value': '9'},
            {'key': 'peer.address', 'type': 'string', 'value': '172.24.79.154:49810'},
            {'key': 'http.method', 'type': 'string', 'value': 'GET'},
            {'key': 'http.url', 'type': 'string', 'value': 'http://usec-var-5:8080/wrk2-api/home-timeline/read?user_id=561&start=67&stop=77'},
            {'key': 'http.host', 'type': 'string', 'value': 'usec-var-5:8080'},
            {'key': 'http.status_code', 'type': 'int64', 'value': 200},
            {'key': 'http.status_line', 'type': 'string', 'value': ''},
            {'key': 'internal.span.format', 'type': 'string', 'value': 'proto'}],
        'logs': [],
        'processID': 'p1',
        'warnings': None
}


def writeFormattedData(opFilename,allOpNames,collectedData,dataChoice):
    header = "traceID"

    if(dataChoice=="durtn"):
        for curOpFullPath in allOpNames:
            curOpUniqPath = collectedData['uniqPathID'][curOpFullPath]
            header = str(header)+"\t"+str(curOpUniqPath)
            print ("\t curOpFullPath: %s\t curOpUniqPath: %s \tlen(collectedData[opTag]): %d "%(curOpFullPath,curOpUniqPath,len(collectedData[curOpFullPath][dataChoice])))

    elif(dataChoice=="startTime"):
        for curOpFullPath in allOpNames:
            curOpUniqPath = collectedData['uniqPathID'][curOpFullPath]
            header = str(header)+"\t"+"st_"+str(curOpUniqPath)
            print ("\t curOpFullPath: %s\t curOpUniqPath: %s\tlen(collectedData[opTag]): %d "%(curOpFullPath,curOpUniqPath,len(collectedData[curOpFullPath][dataChoice])))

    elif(dataChoice=="nonChildDurtn"):
        for curOpFullPath in allOpNames:
            curOpUniqPath = collectedData['uniqPathID'][curOpFullPath]
            header = str(header)+"\t"+"ncd_"+str(curOpUniqPath)
            print ("\t curOpFullPath: %s\t curOpUniqPath: %s\tlen(collectedData[opTag]): %d "%(curOpFullPath,curOpUniqPath,len(collectedData[curOpFullPath][dataChoice])))

    fmtData = []
    actual_data_count = 0
    for curTraceID in collectedData["traceIDs"]:
        fmtData.append([curTraceID])
        actual_data_count += 1

    fmtData.append(["cumul"])
    fmtData.append(["count"])
    fmtData.append(["averg"])

    for curOpIdx,curOpFullPath in enumerate(allOpNames):
        cumulVal = 0.0
        nonZeroCount = 0.0
        for curTraceIdx,curOpDurtn in enumerate(collectedData[curOpFullPath][dataChoice]):
            print(curTraceIdx)
            fmtData[curTraceIdx].append(curOpDurtn)
            if(curOpDurtn!=0.0):
                cumulVal+=curOpDurtn
                nonZeroCount+=1
            if curTraceIdx >= actual_data_count - 1:
                break

        fmtData[curTraceIdx+1].append(cumulVal)
        fmtData[curTraceIdx+2].append(nonZeroCount)
        avgVal = 0.0 if nonZeroCount==0 else (cumulVal/nonZeroCount)
        fmtData[curTraceIdx+3].append('%.3f'%(avgVal))

        print ("\t curOpFullPath: %s cumul: %.3f nonZeroCount: %d avgVal: %.3f "%(curOpFullPath,cumulVal,nonZeroCount,avgVal ))

    opFile = open(opFilename,"w")
    opFile.write(str(header)+"\n")
    for curTraceVals in fmtData:
        curLine = curTraceVals[0]
        for curIdx in range(1,len(curTraceVals)):
            curLine = str(curLine)+"\t"+str(curTraceVals[curIdx])
        opFile.write(str(curLine)+"\n")
    opFile.close()


def listToStr(ipList):
    opStr = ''
    for curTerm in ipList:
        if(opStr==""):
            opStr = str(curTerm)
        else:
            opStr = str(opStr)+"_"+str(curTerm)

    return opStr

def getTraceInfo(traceFilename,allOpNames,collectedData):

    #print ("\t url: %s "%(url))
    #getting some useful information like service, operations involved
    traceFile = open(traceFilename)
    tracesJsonObj = json.load(traceFile)
    allTraces = tracesJsonObj['data']

    opPaths = {}

    allInvalidMsgs = ['invalid parent span ID',' skipping clock skew adjustment']
    for curTrace in allTraces: 
        curTraceID = curTrace['traceID']
        spans = curTrace['spans']

        # Will use timestamps and duration of current op and parent's op to figure out sync/async behavior.
        processedData = {} # Contains 
        startTimes = []

        foundWarning = False
        for curSpan in spans:
            trID = curSpan['traceID']
            spID = curSpan['spanID']
            stTime = curSpan['startTime']
            opName = curSpan['operationName']
            durtn = curSpan['duration']
            if(len(curSpan['references'])!=0):
                if(len(curSpan['references'])>1):
                    print ("\t Yo! traceID: %s and spanID: %s has %d parents, HANDLE it! "%(curTraceID,spID,len(curSpan['references'])))
                
                parent = curSpan['references'][0]['spanID']

            else:
                parent = spID # assuming this happens only for the initial span, which is by Jaeger's design.

            if(parent in processedData):
                processedData[parent]['childName'].append(opName)                        
                processedData[parent]['childSpID'].append(spID)                        

            startTimes.append([stTime,spID,opName])
            processedData[spID] = { 'trID' : trID, 'opName' : opName, 'stTime':  stTime, 'durtn' : durtn, 'parent' : parent,'childName':[],'childSpID':[]}

            if(type(curSpan['warnings'])==list):
                for curWarning in curSpan['warnings']:
                    for curInValidMsgs in allInvalidMsgs:
                        if(curInValidMsgs in curWarning):
                            foundWarning = True
                            #print ("\t WARNING!! SpID: %s has a warning: %s "%(spID,curWarning))
                            break;

            if(foundWarning):
                break;

        if(foundWarning):
            continue;

        #print ("\t processedData[]: %s "%(str(processedData)))
        for curSpan in spans:
            trID = curSpan['traceID']
            spID = curSpan['spanID'] 
            opName = curSpan['operationName']           
            #print ("\n\t trID: %s spID: %s curSpan: %s "%(trID,spID,curSpan))
            #print ("\n\t trID: %s spID: %s processedData: %s "%(trID,spID,processedData[spID]))

            nonChildDurtn = processedData[spID]['durtn']

            for idx,curChildSpID in enumerate(processedData[spID]['childSpID']):
                curChildOp = processedData[spID]['childName'][idx]
                #print ("\t spID: %s op: %s childSpID: %s childOp: %s nonChildDurtn: %d childRuntime: %d "%(spID,opName,curChildSpID,curChildOp,nonChildDurtn,processedData[curChildSpID]['durtn']))
                nonChildDurtn-=processedData[curChildSpID]['durtn']

            processedData[spID]['nonChildDurtn'] = nonChildDurtn
            #print ("\n\t trID: %s spID: %s processedData: %s "%(trID,spID,processedData[spID]))            
        #sys.exit()

        startTimes = sorted(startTimes, key = lambda x : x[0])        
        numOpNames = {}
        opNamesNotInitialized = (len(allOpNames)==0)
        prevOpTag = ''
        numProcTraces = 0
        if(len(allOpNames)>1):
            numProcTraces = len(collectedData[allOpNames[0]]['durtn'])

        filledOps = []
        if(not ("traceIDs" in collectedData)):
            collectedData["traceIDs"] = [curTraceID]
        else:
            collectedData["traceIDs"].append(curTraceID)

        spanIDToPathLookUp = {}
        for curStTime,curSpID,curOpName in startTimes:
            curOpDurtn = processedData[curSpID]['durtn']
            curOpParent = processedData[curSpID]['parent']
            curOpStTime = processedData[curSpID]['stTime']
            curOpNonChildDurtn = processedData[curSpID]['nonChildDurtn']
            #print ("\n\t curStTime: %s curSpID: %s curOpDurtn: %.3f ,curOpName: %s curOpParent: %s curOpStTime: %s "%(curStTime,curSpID,curOpDurtn,curOpName,curOpParent,curOpStTime))

            curOpPath = []; parentPath = []
            if(curOpParent in spanIDToPathLookUp):
                parentPath = copy.deepcopy(spanIDToPathLookUp[curOpParent])
                #print ("\t curSpId: %s parentPath: %s "%(curSpID,parentPath))
            else:
                if(curSpID == curOpParent): # root of this trace. 
                    parentPath = []
                else:
                    print ("\t curSpID: %s's parent is not found in spanIDToPathLookup. curParentID: %s "%(curSpID,curOpParent))
                    print ("\t curSpanData: %s "%(processedData[curSpID]))
                    parentPath = []
                    #print ("\t curParentData: %s "%(processedData[curOpParent]))

                    for curSpan in spans:
                        spID = curSpan['spanID']
                        #print ("spID: %s data --> %s"%(spID,processedData[spID]))
                        print (curSpan)

                    continue #sys.exit()

            curOpPath = copy.deepcopy(parentPath) #.append(curOpName))
            curOpPath.append(curOpName)
            spanIDToPathLookUp[curSpID] = curOpPath
            #print ("\t curSpId: %s curOpPath: %s parentPath: %s spanIDToPathLookUp[]: %s "%(curSpID,curOpPath,parentPath,spanIDToPathLookUp[curSpID]))

            curOpPathStr = listToStr(curOpPath)
            if(not curOpPathStr in allOpNames):
                allOpNames.append(curOpPathStr)
                if(opNamesNotInitialized):
                    collectedData[curOpPathStr] = {}
                    collectedData[curOpPathStr]['durtn'] = []
                    collectedData[curOpPathStr]['startTime'] = []
                    collectedData[curOpPathStr]['nonChildDurtn'] = []
                else:
                    collectedData[curOpPathStr] = {}
                    collectedData[curOpPathStr]['durtn'] = [0 for i in range(numProcTraces)] 
                    collectedData[curOpPathStr]['startTime'] = [0 for i in range(numProcTraces)] 
                    collectedData[curOpPathStr]['nonChildDurtn'] = [0 for i in range(numProcTraces)] 

                collectedData[curOpPathStr]['path'] = curOpPath

            collectedData[curOpPathStr]['durtn'].append(curOpDurtn)
            collectedData[curOpPathStr]['startTime'].append(curOpStTime)
            collectedData[curOpPathStr]['nonChildDurtn'].append(curOpNonChildDurtn)
            prevOpTag = curOpPathStr
            filledOps.append(curOpPathStr)

        for curOpPathStr in allOpNames:
            if(not(curOpPathStr in filledOps)):
                befLen = len(collectedData[curOpPathStr]['durtn'])
                collectedData[curOpPathStr]['durtn'].append(0)
                collectedData[curOpPathStr]['startTime'].append(0)
                collectedData[curOpPathStr]['nonChildDurtn'].append(0)
                #print ("\t *** traceID: %s opTag: %s was missing befLen: %d aftLen: %d "%(curTraceID,curOpFullPath,befLen,len(collectedData[curOpFullPath])))
            #print ("\t opTag: %s len(durtn): %d len(stTime): %d "%(curOpFullPath,len(collectedData[curOpFullPath]['durtn']),len(collectedData[curOpFullPath]['startTime'])))

    uniqOpNames = {} 
    for curOpPathStr in allOpNames:
        pathLen = len(collectedData[curOpPathStr]['path'])
        if(pathLen<1):
            print ("\t Something is not right, pathLen: %d path: %s "%(pathLen,collectedData[curOpPathStr]['path']))
            sys.exit()
        actualOpName = collectedData[curOpPathStr]['path'][pathLen-1]
        print ("\t len(): %d curOpPathStr: %s"%(len(collectedData[curOpPathStr]['durtn']),curOpPathStr))
        if(not(actualOpName in uniqOpNames)):
            uniqOpNames[actualOpName] = [ collectedData[curOpPathStr]['path'] ]
        else:
            uniqOpNames[actualOpName].append(collectedData[curOpPathStr]['path'])

    uniqPathID = {}; duplSet = {}
    for curOpName in uniqOpNames:
        print ("\t <findUniqPath> curOpName: %s len(uniqOpNames[curOpName]): %d "%(curOpName,len(uniqOpNames[curOpName])))

        if(len(uniqOpNames[curOpName])==1):
            curOpPath = uniqOpNames[curOpName][0]
            curOpPathStr = listToStr(curOpPath)
            uniqPathID[curOpPathStr] = curOpName
            print ("\n\t <findUniqPath> 1. curOpPathStr: %s opPathID: %s "%(curOpPathStr,curOpName))
        
        elif(len(uniqOpNames[curOpName])==2):

            sameOpRepeated = False
            sameOpIdx = 100

            for idx,curOpPath in enumerate(uniqOpNames[curOpName]):
                #for curOpTerm in curOpPath:
                opPathLen = len(curOpPath)
                if( opPathLen >=2 ):
                    lastTerm = curOpPath[opPathLen-1] 
                    lastButoneTerm = curOpPath[opPathLen-2] 

                    print ("\t <findUniqPath> 1.5 curOpPath: %s lastTerm: %s lastButoneTerm: %s "%(curOpPath,lastTerm,lastButoneTerm))
                    if(lastTerm == lastButoneTerm):
                        sameOpRepeated = True
                        sameOpIdx = idx

            if(sameOpRepeated):
                curOpPath = uniqOpNames[curOpName][sameOpIdx]
                curOpPathStr = listToStr(curOpPath)
                uniqPathID[curOpPathStr] = curOpName+"_1"

                otherOpIdx = 1-sameOpIdx # only two duplicates are assumed, so idx has to be 0 or 1. By subtracting sameOpIdx from 1, we will get complement of sameOpIdx ( sameOpIdx: 1 ->0 , sameOpidx: 0 -> 1)
                otherOpPath = uniqOpNames[curOpName][otherOpIdx]
                otherOpPathStr = listToStr(otherOpPath)
                uniqPathID[otherOpPathStr] = curOpName+"_2"

                print ("\n\t <findUniqPath> 2. curOpPathStr: %s opPathID: %s otherOpPathStr: %s otherOpPathID: %s "%(curOpPathStr,uniqPathID[curOpPathStr],otherOpPathStr,uniqPathID[otherOpPathStr] ))
            else:
                print ("\t sameOpRepeated: %s adding curOpName: %s to duplSet "%(sameOpRepeated,curOpName))
                duplSet[curOpName] = copy.deepcopy(uniqOpNames[curOpName])    
        else:
            print ("\t len(uniqOpNames[curOpName]): %s adding curOpName: %s to duplSet "%(len(uniqOpNames[curOpName]),curOpName))
            duplSet[curOpName] = copy.deepcopy(uniqOpNames[curOpName])

    for curOpName in duplSet:
        opConstructStrLen = 2 # last term already matches, so atleast need two terms to distinguish.
        uniqComboNotFound = True

        print ("\n\t <findUniqPath> 3.1 curOpName: %s len(duplSet[curOpName]): %d "%(curOpName,len(duplSet[curOpName])))

        while(uniqComboNotFound):
            exit_flag = False
            newOpCombos = []
            print ("\t <findUniqPath> 3.2 curOpName: %s opConstructStrLen: %d "%(curOpName,opConstructStrLen))
            for curOpPath in duplSet[curOpName]:
                curPathLen = len(curOpPath)

                if(curPathLen>=opConstructStrLen):
                    curPathProspectiveID = listToStr(curOpPath[-opConstructStrLen:])
                    newOpCombos.append(curPathProspectiveID)
                else:
                    curPathProspectiveID = listToStr(curOpPath[-opConstructStrLen:])
                    newOpCombos.append(curPathProspectiveID)
                """
                else:
                    print ("\t ERROR! opConstructStrLen: %d is larger than length: %d of path: %s "%(opConstructStrLen,curPathLen,curOpPath))
                    print ("\t duplSet --> "%(duplSet[curOpName]))
                    exit_flag = True
                """
            if(len(newOpCombos) == len(set(newOpCombos)) ): # implies all combos are unique!
                for idx,curOpPath in enumerate(duplSet[curOpName]):
                    curOpPathStr = listToStr(curOpPath)
                    uniqPathID[curOpPathStr] = newOpCombos[idx]
                    print ("\t <findUniqPath> 3. idx: %d curOpPath: %s pathID: %s "%(idx,curOpPath,newOpCombos[idx]))
                uniqComboNotFound = False
            else:
                opConstructStrLen+=1
    collectedData['uniqPathID'] = uniqPathID
    #sys.exit()


def getReqTypeStats(opFolder,fileSuffix,numReqs,reqType,monMachine,exptEndTime):

    traceFile = str(opFolder)+"/"+str(reqType)+"_traceids.txt"
    traceIDs = getTraceIDs(exptEndTime,traceFile,reqType,monMachine,numReqs)

    allOpNames = [] # ordered list.
    collectedData = {} # has an array of values (one per trace) for each entry in allOpNames. 

    getTraceInfo(traceFile,allOpNames,collectedData)

    fSuffix = str(fileSuffix)+".log"
    durtnOpFilename = str(opFolder)+"/"+str(reqType)+"_durtn_"+str(fSuffix)
    stTimeOpFilename = str(opFolder)+"/"+str(reqType)+"_stTime_"+str(fSuffix)
    nonChildDurtnOpFilename = str(opFolder)+"/"+str(reqType)+"_nonChildDurtn_"+str(fSuffix)
    headerMapFilename = str(opFolder)+"/header_"+str(reqType)+".log"

    print ("\t durtnOpFilename: %s "%(durtnOpFilename))
    writeFormattedData(durtnOpFilename,allOpNames,collectedData,'durtn')
    writeFormattedData(stTimeOpFilename,allOpNames,collectedData,'startTime')
    writeFormattedData(nonChildDurtnOpFilename,allOpNames,collectedData,'nonChildDurtn')

    #opFile.write("\n\n uniqPath to complete path mapping")
    opFile = open(headerMapFilename,"w")
    newOpnamesSet = []
    for curOpFullPath in allOpNames:
        print ("\t opTag: %s uniqPathName: %s "%(curOpFullPath,collectedData['uniqPathID'][curOpFullPath]))
        #newOpnamesSet.append(collectedData['uniqPathID'][curOpFullPath])
        opFile.write("%s\t%s\n"%(collectedData['uniqPathID'][curOpFullPath],curOpFullPath))

    opFile.write("\t expected len: %s \n"%(numReqs))
    opFile.write("\t obtained len: %s \n"%(len(collectedData[allOpNames[0]]['durtn'])))
    opFile.close()
    
    print ("\t headerMapFilename: %s "%(headerMapFilename))


def main(args):

    numArgs = 5
    if(len(args)<=numArgs):
        print ("\t Usage: <opFolder> <fileSuffix> <numComposeReqs> <homeReqs> <userReqs> ")
        return

    opFolder = args[1]
    fileSuffix = args[2]

    applnName = args[3]
    monMachine = args[4]
    applnArgsStart = 5

    if(not(applnName in listOfApps)):
        print ("\t Appln: %s is not in recognized list: %s "%(applnName,listOfApps))
        sys.exit()
    
    if(applnName=="SN"):    
        exptEndTime = int(args[applnArgsStart+0])
        numComposeReqs = int(args[applnArgsStart+1])
        numHomeReqs = int(args[applnArgsStart+2])
        numUserReqs = int(args[applnArgsStart+3])

        getReqTypeStats(opFolder,fileSuffix,numComposeReqs,'compose',monMachine,exptEndTime)
        getReqTypeStats(opFolder,fileSuffix,numHomeReqs,'home',monMachine,exptEndTime)
        getReqTypeStats(opFolder,fileSuffix,numUserReqs,'user',monMachine,exptEndTime)

    elif(applnName=="HR"):    
        exptEndTime = int(args[applnArgsStart+0])
        numTotalReqs = int(args[applnArgsStart+1])
        return
        # based on the load mixture, caculate the number of requests, and call getReqTypeStats() 4 times for the 4 different request types.
        getReqTypeStats(opFolder,fileSuffix,numComposeReqs,'compose',monMachine,exptEndTime)
        getReqTypeStats(opFolder,fileSuffix,numHomeReqs,'home',monMachine,exptEndTime)
        getReqTypeStats(opFolder,fileSuffix,numUserReqs,'user',monMachine,exptEndTime)

    elif(applnName=="MM"):    
        exptEndTime = int(args[applnArgsStart+0])

        reviewComposeReqs =  int(args[applnArgsStart+1])
        reviewReadReqs =  int(args[applnArgsStart+2])
        plotReadReqs =  int(args[applnArgsStart+3])   
        
        getReqTypeStats(opFolder,fileSuffix,reviewComposeReqs,'reviewCompose',monMachine,exptEndTime)
        getReqTypeStats(opFolder,fileSuffix,reviewReadReqs,'reviewRead',monMachine,exptEndTime)
        getReqTypeStats(opFolder,fileSuffix,plotReadReqs,'plot',monMachine,exptEndTime)
    elif(applnName=="TT"):
         exptEndTime = int(args[applnArgsStart+0])
 
         book =  int(args[applnArgsStart+1])
         search =  int(args[applnArgsStart+2])
 
         getReqTypeStats(opFolder,fileSuffix,book,'book',monMachine,exptEndTime)
         getReqTypeStats(opFolder,fileSuffix,search,'search',monMachine,exptEndTime)


if __name__ == "__main__":
    main(sys.argv)
