# Sistemas Operacionais - PCS 3446 - 2019 #

Rodrigo Perrucci Macharelli - 9348877

--------------------

## Introdução ##

O projeto tem como objetivo implementar programaticamente um sistema de simulação orientado a eventos cuja intenção é implementar as funcionalidades básicas de um sistema operacional simples, capaz de receber Jobs criados a partir de uma linha de comando, organizar as suas ordens de execução, tratar eventos (aqui simulando o funcionamento de um sistema de interrupções) gerados pelos processos em execução, simular acesso a diferentes dispositivos de entrada e saída e implementa um sistema simples de segmentação de memória com partições fixas, possibilitando um sistema multiprogramado.

## Estrutura do projeto ##

### Máquina de eventos ###
Baseado no artigo apresentado e nas aulas, foi implementado um motor de eventos que implementa uma máquina de estados com seis possíveis estados:

    1. SUBMIT: Estado inicial atribuido aos jobs que são adicionados ao sistema
    2. WAIT_RESOURCES: Estado de espera de alocação de recursos para o Job. Mais especificamente, é durante este estágio que o sistema de administração de memória verifica a possibilidade de alocação do Job, para que este possa ser executado.
    3. READY: Após o Job ser alocado em memória passa para este estado, no qual aguarda ser escalonado para utilização da CPU, e consequentemente, sua execução.
    4. RUNNING: Neste estado o Job passa a ser efetivamente um processo em execução no simulador, podendo gerar eventos de comunicação com os dispositivos de entrada e saída disponíveis.
    5. WAIT_IO: Estado que representa os Jobs que estão aguardando a resposta de um pedido a um dispositivo de entrada e saída (descritos adiante), para que possa então seguir a sua execução, voltando ao estado READY e podendo ser escalonado novamente para a utilização da CPU.
    6. DONE: Estado final da simulação, representando o fim da execução e finalização de todos os pedidos de comunicação com os dispositivos I/O.  