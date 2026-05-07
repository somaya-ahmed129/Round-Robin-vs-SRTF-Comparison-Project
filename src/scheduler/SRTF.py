from src.model.process import Process


def srtf_scheduler(processes):
    """
    Parameters
    ----------
    processes : list of Process objects (will NOT be mutated)

    Returns
    -------
    gantt   : list[(pid, start, end)]
    metrics : dict{ pid: {'WT':int, 'TAT':int, 'RT':int} }
    """
    if not processes:
        return [], {}

    proc_list = [Process(p.pid, p.arrival_time, p.burst_time) for p in processes]
    proc_list.sort(key=lambda p: (p.arrival_time, p.pid))

    n            = len(proc_list)
    done         = 0
    current_time = min(p.arrival_time for p in proc_list)
    gantt        = []
    first_start  = {}
    completion   = {}

    prev_pid    = None
    block_start = current_time

    while done < n:
        available = [p for p in proc_list
                     if p.arrival_time <= current_time and p.remaining_time > 0]

        # Idle gap
        if not available:
            if prev_pid is not None:
                gantt.append((prev_pid, block_start, current_time))
                prev_pid = None
            nxt = min((p.arrival_time for p in proc_list if p.remaining_time > 0),
                      default=None)
            if nxt is None:
                break
            current_time = nxt
            block_start  = current_time
            continue

        cur = min(available, key=lambda p: (p.remaining_time, p.arrival_time, p.pid))

        if cur.pid not in first_start:
            first_start[cur.pid] = current_time

        if cur.pid != prev_pid:
            if prev_pid is not None:
                gantt.append((prev_pid, block_start, current_time))
            block_start = current_time
            prev_pid    = cur.pid

        cur.remaining_time -= 1
        current_time       += 1

        if cur.remaining_time == 0:
            completion[cur.pid] = current_time
            done               += 1
            gantt.append((cur.pid, block_start, current_time))
            prev_pid    = None
            block_start = current_time

    if prev_pid is not None:
        gantt.append((prev_pid, block_start, current_time))

    # Merge consecutive same-pid blocks
    gantt = _merge(gantt)

    metrics = {}
    for p in proc_list:
        tat = completion[p.pid] - p.arrival_time
        wt  = tat - p.burst_time
        rt  = first_start[p.pid] - p.arrival_time
        metrics[p.pid] = {'WT': wt, 'TAT': tat, 'RT': rt}

    return gantt, metrics


def _merge(gantt):
    if not gantt:
        return gantt
    merged = [gantt[0]]
    for entry in gantt[1:]:
        last = merged[-1]
        if entry[0] == last[0] and entry[1] == last[2]:
            merged[-1] = (last[0], last[1], entry[2])
        else:
            merged.append(entry)
    return merged

            
        







