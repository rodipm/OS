import sys
import random
import inspect
import threading
import enum

from core.OS import OS
from core.job import Job, JobPriority
from core.devices.device import Device
from core.event import IOFinishedEvent, DiskFinishedEvent, LeitoraUmFinishedEvent, LeitoraDoisFinishedEvent, ImpressoraUmFinishedEvent, ImpressoraDoisFinishedEvent 

class CLI:
    def __init__(self):
        self.command_list = {
                "add": {
                        "exec": self.add_command,
                        "desc": "Adiciona um ou mais jobs ao sistema"
                    },
                "start": {
                        "exec": self.start_command,
                        "desc": "Inicia a simulacao do sistema operacional"
                    },
                "ls": {
                        "exec": self.ls_command,
                        "desc": "Lista os comandos disponíveis"
                    },
                "exit": {
                    "exec": self.exit_command,
                    "desc": "Termina a execução do simulador"
                    }
                }
        self.os = OS()
        self.job_ids = 0

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
                print("Comando Inválido! Digite 'ls' para obter a lista de comandos disponĩveis")

    ##########    
    # commands
    ##########    

    def add_command(self, run_time, number):
        run_time = int(run_time)
        number = int(number)

        for _ in range(number):
            io = {
                "disco": None,
                "leitora1": None,
                "leitora2": None,
                "impressora1": None,
                "impressora2": None
            }

            for dev in io.keys():
                has_device = bool(random.randint(0, 1))

                try:
                    start_cycle = random.randint(2, run_time - 1) if has_device else 0
                except ValueError:
                    has_device = False
                    start_cycle = 0

                read_cycles = random.randint(10, 100) if has_device else 0

                if has_device:
                    io[dev] = Device(dev, start_cycle, read_cycles, LeitoraUmFinishedEvent)


            job_priority = random.choice(list(JobPriority)) 
            
            new_job = Job(self.job_ids, run_time, job_priority, io)
            
            self.job_ids += 1

            self.os.add_job(new_job)

    def start_command(self):
        t1, t2 = self.os.start()
        t1.join()
        t2.join()


    def ls_command(self):
        print("Comandos disponiveis:")
        for cmd in self.command_list.keys():
            print(cmd, ": ", self.command_list[cmd]["desc"])

    def exit_command(self):
        sys.exit()
