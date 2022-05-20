

with open("cmd_get") as cmd_get_f:
    cmd_get_list = cmd_get_f.readlines()

with open("get_hits") as get_hits_f:
    get_hits_list = get_hits_f.readlines()

cmd_get_list = [int(i) for i in cmd_get_list]
get_hits_list = [int(i) for i in get_hists_list]



