import pandas as pd
import numpy as np
import subprocess
import os

def get_percentiles(wrk2_log):
    ouptut = []
    output = subprocess.check_output("awk '/50.000%%|75.000%%|90.000%%|99.000%%|99.900%%/{print $2}' %s"%(wrk2_log),shell=True,universal_newlines=True).split()
    #convert everything to 'ms' and strip units
    output = remove_units(output)
    #output = list(map(float,output))
    return output

def get_metrics(wrk2_log):
    # Elements order: <max>, <total_count>, <mean>, <std_dev> 
    output = []
    output += [element[:-1] for element in subprocess.check_output("awk '/Max/{print $3, $7}' %s"%(wrk2_log),shell=True,universal_newlines=True).split()] # ']' and ',' character is part of the output.So remove them from the output of the command.
    output += [element[:-1] for element in subprocess.check_output("awk '/Mean/{print $3, $6}' %s"%(wrk2_log),shell=True,universal_newlines=True).split()]
    return output


def remove_units(output):
    output_temp = []
    for num in output:
        if num.endswith('ms'):
            output_temp.append(float(num[:-2]))
        elif num.endswith('s'):
            output_temp.append(float(num[:-1])*1000)
        elif num.endswith('m'):
            output_temp.append(float(num[:-1])*1000*60)
    return output_temp

def find_neighbours(df,value):
    #source: https://stackoverflow.com/questions/30112202/how-do-i-find-the-closest-values-in-a-pandas-series-to-an-input-number
    exactmatch=df[df.requests_cum_perc==value]
    if not exactmatch.empty:
        latency =  df.iloc[exactmatch.index.values[0]].latency #if multiple rows match, choose the first index
    else:
        lowerneighbour_ind = df[df.requests_cum_perc<value].requests_cum_perc.idxmax()
        upperneighbour_ind = df[df.requests_cum_perc>value].requests_cum_perc.idxmin()
        #return [lowerneighbour_ind, upperneighbour_ind]
        latency  = df.iloc[upperneighbour_ind].latency
    return latency

def percentiles_from_merged_latency_distribution(merged_percentile_file,target_folder):
    percentiles_list = []
    percentile_file = target_folder + "/percentile.csv"
    percentiles_needed = [50,75,80,90,95,99]
    os.system("sort -k1 -n %s > %s"%(merged_percentile_file,percentile_file))
    percentiles_df = pd.read_csv(percentile_file,sep=' ',names=["latency","old_percentile","bucket_size","dummy"])
    percentiles_df["requests_cum_sum"] = percentiles_df["bucket_size"].cumsum()
    percentiles_df["requests_cum_perc"] = 100 * percentiles_df["requests_cum_sum"]/percentiles_df["bucket_size"].sum()
    percentiles_df["requests_cum_perc"] = percentiles_df["requests_cum_perc"].round(2) 

    for percentile in percentiles_needed:
       percentiles_list.append(find_neighbours(percentiles_df,percentile))
    #https://stackoverflow.com/questions/30112202/how-do-i-find-the-closest-values-in-a-pandas-series-to-an-input-number
    # find the percentile using this and print the latency value in htat row
    return percentiles_list

def percentile_across_requests(experiment_folder,app):
    percentiles_dict = {}
    request_dict = {"SN":["compose","user","home"], "MM" : ["review_compose","review_read","plot_read"]}
    request_types = request_dict[app]
    percentile_temp_file = "/tmp/percentiles.tmp"
    os.system("sudo echo > %s"%percentile_temp_file)
    for request in request_types:
        wrk2_log = experiment_folder + "/%s.log"%(request)
        # 1) Cut all the text between the line starting with "Value" and ending with "#[Mean=".
        # 2) Remove the first 2 lines and the last one line. Matching lines and the empty lines are removed.
        # 3) Subract successive rows along column 3, the total request count colum. awk saves the value in the third column of the first row in the variable old for the first line (NR==1). For the successive lines, the column 3 value is subtracted from previous row's column 3 element. 
        os.system("sed -n '/Value/,/#\[Mean/p' %s | tail -n+3 | head -n -1 | awk 'NR == 1{old = $3; next}{print $1,$2,$3 - old,$4; old = $3}' >> %s"%(wrk2_log,percentile_temp_file))
    return percentiles_from_merged_latency_distribution(percentile_temp_file, experiment_folder)    

def metrics_across_iterations(stats_iter):
    stats_np = np.array(stats_iter).astype(np.float)
    return stats_np[:,2].max(),stats_np[:,3].sum(),stats_np[:,4].mean()

def metrics_across_requests(experiment_folder,app):
    request_dict = {"SN":["compose","user","home"], "MM" : ["review_compose","review_read","plot_read"]}
    request_types = request_dict[app]
    num_requests = len(request_types)
    max_latency = -1
    total_requests = 0
    total_avg_latency = 0

    for request in request_types:
        #max and total
        wrk2_log = experiment_folder + "/%s.log"%request
        max_temp, cur_total = [element[:-1] for element in subprocess.check_output("awk '/Max/{print $3, $7}' %s"%(wrk2_log),shell=True,universal_newlines=True).split()] # ']' and ',' character is part of the output.So remove them from the output of the command.
        #mean and std 
        avg, std = [element[:-1] for element in subprocess.check_output("awk '/Mean/{print $3, $6}' %s"%(wrk2_log),shell=True,universal_newlines=True).split()]
        if(float(max_temp) > max_latency):
            max_latency = float(max_temp)
        total_requests += float(cur_total)
        total_avg_latency += float(avg)
    return [max_latency, total_requests, total_avg_latency/num_requests]
    

def all_metrics_across_iterations(experiment_folder,cur_rps,iterations,app):
    stats_iter = []
    merged_temp_file = "/tmp/merged.tmp"
    os.system("echo > %s"%merged_temp_file)

    for i in range(1,iterations+1):
        # Add an entry for each iteration
        cur_experiment_folder = experiment_folder+"i%d"%i
        cur_row = []
        cur_row.append(cur_rps)
        cur_row.append(i)
        cur_row += metrics_across_requests(cur_experiment_folder,app)
        cur_row += percentile_across_requests(cur_experiment_folder,app)
        stats_iter.append(cur_row)
        # merge the latency distribution of all the iterations into one file
        os.system("cat " + cur_experiment_folder+"/percentile.csv" + " >> %s"%merged_temp_file)
    # Aggregate across iterations in one entry. The iteration field is 0 to convey that it is aggregate.
    cur_row=[]
    cur_row.append(cur_rps)
    cur_row.append(0) #across all iterations
    cur_row += metrics_across_iterations(stats_iter)
    cur_row += percentiles_from_merged_latency_distribution(merged_temp_file,experiment_folder)
    stats_iter.append(cur_row)
    return stats_iter

def collect_stats(results_folder,version,app_config_iteration,app,rps_list,iterations):
    """
    Merge the histograms by sorting the buckets and picking the bucket that corresponds to 99th.
    """
    df_columns = ["rps","iter","max", "total_count","avg","P_50","P_75","P_80","P_90","P_95","P_99"]
    experiment_folder_template =  results_folder+"/%s/v_%s_%s_rps"%(version,version, app_config_iteration) + "%s/"
    for cur_rps in rps_list:
        summary_file = "%s/%s/v_%s_%s_rps%s/summary_merged_stats.csv"%(results_folder,version,version,app_config_iteration,cur_rps) 
        try:
            cur_rps_stats = all_metrics_across_iterations(experiment_folder_template%(cur_rps),cur_rps,iterations,app)
            rps_stats_df = pd.DataFrame(cur_rps_stats,columns=df_columns)
            #rps_stats_df["normal_std"] =  rps_stats_df["std"].astype(float)/ rps_stats_df["avg"].astype(float)
            rps_stats_df.to_csv(summary_file)
        except:
            os.system("cp ./results/failure_merged_stats.csv %s"%summary_file)

def individual_requests_percentiles_across_iterations(experiment_folder,request_type,iterations):
    percentiles_dict = {}
    percentile_temp_file = "/tmp/percentiles.tmp"
    os.system("sudo echo > %s"%percentile_temp_file)
    wrk2_log_filename ="/%s.log"%request_type
    for i in range(1,iterations+1):
        wrk2_log = experiment_folder + "/i%s"%i + wrk2_log_filename
        # 1) Cut all the text between the line starting with "Value" and ending with "#[Mean=".
        # 2) Remove the first 2 lines and the last one line. Matching lines and the empty lines are removed.
        # 3) Subract successive rows along column 3, the total request count colum. awk saves the value in the third column of the first row in the variable old for the first line (NR==1). For the successive lines, the column 3 value is subtracted from previous row's column 3 element. 
        os.system("sed -n '/Value/,/#\[Mean/p' %s | tail -n+3 | head -n -1 | awk 'NR == 1{old = $3; next}{print $1,$2,$3 - old,$4; old = $3}' >> %s"%(wrk2_log,percentile_temp_file))
    return percentiles_from_merged_latency_distribution(percentile_temp_file, experiment_folder)

def individual_requests_metrics_across_iterations(stats_request):
    # columns: "request_type","version","iter","max", "total_count","avg","std","P_50","P_75","P_90","P_99","P_99.9","P_95"
    stats_np = np.array(stats_request)
    filtered_np = stats_np[:,3:6].astype(np.float) #convert all the requried columns to numberic.
    return [filtered_np[:,0].max(),filtered_np[:,1].sum(),filtered_np[:,2].mean()]

def collect_stats_individual_requests(results_folder,version,subversion,app,rps_list,iterations):
    request_dict = {"SN":["compose","user","home"], "MM" : ["review_compose","review_read","plot_read"]}
    request_types = request_dict[app]
    df_columns = ["request_type","version","iter","max", "total_count","avg","std","P_50","P_75","P_90","P_99","P_99.9","P_95"]
    results_folder = "./results/"
    wrk2_log_file_template = results_folder+"%s/v_%s_%s_rps%s/i%d/%s.log" 
    #remove units and convert all time data to millisecond
    #create a 2-D array of values and convert to dataframe
    rps_stats = []
    for cur_rps in rps_list:
        for cur_request_type in request_types:
            request_stats = []
            for cur_iter in range(1,iterations+1):
                # create a dataframe similar to lat_summary.log	
                #compose	v0.74_rps100	100	15.150	4.737
                # <request_type>, <version>, <avg>, <std>...<other metrics>
                cur_row = []
                cur_row.append(cur_request_type)
                cur_row.append(version)
                cur_row.append(cur_iter)
                
                #for new experiments, this line can be removed and all the metrics can be directly.
                wrk2_log_file = wrk2_log_file_template%(version,version,subversion,cur_rps,cur_iter,cur_request_type)
                output_percentiles = get_percentiles(wrk2_log_file) 
                output_metrics = get_metrics(wrk2_log_file)
                p_95 = subprocess.check_output(" awk '/0.950000/{print $1}' %s"%wrk2_log_file,shell=True,universal_newlines=True).strip()
                p_95 = float(p_95)
                #compose	v0.74_rps100	100	15.150	4.737
                cur_row += output_metrics + output_percentiles + [p_95]  # metrics + percentiles + P_95
                request_stats.append(cur_row)

            cur_row = []
            cur_row.append(cur_request_type)
            cur_row.append(version)
            cur_row.append(0)
            output_percentiles = individual_requests_percentiles_across_iterations("%s/%s/v_%s_%s_rps%s/"%(results_folder,version,version,subversion,cur_rps),cur_request_type,iterations)
            output_metrics = individual_requests_metrics_across_iterations(request_stats)
            cur_row += output_metrics + output_percentiles
            request_stats.append(cur_row)
            rps_stats.extend(request_stats)
        rps_stats_df = pd.DataFrame(rps_stats,columns=df_columns)
        rps_stats_df["normal_std"] =  rps_stats_df["std"].astype(float)/ rps_stats_df["avg"].astype(float)
        rps_stats_df.to_csv("%s/%s/v_%s_%s_rps%s/individual_requests_summary_stats.csv"%(results_folder,version,version,subversion,cur_rps))
