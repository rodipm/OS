import sys
import random
import enum

from core.OS import OS
from core.job import Job, JobPriority
from core.devices.device import Device
from core.event import IOFinishedEvent, DiskFinishedEvent, LeitoraUmFinishedEvent, LeitoraDoisFinishedEvent, ImpressoraUmFinishedEvent, ImpressoraDoisFinishedEvent 

io_config = {
        "disco": (10, 50),
        "leitora1": (30, 70),
        "leitora2": (50, 90),
        "impressora1": (70,100),
        "impressora2": (70, 120)
}
class CLI:
    def __init__(self):
        self.command_list = {
                "add": {
                        "exec": self.add_command,
                        "desc": "Adiciona um ou mais jobs ao sistema"
                    },
                "start": {
                        "exec": self.start_command,
                        "desc": "Inicia a simulação do sistema operacional"
                    },
                "ls": {
                        "exec": self.ls_command,
                        "desc": "Lista os comandos disponíveis"
                    },
                "jobs-list": {
                    "exec": self.jobs_list_command,
                    "desc": "Lista os Jobs presentes no sistema, assim como estatisticas de execução"
                },
                "exit": {
                    "exec": self.exit_command,
                    "desc": "Termina a execução do simulador"
                    }
                }
        self.os = OS()
        self.job_ids = 0
        self.total_cycles_io = 0
        self.total_cycles_cpu = 0

    def listen_to_commands(self):
        while True:
            cmd = input("> ").split()

            print(cmd)

            if cmd[0] in self.command_list.keys():
                if len(cmd) > 1 and len(inspect.getargspec(self.command_list[cmd[0]]["exec"]).args) > 1:
                    args = cmd[1:]
                    self.command_list[cmd[0]]["exec"](*args)
                else:
                    self.command_list[cmd[0]]["exec"]()
            else:
                print("Comando Inválido! Digite 'ls' para obter a lista de comandos disponíveis")

    ##########    
    # commands
    ##########    

    def add_command(self, run_time, number):
        run_time = int(run_time)
        number = int(number)
        finish_events = {
            "disco": DiskFinishedEvent,
            "leitora1": LeitoraUmFinishedEvent,
            "leitora2": LeitoraDoisFinishedEvent,
            "impressora1": ImpressoraUmFinishedEvent,
            "impressora2": ImpressoraDoisFinishedEvent
        }

        for _ in range(number):
            io = {
                "disco": None,
                "leitora1": None,
                "leitora2": None,
                "impressora1": None,
                "impressora2": None
            }

            last_start_cycles = [1]

            for dev in io.keys():
                io_requests = []
                has_device = bool(random.random() < 0.9)

                if not has_device:
                    continue

                number_requests = random.randint(1, 5)

                for i in range(number_requests):
                    io_cycles = random.randint(*io_config[dev])
                    start_cycle = 1

                    try:
                        start_cycle = random.randint(last_start_cycles[-1], i * run_time//number_requests - io_cycles)
                        if start_cycle in last_start_cycles:
                            continue

                        last_start_cycles.append(start_cycle)
                    except ValueError:
                        continue
                        
                    io_requests.append((start_cycle, io_cycles))


                if len(io_requests):
                    io[dev] = Device(dev, io_requests, finish_events[dev])


            job_priority = random.choice(list(JobPriority)) 
            job_size = random.randint(10, 70)
            
            new_job = Job(self.job_ids, run_time, job_priority, io, job_size)
            
            self.job_ids += 1

            self.os.add_job(new_job)

    def start_command(self):
        self.os.start()

    def ls_command(self):
        print("Comandos disponiveis:")
        for cmd in self.command_list.keys():
            print(cmd, ": ", self.command_list[cmd]["desc"])

    def jobs_list_command(self):
        total_cycles_io = 0
        total_cycles_cpu = 0

        for jb in self.os.jobs_list:
            print(jb)
            self.total_cycles_cpu += jb.cpu_cycles
            self.total_cycles_io += jb.io_cycles
            print("="*15)
            print(f"Total Simulated Cycles: {self.os.current_cycle}")
            print(
                f"Total cpu Cycles: {self.total_cycles_cpu} ({(self.total_cycles_cpu / self.os.current_cycle)*100:.2f}%)")
            print(
                f"Total IO Cycles: {self.total_cycles_io} ({(self.total_cycles_io / self.os.current_cycle)*100:.2f}%)")


    def exit_command(self):
        sys.exit()
