import copy
from src.GUI.GanttChart import GanttEntry
from model.process import Process


def run_srtf(processes):

    procs=[copy.deepcopy(p) for p in processes]

    gantt=[]      #will hold the gannt_chart object
    completed=[]  #processs thta have finished
    time=0        #current clock_tick

    current_pid=None
    segmant_start=0

    while len(completed) < len(procs):

        ready=[p for p in procs if p.arrival_time<=time and not p.is_finished()]

        if not ready:
            # CPU idle
            if current_pid is not None:
                gantt.append(GanttEntry(current_pid,segmant_start,time))
                current_pid= None

            
            #jump forward to the next process arrival
            next_arrival=min(p.arrival_time for p in procs if not p.is_finished())  
            gantt.append(GanttEntry("IDLE", time, next_arrival))
            time=next_arrival
            segmant_start=time
            continue 
        #pick process with shortest remaining_time

        chosen=min(ready,key=lambda p:(p.remaining_time,p.arrival_time,p.pid))

        #record the first time this process touches the CPU

        if chosen.start_time is None:
            chosen.start_time=time
            chosen.response_time=time-chosen.arrival_time

        #if the running process changed,close the previous segmant and open a new one for the chosen process

        if chosen.pid != current_pid:
            if current_pid is not None:
                gantt.append(GanttEntry(current_pid,segmant_start,time))
            current_pid=chosen.pid
            segmant_start=time
        #execute for exactly one time unit

        chosen.remaining_time -=1
        time +=1

        #check if the process just finished

        if chosen.is_finished():
            chosen.finish_time=time
            chosen.turnaround_time=chosen.finish_time-chosen.arrival_time
            chosen.waiting_time=chosen.turnaround_time-chosen.burst_time
            completed.append(chosen)

            #close its gantt segmant

            gantt.append(GanttEntry(chosen.pid,segmant_start,time))
            current_pid=None
            segmant_start=time

    #Sort the results by PID for consistent display in the UI
    completed.sort(key=lambda p:p.pid)

    # Merge adjacent entries that have the same PID (can happen after idle
    # slots or when two separate segments are actually contiguous)
    gantt = _merge_consecutive(gantt)
 
    return completed, gantt

# ─── Helper ──────────────────────────────────────────────────────────────────
 
def _merge_consecutive(gantt):
    """
    Merge back-to-back Gantt entries that share the same PID.
 
    Example:
        [("P1", 0, 2), ("P1", 2, 4)]  →  [("P1", 0, 4)]
 
    This happens when SRTF runs the same process for multiple ticks without
    interruption — the one-tick loop produces many tiny entries that we tidy
    up here rather than cluttering the main loop logic.
    """
    if not gantt:
        return gantt
 
    merged = [gantt[0]]
 
    for entry in gantt[1:]:
        last = merged[-1]
        # If same PID and the new entry starts exactly where the last one ended
        if entry.pid == last.pid and entry.start == last.end:
            # Extend the last entry instead of appending a new one
            merged[-1] = GanttEntry(last.pid, last.start, entry.end)
        else:
            merged.append(entry)
 
    return merged
            
        







