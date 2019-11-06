import logging
import copy
import coloredlogs
import sys
import time
import threading

from .job import Job, JobState, JobPriority
from .event import IOFinishedEvent, KillProcessEvent, Event
from .devices.device import Device
from queue import Queue, PriorityQueue, Empty

logger = logging.getLogger(__name__)

class OS:
    def __init__(self, multiprogramming=4):
        self.event_queue = Queue()
        self.jobs_queue = PriorityQueue()
        self.ready_jobs = []
        self.active_jobs = []

        self.waiting_io_jobs = {
            "disco": [],
            "leitora1": [],
            "leitora2": [],
            "impressora1": [],
            "impressora2": []
        }

        self.running_jobs = 0

        self.processing = threading.Lock()

        self.multiprogramming = multiprogramming
        self.current_cycle = 0

        self.schedulers = None 
        self.processor = None 
        self.started = False


    def start(self):
        self.schedulers = threading.Thread(target=self._schedulers)
        self.processor = threading.Thread(target=self._run)
        self.started = True
        self.schedulers.start()
        self.processor.start()
        return (self.schedulers, self.processor)


    def _event_process(self):
        try:
            event = self.event_queue.get(False)
        except Empty:
            return

        event_name = type(event).__name__
        event_base_class = type(event).__bases__[0]

        if event_base_class == IOFinishedEvent:
            print(f'[{self.current_cycle:05d}] SO: Processing event {event_name} for Job {event.job_id}.')
            event.process()

            waiting_io_jobs_cp = copy.deepcopy(self.waiting_io_jobs)

            dev = event.device_name

            for j in waiting_io_jobs_cp[dev]:
                if j.id == event.job_id:
                    self.waiting_io_jobs[dev].remove(j)
                    j.state = JobState.READY
                    self.ready_jobs.append(j)
                    return

        if type(event) == KillProcessEvent:
            print(f'[{self.current_cycle:05d}] SO: Processing event {event_name} for Job {event.job_id}.')
            event.process()

            for dev in waiting_io_jobs_cp.keys():
                for j in waiting_io_jobs_cp[dev]:
                    if j.id == event.job_id:
                        self.waiting_io_jobs[dev].remove(j)
                        j.state = JobState.DONE
                        return

            for j in self.active_jobs[:]:
                if j.id == event.job_id:
                    self.running_jobs -= 1
                    self.active_jobs.remove(j)
                    j.state = JobState.DONE
                    return

            for j in self.ready_jobs[:]:
                if j.id == event.job_id:
                    self.ready_jobs.remove(j)
                    j.state = JobState.DONE
                    return

        logger.warning(f'[{self.current_cycle:05d}] SO: Unknown event {event_name}')

    def _job_scheduler(self):
        try:
            new_job = self.jobs_queue.get(False)  # Get job from Priority Queue
        except Empty:
            return

        print(f'[{self.current_cycle:05d}] Job Scheduler: Job {new_job.id} now READY after {self.current_cycle - new_job.arrive_time} cycles.')
        new_job.state = JobState.READY
        new_job.start_time = self.current_cycle
        self.ready_jobs.append(new_job)  # Add job to active jobs list

    def _process_scheduler(self):
        for job in self.ready_jobs[:]:
            if self.running_jobs >= self.multiprogramming:
                continue

            print(f'[{self.current_cycle:05d}] Process Scheduler: Starting job {job.id} after {self.current_cycle - job.arrive_time} cycles')
            self.ready_jobs.remove(job)
            job.state = JobState.RUNNING
            self.running_jobs += 1
            self.active_jobs.append(job) # Initilize job with 0 used cycles


    def add_job(self, job: Job):
        devs = []

        for dev in job.io.keys():
            if job.io[dev] != None:
                devs.append(job.io[dev])

        if len(devs):
            dev_list = " | ".join([dev.name +" "+ str(len(dev.io_requests)) for dev in devs])
            print(f'[{self.current_cycle:05d}] SO: Received Job (id {job.id}) with {job.priority} priority and I/O accesses: {dev_list}. Adding to queue.')
        else:
            print(f'[{self.current_cycle:05d}] SO: Received Job (id {job.id}) with {job.priority} priority and no I/O. Adding to queue.')
        job.state = JobState.WAIT_RESOURCES
        job.arrive_time = self.current_cycle
        self.jobs_queue.put(job)

    def io_finish(self, job_id, finish_event: Event):
        evt = finish_event(job_id)
        self.event_queue.put(evt)

    def _schedulers(self):
        while self.started:
            self.processing.acquire()
            self._job_scheduler()
            self._process_scheduler()
            self._event_process()
            self.processing.release()
        del(self.schedulers)

    def _run(self):
        while self.started:
            self.processing.acquire()

            if len(self.active_jobs) == 0:
                self.current_cycle += 1
                self.processing.release()
                time.sleep(0.1)
                self.started = False
                continue


            for job in self.active_jobs[:]:
                job.cycle()

                for dev in job.io.keys():
                    if not job.io[dev]:
                        continue

                    request_io = False

                    for req in job.io[dev].io_requests:
                        if req[0] == job.current_cycle:
                            request_io = req
                            break

                    if request_io:

                        print(f'[{self.current_cycle:05d}] SO: Job {job.id} requesting I/O operation on {job.io[dev].name}.')
                        t = threading.Timer(0.1 * request_io[1], self.io_finish, [job.id, job.io[dev].finish_event]) # espera clock * device_read_cycles
                        job.state = JobState.WAIT_IO

                        self.running_jobs -= 1
                        self.active_jobs.remove(job)
                        self.waiting_io_jobs[dev].append(job)

                        t.start()

                if job.state == JobState.DONE:
                    print(f'[{self.current_cycle:05d}] SO: Job {job.id} finished after {self.current_cycle - job.start_time} cycles.')

                    self.running_jobs -= 1
                    self.active_jobs.remove(job)

                self.current_cycle += 1
                time.sleep(0.1)

            self.processing.release()
            time.sleep(0.01)
        #self.processor.terminate()
        del(self.processor)
