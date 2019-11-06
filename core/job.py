import time
import enum
import logging

logger = logging.getLogger(__name__)

JobState = enum.Enum('JobState', 'SUBMIT WAIT_RESOURCES READY RUNNING WAIT_IO DONE')
JobPriority = enum.IntEnum('JobPriority', 'LOW NORMAL HIGH CRITICAL')

io = { "disco": None,"leitora1": None,"leitora2": None,"impressora1": None,"impressora2": None }

class Job:
    def __init__(self, _id, execution_time, priority=JobPriority.NORMAL, io={ "disco": None,"leitora1": None,"leitora2": None,"impressora1": None,"impressora2": None }):
        self.id = _id
        self.total_cycles = execution_time
        self.priority = priority

        self.arrive_time = 0
        self.start_time = 0
        self.current_cycle = 0
        self._state = JobState.SUBMIT

        self.io = io

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, st):
        if self._state != JobState.DONE:
            self._state = st

    def __str__(self):
        return str(self.id)

    def __lt__(self, other):
        return self.priority < other.priority

    def __gt__(self, other):
        return self.priority > other.priority

    def __eq__(self, other):
        return self.id == other.id

    def cycle(self):
        self.current_cycle += 1
        print(f'Job {self.id} running cycle {self.current_cycle} of {self.total_cycles}.')
        if self.current_cycle == self.total_cycles:
            self.state = JobState.DONE
