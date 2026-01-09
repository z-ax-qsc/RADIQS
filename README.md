# RADIQS

Rapid advancements in cloud based platforms providing access to quantum computing capabilities have opened up
several challenges for efficient usage of these highly delicate and
costly devices. Although most of the current systems use a priority
based access protocol, they are unable to fully support reliable,
efficient, and scalable execution of larger-scale applications. To
overcome this limitation, we propose a comprehensive solution
for efficient allocation of quantum programs to appropriate
quantum devices, considering all the relevant cost metrics into
account including, fidelity, execution time and communication
overhead. We also formulate use-cases for distributed quantum
workflow and propose modified graph based algorithms to solve
for allocation of such use-cases, assuming a hybrid classical-
quantum network. Since hardware advancements in large standalone devices is an ongoing process, it is critical to investigate
such distributed workflows to maximize the best utilization of
current NISQ devices.

## Usage Guidelines

1. Download dependencies from **requirements.txt** file
2. Generate dataset from scripts in **qdataset/** folder in following order of scripts:
    1. *qd-generation/qdataset_gen.py*
    2. *qd-generation/subset-generation.py*
    3. *qd-expansion/dataset_expansion.py*
3. Update **qsimpy/utils/Params.py** file with required hyperparameters
4. Run **evaluator_networked.py** file and analye the result stored in **evaluation/** folder

