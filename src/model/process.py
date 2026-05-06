class Process:

    def __init__(self,pid,arrival_time,burst_time):

        #core process information thta never changes
        self.pid=pid
        self.arrival_time=arrival_time
        self.burst_time=burst_time

        #information thta get updated during simulation

        self.remaining_time=burst_time
        self.start_time=None
        self.finish_time=None
        self.waiting_time=0
        self.turnaround_time=0
        self.response_time=None

        #when the user clicks run second time

        def reset(self):

            self.remaining_time=self.bust_time
            self.start_time = None
            self.finish_time = None
            self.waiting_time = 0
            self.turnaround_time = 0
            self.response_time = None
        
        def is_finished(self):
            return self.remaining_time==0
        
        def __rep__(self):
            return(
                f"process(pid={self.pid}, arrival={self.arrival_time}, "
                f"burst={self.burst_time}, remaining={self.remaining_time})"
            )




          
         

