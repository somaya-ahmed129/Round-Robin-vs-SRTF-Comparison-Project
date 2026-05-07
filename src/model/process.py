class Process:
    def __init__(self, pid, arrival_time, burst_time):
        self.pid          = pid
        self.arrival_time = arrival_time
        self.burst_time   = burst_time

        self.remaining_time = burst_time
        self.start_time     = None
        self.finish_time    = None
        self.waiting_time   = 0
        self.turnaround_time = 0
        self.response_time  = None

    def reset(self):
        self.remaining_time  = self.burst_time
        self.start_time      = None
        self.finish_time     = None
        self.waiting_time    = 0
        self.turnaround_time = 0
        self.response_time   = None

    def is_finished(self):
        return self.remaining_time == 0

    def __repr__(self):
        return (f"Process(pid={self.pid}, arrival={self.arrival_time}, "
                f"burst={self.burst_time}, remaining={self.remaining_time})")




          
         

