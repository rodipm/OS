import logging
import coloredlogs
import sys
import time
import threading

from .job import Job, JobState, JobPriority
from .event import IOFinishedEvent, KillProcessEvent
from queue import Queue, PriorityQueue, Empty

logger = logging.getLogger(__name__)

class OS:
    def __init__(self, multiprogramming=4):
        self.event_queue = Queue()
        self.jobs_queue = PriorityQueue()
        self.ready_jobs = []
        self.active_jobs = []
        self.waiting_io_jobs = []
        self.running_jobs = 0

        self.processing = threading.Lock()

        self.multiprogramming = multiprogramming
        self.current_cycle = 0

        print(f'[{self.current_cycle:05d}] Initializing Job Scheduler')
        print(f'[{self.current_cycle:05d}] Initializing Process Scheduler')
        print(f'[{self.current_cycle:05d}] Initializing Traffic Controller')

        self.schedulers = threading.Thread(target=self._schedulers)
        self.processor = threading.Thread(target=self._run)

        self.schedulers.start()
        self.processor.start()

    def _event_process(self):
        # while True:
        try:
            event = self.event_queue.get(False)
        except Empty:
            return

        event_name = type(event).__name__

        if type(event) == IOFinishedEvent:
            print(f'[{self.current_cycle:05d}] SO: Processing event {event_name} for Job {event.job_id}.')
            event.process()

            for j in self.waiting_io_jobs[:]:
                if j.id == event.job_id:
                    self.waiting_io_jobs.remove(j)
                    j.state = JobState.READY
                    self.ready_jobs.append(j)
                    return

        if type(event) == KillProcessEvent:
            print(f'[{self.current_cycle:05d}] SO: Processing event {event_name} for Job {event.job_id}.')
            event.process()

            for j in self.waiting_io_jobs[:]:
                if j.id == event.job_id:
                    self.waiting_io_jobs.remove(j)
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

    def _traffic_controller(self):
        pass

    def add_job(self, job: Job):
        if job.io[0]:
            print(f'[{self.current_cycle:05d}] SO: Received Job (id {job.id}) with {job.priority.name} priority and I/O on cycle {job.io[1]}|{job.io[2]}. Adding to queue.')
        else:
            print(f'[{self.current_cycle:05d}] SO: Received Job (id {job.id}) with {job.priority.name} priority and no I/O. Adding to queue.')
        job.state = JobState.WAIT_RESOURCES
        job.arrive_time = self.current_cycle
        self.jobs_queue.put(job)

    def io_finish(self, job_id):
        evt = IOFinishedEvent(job_id)
        self.event_queue.put(evt)

    def _schedulers(self):
        while True:
            self.processing.acquire()
            self._job_scheduler()
            self._process_scheduler()
            self._traffic_controller()
            self._event_process()
            self.processing.release()

    def _run(self):
        while True:
            self.processing.acquire()

            if len(self.active_jobs) == 0:
                self.current_cycle += 1
                self.processing.release()
                time.sleep(0.1)
                continue


            for job in self.active_jobs[:]:
                job.cycle()

                if job.io[0] and job.current_cycle == job.io[1]:
                    print(f'[{self.current_cycle:05d}] SO: Job {job.id} requesting I/O operation.')
                    t = threading.Timer(0.1 * job.io[2], self.io_finish, [job.id])
                    job.state = JobState.WAIT_IO

                    self.running_jobs -= 1
                    self.active_jobs.remove(job)
                    self.waiting_io_jobs.append(job)

                    t.start()

                if job.state == JobState.DONE:
                    print(f'[{self.current_cycle:05d}] SO: Job {job.id} finished after {self.current_cycle - job.start_time} cycles.')

                    self.running_jobs -= 1
                    self.active_jobs.remove(job)

                self.current_cycle += 1
                time.sleep(0.1)

            self.processing.release()
            time.sleep(0.01)
