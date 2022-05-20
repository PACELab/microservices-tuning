#! /usr/bin/python3

import sys,time,docker,subprocess

numArgs = 3
if(len(sys.argv)<=numArgs):
    #print ("\t Usage numConts: %d numSeconds: %d "%(numConts,numSeconds))
    print ("\t Usage <numConts> <numSeconds> <outputFolder> <experiment_iteration_number> ")
    sys.exit()

numConts = int(sys.argv[1])
numSeconds = int(sys.argv[2])
tempOutputFolder = sys.argv[3]
iter_num = int(sys.argv[4])
outputFolder = tempOutputFolder.split(' ')[0]

try:
    subprocess.check_output("mkdir "+str(outputFolder),shell=True,universal_newlines=True)
except Exception as err:
    print ("\t Likely folder: %s already exists err: %s "%(outputFolder,err))

client = docker.from_env()
allConts = client.containers.list()

# fields of stats: ['read', 'preread', 'pids_stats', 'blkio_stats', 'num_procs', 'storage_stats', 'cpu_stats', 'precpu_stats', 'memory_stats', 'name', 'id', 'networks']
    # 'read': curTS,
    # 'preread': preread_TS, 
    # 'pids_stats': ['current'], 
    # 'blkio_stats' : ['io_service_bytes_recursive', 'io_serviced_recursive', 'io_queue_recursive', 'io_service_time_recursive', 'io_wait_time_recursive', 'io_merged_recursive', 'io_time_recursive', 'sectors_recursive']  
    # 'num_procs' : num_procs_val, 
    # 'storage_stats': {}, 
    # 'cpu_stats' : { cpu_usage: {total_usage,percpu_usage:[],usage_in_kernelmode,usage_in_usermode} , system_cpu_usage: system_cpu_usage_val, online_cpus : online_cpus_val, throttling_data :{periods,throttled_periods,throttled_time}  } , 
    # 'precpu_stats' : { cpu_usage: {total_usage,percpu_usage:[],usage_in_kernelmode,usage_in_usermode} , system_cpu_usage: system_cpu_usage_val, online_cpus : online_cpus_val, throttling_data :{periods,throttled_periods,throttled_time}  } , 
    # 'memory_stats' : ['usage', 'max_usage', 'limit', 
    #                   stats: {'active_anon','active_file','cache','dirty','hierarchical_memory_limit','hierarchical_memsw_limit','inactive_anon','inactive_file','mapped_file','pgfault','pgmajfault',
    #                           'pgpgin','pgpgout','rss','rss_huge','total_active_anon','total_active_file','total_cache','total_dirty','total_inactive_anon','total_inactive_file','total_mapped_file',
    #                           'total_pgfault','total_pgmajfault','total_pgpgin','total_pgpgout','total_rss','total_rss_huge','total_unevictable','total_writeback','unevictable','writeback'}] , 
    # 'name', 
    # 'id', 
    # 'networks' : {interface: {{'rx_bytes','rx_packets','rx_errors','rx_dropped','tx_bytes','tx_packets','tx_errors','tx_dropped'}}}

# Ignoring following fields/subfields
    # cpu_stats: throttling_data and percpu_usage within cpu_usage
    # memory_stats: only subset of memory data.

    # precpu_stats: all of it
    # blkio_stats: all of it
    # num_procs: all of it
    # pids_stats: all of it
    # storage_stats 

start = time.time()
allContObjs = {}
sampling_interval = 1 #in seconds

#initialise the data structure
for idx,container in enumerate(allConts):
    stats = container.stats(decode=True)#,stream=False)
    if iter_num!= 0:
        clearDockerCmd = " sudo sh -c \" echo \"\" > $(docker inspect --format='{{.LogPath}}' "+str(container.id)+") \" "
        print ("\n%d.\t%s\tclearDockerCmd: %s "%(idx,container.id,clearDockerCmd))
        try:
            subprocess.check_output(clearDockerCmd,shell=True,universal_newlines=True)
        except Exception as err:
            print ("\t 1. err: %s happened while clearing logs of container: %s "%(err,container.id))

    allContObjs[container.name] = {}
    allContObjs[container.name]['obj'] = container
    allContObjs[container.name]['stats'] = stats
    allContObjs[container.name]['statsdump'] = []
    if(idx>=numConts):
        print("Warning: The number of containers is greater than the argument passed (%d)"%numConts)
        break

#collect stats in increments of <sampling_inteval> seconds
tsIdx = 1
while(tsIdx < numSeconds):
    for curContName in allContObjs:
        a = next(allContObjs[curContName]['stats'])
        allContObjs[curContName]['statsdump'].append(a)
        if(tsIdx%10==0): 
            timeElapsed = time.time()-start
            print ("\t tsIdx: %d timeElapsed: %.3f curContId: %s "%(tsIdx,timeElapsed,curContName))

    time.sleep(sampling_interval)
    tsIdx+=1

end = time.time()

subFields = {
    # 's' : scala values, 'v' : vector values. 'v' : An array of all the vector like elements. 
    # Each member of the array is a subarray of size 2, first member of the subarray being the 'key' and second member being the 'value'
    # 'v': [ [ , [] ] , [ , [] ] ]
    'cpu_stats' : { 's':['system_cpu_usage','online_cpus',], 'v': [ ['cpu_usage',['total_usage','usage_in_kernelmode','usage_in_usermode']] ], }, # ignoring throttling_data and percpu_usage within cpu_usage
    'memory_stats' : { 's' : ['usage','max_usage','limit'], 'v': [ [ 'stats' , ['active_anon','active_file','cache','dirty','hierarchical_memory_limit','total_mapped_file','total_pgfault','total_pgmajfault','total_pgpgin','total_pgpgout','total_rss','total_rss_huge','total_unevictable','total_writeback','unevictable','writeback'] ] ] },
    'networks' : {'s':[],'v': [ [ 'eth0' , ['rx_bytes','rx_packets','rx_errors','rx_dropped','tx_bytes','tx_packets','tx_errors','tx_dropped'] ] ]},
}

sortedSubFields = sorted(subFields.keys())
statsFiles = []
for curContName in allContObjs:

    curContLogFile = str(outputFolder)+"/log_"+str(curContName)+".log"
    #collectLogs_DockerCmd = " sudo sh -c \" cat $(docker inspect --format='{{.LogPath}}' "+str(container.id)+") > "+str(curContLogFile)+" \" "
    collectLogs_DockerCmd = "docker logs "+str(curContName)+" > "+str(curContLogFile)+" 2>&1 "
    print ("\t curContName: %s collectLogs_DockerCmd: %s "%(curContName,collectLogs_DockerCmd))    
    try: 
        subprocess.check_output(collectLogs_DockerCmd,shell=True,universal_newlines=True)
    except Exception as err:
        print ("\t 2. err: %s happened while collecting logs of container: %s "%(err,container.id))

    curContOutFilename = str(outputFolder)+"/"+str(curContName)+".log"
    curContOutFile = open(curContOutFilename,'w')
    statsFiles.append(curContOutFilename)

    statsHeader = ""
    for tsIdx,curContStats in enumerate(allContObjs[curContName]['statsdump']):
        #print ("\n\t%d\t%s"%(tsIdx,curContStats))
        if(tsIdx%10==0): print ("\t tsIdx: %d "%(tsIdx))

        statsLine = ""
        for curField in sortedSubFields:
            curSet = 's'
            for curSubField in subFields[curField][curSet]:
                #print ("\t curField: %s subField: %s val: %s "%(curField,curSubField,curContStats[curField][curSubField]))
                #print ("\t curField: %s subField: %s "%(curField,curSubField))
                if(tsIdx==0): 
                    if(statsHeader == ""):
                        statsHeader = str(curField)+"_"+str(curSubField)
                    else:
                        statsHeader = str(statsHeader)+","+str(curField)+"_"+str(curSubField)

                if(statsLine == ""):
                    statsLine = str(curContStats[curField][curSubField])
                else:
                    statsLine = str(statsLine)+","+str(curContStats[curField][curSubField])

            curSet = 'v'

            for vecName,curVecSubFields in subFields[curField][curSet]:
                for sfIdx,curSubField in enumerate(curVecSubFields):
                    #print ("\t curField: %s subField: %s val: %s "%(curField,curSubField,curContStats[curField][vecName][curSubField]))  

                    if(tsIdx==0): 
                        if(sfIdx==0):
                            statsHeader = str(statsHeader)+","+str(curField)+"_"+str(vecName)+"_"+str(curSubField)
                        else:
                            statsHeader = str(statsHeader)+","+str(curField[:1])+"_"+str(vecName[:1])+"_"+str(curSubField)

                    if(statsLine == ""):
                        statsLine = str(curContStats[curField][vecName][curSubField])
                    else:
                        statsLine = str(statsLine)+","+str(curContStats[curField][vecName][curSubField])
        if(tsIdx==0):
            curContOutFile.write(str(statsHeader)+"\n")
        curContOutFile.write(str(statsLine)+"\n")

        #print (statsLine)
    curContOutFile.close()

print ("\t diff: %.3f all log files --> "%( (end-start)))
for curStatFilename in statsFiles:
    print ("%s"%(curStatFilename))
