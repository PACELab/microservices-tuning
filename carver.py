import pandas as pd
import numpy as np
import random

class Carver:
    def __init__(self,parameter_csv,config_template,rps_list,iterations,current_config_index=-1,num_samples=15,num_buckets=8,sampling_choice="median"):
        """
        perform LHC sampling based on the input and store it in a data structure.
        """
        self.parameter_csv = parameter_csv
        self.config_file_template = config_template
        self.iterations = iterations
        self.parameters_df = pd.read_csv(parameter_csv)
        self.current_config_index = current_config_index
        self.pending_samples_per_parameter = num_samples - (current_config_index+1) #If an experiment run for 'n' samples exits after 'i' steps, do the remaining (n-i). Change the name to pending_samples
        self.total_samples_per_parameter = num_samples
        self.num_buckets = num_buckets
        self.sampled_config_set = self.lhc()
        self.sampling_choice = sampling_choice

    def random_samples(self,low,high,is_float):
        """
        Splits the range into num_samples equal sized intervals.
        Picks a random value from each interval.
        Returns the list of random values picked for each interval.
        """
        random_samples = []
        """
        if is_float:
            low = float(low)
            high = float(high)
            rand_method = random.uniform
            step = (high-low)/num_samples
        else:
            low = int(low)
            high = int(high)
            rand_method = random.randrange
            step = (high-low)//num_samples
        #TODO: A more consistent way of choosing the intervals. For example, low =1, high=60, samples=15 imlpies step = 3 although the actual value of step is 3.93. Use random.uniform always with float steps but round the obtained sample?
        """
        low = float(low)
        high = float(high)
        rand_method = random.uniform
        step = (high-low)/self.pending_samples_per_parameter
        #while low + step <= high :
        count = 0
        while count <= self.pending_samples_per_parameter:
            random_samples.append(rand_method(low,low+step))
            low = low+step
            count += 1
        if not is_float:
            random_samples = list(map(int,random_samples))
        return random_samples

    def median_samples(self,low,high,is_float):
        low = float(low)
        high = float(high)
        step = (high-low)/self.num_buckets # divide the range into num_buckets intervals
        count = 0
        samples = []
        if is_float:
            while count < self.num_buckets:
                samples.append(round((low+step + low)/2,3))
                low = low + step
                count += 1
        else:
            cardinality = high - low + 1
            if cardinality >= self.num_buckets:  #check if there are enough unique integers
                while count < self.num_buckets:
                    samples.append(round((low+step + low)/2))
                    low = low + step
                    count += 1
            else:
                # all the values along with extra randomly chosen values are sampled.
                num_extra_samples = self.num_buckets - cardinality
                samples = range(low,high+1) + random.choices(range(low,high+1),k=num_extra_samples)
        return samples 


    def lhc(self):
        """
        Implements Latin Hypercube Sampling technique
        """
        num_parameters = self.parameters_df.shape[0]
        param_values = np.empty((num_parameters,self.pending_samples_per_parameter), object)
        for index,row in self.parameters_df.iterrows():
            if pd.notnull(row["parameter"]): #not needed as ideally all parameters will have config values
                param_range = row["range"].split(';')
                num_extra_categorical_data = self.pending_samples_per_parameter - len(param_range)

                if int(row["categorical"]):
                    param_values[index] = param_range + random.choices(param_range,k=num_extra_categorical_data) # random samples with repetitions  
                else:
                    param_values[index] = self.median_samples(param_range[0],param_range[1],int(row["float"]))* (self.pending_samples_per_parameter//self.num_buckets)
        np.random.shuffle(param_values.T)# n*m np array with n parameters and m sampled values for each parameters. Shuffle the values of each parameter. Each column is a configuration.
        return  param_values 


    def get_parameter_importance(self,result_folder, app_config_dir, version, app, rps_list):
        """
        Returns the importance of the current parameter
        """
        # All the stats files are available in the csv format. the last num_samples columns to get all the configurations.
        metric = "P_95"
        app_prefix = {"SN":"social_networking"}
        all_config_csv = app_config_dir +  "/" + app_prefix[app] +"_configs.csv"
        all_config_df = pd.read_csv(all_config_csv)
        for rps in rps_list:
            for i in range(self.total_samples_per_parameter):
                #stats_file = result_folder + "/" + version + "/v_%s_%s_%s"%(version,i,rps) +"/summary_merged_stats.csv"
                stats_file = result_folder + "/" + version + "/v%s_rps%s"%(i,rps) +"/summary_merged_stats.csv"
                print(pd.read_csv(stats_file))

    def stop_config_generation(self,stats_file):
        """
        Returns false when all the sampled configurations have been tried out
        """
        return self.current_config_index != (self.total_samples_per_parameter - 1) #current config is already the last element. Stop the experiments
    
    def next_config(self,stats_file):
        """
        Returns the next config from the list of configurations sampled by lhc()
        """
        self.current_config_index = self.current_config_index + 1
        return self.sampled_config_set[:,self.current_config_index - (self.total_samples_per_parameter-self.pending_samples_per_parameter)] # each column is a complete application configuration

    def analysis(result_folder, app_config_dir, current_config_index, version, app, rps_list):
        """
        Records the important parameters based on the parameter importance
        """
        #if self.pending_samples_per_parameter != 0:
        #    return
        self.get_parameter_importance(result_folder, app_config_dir, version, app, rps_list)
        # Deal with the configs based on index. Once the order of significance is found, use the <>_parameters.csv to print out the order of significance. 
