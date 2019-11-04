import sys
import random
import inspect

from core.OS import OS
from core.job import Job

class CLI:
    def __init__(self):
        self.command_list = {
                "add": {
                        "exec": self.add_command,
                        "desc": "Adiciona um ou mais jobs ao sistema"
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
            has_io = bool(random.randint(0, 1))

            try:
                io_start_time = random.randint(2, run_time - 1) if has_io else 0
            except ValueError:
                has_io = False
                io_start_time = 0

            io_duration = random.randint(10, 100) if has_io else 0

            new_job = Job(self.job_ids, run_time, io=(has_io, io_start_time, io_duration))
            self.job_ids += 1

            self.os.add_job(new_job)

    def ls_command(self):
        print("Comandos disponiveis:")
        for cmd in self.command_list.keys():
            print(cmd, ": ", self.command_list[cmd]["desc"])

    def exit_command(self):
        sys.exit()
