import networkx as nx
from copy import copy as cp
from qsimpy.utils.Checks import check_connectivity, qubit_condition
from qsimpy.utils.Metrics import assignment_cost
from networkx.algorithms import isomorphism

THRESHOLD_MAX = 0.03;
THRESHOLD_PREV = 0.03;

def policy_iso(env, wt, skipped_list, early_stop = True):
    tasks, nodes = env.current_obs;
    best = {};

    node_graph = env.node_graph.copy();
    attr = {q.id:q.generate_att_dict() for q in nodes}
    nx.set_node_attributes(node_graph, attr)

    task_graph = nx.fast_gnp_random_graph(len(tasks), p = 0.3, seed = env.rng, directed=False); 
    lb = sorted(task_graph);
    task_graph = nx.relabel_nodes(task_graph, {lb[i]:tasks[i].id for i in range(len(lb))})
    attt = {t.id: t.generate_att_dict() for t in tasks};
    nx.set_node_attributes(task_graph, attt);

    # task_graph = nx.complete_graph(len(tasks)); 

    def find_best(i_sub, isMono = False):
        min_cost = float("inf");
        max_cost = -float("inf");
        previous_cost = 0;
        best_choice = {}
        counter = 0;
        for sub in i_sub:
            keys = list(sub.keys()); # Node ids
            cost = assignment_cost(node_graph.subgraph(keys), task_graph, tasks, nodes, {v:k for k,v in sub.items()}, weights=wt);
            #sum(nx.get_node_attributes(node_graph.subgraph(keys), "next_available_time").values())
            if (cost <= min_cost
                and check_connectivity(task_graph, {v:k for k,v in sub.items()}, node_graph) 
                and qubit_condition(node_graph.subgraph(keys), task_graph, sub)):
                best_choice = cp(sub)
                min_cost = cost
            if isMono:
                if counter == 0:
                    previous_cost = cost;
                max_cost = max(cost, max_cost);
                den = cost if cost !=0 else previous_cost
                # Early stopping
                if den != 0 and best_choice != {} and (abs((cost - previous_cost)/den) > THRESHOLD_PREV and abs((cost - max_cost)/den) > THRESHOLD_MAX):
                    # print(counter)
                    break;
                # early stopping
                if early_stop and counter > 10**env.task_per_set:
                # n_nodes**(task_per_set)//task_per_set:
                    # print(counter)
                    break;
                previous_cost = cost;
                counter +=1;
        return best_choice;
    
    ismags = isomorphism.ISMAGS(node_graph, task_graph)
    iter_iso = ismags.subgraph_isomorphisms_iter();
    best = cp(find_best(iter_iso));

    if best == {}:
        VF2 = isomorphism.GraphMatcher(node_graph, task_graph)
        iter_mono = VF2.subgraph_monomorphisms_iter();
        best = cp(find_best(iter_mono, isMono=True));
        # print("Selection through monomorphism")

    return list(dict(sorted(best.items(), key = lambda x : x[1])).keys()), task_graph;
