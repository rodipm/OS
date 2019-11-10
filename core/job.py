import time
import enum
import logging

logger = logging.getLogger(__name__)

JobState = enum.Enum('JobState', 'SUBMIT WAIT_RESOURCES READY RUNNING WAIT_IO DONE')
JobPriority = enum.IntEnum('JobPriority', 'LOW NORMAL HIGH CRITICAL')

io = { "disco": None,"leitora1": None,"leitora2": None,"impressora1": None,"impressora2": None }

class Job:
    def __init__(self, _id, execution_time, priority=JobPriority.NORMAL, io={ "disco": None,"leitora1": None,"leitora2": None,"impressora1": None,"impressora2": None }, size=10):
        self.id = _id
        self.total_cycles = execution_time
        self.priority = priority
        self.size = size

        self.arrive_time = 0
        self.start_time = 0
        self.current_cycle = 0
        self._state = JobState.SUBMIT

        self.waiting_current_io_cycles = 0
        self.current_io_req = None

        self.io = io

        self.cpu_cycles = 0
        self.io_cycles = 0

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, st):
        if self._state != JobState.DONE:
            self._state = st

    def __str__(self):
        ret_str = f"JOB ID: {self.id} | STATE: {self._state}\n"
        has_io = False
        io_str = str()
        for dev_key in self.io.keys():
            if self.io[dev_key] != None:
                has_io = True
                io_str += f"\t {self.io[dev_key].name}: "
                for i, req in enumerate(self.io[dev_key].io_requests):
                    if i != 0:
                        io_str += " | "
                    io_str += f"{req[0]}[{req[1]}]"
                io_str += "\n"
        if has_io:
            ret_str += "\tIO: \n"
            ret_str += io_str + "\n"

        ret_str += f"\tTotal Cycles: {self.cpu_cycles + self.io_cycles}\n"
        ret_str += f"\tCPU Cycles: {self.cpu_cycles} ({(self.cpu_cycles / (self.cpu_cycles + self.io_cycles))*100:.2f}%)\n"
        ret_str += f"\tIO Cycles: {self.io_cycles} ({(self.io_cycles / (self.cpu_cycles + self.io_cycles))*100:.2f}%)\n"
        return ret_str

    def __lt__(self, other):
        return self.priority < other.priority

    def __gt__(self, other):
        return self.priority > other.priority

    def __eq__(self, other):
        return self.id == other.id

    def cycle(self):
        self.current_cycle += 1
    
        if self._state == JobState.RUNNING:
            self.cpu_cycles += 1

        if self._state == JobState.WAIT_IO:
            self.waiting_current_io_cycles += 1
            self.io_cycles += 1

        if self.cpu_cycles == self.total_cycles:
            self.state = JobState.DONE
