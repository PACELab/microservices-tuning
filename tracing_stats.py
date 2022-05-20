#! /usr/bin/python3

import sys,json,time,subprocess,copy
import requests
import random
import pandas as pd
from queue import Queue

application_list = ["SN","HR","MM", "TT"]
trace_collection_duration = (2*24*60*60*1000*1000)
n_traces_per_iteration = 1500

service_name_lookup = {
    'compose': 'nginx-web-server',
    'home' :  'nginx-web-server',
    'user' : 'nginx-web-server' ,
    'reviewCompose' : 'compose-review-service',
    'reviewRead' : 'movie-review-service&operation=ReadMovieReviews',
    'cast' : 'cast-info-service&operation=ReadCastInfo',
    'plot' : 'plot-service',
    # TT app
    'book': 'ts-preserve-other-service',
    'search': 'ts-travel-service',

}

operation_name_lookup = {
        'compose' : '/wrk2-api/post/compose',
        'home' : '/wrk2-api/home-timeline/read',
        'user' : '/wrk2-api/user-timeline/read'  ,
        #MM app
    'reviewCompose' : '/wrk2-api/review/compose',
    'reviewRead' : '/wrk2-api/review/read',
    'plot' : '/wrk2-api/plot/read',
    #TT app
    'search': 'queryInfo',
    'book': 'preserve',

        }


class TreeNode:
    def __init__(self, span = None, parent = None, value = 0, children = []):
        self.span = span
        self.parent = parent
        self.actual_duration = value
        self.visited = False
        self.children = children
                    # if reference ID (parent ID) of the current span matches that of the parent, add it.
def buildTree(spans, ignore_warnings = True):
    root = None
    
    #this is the root node
    for span in spans:
        if span["spanID"] == span["traceID"]:
            root = TreeNode(span, None, span['duration'], [])
            break
    que = Queue()
    que.put(root)
    
    while not que.empty():
        current = que.get()
        for span in spans:
            if not ignore_warnings and span["warnings"] is not None:
                raise
            if len(span["references"]) != 0 and span["references"][0]["spanID"] == current.span["spanID"]:
                value = span['duration'] 
                node = TreeNode(span, current, value, [])
                que.put(node)
                current.children.append(node)
        current.children.sort(key = lambda node: node.span["startTime"] + node.span["duration"]) # sort the children in ascending order of their end time. 
    return root

path = []
total = 0
def preorder_service_time_along_paths(root, current_path, current_total):
    global path
    global total
    if root:
        #print(processes[root.span["processID"]], root.span["operationName"], root.value)
        current_path.append((processes[root.span["processID"]],root.span["operationName"]))
        current_total += root.value
        for child in root.children:
            preorder_service_time_along_paths(child, current_path, current_total)
        if not root.children and current_total > total:
            total = current_total
            path = copy.deepcopy(current_path)
        current_path.remove((processes[root.span["processID"]],root.span["operationName"]))
        current_total -= root.value


critical_path = []
def find_critical_path(root):
    if root.children: 
        last_child = root.children[-1]
        children_duration = 0
        #print("find_critical_path(%s, %s)"%(processes[last_child.span["processID"]],last_child.span["operationName"]))
        find_critical_path(last_child)
        current_state = "async" # assume the children have overlap. If not, will be set to False.
        async_start = last_child.span["startTime"] 
        async_end = last_child.span["startTime"] + last_child.span["duration"]
        async_duration = async_end - async_start
        sync_duration = 0
        for younger_sibling in root.children[-2::-1]:
            if not younger_sibling.visited:
                if ( younger_sibling.span["startTime"] + younger_sibling.span["duration"]) < async_start:
                    if current_state == "async":
                        children_duration += async_duration
                        async_duration = 0
                    if current_state == "sync":
                        sync_duration += younger_sibling.span["duration"]
                    find_critical_path(younger_sibling)
                    current_state = "sync"
                else:
                    if current_state == "sync":
                        children_duration += sync_duration
                        sync_duration = 0
                        async_start = younger_sibling.span["startTime"]
                        async_end = younger_sibling.span["startTime"] + younger_sibling.span["duration"]
                    else:
                        if younger_sibling.span["startTime"] < async_start:
                            async_start = younger_sibling.span["startTime"]
                        async_duration = async_end - async_start
                    #print("younger " ,(processes[younger_sibling.span["processID"]],younger_sibling.span["operationName"]))
                    #print(younger_sibling.span["duration"])
                    current_state = "async"
        root.actual_duration -= (children_duration + sync_duration + async_duration )
    insert_node(root)

def insert_node(root):
    global critical_path
    root.visited = True
    if root.actual_duration > 1000 : #greater than 1ms
        critical_path.append((processes[root.span["processID"]], root.span["operationName"]))

def find_critical_path_buggy(root, relationship, ignore_relationship=False):
    """
    First include the last ending node. Recursively include its parent, grandparent, etc. This is similar to the FIRM code but the algorithm in the paper is different.
    """
    critical_path = []
    current_parent = root
    critical_path.append((processes[current_parent.span["processID"]], current_parent.span["operationName"]))
    while current_parent.children:
        # service, operation pair of the parent
        parent = ",".join([processes[current_parent.span["processID"]],current_parent.span["operationName"]])
        children_left = len(current_parent.children)
        # The sychronous child that ends the last should be included in the path. Since the children are already sorted in asceding order wrt to the end time, starting from the end. If that is asynchronous, choose the last but one (repeat until you run out of children or find a synchronous one)
        while children_left:
            candidate_next_parent = current_parent.children[children_left - 1] # The child that ends last is at the end
            # service, operation pair of the child/candidate_next_parent
            child = ",".join([processes[candidate_next_parent.span["processID"]],candidate_next_parent.span["operationName"]])
            try:
                if ignore_relationship or (not relationship[(relationship.parent == parent) & (relationship.child == child)]["async"].values[0]): #worst code. use dictionaries
                    current_parent = candidate_next_parent
                    critical_path.append((processes[current_parent.span["processID"]], current_parent.span["operationName"]))
                    break
            except Exception as e:
                print("%s add entry to the relationship.csv for caller %s and callee %s and try again"%(e, parent, child))
                sys.exit(0)
            children_left -= 1
        else:
            break
    return critical_path
    
def levelOrderTraverseTree(root):
    que = Queue()
    que.put(root)
    
    level = 0
    while not que.empty():
        print("LEVEL ", level)
        sz = que.qsize()
        for i in range(sz):
            temp = que.get()
            if temp.parent is None:
                print(processes[temp.span["processID"]], temp.span["operationName"])
            else: 
                print(processes[temp.span["processID"]],processes[temp.parent.span["processID"]], temp.span["operationName"])
            #print("children length ", len(temp.children))
            for child in temp.children:
                que.put(child)
        level += 1


#this is method which will work on service level
def processTreeServ(root, processes, service_time_dict, pcreldict):
    que = Queue()
    que.put(root)
    
    while not que.empty():
        sz = que.qsize()
        for i in range(sz):
            temp = que.get()
            curr_service_time = temp.span["duration"]
            pr_serv_op = processes[temp.span["processID"]] + ","+ temp.span["operationName"]
            
            for child in temp.children:
                child_serv_op = processes[child.span["processID"]] + "," + child.span["operationName"]
                final_serv_op = pr_serv_op + "," + child_serv_op
                if pcreldict[final_serv_op] == 1:
                    curr_service_time -= child.span["duration"]
                que.put(child)
            
            if processes[temp.span["processID"]] in service_time_dict:
                service_time_dict[processes[temp.span["processID"]]].append(curr_service_time)
            else:
                service_time_dict[processes[temp.span["processID"]]] = [curr_service_time]


processes = {}
service_operation = []
def get_service_and_operation_names(trace):
    global service_operation
    global processes
    service_operation = []
    processes = {}
    for process, data in trace['processes'].items():
        processes[process] = data["serviceName"]
    
    spans = trace['spans']
    
    for span in spans:
        service_name = processes[span["processID"]]
        operation_name = span["operationName"]
        service_operation.append(service_name + "," + operation_name)
    service_operation = list(set(service_operation))

def validate_trace(trace):
    if trace["warnings"] is not None:
        print(trace["warnings"])
        return False
    return True

def get_trace_info(trace_filename):
    global critical_path
    with open(trace_filename) as trace_data_f:
        traces_json_data = json.load(trace_data_f)
    traces_list = traces_json_data['data']
    loop_counter = 0
    #relationship = pd.read_csv("configs/meta/relationships_fake.csv", delim_whitespace = True)
    critical_path_services_count = {}
    critical_path_services_operation_count = {}
    total_issues = 0
    for trace in traces_list:
        loop_counter +=1
        #if loop_counter != 3:
            #continue
        #if loop_counter > 1:
        #    break
        if validate_trace(trace):
            get_service_and_operation_names(trace)
            spans = trace['spans']
            try:
                # set ignore warning to False for SN and MM
                root = buildTree(spans, ignore_warnings = True)
            except:
                total_issues += 1
                continue
            critical_path = []
            find_critical_path(root)
    
            # update services and operation count. TODO: move to a method
            services_only = set()
            for service_operation_pair in critical_path:
                services_only.add(service_operation_pair[0])
                if service_operation_pair not in critical_path_services_operation_count :
                    critical_path_services_operation_count[service_operation_pair] = 1 
                else:
                    critical_path_services_operation_count[service_operation_pair] += 1
    
            # update srvices count. TODO: move to a method
            for service in services_only:
                if service not in critical_path_services_count:
                    critical_path_services_count[service] = 1
                else:
                    critical_path_services_count[service] += 1
            #levelOrderTraverseTree(root)
            #preorder(root,[],0)
    for key in critical_path_services_count:
        print("%s %d"%(key, critical_path_services_count[key]))

    for key in critical_path_services_operation_count:
        print("%s %d"%(key, critical_path_services_operation_count[key]))
    print("Total issues %d"%total_issues)


def main(args):
    get_trace_info(args[1])
    sys.exit(0)
    numArgs = 5
    if(len(args)<=numArgs):
        print ("\t Usage: <opFolder> <fileSuffix> <numComposeReqs> <homeReqs> <userReqs> ")
        return

    opFolder = args[1]
    fileSuffix = args[2]

    applnName = args[3]
    monMachine = args[4]
    applnArgsStart = 5

    if(not(applnName in application_list)):
        print ("\t Appln: %s is not in recognized list: %s "%(applnName,application_list))
        sys.exit()
    
    if(applnName=="SN"):    
        experiment_end_time = int(args[applnArgsStart+0])
        numComposeReqs = int(args[applnArgsStart+1])
        numHomeReqs = int(args[applnArgsStart+2])
        numUserReqs = int(args[applnArgsStart+3])

        getReqTypeStats(opFolder,fileSuffix,numComposeReqs,'compose',monMachine,experiment_end_time)
        getReqTypeStats(opFolder,fileSuffix,numHomeReqs,'home',monMachine,experiment_end_time)
        getReqTypeStats(opFolder,fileSuffix,numUserReqs,'user',monMachine,experiment_end_time)

    elif(applnName=="HR"):    
        experiment_end_time = int(args[applnArgsStart+0])
        numComposeReqs = int(args[applnArgsStart+1])
        numHomeReqs = int(args[applnArgsStart+2])
        numUserReqs = int(args[applnArgsStart+3])

        getReqTypeStats(opFolder,fileSuffix,numComposeReqs,'compose',monMachine,experiment_end_time)
        getReqTypeStats(opFolder,fileSuffix,numHomeReqs,'home',monMachine,experiment_end_time)
        getReqTypeStats(opFolder,fileSuffix,numUserReqs,'user',monMachine,experiment_end_time)

    elif(applnName=="MM"):    
        experiment_end_time = int(args[applnArgsStart+0])

        reviewComposeReqs =  int(args[applnArgsStart+1])
        reviewReadReqs =  int(args[applnArgsStart+2])
        castInfoReqs =  int(args[applnArgsStart+3])
        plotReadReqs =  int(args[applnArgsStart+4])   
        
        getReqTypeStats(opFolder,fileSuffix,reviewComposeReqs,'reviewCompose',monMachine,experiment_end_time)
        getReqTypeStats(opFolder,fileSuffix,reviewReadReqs,'reviewRead',monMachine,experiment_end_time)
        getReqTypeStats(opFolder,fileSuffix,castInfoReqs,'cast',monMachine,experiment_end_time)
        getReqTypeStats(opFolder,fileSuffix,plotReadReqs,'plot',monMachine,experiment_end_time)

if __name__ == "__main__":
    main(sys.argv)
