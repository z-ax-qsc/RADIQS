
import networkx as nx
from itertools import combinations

from qsimpy.utils.Checks import check_connectivity, qubit_condition
from qsimpy.utils.Metrics import assignment_cost

def map_task_to_community(community, task_graph, node_graph):
    # Create subgraph for the community
    subgraph = node_graph.subgraph(community)
    
    # Sort nodes in task_graph by their weighted degree (most connected first)
    sorted_nodes = sorted(task_graph.nodes(), key=lambda x: task_graph.degree(x), reverse=True)
    
    result = {}

    if len(subgraph.nodes()) < len(sorted_nodes):
        return result;

    node_qubits = nx.get_node_attributes(subgraph, "qubit_number");
    task_qubits = nx.get_node_attributes(task_graph, "qubit_number");

    for node_1 in sorted_nodes:
        # Find the most suitable node in the community for this task
        try:
            # Try to find the center of the remaining subgraph
            center_node = nx.center(subgraph)
            center = [center_node[0]]
            if len(center_node) > 1:
                # If multiple centers, pick the one with highest degree
                max_degree = 0
                for node in center_node:
                    if subgraph.degree(node) > max_degree and node_qubits[node] >= task_qubits[node_1]:
                        max_degree = subgraph.degree(node)
                        center = [node]
                result[node_1] = center[0]
            else:
                result[node_1] = center[0]
        except:
            # If can't find center (e.g., disconnected graph), pick highest degree node
            center_node = list(subgraph.nodes())
            center = [center_node[0]]
            max_degree = 0
            for node in center_node:
                if subgraph.degree(node) > max_degree and node_qubits[node] >= task_qubits[node_1]:
                    max_degree = subgraph.degree(node)
                    center = [node]
            result[node_1] = center[0]
            
        # Remove the assigned node from consideration for future mappings
        rest_nodes = subgraph.nodes() - {center[0]}
        subgraph = nx.subgraph(subgraph, rest_nodes)
        
    # sorted as per task order
    return dict(sorted(result.items(), key = lambda x: x[0]));


def best_community(task_graph, node_graph, communities, tasks, nodes, wt):
    # Try to map to each community
    result = list(map(lambda x: map_task_to_community(x, task_graph, node_graph), communities))
    
    # Filter out unsuccessful mappings
    result = list(filter(lambda x: x != {}
                          and check_connectivity(task_graph, x, node_graph) 
                          and qubit_condition(node_graph.subgraph(x.values()),task_graph, {v:k for k,v in x.items()})
                          , result))
    
    if result:
        # Return the best mapping
        try:
            best = min(result, key=lambda x: assignment_cost(node_graph.subgraph(x.values()), task_graph, tasks, nodes, x, weights=wt)
                    #    sum(nx.get_node_attributes(node_graph.subgraph(x.values()), "next_available_time").values())
                );
            return list(best.values());
        except:
            print('Not possible to find optimal mapping', )
            return [];

def policy_cloudqc(env, wt, skipped_list):
    tasks, nodes = env.current_obs;

    node_graph = env.node_graph.copy();
    attr = {q.id:q.generate_att_dict() for q in nodes}
    nx.set_node_attributes(node_graph, attr)

    task_graph = nx.fast_gnp_random_graph(len(tasks), p = 0.3, seed = env.rng, directed=True); 
    lb = sorted(task_graph);
    task_graph = nx.relabel_nodes(task_graph, {lb[i]:tasks[i].id for i in range(len(lb))})
    attt = {t.id: t.generate_att_dict() for t in tasks};
    nx.set_node_attributes(task_graph, attt);

    communities = nx.community.greedy_modularity_communities(node_graph)
    # communities = max(nx.community.girvan_newman(node_graph), key = lambda x: nx.community.modularity(node_graph, x))

    result = best_community(task_graph, node_graph, communities, tasks, nodes, wt)

    if result is not None and result != []:
        return result, task_graph;

    # If no single community works, try combinations of communities
    possible_combinations = []
    for r in range(2, len(communities) + 1):
        for combo in combinations(communities, r):
            #TODO: Compatibility check
            possible_combinations.append(combo)
    
    # Merge the communities
    merged_sets = []
    for frozensets in possible_combinations:
        merged_frozenset = frozenset().union(*frozensets)
        merged_sets.append(merged_frozenset)
        
    # Find minimal merged sets (not supersets of others)
    minimal_sets = []
    for current_set in merged_sets:
        if all(not current_set.issuperset(other_set) for other_set in merged_sets if current_set != other_set):
            minimal_sets.append(current_set)
            
    # Only consider connected merged communities
    minimal_sets = list(filter(lambda x: nx.is_connected(node_graph.subgraph(x)), minimal_sets))
    
    result = best_community(task_graph, node_graph, communities,  tasks, nodes, wt);

    if result is not None and result != []:
        return result, task_graph;

    return best_community(task_graph, node_graph, [frozenset(node_graph.nodes())],  tasks, nodes, wt), task_graph;
