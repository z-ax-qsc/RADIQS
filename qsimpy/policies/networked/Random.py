import networkx as nx
from copy import copy as cp
from qsimpy.utils.Checks import check_connectivity
from qsimpy.utils.Metrics import assignment_cost
from bisect import bisect


def random_map(rng, task_graph, node_graph, desc = False):       
    result = {}

    node_qubits = nx.get_node_attributes(node_graph, "qubit_number");
    task_qubits = nx.get_node_attributes(task_graph, "qubit_number");

    sorted_tasks = dict(sorted(task_qubits.items(), key = lambda x: x[1], reverse=desc))
    sorted_nodes = dict(sorted(node_qubits.items(), key = lambda x: x[1], reverse=desc))

    # Assign sorted task by qubit to random node with required number of qubits.
    for task in sorted_tasks.items():
        loc = bisect(list(sorted_nodes.values()), task[1]);
        if loc == len(sorted_nodes):
            break;
        sel = rng.integers(loc, len(sorted_nodes));
        qpu = list(sorted_nodes.keys())[sel];
        result[task[0]] = qpu;
        sorted_nodes.pop(qpu);
    
    if len(result) < len(task_qubits): # All tasks not assigned
        return {}; 

    # sorted as per task order
    return dict(sorted(result.items(), key = lambda x: x[0])) if check_connectivity(task_graph, result, node_graph) else {};


def policy_random(env, wt, skipped_list):
    tasks, nodes = env.current_obs;

    node_graph = env.node_graph.copy();
    attr = {q.id:q.generate_att_dict() for q in nodes}
    nx.set_node_attributes(node_graph, attr)

    task_graph = nx.fast_gnp_random_graph(len(tasks), p = 0.3, seed = env.rng, directed=True); 
    lb = sorted(task_graph);
    task_graph = nx.relabel_nodes(task_graph, {lb[i]:tasks[i].id for i in range(len(lb))})
    attt = {t.id: t.generate_att_dict() for t in tasks};
    nx.set_node_attributes(task_graph, attt);

    result = [];

    trials = env.task_per_set
    for i in range(trials):
        result.append(random_map(env.rng, task_graph, node_graph));
    
    result = list(filter(lambda x: x != {} and check_connectivity(task_graph, x, node_graph), result))
    
    if result:
        best = min(result, key=lambda x: assignment_cost(node_graph.subgraph(x.values()), task_graph, tasks, nodes, x, weights=wt)
                #    sum(nx.get_node_attributes(node_graph.subgraph(x.values()), "next_available_time").values())
                    );
        return list(best.values()), task_graph;
    else:
        return None, task_graph;
