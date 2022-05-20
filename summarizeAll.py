#! /usr/bin/python3

import sys,subprocess

verbose = 0
snReqTypes = ["compose","home","user"]
mmReqTypes = ["review_compose","review_read","plot_read"]
rpsRes = [100,200,300,400,600,650,700,750,800,850]#,900,950,1000]

def checkColumns(folderPrefix,allReqTypes):
    start = 50
    end = 60

    numIters = 3
    for curReqType in allReqTypes:
        print ("\n\n\t **** Cur req type: %s *****"%(curReqType))
        initOp = []

        for curRps in rpsRes:
            for curIter in range(1,numIters+1):
                curDir = str(folderPrefix)+str(curRps)+"/i"+str(curIter)
                # All columns
                if( ( (curRps==100) or (curRps == 650) ) and (curIter==1)): continue;        

                grepCmd = "grep traceID "+str(curDir)+"/"+str(curReqType)+"*durtn*"
                #print (grepCmd)
                op = subprocess.check_output(grepCmd,shell=True,universal_newlines=True)
                tempOp = sorted(op.split("\t"))
                sortedOp = []
                for curOp in tempOp:
                    sortedOp.append(curOp.strip())

                if(len(initOp) ==0):
                    initOp = sortedOp
                    if(verbose): print ("Len(initOps): %d\n%s"%(len(initOp),initOp))

                compArrayRes = (initOp == sortedOp)
                if(verbose): print ("\nDir: %s\t%s"%(curDir,compArrayRes))
                if(not compArrayRes):
                    missingInInitOp = [ curOp for curOp in sortedOp if not curOp in initOp ]
                    if(verbose): print ("\t missingInInitOp: %s \t len(sortedOp): %d "%(missingInInitOp,len(sortedOp)))

                    initOp = initOp + missingInInitOp
                    initOp = sorted(initOp)
                    #print (sortedOp)
    
        curTermAvgVals = {}
        curTermCountVals = {}
        for curOp in initOp:
            curTermAvgVals[curOp] = []
            curTermCountVals[curOp] = []

        avgValsHeader = "\top-name"
        for curRps in rpsRes:
            for curIter in range(1,numIters+1):
                curDir = str(folderPrefix)+str(curRps)+"/i"+str(curIter)
                # All columns
                if( ( (curRps==100) or (curRps == 650) ) and (curIter==1)): continue;        
                if( (curRps ==800) and (curIter==3)): continue
                grepCmd = "grep traceID "+str(curDir)+"/"+str(curReqType)+"*durtn*" 
                op = subprocess.check_output(grepCmd,shell=True,universal_newlines=True)
                curDirOps = op.split("\t")

                grepCmd = "grep averg "+str(curDir)+"/"+str(curReqType)+"*durtn*" 
                op = subprocess.check_output(grepCmd,shell=True,universal_newlines=True)
                curDirOpsAvgVals = op.split("\t")

                grepCmd = "grep count "+str(curDir)+"/"+str(curReqType)+"*durtn*" 
                op = subprocess.check_output(grepCmd,shell=True,universal_newlines=True)
                curDirOpsCountVals = op.split("\t")

                collectedOps = []
                if(  ( len(curDirOps) != len(curDirOpsAvgVals) ) or ( len(curDirOps) != len(curDirOpsCountVals) ) ):
                    print ("\t curDir: %s len(curDirOps): %d len(curDirOpsAvgVals): %d len(curDirOpsCountVals): %d "%(curDir,len(curDirOps),len(curDirOpsAvgVals),len(curDirOpsCountVals)))
                    sys.exit();

                for opIdx,curOp in enumerate(curDirOps): 
                    curOp = curOp.strip()
                    curTermAvgVals[curOp].append(curDirOpsAvgVals[opIdx].strip())
                    curTermCountVals[curOp].append(curDirOpsCountVals[opIdx].strip())
                    collectedOps.append(curOp)

                for curOp in initOp:
                    if(not (curOp in collectedOps)):
                        curTermAvgVals[curOp].append(0)
                        curTermCountVals[curOp].append(0)

                avgValsHeader=str(avgValsHeader)+"\t"+str(curRps)+"_i"+str(curIter)

        
        for curRps in rpsRes:
            avgValsHeader=str(avgValsHeader)+"\t"+str(curRps)

        print ("%s"%(avgValsHeader))
        avgVals = []
        countVals = []
        for curOp in initOp:

            curOpAvgStmt = "\t"+str(curOp)
            curOpCountStmt = "\t"+str(curOp)
            rpsIterIdx = 0
            for curRps in rpsRes:
                for curIter in range(1,numIters+1):
                    if( ( (curRps==100) or (curRps == 650) ) and (curIter==1)): continue;        
                    if( (curRps ==800) and (curIter==3)): continue;

                    curOpAvgStmt = str(curOpAvgStmt)+"\t"+str(curTermAvgVals[curOp][rpsIterIdx])
                    curOpCountStmt = str(curOpCountStmt)+"\t"+str(curTermCountVals[curOp][rpsIterIdx])
                    rpsIterIdx+=1

            avgVals.append(curOpAvgStmt)
            countVals.append(curOpCountStmt)

        print ("\t Avg Vals -->")
        print ("%s"%(avgValsHeader))
        for curLine in avgVals:
            print(curLine)

        print ("\t Count Vals -->")
        print ("%s"%(avgValsHeader))
        for curLine in countVals:
            print(curLine)


def findRepeatedID():
    filename = "sort_comb.log"
    sortFile = open(filename).readlines()
    prevLine = ""
    listOfMatches = []
    for curLine in sortFile:
        curLine = curLine.strip()
        if(prevLine == curLine):
            listOfMatches.append(curLine)
        prevLine = curLine

    i1IDs = []; i2IDs = []; i3IDs = []; 
    i1Contents = open("i1.log").readlines(); 
    for curLine in i1Contents: 
        i1IDs.append(curLine.strip())

    i2Contents = open("i2.log").readlines()
    for curLine in i2Contents: 
        i2IDs.append(curLine.strip())
    
    i3Contents = open("i3.log").readlines()
    for curLine in i3Contents: 
        i3IDs.append(curLine.strip())

    i1i3matches = []
    for idx in range(len(i1IDs)):
        if(i1IDs[idx] in i3IDs):
            i1i3matches.append(i1IDs[idx])
    print ("\t Comparing i1 and i3\n%s\n%d "%(i1i3matches,len(i1i3matches)))

    i1i2matches = []
    for idx in range(len(i2IDs)):
        if(i2IDs[idx] in i1IDs):
            i1i2matches.append(i2IDs[idx])
    print ("\t Comparing i1 and i2\n%s\n%d "%(i1i2matches,len(i1i2matches)))

    i3i2matches = []
    for idx in range(len(i2IDs)):
        if(i2IDs[idx] in i3IDs):
            i3i2matches.append(i2IDs[idx])
    print ("\t Comparing i3 and i2\n%s\n%d "%(i3i2matches,len(i3i2matches)))
    #print ("\t %s\n len(listOfMatches): %d  "%(listOfMatches,len(listOfMatches)))

def get_num(x):
    return float(''.join(ele for ele in x if ele.isdigit() or ele == '.'))

def getAvg(folderPrefix,allReqTypes):

    summary = {}
    for curReqType in allReqTypes:
        print ("\t **** Cur req type: %s *****"%(curReqType))
        initOp = []
        summary[curReqType] = {}
        summary[curReqType]['mean'] = []
        summary[curReqType]['stddev'] = []

        for curRps in rpsRes:
            curDir = str(folderPrefix)+str(curRps)
            print ("\t curDir: %s "%(curDir))

            #cat results/v0.50*/summary_avg* | grep compose | awk '{print $3"\t"$6}' 
            grepCmd = "cat "+str(curDir)+"/summary_avg* | grep Mean | grep "+str(curReqType)+" | awk '{print $3\"\t\"$6}'" 
            op = subprocess.check_output(grepCmd,shell=True,universal_newlines=True)
            sortedOp = sorted(op.split("\n"))

            meanAccum = 0.0
            stdDevAccum = 0.0 # this is WRONG, but trying to use it for now.
            count = 0

            for curLine in sortedOp:
                if(curLine==""):
                    continue;
                curLineTerms = curLine.split("\t")
                if(len(curLineTerms)!=2):
                    print ("\t Some error with opLine: %s len(curLineTerms): %s "%(curLine,curLineTerms))
                    sys.exit()

                print ("\t curLineTerms: %s "%(curLineTerms))
                mean = get_num(curLineTerms[0])
                stddev = get_num(curLineTerms[1])

                meanAccum+=mean
                stdDevAccum+=stddev
                count+=1
                print ("\t RPS: %s mean: %.3f stddev: %.3f "%(curRps,mean,stddev))
            print ("")
            summary[curReqType]['mean'].append(meanAccum/count)
            summary[curReqType]['stddev'].append(stdDevAccum/count)

    
    for curReqType in allReqTypes:
        print ("\n")
        dirIdx = 0
        for curRps in rpsRes:
            #resStr = str(curReqType)+"\tv0."+str(curDir)+"\t"+str(rps['0.'+str(curDir)])+"\t"+str('%.3f'%(summary[curReqType]['mean'][dirIdx]))+"\t"+str('%.3f'%(summary[curReqType]['stddev'][dirIdx]))
            curDir = str(folderPrefix)+str(curRps)
            resStr = str(curReqType)+"\t"+str(curDir)+"\t"+str(curRps)+"\t"+str('%.3f'%(summary[curReqType]['mean'][dirIdx]))+"\t"+str('%.3f'%(summary[curReqType]['stddev'][dirIdx]))
            dirIdx+=1
            print ("%s"%(resStr))



def analyzeLargestColumn(folderPrefix,allReqTypes):
    #grep averg results/v0.64/i2/home_durtn*.log | awk '{sum=0;largestIdx=0;for(i=2;i<=NF;i++) if(sum<$i){sum=$i;largestIdx=i}; print sum"\t"largestIdx}'

    startBin = 0 
    numBins = 20
    largestBinMultiplier = 5

    for curRps in rpsRes:
        curDir = str(folderPrefix)+str(curRps)

        for curIter in range(1,numIters+1):
            # Number of columns
            if( ( (curRps==100) or (curRps == 650) ) and (curIter==1)):
                continue;
            for curReq in allReqs:

                #filename = "results/v0."+str(curDir)+"/i"+str(curIter)+"/"+str(curReq)+"_durtn*.log"
                #probFilename = "results/v0."+str(curDir)+"/i"+str(curIter)+"/problem_"+str(curReq)+".log"
                filename = str(curDir)+"/i"+str(curIter)+"/"+str(curReq)+"_durtn*.log"
                probFilename = str(curDir)+"/i"+str(curIter)+"/problem_"+str(curReq)+".log"

                grepCmd = "grep averg "+str(filename)+" | awk '{sum=0;largestIdx=0;for(i=2;i<=NF;i++) if(sum<$i){sum=$i;largestIdx=i}; print sum\"\t\"largestIdx}' "
                grepOp = subprocess.check_output(grepCmd,shell=True,universal_newlines=True)
                grepOp = grepOp.split("\t")

                #print ("\t grepCmd: %s grepOp: %s "%(grepCmd,grepOp))
                larIdx_avgVal = float(grepOp[0])
                larIdx = int(grepOp[1])

                findLarColumnCmd = "grep traceID "+str(filename)+" | awk '{print $"+str(larIdx)+"}'"
                larColumnOp = subprocess.check_output(findLarColumnCmd,shell=True,universal_newlines=True)
                larColumn = larColumnOp.strip().split('\t')[0]
                largestBin = largestBinMultiplier*larIdx_avgVal
                binSize = (largestBin-startBin) / numBins

                binBoundaries = [ idx*(binSize) for idx in range(numBins+1)]
                print ("\t curReq: %s filename: %s larColumn: %s larIdx: %d larIdx_avgVal: %.3f ms"%(curReq,filename,larColumn,larIdx,larIdx_avgVal/1e3))
                binCounts = []
                
                print ("\n\tbinBoundary\tbinCount")
                for curBinMax in binBoundaries:
                    awkCmd = "awk '{ if ($"+str(larIdx)+" > "+str(curBinMax)+") print }' "+str(filename)+" | wc -l "
                    awkOp = subprocess.check_output(awkCmd,shell=True,universal_newlines=True)
                    curBinCount = int(awkOp.strip().split("\t")[0])
                    #print ("\t awkCmd: %s \t awkOp: %d "%(awkCmd,curBinCount))
                    print ("\t%.3f ms\t%d"%(curBinMax/1e3,curBinCount))
                    binCounts.append(curBinCount)

                getProbColumns = "awk '{ if ($"+str(larIdx)+" > "+str((largestBinMultiplier-1)*larIdx_avgVal)+") print }' "+str(filename)+" | sort -grk"+str(larIdx)+" > "+str(probFilename)
                subprocess.check_output(getProbColumns,shell=True,universal_newlines=True)
                #print ("\t probFilename: %s "%(probFilename))
                #sys.exit()

#checkColumns()
#findRepeatedID()
listOfApps = ["SN","HR","MM"]
appReqTypeMap = {
    "SN" : snReqTypes,
    "MM" : mmReqTypes,
}

folderPrefix = sys.argv[1]
appCode = sys.argv[2]

if(not appCode in listOfApps):
    print ("\t appCode: %s is not found in list of apps.. "%(appCode,listOfApps))
    sys.exit()

curAppReqTypes = appReqTypeMap[appCode]

getAvg(folderPrefix,curAppReqTypes)
#analyzeLargestColumn(folderPrefix,curAppReqTypes)
#checkColumns(folderPrefix,curAppReqTypes)
