#! /usr/bin/python3

import sys,subprocess
import multiprocessing

import pandas as pd

cpuCols = ['cpu_stats_system_cpu_usage', 'cpu_stats_online_cpus','cpu_stats_cpu_usage_total_usage', 'c_c_usage_in_kernelmode', 'c_c_usage_in_usermode']
memoryCols = [ 'memory_stats_usage','memory_stats_max_usage']
memoryDetailedCols = ['memory_stats_limit', 'memory_stats_stats_active_anon', 'm_s_active_file', 'm_s_cache', 'm_s_dirty', 
    'm_s_hierarchical_memory_limit', 'm_s_total_mapped_file','m_s_total_pgfault', 'm_s_total_pgmajfault', 'm_s_total_pgpgin', 'm_s_total_pgpgout', 'm_s_total_rss', 
    'm_s_total_rss_huge', 'm_s_total_unevictable', 'm_s_total_writeback', 'm_s_unevictable', 'm_s_writeback' ]
networkCols = ['networks_eth0_rx_bytes', 'n_e_rx_packets', 'n_e_rx_errors', 'n_e_rx_dropped', 'n_e_tx_bytes', 'n_e_tx_packets','n_e_tx_errors', 'n_e_tx_dropped']

allCols = cpuCols + memoryCols + memoryDetailedCols + networkCols
numCores = multiprocessing.cpu_count()

# Will ignore first row of data.
def getCpuPercent(ipData,procData):
    numCols = len(ipData)
    print ("\tnumRows: %d\t interested cols: %s"%(numCols,cpuCols))
    prevRow = ipData.iloc[0]#[cpuCols]

    allStats = [] #cpuStats = []; memStats = []; netRxStats = []; netTxStats = []
    allStrStats = []
    for curRowNum in range(1,numCols):
        curRow = ipData.iloc[curRowNum]#[cpuCols]
        if(curRowNum%20==0): print ("row: %d "%(curRowNum)) #print ("\tcurRow: %s \t prevRow: %s "%(curRow[cpuCols],prevRow[cpuCols]))

        cpuDelta = curRow['cpu_stats_cpu_usage_total_usage'] - prevRow['cpu_stats_cpu_usage_total_usage']
        systemDelta = curRow['cpu_stats_system_cpu_usage'] - prevRow['cpu_stats_system_cpu_usage'] #float64(v.CPUStats.SystemUsage) - float64(previousSystem)

        cpuPercent = 0.0
        if( (systemDelta > 0.0) and (cpuDelta > 0.0) ):
            cpuPercent = (cpuDelta / systemDelta) * numCores*100.0 #float64(len(v.CPUStats.CPUUsage.PercpuUsage)) * 100.0
        #cpuStats.append(cpuPercent)

        memPercent = 0.0
        if(curRow['memory_stats_limit']!=0):
            memPercent = (float(curRow['memory_stats_usage'])/curRow['memory_stats_limit'])*100.0
        #memStats.append(memPercent)

        rxKBytes = float( (curRow['networks_eth0_rx_bytes']-prevRow['networks_eth0_rx_bytes'])/1024) 
        txKBytes = float( (curRow['n_e_tx_bytes']-prevRow['n_e_tx_bytes'])/1024) 
        #netRxStats.append(rxKBytes); netTxStats.append(txKBytes)

        procRowStats = [ cpuPercent,memPercent,rxKBytes,txKBytes ]
        allStats.append(procRowStats)
        procRowLine = str('%.3f'%(cpuPercent))+","+str('%.3f'%(memPercent))+","+str('%.3f'%(rxKBytes))+","+str('%.3f'%(txKBytes))
        allStrStats.append(procRowLine)

        #print ("\t cpuDelta: %.3f systemDelta: %.3f cpuPercent: %.3f "%(cpuDelta,systemDelta,cpuPercent))
        prevRow = curRow

    #procData['cpuStats'] = cpuStats; procData['memStats'] = memStats; procData['netRxStats'] = netRxStats; procData['netTxStats'] = netTxStats
    procData['allStats'] = allStats
    procData['allStrStats'] = allStrStats
    return

ipDir = sys.argv[1]
ipFile = sys.argv[2]

ipFilePath = str(ipDir)+"/"+str(ipFile)
ipData = pd.read_csv(ipFilePath,sep=",",header=0)
print ("\t len(ipData.columns): %d"%(len(ipData.columns)))

procData = {}
getCpuPercent(ipData,procData)

opFilename = str(ipDir)+"/proc_"+str(ipFile)
opFile = open(opFilename,"w")
header = "cpu_pct,mem_pct,net_rx_kbytes,net_tx_kbytes"

opFile.write(str(header)+"\n")
for curLine in procData['allStrStats']:
    #print (curLine)
    opFile.write(str(curLine)+"\n")
opFile.close()

print ("\t Output file: %s "%(opFilename))
