#! /usr/bin/python3

import time,sys,subprocess

def getNumReqs(reqIdentifier):
    #the wrk logs files might not be copied yet. So sleeping for 30s
    error_mesgs = ["unable to connect to"]
    grepCmd = "grep requests "+str(ipFolder)+"/"+str(reqIdentifier)+".log | awk '{print $1}' " 
    print ("\t grepCmd: %s "%(grepCmd))
    output = subprocess.check_output("cat "+str(ipFolder)+"/"+str(reqIdentifier)+".log",shell=True,universal_newlines=True)
    for mesg in error_mesgs:
        if mesg in output:
            diffReqsStr = "0"
    diffReqsStr = subprocess.check_output(grepCmd,shell=True,universal_newlines=True)
    diffReqsStr = subprocess.check_output(grepCmd,shell=True,universal_newlines=True)
    print ("output %s"%(diffReqsStr))
    return int(diffReqsStr.strip())    

"""
def mpstats_summary():
    
    subprocess.check_output("awk '/all/ {printf $12"\n" }' v_default_dsb_0_rps300/i1/mpstats_v_default_dsb_0_rps300_userv5.log | datamash max 1 min 1 mean 1 median 1",shell=True,universal_newlines=True)
"""

listOfApps = ["SN","HR","MM", "TT"]

ipFolder = sys.argv[1]
exptVersion = sys.argv[2]
applnName = sys.argv[3]
monMachine = sys.argv[4]
emailRecipient = sys.argv[5]

if(not(applnName in listOfApps)):
    print ("\t Appln: %s is not in recognized list: %s "%(applnName,listOfApps))
    sys.exit()

if(applnName=="SN"):
    composeReqs =  getNumReqs("compose")
    homeReqs =  getNumReqs("home")
    userReqs =  getNumReqs("user")

    epochUS = int(time.time()*1e6)

    extractJaegerCmd = "./extractJaegerData.py "+str(ipFolder)+" "+str(exptVersion)+" "+str(applnName)+" "+str(monMachine)+" "+str(epochUS)+" "+str(composeReqs)+" "+str(homeReqs)+" "+str(userReqs)+" "+str(epochUS)

elif(applnName=="HR"):
    latencyReqs =  getNumReqs("latency")

    epochUS = int(time.time()*1e6)

    extractJaegerCmd = "./extractJaegerData.py "+str(ipFolder)+" "+str(exptVersion)+" "+str(applnName)+" "+str(monMachine)+" "+str(epochUS)+" "+str(latencyReqs)+" "+str(epochUS)

elif(applnName=="MM"):
    reviewComposeReqs =  getNumReqs("review_compose")
    reviewReadReqs =  getNumReqs("review_read")
    plotReadReqs =  getNumReqs("plot_read")

    epochUS = int(time.time()*1e6)

    extractJaegerCmd = "./extractJaegerData.py "+str(ipFolder)+" "+str(exptVersion)+" "+str(applnName)+" "+str(monMachine)+" "+str(epochUS)+" "+str(reviewComposeReqs)+" "+str(reviewReadReqs)+" "+str(plotReadReqs)
elif(applnName == 'TT'):

    tt_total_requests =  getNumReqs("latency")
    epochUS = int(time.time()*1e6)

    extractJaegerCmd = "./extractJaegerData.py "+str(ipFolder)+" "+str(exptVersion)+" "+str(applnName)+" "+str(monMachine)+" "+str(epochUS)+"  "+str(tt_total_requests//2)+" "+str(tt_total_requests//2)

analyzeFilename = str(ipFolder)+"/analyze.sh"
analyzeFile = open(analyzeFilename,"w")

analyzeFile.write("#! /bin/bash "+"\n\n")
analyzeFile.write(str(extractJaegerCmd)+"\n")

content = "echo \" `ls -ltr "+str(ipFolder)+"` \" "
mailHeading = " \"Jaeger data downloaded for expt version "+str(exptVersion)+" at `date` \" %s@cs.stonybrook.edu "%(emailRecipient) #-A "+str(summaryFilename)
emailCmd = str(content)+"  | mail -s "+str(mailHeading)

analyzeFile.write("\n"+str(emailCmd)+"\n")
analyzeFile.close()

subprocess.check_output("chmod +x "+str(analyzeFilename),shell=True,universal_newlines=True)
print ("\t analyzeFilename: %s extractJaegerCmd: %s "%(analyzeFilename,extractJaegerCmd))

#extrJaegerOutput = subprocess.check_output(extractJaegerCmd,shell=True,universal_newlines=True)
#print (extrJaegerOutput)
