"""
metrics/calculator.py
---------------------
Pure functions — no GUI dependencies.
All functions accept plain dicts so they work with both scheduler outputs.
"""


def calculate_tat(completion_time, arrive_time):
    return {p: completion_time[p] - arrive_time[p] for p in arrive_time}


def calculate_avg_tat(completion_time, arrive_time):
    tat = calculate_tat(completion_time, arrive_time)
    return round(sum(tat.values()) / len(tat), 2)


def calculate_wt(completion_time, arrive_time, burst_time):
    tat = calculate_tat(completion_time, arrive_time)
    return {p: tat[p] - burst_time[p] for p in tat}


def calculate_avg_wt(completion_time, arrive_time, burst_time):
    wt = calculate_wt(completion_time, arrive_time, burst_time)
    return round(sum(wt.values()) / len(wt), 2)


def calculate_rt(first_start, arrive_time):
    return {p: first_start[p] - arrive_time[p] for p in first_start}


def calculate_avg_rt(first_start, arrive_time):
    rt = calculate_rt(first_start, arrive_time)
    return round(sum(rt.values()) / len(rt), 2)


def averages_from_metrics(metrics: dict) -> dict:
    """
    Given the metrics dict produced by RoundRobin / SRTF schedulers
    { pid: {'WT':x, 'TAT':x, 'RT':x} }
    return { 'WT': avg, 'TAT': avg, 'RT': avg }
    """
    n = len(metrics)
    if n == 0:
        return {'WT': 0.0, 'TAT': 0.0, 'RT': 0.0}
    return {
        'WT':  round(sum(v['WT']  for v in metrics.values()) / n, 2),
        'TAT': round(sum(v['TAT'] for v in metrics.values()) / n, 2),
        'RT':  round(sum(v['RT']  for v in metrics.values()) / n, 2),
    }
