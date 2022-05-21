#! /usr/bin/python3

import sys,subprocess
import socket

def initializeUser(frontEndHostname,durtnSeconds,rps,user_id):
    frontEndHostIP = socket.gethostbyname(frontEndHostname)  
    wrkCmdPrefix = "/home/ubuntu/uservices/uservices-perf-analysis/socialNetwork/snWrk/wrk -D exp -t 1 -c 1 -d "+str(durtnSeconds)
    wrkCmdUrl = " -L -s /home/ubuntu/uservices/uservices-perf-analysis/socialNetwork/snWrk/scripts/social-network/init-posts.lua http://"+str(frontEndHostIP)+":8080/wrk2-api//post/compose "
    wrkCmd = str(wrkCmdPrefix)+" "+str(wrkCmdUrl)+" -R "+str(rps)+" -- "+str(user_id)

    print ("\t wrkCmd: %s "%(wrkCmd))
    try: 
        stdout = subprocess.check_output(wrkCmd,shell=True,universal_newlines=True)
        print (stdout)
    except Exception as err:
        print ("\t Error: %s happened while initializing user: %d "%(user_id))
        
def main(args):
    numArgs = 5
    if(len(args)<=numArgs):
        print ("\t Usage: <frontEndHostname> <numRequests> <rps> <startUserId> <endUserId>")
        return

    frontEndHostname = args[1]
    numRequests = int(args[2])
    rps = int(args[3])
    startUserId = int(args[4])
    endUserId = int(args[5])

    durtnSeconds = int(numRequests/rps) 
    for curUserId in range(startUserId,endUserId+1):
        initializeUser(frontEndHostname,durtnSeconds,rps,curUserId)


if __name__ == "__main__":
    main(sys.argv)
