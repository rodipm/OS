from ..event import Event

# io_requests = [(start_cycle, io_cycles)]
class Device:
    def __init__(self, name, io_requests, finish_event: Event):
        self.name = name
        self.io_requests = io_requests
        self.finish_event = finish_event
