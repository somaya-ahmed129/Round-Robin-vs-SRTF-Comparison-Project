"""
scheduler/RoundRobin.py
-----------------------
Round Robin scheduling algorithm.

Returns
-------
gantt   : list of (pid, start, end) tuples
metrics : dict  { pid: {'WT': int, 'TAT': int, 'RT': int} }
"""

from collections import deque
from src.model.process import Process


def round_robin_scheduler(processes, quantum):
    """
    Parameters
    ----------
    processes : list of Process objects (will NOT be mutated)
    quantum   : positive int

    Returns
    -------
    gantt   : list[(pid, start, end)]
    metrics : dict{ pid: {'WT':int, 'TAT':int, 'RT':int} }
    """
    if quantum <= 0:
        raise ValueError("Quantum must be a positive integer.")
    if not processes:
        return [], {}

    # Deep-copy so we never mutate the caller's list
    proc_list = [Process(p.pid, p.arrival_time, p.burst_time) for p in processes]
    proc_list.sort(key=lambda p: (p.arrival_time, p.pid))

    n            = len(proc_list)
    ready        = deque()
    enqueued     = set()
    gantt        = []
    first_start  = {}
    completion   = {}
    current_time = 0
    done         = 0
    idx          = 0

    # Seed with processes that arrive at time 0
    while idx < n and proc_list[idx].arrival_time <= current_time:
        ready.append(proc_list[idx])
        enqueued.add(proc_list[idx].pid)
        idx += 1

    while done < n:
        # Idle gap
        if not ready:
            if idx < n:
                current_time = proc_list[idx].arrival_time
                while idx < n and proc_list[idx].arrival_time <= current_time:
                    ready.append(proc_list[idx])
                    enqueued.add(proc_list[idx].pid)
                    idx += 1
            continue

        cur  = ready.popleft()
        pid  = cur.pid

        if pid not in first_start:
            first_start[pid] = current_time

        run   = min(quantum, cur.remaining_time)
        t_end = current_time + run

        # Merge consecutive same-pid Gantt blocks
        if gantt and gantt[-1][0] == pid and gantt[-1][2] == current_time:
            gantt[-1] = (pid, gantt[-1][1], t_end)
        else:
            gantt.append((pid, current_time, t_end))

        cur.remaining_time -= run
        current_time        = t_end

        # Enqueue arrivals during this slice (before re-adding cur)
        while idx < n and proc_list[idx].arrival_time <= current_time:
            if proc_list[idx].pid not in enqueued:
                ready.append(proc_list[idx])
                enqueued.add(proc_list[idx].pid)
            idx += 1

        if cur.remaining_time > 0:
            ready.append(cur)
        else:
            completion[pid] = current_time
            done           += 1

    # Build metrics dict
    metrics = {}
    for p in proc_list:
        tat = completion[p.pid] - p.arrival_time
        wt  = tat - p.burst_time
        rt  = first_start[p.pid] - p.arrival_time
        metrics[p.pid] = {'WT': wt, 'TAT': tat, 'RT': rt}

    return gantt, metrics
