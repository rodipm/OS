# Sistemas Operacionais - PCS 3446 - 2019 #

Rodrigo Perrucci Macharelli - 9348877

--------------------

## Introdução ##

O projeto tem como objetivo implementar programaticamente um sistema de simulação orientado a eventos cuja intenção é implementar as funcionalidades básicas de um sistema operacional simples, capaz de receber Jobs criados a partir de uma linha de comando, organizar as suas ordens de execução, tratar eventos (aqui simulando o funcionamento de um sistema de interrupções) gerados pelos processos em execução, simular acesso a diferentes dispositivos de entrada e saída e implementa um sistema simples de segmentação de memória com partições fixas, possibilitando um sistema multiprogramado.

## Estrutura do projeto ##

O projeto foi estruturado de forma a conter uma interface de linha de comando **CLI**, pela qual é possível interagir com o sistema, adicionando Jobs e obtendo dados da simulação, uma **Máquina de Eventos** responsável pela simulação propriamente dita de um sistema operacional simples, um módulo de **Memória** segmentada e **Devices I/O** para os quais os processos em execução podem efetuar requerimentos.

### Máquina de eventos ###
Baseado no artigo apresentado e nas aulas, foi implementado um motor de eventos que implementa uma máquina de estados com seis possíveis estados:

1. SUBMIT: Estado inicial atribuído aos jobs que são adicionados ao sistema
2. WAIT_RESOURCES: Estado de espera de alocação de recursos para o Job. Mais especificamente, é durante este estágio que o sistema de administração de memória verifica a possibilidade de alocação do Job, para que este possa ser executado.
3. READY: Após o Job ser alocado em memória passa para este estado, no qual aguarda ser escalonado para utilização da CPU, e consequentemente, sua execução.
4. RUNNING: Neste estado o Job passa a ser efetivamente um processo em execução no simulador, podendo gerar eventos de comunicação com os dispositivos de entrada e saída disponíveis.
5. WAIT_IO: Estado que representa os Jobs que estão aguardando a resposta de um pedido a um dispositivo de entrada e saída (descritos adiante), para que possa então seguir a sua execução, voltando ao estado READY e podendo ser escalonado novamente para a utilização da CPU.
6. DONE: Estado final da simulação, representando o fim da execução e finalização de todos os pedidos de comunicação com os dispositivos I/O.

Este motor de eventos é representado pela classe **OS**.

```python
class OS:
    def __init__(self, num_threads=4):
        self.clock = 0.0

        self.memory = Memory()

        self.event_queue = Queue()
        self.jobs_queue = PriorityQueue()
        self.ready_jobs = []
        self.active_jobs = []
        self.completed_jobs = 0

        self.waiting_io_jobs = {
            "disco": [],
            "leitora1": [],
            "leitora2": [],
            "impressora1": [],
            "impressora2": []
        }

        self.running_jobs = 0
        self.jobs_list = []

        self.num_threads = num_threads
        self.current_cycle = 0

        self.schedulers = None 
        self.processor = None 
        self.started = False
```
Para sua implementação foram considerados alguns dos principais elementos presentes em um sistema operacional, implementados nesta classe e descritos a seguir.

#### Job Scheduler ####

Responsável por obter os jobs submetidos, alocados na fila de prioridade "jobs_queue", de forma que possam ser alocados em memória. As prioridades dos Jobs implementadas nesta simulação são as seguintes: LOW, NORMAL, HIGH, CRITICAL, sendo o último de maior prioridade.
Neste elemento estão também incluídas funcionalidades do administrador de memória, que tem como finalidade verificar a disponibilidade de alocação de memória para o Job que, em caso positivo deve faze-lo nas partições disponíveis, sejam elas contíguas ou não. Em caso negativo o Job volta para a fila de jobs em estado SUBMIT para que possa aguardar até que um outro job seja concluído e parte da memória seja liberada. O módulo de memória implementado será tratado mais adiante.

```python
def _job_scheduler(self):

        try:
            new_job = self.jobs_queue.get(False)
        except Empty:
            return

        allocated_segments = self.memory.allocate(new_job.id, new_job.size)

        if allocated_segments:
            print(f'[{self.current_cycle:05d}] Job Scheduler: Job {new_job.id} está no estado READY depois de {job.current_cycle} ciclos.')
            print(self.memory)
            new_job.state = JobState.READY
            new_job.start_time = self.current_cycle
            self.ready_jobs.append(new_job)
            self._update_jobs_list(new_job)
        else:
            self.jobs_queue.put(new_job)
            self._update_jobs_list(new_job)
```

#### Process Scheduler ####

Responsável por transformar os Jobs prontos para execução (READY) em processos própriamente ditos, ou seja, os escalona para execução na CPU, associando-os ao estado RUNNING. É neste elemento em que tomam-se as medidas para possibilitar a multiprogramação do sistema, isto é, pode haver mais de um job em memória ao mesmo tempo, sendo executados de forma intercalada pelo sistema. Os processos em execução sao alocados em "active_jobs".

```python
def _process_scheduler(self):
        for job in self.ready_jobs[:]:
            if self.running_jobs >= self.num_threads:
                return

            print(f'[{self.current_cycle:05d}] Process Scheduler: Iniciando job {job.id} depois de {job.current_cycle} ciclos')
            self.ready_jobs.remove(job)
            job.state = JobState.RUNNING
            self.running_jobs += 1
            self.active_jobs.append(job)
            self._update_jobs_list(job)
```

#### Tratador de Eventos ####

Responsável por tratar os eventos gerados pelo sistema, isto é, gerados pelos dispositivos de I/O ao término de suas execuções ou por eventos externos como o evento de finalização forçada de um processo. Os Jobs atendidos por este elemento são os que estão no estado WAIT_IO, que passam ao estado READY ao final do tratamento de um evento de termino de I/O. Neste caso os Jobs são removidos da lista de "waiting_io_jobs" e voltam a lista de "ready_jobs".

```python
    def _event_process(self):
        try:
            event = self.event_queue.get(False)
        except Empty:
            return

        event_name = type(event).__name__
        event_base_class = type(event).__bases__[0]

        if event_base_class == IOFinishedEvent:
            print(f'SO: Processando evento {event_name} para o Job {event.job_id}.')
            event.process()

            waiting_io_jobs_cp = copy.deepcopy(self.waiting_io_jobs)

            dev = event.device_name

            for j in waiting_io_jobs_cp[dev]:
                if j.id == event.job_id:
                    self.waiting_io_jobs[dev].remove(j)
                    j.state = JobState.READY
                    j.current_io_req = None
                    j.waiting_current_io_cycles = 0
                    self.ready_jobs.append(j)
                    self._update_jobs_list(j)
                    return

        if type(event) == KillProcessEvent:
            print(f'SO: Processando evento {event_name} para o Job {event.job_id}.')
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

        print(f"SO: Evento desconhecido {event_name}")
```

#### Processador ####

O processador foi aqui representado pela função mostrada a seguir. 

```python
def _run(self):

        if len(self.jobs_list) == self.completed_jobs:
            print(f"[{self.current_cycle}] Todos os jobs foram completados!")
            self.started = False
            return
             
        for job in self.active_jobs[:]:
            job.cycle()
            self._update_jobs_list(job)

            for dev in job.io.keys():
                if job.io[dev] == None:
                    continue

                request_io = False

                for req in job.io[dev].io_requests:
                    if req[0] == job.cpu_cycles:
                        request_io = req
                        break

                if request_io:
                    print(f'[{self.current_cycle:05d}] SO: Job {job.id} pedindo acesso ao dispositivo I/O {job.io[dev].name}.')
                    job.state = JobState.WAIT_IO
                    job.current_io_req = (dev, request_io)
                    self.running_jobs -= 1
                    self.active_jobs.remove(job)
                    self.waiting_io_jobs[dev].append(job)
                    self._update_jobs_list(job)


                
            if job.state == JobState.DONE:
                print(f'[{self.current_cycle:05d}] SO: Job {job.id} finalizado depois de {self.current_cycle - job.start_time} ciclos.')

                self.memory.deallocate(job.id)
                print(f"[{self.current_cycle:05d}] SO: Estado atual da memõria:")
                print(self.memory)
                self.running_jobs -= 1
                self.active_jobs.remove(job)
                self.completed_jobs += 1
                self._update_jobs_list(job)


            self.current_cycle += 1
            time.sleep(self.clock)

        for dev in self.waiting_io_jobs:
            for job in self.waiting_io_jobs[dev]:
                job.cycle()
                self.current_cycle += 1
                if job.current_io_req[1][1] == job.waiting_current_io_cycles:
                    self.io_finish(job.id, job.io[job.current_io_req[0]].finish_event)

        time.sleep(0.1*self.clock)
```

Este é responsável por simular a execução dos processos ativos no sistema, atualizando seus estados de ciclos e dando continuidade a simulação. Caso existam requerimentos de dispositivos de entrada e saída associados ao job sendo processado no tempo de simulação corrente, serão tratados e inseridos os respectivos eventos a lista de eventos a serem processados, alterando o estado do job para WAIT_IO. Caso o Job tenha sido finalizado, este é removido da memória, liberando espaço para outros jobs que estejam aguardando a disponibilidade de recursos.
Caso o número de jobs completos seja igual ao número de Jobs submetidos ao sistema, a simulação é finalizada.

#### Execução da simulação ####

Sendo expostos os principais componentes da simulação, pode-se mostrar como foi feita a elaboração de sua execução, representada por um laço que executa os componentes citados acima de forma a representar o processo real de funcionamento de um sistema operacional.

```python
def start(self):
    self.schedulers = self._schedulers
    self.processor = self._run
    self.started = True
    while self.started:
        self.schedulers()
        self.processor()
```

Sendo que "_schedulers" representa os três elementos de manipulação dos jobs:

```python
def _schedulers(self):
    self._job_scheduler()
    self._process_scheduler()
    self._event_process()
```

### Representação do Job ###

Os Jobs foram representados pela classe de mesmo nome descrita a seguir:

```python
JobState = enum.Enum('JobState', 'SUBMIT WAIT_RESOURCES READY RUNNING WAIT_IO DONE')
JobPriority = enum.IntEnum('JobPriority', 'LOW NORMAL HIGH CRITICAL')

class Job:
    def __init__(self, _id, execution_time,
            priority=JobPriority.NORMAL, 
            io={ "disco": None,"leitora1": None,"leitora2": None,"impressora1": None,"impressora2": None },
            size=10):

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
```

Nas primeiras duas linhas são definidos os estados e prioridades já discutidos anteriormente. A classe Job apresenta os seguintes atributos:

* **id**: Identificador único do Job.
* **total_cycles**: Quantidade de ciclos de execução de CPU, representa, a grosso modo, a quantidade de instruções a serem executadas na CPU (esta representação torna-se mais realista se considerarmos um processador com arquitetura de pipeline considerando-o cheio, de forma que apresentaria um throughput de 1 instrução por ciclo em funcionamento normal). É com base neste valor que sabemos o fim do ciclo de vida do Job.
* **priority**: Prioridade associada ao Job.
* **size**: Representa o tamanho médio que o programa ocupará na memória em tempo de execução, tanto com dados quanto com instruções.
* **arrive_time, start_time, current_cycle**: Marcadores dos ciclos de chegada do job ao sistema, ciclo de inicio de execução do processo e ciclo atual do Job.
* **_state**: Estado atual do Job (SUBMIT, WAIT_RESOURCES, READY, RUNNING, WAIT_IO, DONE)
* **waiting_current_io_cycles**: Contador de cíclos de espera de resposta de despositivo