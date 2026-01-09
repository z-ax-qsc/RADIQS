import itertools as it

Qnodes = ["brisbane", "torino", "marrakesh"];
N_nodes = [20];
Task_per_set = [2];
Edge_prob = [0.3];
Node_types = [("brisbane", "torino", "marrakesh")]; # 2,3 combinations
Algo = ['SoftIso']
Weights = [[(0.5,0.5), (0.33,0.33,0.33)], [(1, 0), (0.33,0.33,0.33)], [(0, 1), (0.33,0.33,0.33)]]
Datasize = [50];

all_combinations = list(it.product(N_nodes,
                                   Task_per_set,
                                   Edge_prob,
                                   Node_types,
                                   Algo,
                                   Weights,
                                   Datasize));