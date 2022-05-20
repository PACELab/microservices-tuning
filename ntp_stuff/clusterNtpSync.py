#! /usr/bin/python3

import sys,subprocess,time

#userv1 is the ntp server
allMachines = ["userv2","userv3","userv4","userv5","userv6","userv7","userv8"] 
allMachines = []

scpConfFile = ["scp","-i","/home/ubuntu/compass.key","/home/ubuntu/uservices/uservices-perf-analysis/ntp_stuff/ntp.conf","scpPath /etc"]  
scpCmd8 = ["scp","-i","/home/ubuntu/compass.key","ntpSync.sh","scpPath ~/"]
runScpScriptCmd = ["ssh","-i","/home/ubuntu/compass.key","sshMachine","/home/ubuntu/ntpSync.sh","&"]
scpCmd9 = ["scp","-i","/home/ubuntu/compass.key","scpPath ~/ntp_*.log","ntp_logs/"]
runSynthLogsCmd = ["./printLogFiles.sh"]
toRunCmds = [scpConfFile, scpCmd8,runScpScriptCmd,"sleepCmd",scpCmd9]
#toRunCmds = [scpCmd9]

for curCmdPrefix in toRunCmds:
    print(curCmdPrefix)
    if(curCmdPrefix=="sleepCmd"):
        time.sleep(550) #(420)
        continue;
    for curMachineIdx,curMachine in enumerate(allMachines):
        curCmd = []
        for curTerm in curCmdPrefix:
            
            if(curTerm.startswith("scpPath")):
                splitTerm = curTerm.split(" ")

                if(len(splitTerm)==2):
                    dirPath = splitTerm[1]
                else:
                    print ("\t Error! curTerm: %s splitTerm: %s "%(curTerm,splitTerm))
                    sys.exit()
                
                curCmd.append(str('ubuntu@'+str(curMachine)+':'+str(dirPath)))

            elif(curTerm.startswith("sshMachine")):
                curCmd.append(str('ubuntu@'+str(curMachine)))
            else:
                curCmd.append(curTerm)

        #out = subprocess.check_output(curCmd,stderr=subprocess.PIPE,stdout=subprocess.PIPE,universal_newlines=True)

        # try: 
        #     out = subprocess.check_output(curCmd,universal_newlines=True)
        # except Exception as e:
        #     print ("\t Error: %s "%(e))

        try:
            #out = subprocess.check_output(curCmd,universal_newlines=True)
            print(" ".join(curCmd))
            Pobj = subprocess.Popen(curCmd,stderr=subprocess.PIPE,stdout=subprocess.PIPE,universal_newlines=True)
            #print ("\t out: %s "%(out))
        except Exception as e:
            print ("\t Error: %s "%(e))
    time.sleep(2)

out = subprocess.check_output(runSynthLogsCmd,universal_newlines=True)
print ("\t out: %s "%(out))
