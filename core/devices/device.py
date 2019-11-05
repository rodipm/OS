from ..event import Event

class Device:
    def __init__(self, name, start_cycle, read_cycles, finish_event: Event):
        self.name = name
        self.start_cycle = start_cycle
        self.read_cycles = read_cycles
        self.finish_event = finish_event
