def round_robin_scheduler(processes, quantum):

    if quantum <= 0:
        return "Error: Invalid quantum value.", {}, {}, []


    processes_copy = [p.copy() for p in processes]
    n = len(processes_copy)

    remaining_burst = {p['id']: p['burst_time'] for p in processes_copy}

    completion_time = {}
    first_start = {}
    execution_sequence = []

    current_time = 0
    ready_queue = []

    processes_copy.sort(key=lambda x: x['arrival_time'])

    idx = 0
    while idx < n and processes_copy[idx]['arrival_time'] <= current_time:
        ready_queue.append(processes_copy[idx])
        idx += 1

    completed_processes = 0

    while completed_processes < n:
        if len(ready_queue) == 0:
            current_time = processes_copy[idx]['arrival_time']
            while idx < n and processes_copy[idx]['arrival_time'] <= current_time:
                ready_queue.append(processes_copy[idx])
                idx += 1
            continue

        current_process = ready_queue.pop(0)
        pid = current_process['id']

        if pid not in first_start:
            first_start[pid] = current_time

        time_to_execute = min(quantum, remaining_burst[pid])


        execution_sequence.append((pid, current_time, current_time + time_to_execute))

        current_time += time_to_execute
        remaining_burst[pid] -= time_to_execute

        while idx < n and processes_copy[idx]['arrival_time'] <= current_time:
            ready_queue.append(processes_copy[idx])
            idx += 1

        if remaining_burst[pid] > 0:
            ready_queue.append(current_process)
        else:
            completion_time[pid] = current_time
            completed_processes += 1
    return completion_time, first_start, execution_sequence