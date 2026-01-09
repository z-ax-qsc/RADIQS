import csv
import os
import json
import numpy as np

class Log:
    log = False

    @staticmethod
    def format_time(env_now):
        hours = int(env_now // 3600)
        minutes = int((env_now % 3600) // 60)
        seconds = round(env_now % 60, 4)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    @staticmethod
    def print_with_current_time(env_now, message):
        if Log.log:
            print(f"{Log.format_time(env_now)} {message}")
        else:
            pass

    @staticmethod
    def print_error(message):
        # Print message in red color
        if Log.log:
            print(f"\033[91m{message}\033[00m")
        else:
            pass

    @staticmethod
    def print_warning(message):
        # Print message in yellow color
        if Log.log:
            print(f"\033[93m{message}\033[00m")
        else:
            pass

    @staticmethod
    def print_success(message):
        # Print message in green color
        if Log.log:
            print(f"\033[92m{message}\033[00m")
        else:
            pass

    @staticmethod
    def print_simulation_results(qnodeList):
        if Log.log:
            total_waiting_time = 0
            total_execution_time = 0
            total_wall_time = 0
            # Create a list of all completed tasks across all QNodes
            all_completed_tasks = []
            all_failed_tasks = []
            for qnode in qnodeList:
                all_completed_tasks.extend(qnode.completed_tasks)
                all_failed_tasks.extend(qnode.failed_tasks)

            # Sort the tasks based on their IDs
            sorted_tasks = sorted(all_completed_tasks, key=lambda x: x.id)
            sorted_failed_tasks = sorted(all_failed_tasks, key=lambda x: x.id)
            print("=================================")
            print("Simulation Results:")
            print(f"✨ {len(all_completed_tasks)} SUCCESSFUL TASKS ✨")
            print("=================================")
            print(
                " QTask ID | QNode | Arrival Time | Waiting Time | Start Time   | Execution Time  | Wall Time   | Finish Time "
            )
            print(
                "----------|-------|--------------|--------------|--------------|-----------------|-------------|-------------"
            )

            # Print the sorted tasks
            for qtask in sorted_tasks:
                wall_time = qtask.waiting_time + qtask.execution_time
                qtask.start_running_time=qtask.arrival_time+qtask.waiting_time
                qtask.finish_time=qtask.start_running_time+qtask.execution_time
                print(
                    f" {qtask.id:^8} | {qtask.qnode.id:^5} | {round(qtask.arrival_time, 4):^12.4f} | {round(qtask.waiting_time, 4):^12.4f} | {round(qtask.start_running_time, 4):^12.4f} |  {round(qtask.execution_time, 4):^14.4f} | {round(wall_time, 4):^11.4f} | {round(qtask.finish_time, 4):^11.4f} "
                )
                # Accumulate the waiting and execution times
                total_waiting_time += qtask.waiting_time
                total_execution_time += qtask.execution_time
                total_wall_time += wall_time

            print("=================================")
            print(f"❌ {len(all_failed_tasks)} FAILED TASKS ❌")
            if len(all_failed_tasks) > 0:
                print(
                    " QTask ID | QNode | Arrival Time | Error                                                         "
                )
                print(
                    "----------|-------|--------------|---------------------------------------------------------------"
                )
                for qtask in sorted_failed_tasks:
                    print(
                        f" {qtask.id:^8} | {qtask.qnode.id:^5} | {round(qtask.arrival_time, 4):^12.4f} | {qtask.error:^9} "
                    )

            print(f"Total Waiting Time: {round(total_waiting_time, 2)}")
            print(f"Total Execution Time: {round(total_execution_time, 2)}")
            print(f"Total Wall Time: {round(total_wall_time, 2)}")
            print("QNode Relative Utilizations based on Share of Work:")
            for qnode in qnodeList:
                qnode.total_busy_time=sum(task.execution_time for task in qnode.completed_tasks)
                relative_utilization = 0 if total_execution_time == 0 else qnode.total_busy_time / total_execution_time
                print(f"- QNode {qnode.id}: {relative_utilization:.2%}")
        else:
            pass
    
    @staticmethod
    def export_simulation_results(
        decision_time, qnodeList, params, unfullfilled_tasks, output_folder="evaluation", output_file="evaluation_result"
    ):
        # Create a list of all completed tasks across all QNodes
        all_completed_tasks = []
        for qnode in qnodeList:
            all_completed_tasks.extend(qnode.completed_tasks)

        # Sort the tasks based on their IDs
        sorted_tasks = sorted(all_completed_tasks+unfullfilled_tasks, key=lambda x: x.id)

        # Ensure the output folder exists
        os.makedirs(output_folder + '/task' ,exist_ok=True)
        os.makedirs(output_folder + '/summary' ,exist_ok=True)
        # Get the current date and time
        # now = datetime.utcnow() + timedelta(hours=10)  # Convert to AEST
        # timestamp = now.strftime("%d_%m-%H_%M_%S")
        par = '_'.join(map(str,params.values()))
        result_file = output_file + f"_{par}.csv"
        output_path = os.path.join(output_folder, 'task', result_file)

        # Define the header
        header = [
            "qtask_id",
            "qtask_qubits"
            "qnode",
            "qnode_qubits",
            "arrival_time",
            "schedule_time",
            "waiting_time",
            "start_time",
            "execution_time",
            "wall_time",
            "finish_time",
            "rescheduling_count",
            "fidelity",
            "communication_cost"
        ]

        total_wait_time = 0;
        total_execution_time = 0;
        total_wall_time = 0;
        total_fidelity = 0;
        total_communication = 0; 
        # Write the results to the CSV file
        with open(output_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(header)
            for qtask in sorted_tasks:
                waiting_time = (
                    qtask.waiting_time + qtask.arrival_time - qtask.init_arrival_time
                )
                wall_time = waiting_time + qtask.execution_time
                writer.writerow(
                    [
                        f"{qtask.id:06}",
                        qtask.qubit_number,
                        -1 if qtask.qnode is None else qtask.qnode.id,
                        0 if qtask.qnode is None else qtask.qnode.qubit_number,
                        round(qtask.init_arrival_time, 4),
                        round(qtask.arrival_time, 4),
                        round(waiting_time, 4),
                        round(qtask.start_running_time, 4),
                        round(qtask.execution_time, 4),
                        round(wall_time, 4),
                        round(qtask.finish_time, 4),
                        qtask.rescheduling_count,
                        round(qtask.fidelity, 4),
                        round(qtask.communication_cost, 4),
                    ]
                )
                total_wait_time += max(0,waiting_time); # ignore negative;
                total_execution_time += max(0,qtask.execution_time);
                total_wall_time += max(0, wall_time);
                total_fidelity += qtask.fidelity;
                total_communication += qtask.communication_cost;

        get_qubits = lambda x: sum([t.qubit_number for t in x])
        get_runtime = lambda x: sum([max(0,t.execution_time) + max(0,t.communication_cost) for t in x])                    
        div = lambda x,y: x/y if y else 0;

        summary = {
            "decision_time": round(decision_time, 4),
            "wait_time": round(total_wait_time,2),
            "execution_time": round(total_execution_time,2),
            "wall_time": round(total_wall_time,2),
            "fidelity": round(div(total_fidelity,len(all_completed_tasks)), 3),
            "communication_overhead": round(total_communication / 2, 2),
            "sla_count": round(div(len(unfullfilled_tasks),len(sorted_tasks)), 2),
            "sla_qubit": round(div(get_qubits(unfullfilled_tasks),get_qubits(sorted_tasks)), 2),
            "workload_distribution_task": {q.id: round(div(len(q.completed_tasks),len(sorted_tasks)),2) for q in qnodeList},
            "workload_distribution_time": {q.id: round(div(get_runtime(q.completed_tasks),total_execution_time),2)
                                            for q in qnodeList},
            "workload_distribution_qubits":{q.id: 
                                            round(div(get_qubits(q.completed_tasks),len(q.completed_tasks)*q.qubit_number),2)
                                            for q in qnodeList
                                            },
        }
        summary_file = output_file + f"_{par}.json"
        summary_path = os.path.join(output_folder, "summary", summary_file)
        # Save the dictionary to a JSON file with pretty-printing
        with open(summary_path, "w") as json_file:
            json.dump(summary, json_file, indent=4, sort_keys=True)

        print(f"Results exported to {output_path}, {summary_path}")