import networkx as nx
from bisect import bisect

from qsimpy.utils.Checks import check_connectivity

def greedy_dfs_mapping(task_graph, node_graph, desc = False):  
    # assignment of sorted task by qubits in BFS of node graph      
    result = {}

    node_qubits = nx.get_node_attributes(node_graph, "qubit_number");
    task_qubits = nx.get_node_attributes(task_graph, "qubit_number");

    def all_neighbors(x):
        dt = {n:node_qubits[n] for n in nx.all_neighbors(node_graph, x)};
        return dict(sorted(dt.items(), key = lambda x: x[1], reverse=desc));

    sorted_tasks = dict(sorted(task_qubits.items(), key = lambda x: x[1], reverse=desc))
    sorted_nodes = dict(sorted(node_qubits.items(), key = lambda x: x[1], reverse=desc))
    node_qb = list(sorted_nodes.values());
    node_ids = list(sorted_nodes.keys());

    assigned = [];    
    neighbors = [node_ids, node_qb];
    back = -1;

    while sorted_tasks:
        task = list(sorted_tasks.items())[0];
        loc = bisect(neighbors[1], task[1]);
        
        if len(assigned) == len(node_qubits): # All qpus assigned
            break; 
        
        for i in range(loc, len(neighbors[1])):
            qpu = neighbors[0][i];
            if qpu not in assigned: # QPU is free
                result[task[0]] = qpu;
                assigned.append(qpu);
                nbr = all_neighbors(qpu);
                neighbors = [list(nbr.keys()), list(nbr.values())];
                sorted_tasks.pop(task[0]);
                break;
        
        if task[0] not in result and len(neighbors[1]) == len(node_qubits): # not assignable in entire graph
            break;
        if task[0] not in result: # Task not assigned check for full qpu graph in next iteration
            if back < -len(assigned):
                neighbors = [node_ids, node_qb];
            else:
                nbr = all_neighbors(assigned[back]);
                neighbors = [list(nbr.keys()), list(nbr.values())];
            back -= 1;
            # neighbors = [node_ids, node_qb];
    
    if len(result) < len(task_qubits): # All tasks not assigned
        return {}; 

    # sorted as per task order
    return dict(sorted(result.items(), key = lambda x: x[0])) if check_connectivity(task_graph, result, node_graph) else {};


def policy_greedy_dfs(env, skipped_list):
    tasks, nodes = env.current_obs;

    node_graph = env.node_graph.copy();
    attr = {q.id:q.generate_att_dict() for q in nodes}
    nx.set_node_attributes(node_graph, attr)

    task_graph = nx.fast_gnp_random_graph(len(tasks), p = 0.3, seed = env.rng, directed=True); 
    lb = sorted(task_graph);
    task_graph = nx.relabel_nodes(task_graph, {lb[i]:tasks[i].id for i in range(len(lb))})
    attt = {t.id: t.generate_att_dict() for t in tasks};
    nx.set_node_attributes(task_graph, attt);

    best = greedy_dfs_mapping(task_graph, node_graph, desc = False);

    return list(best.values()), task_graph;
