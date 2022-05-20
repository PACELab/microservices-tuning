import argparse

def argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("config_folder", help="The folder where the details of the application are present")
    parser.add_argument("main_version", help="The name for this round of experiments")
    parser.add_argument("app", help= "The application being used", choices=["SN","MM","HR","TT"])
    parser.add_argument("cluster_number", help = "The cluster on which the experiments are to be run.", choices=[1,2], type=int)
    parser.add_argument("approach", help="The optimization algorithm to be used")
    parser.add_argument("--rps_list","-r","-R" ,help="The rps list at which experiments are to be run", nargs="+", type=int )
    parser.add_argument("--iterations", "-i", help="The number of iterations the algorithm is run in each sequence", default=12, type=int)
    parser.add_argument("--sequence_count","-sc", help = "The number of times the algorithm is rerun", default=2)
    parser.add_argument("--start_sequence","-ss", help="Starting sequence number", default=1)
    parser.add_argument("--dimensionality_reduction","-d", help="The dimensionality reduction method used", default="critical_path")
    parser.add_argument("--acquisition_function","-a", help="The acquisition function to be used with Bayesian methods",default="EI")
    parser.add_argument("--init", action="store_true")
    args = parser.parse_args()
    print(args)
    return args
