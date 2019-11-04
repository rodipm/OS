import logging
import coloredlogs
import sys

fmt = '[{levelname:7s}] {name:s}: {message:s}'
logger = logging.getLogger(__name__)
coloredlogs.DEFAULT_FIELD_STYLES['levelname']['color'] = 'white'

if len(sys.argv) >= 2 and sys.argv[1] in ['-d', '--debug']:
    coloredlogs.install(level=logging.DEBUG, logger=logger, fmt=fmt, style='{')
else:
    coloredlogs.install(level=logging.WARNING, logger=logger, fmt=fmt, style='{')

class Event:
    def process(self):
        logger.warning(f'Processamento do evento não implementado!')

class IOFinishedEvent(Event):
    def __init__(self, job_id):
        super(IOFinishedEvent, self).__init__()
        self.job_id = job_id

    def process(self):
        print(f'Job {self.job_id} I/O event finished.')

class KillProcessEvent(Event):
    def __init__(self, job_id):
        super(KillProcessEvent, self).__init__()
        self.job_id = job_id

    def process(self):
        print(f'Job {self.job_id} killed.')
