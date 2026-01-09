from qsimpy.tasks import QTask
from qsimpy.resources import QNode
import enum
import math
import networkx as nx

WEIGHTS = [(1/2, 1/2), (1/3, 1/3, 1/3)]; # [(availablity, other costs), (runtime, error, communication)]
GATES2Q = ['ecr', 'cz', 'rzz'];
MEASURE = 'measure';
SIG = lambda x: 1/(1 + math.exp(-x));
CLASSICAL_LATENCY = 0.02; # Seconds per qubit
EPR_FIDELITY = 0.9;
SUCCESS_PROB = 0.3;

class ErrorKeys(enum.Enum):
    T1 = "T1"
    T2 = "T2"
    READOUT = "MEDIAN READOUT ERROR"
    ERROR_1 = "MEDIAN SINGLE QUBIT ERROR"
    ERROR_2 = "MEDIAN TWO QUBIT ERROR"
    ERROR_2_BEST = "LEAST TWO QUBIT ERROR"
    ERROR_2_LAYER = "TWO QUBIT LAYERED ERROR"

class TimeKeys(enum.Enum):
    QUBIT1 = "1qubit",
    QUBIT2 = "2qubit",
    READOUT ="readout",

# TODO:
# These functions are compatible to only simulate mode and qdata is provide in QTasks.

def runtime(node: QNode, task: QTask):
    return SIG(task.get_node_circuit_layers(node.qnode_model) * task.shots / node.clops);

def error(node: QNode, task: QTask):
    error = node.get_state()['error'];
    qbt_1 = (1 - error[ErrorKeys.ERROR_1.value])**task.get_node_circuit_layers(node.qnode_model)
    qbt_2 = (1 - error[ErrorKeys.ERROR_2_LAYER.value])**(math.sqrt(task.get_node_circuit_2qgates(node.qnode_model)))
    readout = (1 - error[ErrorKeys.READOUT.value])**task.get_node_circuit_measure(node.qnode_model)
    return 1 - SIG(qbt_1*qbt_2*readout)

def communication(node: QNode, task: QTask):
    error = node.get_state()['error'];
    time = node.get_state()['runtimes'];
    T_dec = error[ErrorKeys.T1.value] * error[ErrorKeys.T2.value] / (error[ErrorKeys.T1.value] + error[ErrorKeys.T2.value]);
    T_epr = 10 * time[TimeKeys.QUBIT2.value]
    T_quantum = task.qubit_number * T_epr / T_dec;
    T_classical = task.get_node_circuit_measure(node.qnode_model) * CLASSICAL_LATENCY;
    return SIG(T_classical + T_quantum);

def nexAvailable(node_graph):
    next_times = nx.get_node_attributes(node_graph, "next_available_time").values()
    return SIG(max(next_times)) if next_times else 0;

def getObjectFromList(objectlist, id):
    return list(filter(lambda x: x.id == id, objectlist))[0];

def linkCost(node1, task1, node2 , task2):
    return (communication(node1, task1) + communication(node2, task2))/2;

def neighborCommunicationCost(task_graph, node, task, mappings, nodes, tasks):
    res = 0;
    neighbour_tasks = set(nx.all_neighbors(task_graph, task.id));
    for x in neighbour_tasks:
        res += linkCost(node, task, getObjectFromList(nodes, mappings[x]), getObjectFromList(tasks, x));
    return res; # BUG: to be divided by number of neighbors

def assignment_cost(node_graph, task_graph, tasks, nodes, mappings, weights = WEIGHTS):
    # node_graph is subgraph as per mapping

    Cost_availablity = nexAvailable(node_graph);
    Cost_runtime = 0;
    Cost_error = 0;
    Cost_communication = 0;

    for t,n in mappings.items():
        task = getObjectFromList(tasks, t);
        node = getObjectFromList(nodes, n);
        Cost_runtime += runtime(node, task);
        Cost_error += error(node, task);
        # get all neighboring edge of task currenlty checking from task graph
        Cost_communication += neighborCommunicationCost(task_graph, node, task, mappings, nodes, tasks)
    
    Cost_communication /= 2; # Edges considered twice in above loop
    
    return weights[0][0]*Cost_availablity + weights[0][1]*(weights[1][0]*Cost_runtime + weights[1][1]*Cost_error + weights[1][2]*Cost_communication); 

