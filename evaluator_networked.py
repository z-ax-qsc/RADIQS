import networkx as nx
from matplotlib import pyplot as plt
import itertools as it
from qsimpy.policies.networked.CloudQC import policy_cloudqc
from qsimpy.policies.networked.GreedyDfs import policy_greedy_dfs
from qsimpy.policies.networked.IsoMorphism import policy_iso
from qsimpy.policies.networked.Random import policy_random
import multiprocessing as mp
from env_creator import qsimpy_env_creator
from joblib import Parallel, delayed
from time import time
from qsimpy.utils.Params import *
nx.config.backend_priority = ["parallel"]

cpus = mp.cpu_count();

def run_exp(params):
    """_summary_

    Args:
        params (_type_): _description_
    """

    PARAMS = {
    "n_nodes": params[0],
    "task_per_set": params[1],
    "edge_prob": params[2],
    "node_types": params[3],
    "algo": params[4],
    "weights": params[5],
    "data_size": params[6]
    }

    PARAMS = dict(sorted(PARAMS.items(), key=lambda item: item[0]))

    print(f"Running for {PARAMS}");

    eval_env = qsimpy_env_creator(
        env_config={
            # "obs_filter": "rescale_-1_1",
            "reward_filter": None,
            "dataset": f"qdataset/qd-generation/new/synds_1_sub_{PARAMS['data_size']}.csv",
            "config": {"evaluation": True, "policy": "networked", "task_per_set": PARAMS["task_per_set"], "qnodes": PARAMS["n_nodes"], "params": PARAMS},
            'algo': PARAMS["algo"]
        }
    )

    skipped_list = []

    # Run the evaluation
    num_episodes = 100  # Set the number of task set for evaluation

    for episode in range(num_episodes):
        # First setup nodes then reset
        eval_env.setup_quantum_resources(qnodes=PARAMS["n_nodes"], qnode_names = PARAMS["node_types"],  edge_prob = PARAMS["edge_prob"])
        _,_ = eval_env.reset(seed=22)
        # print(f"Episode {episode} started with observation: {obs}")
        terminate = False
        episode_reward = 0

        # nx.draw(eval_env.node_graph);
        # plt.show();
        # print(nx.number_of_edges(eval_env.node_graph), nx.degree_histogram(eval_env.node_graph))
        start = time();
        while not terminate:
            # print("remaining tasks: ", len(eval_env.qtasks))
            match PARAMS["algo"]:
                case 'SoftIso':
                    action, task_graph = policy_iso(eval_env, PARAMS["weights"], skipped_list, early_stop=True)
                case 'Random':
                    action, task_graph = policy_random(eval_env, PARAMS["weights"], skipped_list)
                case 'GreedyDfs':
                    action, task_graph = policy_greedy_dfs(eval_env, skipped_list)
                case 'CloudQC':
                    action, task_graph = policy_cloudqc(eval_env, PARAMS["weights"], skipped_list)
                case _:
                    print("Incorrect alogrithm name");
                    break
            obs, reward, terminate, _, info = eval_env.step_network(action, task_graph)
            if terminate:
                print(f"Episode {episode} finished with reward {episode_reward}")
                break
        end = time();
        # Run and close the evaluation environment
        eval_env.close(end-start);
    return 1;

print(f"Total Experiments = {len(all_combinations)}");

res = Parallel(n_jobs=cpus, backend="threading")(delayed(run_exp)(par) for par in all_combinations);