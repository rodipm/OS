import sys

class Event:
    def process(self):
        print(f'Processamento do evento não implementado!')

class IOFinishedEvent(Event):
    def __init__(self, job_id):
        super(IOFinishedEvent, self).__init__()
        self.job_id = job_id

    def process(self):
        print(f'Job {self.job_id}: evento de dispositivo I/O: Finalizado.')

class DiskFinishedEvent(IOFinishedEvent):
    def __init__(self, job_id):
        super().__init__(job_id)
        self.device_name = "disco"

class LeitoraUmFinishedEvent(IOFinishedEvent):
    def __init__(self, job_id):
        super().__init__(job_id)
        self.device_name = "leitora1"

class LeitoraDoisFinishedEvent(IOFinishedEvent):
    def __init__(self, job_id):
        super().__init__(job_id)
        self.device_name = "leitora2"

class ImpressoraUmFinishedEvent(IOFinishedEvent):
    def __init__(self, job_id):
        super().__init__(job_id)
        self.device_name = "impressora1"

class ImpressoraDoisFinishedEvent(IOFinishedEvent):
    def __init__(self, job_id):
        super(ImpressoraDoisFinishedEvent, self).__init__(job_id)
        self.device_name = "impressora2"

class KillProcessEvent(Event):
    def __init__(self, job_id):
        super(KillProcessEvent, self).__init__()
        self.job_id = job_id

    def process(self):
        print(f'Job {self.job_id} finalizado.')
