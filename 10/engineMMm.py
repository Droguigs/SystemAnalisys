import numpy as np
import scipy.stats as st
from math import factorial
from math import exp

class engineMMm:
    def calculaP0(self):
        temp = 1 + ((self.m * self.ro) ** self.m) / (factorial(self.m) * (1 - self.ro))
        for k in range(1, self.m):
            temp = temp + (((self.m * self.ro) ** k) / factorial(k))
        return 1 / temp


    def __init__(self, lb, mu, m):
        if (lb >= m*mu):
            raise ValueError('Lambda deve ser menor do que m*mu')
        self.lb = float(lb)
        self.mu = float(mu)
        self.m = m
        self.limite_fila = 1000
        self.ro = lb / (m*mu)
        self.p0 = self.calculaP0()
        self.epsilon = ((self.m*self.ro)**self.m)/((1-self.ro)*factorial(self.m))*self.p0
        # valor esperado de Ns (quantidade media de tarefas servidas)
        self.E_Ns = self.m * self.ro
        # valor esperado de Nq (tamanho medio da fila)
        self.E_Nq = (self.epsilon * self.ro) / (1 - self.ro)
        # valor esperado de N 9quentidade media de tarefas no sistema)
        self.E_N = self.E_Nq + self.E_Ns
        # valor esperado de S (tempo de serviço médio)
        self.E_S = 1 / self.mu
        # valor esperado de W (tempo de espera medio na fila)
        self.E_W = self.epsilon / (self.m * self.mu * (1 - self.ro))
        # valor esperado de R (tempo de resposta medio)
        self.E_R = self.E_S + self.E_W

        # variáveis do engine
        self.tempo_medio_entre_chegadas = 1 / self.lb
        self.tempo_de_servico_medio = 1 / self.mu
        self.tempo = st.expon.rvs(0, self.tempo_medio_entre_chegadas,size=1)
        self.Agenda = np.ones((1,self.m+1))*exp(30)
        self.Agenda[0, m] = self.tempo
        self.perda = 0
        self.tamanho_da_fila = 0
        self.estado_servidor = np.zeros((1, self.m))  # todos livres
        self.tamanho_da_fila = 0
        self.tempo_do_ultimo_evento = 0.0
        self.tempo_total_de_espera = 0.0
        self.total_de_tempo_de_servico = 0.0
        self.tempo_de_chegada_na_fila = np.zeros(100*self.limite_fila)
        self.tamanho_fila_x_tempo = 0.0
        self.estado_do_sistema = 0
        self.estado_sistema_x_tempo = 0.0
        self.numero_de_eventos = 1
        self.servidor = float(0)

    def proximo_evento(self):
        return (self.Agenda == self.Agenda.min(1, keepdims=True)).argmax(1)

    def simula(self, nsim):
        while (self.numero_de_eventos < nsim):
            indice_proximo_evento = (self.Agenda == self.Agenda.min(1, keepdims=True)).argmax(1)[0]
            # Determina tipo do próximo evento(chegada ou saída)
            if (indice_proximo_evento == self.m):
                tipo_proximo_evento = 1 # chegada
            else:
                tipo_proximo_evento = 0 # saída
                self.servidor = indice_proximo_evento
            # Recupera o tempo do próximo evento
            self.tempo = self.Agenda[0, indice_proximo_evento]

            #Atualiza os acumuladores estatisticos
            self.atualiza()

            # Processa o próximo evento de acordo com o tipo
            if (tipo_proximo_evento == 1):
                self.chegada() # Chama rotina de chegada
            else:
                self.saida() # Chama rotina de saida

        self.estatisticas(nsim)

    def atualiza(self):
        # print('**** atualiza')
        # Calcula intervalo decorrido desde ultimo evento
        # Na primeira chamada tempo_do_ultimo_evento é igual a 0
        # Variável tempo_do_ultimo_evento é atualizada aqui
        intervalo_do_ultimo_evento = self.tempo - self.tempo_do_ultimo_evento
        self.tempo_do_ultimo_evento = self.tempo

        # Acumula quantidade de elementos na fila multiplicado
        # pelo tempo decorrido desde o ultimo evento

        # A divisão da variável tamanho_fila_x_tempo pela variável tempo
        # vai fornecer o tamanho médio da fila

        # A variável tamanho_da_fila é atualizada em chegada e saida
        self.tamanho_fila_x_tempo = \
            self.tamanho_fila_x_tempo + \
            self.tamanho_da_fila * intervalo_do_ultimo_evento

        # Acumula estado do servidor multiplicado
        # pelo tempo decorrido desde o ultimo evento
        # A divisão da variável estado_servidor_x_tempo pela variável tempo
        # vai fornecer a utlização do servidor
        # A variável estado_do_servidor é atualizada em chegada e saida
        self.estado_sistema_x_tempo = \
            self.estado_sistema_x_tempo + \
            self.estado_do_sistema * intervalo_do_ultimo_evento

    def chegada(self):
        #print('**** chegada')
        #print(self.Agenda)
        #print('estado_servidor')
        #print(self.estado_servidor)
        quantidade_servindo = np.sum(self.estado_servidor)
        #print('quantidade_servindo')
        #print(quantidade_servindo)

        if (quantidade_servindo < self.m):
            self.servidor = \
                (self.estado_servidor == self.estado_servidor.min(1, keepdims=True)).argmax(1)
            self.estado_servidor[0,self.servidor] = 1 # Servidor ocupado
            #print('estado_servidor')
            #print(self.estado_servidor)
            self.estado_do_sistema = 1 # Sistema ocupado
            #print('estado_do_sistema')
            #print(self.estado_do_sistema)

            # Agenda a saida da tarefa que está no servidor
            tempo_de_servico = st.expon.rvs(0, self.tempo_de_servico_medio,size=1)
            self.Agenda[0,self.servidor] = self.tempo + tempo_de_servico
            #print(self.Agenda)
            self.total_de_tempo_de_servico = \
            self.total_de_tempo_de_servico + tempo_de_servico

        else: # Todos servidores ocupados
            # Incrementa numero de eventos na fila
            self.tamanho_da_fila = self.tamanho_da_fila + 1
            #print('tamanho_da_fila')
            #print(self.tamanho_da_fila)

            # Salva tempo de chegada da tarefa que foi colocada na fila
            #print('tempo_de_chegada_na_fila')
            #print(self.tempo_de_chegada_na_fila)
            self.tempo_de_chegada_na_fila[self.tamanho_da_fila-1] = self.tempo
            #print('tempo_de_chegada_na_fila')
            #print(self.tempo_de_chegada_na_fila)

            # Testa se houve estouro na fila e registra perda
            if (self.tamanho_da_fila > self.limite_fila):
                self.perda = self.perda + 1
                raise Exception('Estouro na fila')

        # Agenda a proxima chegada
        self.Agenda[0,self.m] = \
            self.tempo + st.expon.rvs(0, self.tempo_medio_entre_chegadas,size=1)
        #print(self.Agenda)

        # Incrementa quantidade de eventos que passaram pelo sistema
        # É usado para calcular o tempo médio na fila
        #print('@@@@@@@@@@@@@@@@@@@')
        self.numero_de_eventos = self.numero_de_eventos + 1


    def saida(self):
        #print('**** saida')
        #print(self.Agenda)
        #print('tamanho_da_fila')
        #print(self.tamanho_da_fila)
        if (self.tamanho_da_fila == 0): # Fila vazia
            # Marca o servidor como disponivel
            self.estado_servidor[0,self.servidor] = 0
            #print('estado_servidor')
            #print(self.estado_servidor)
            # Tratamento do proximo evento de fim de servico (muito grande)
            self.Agenda[0,self.servidor] = exp(30)
            # Atualiza quantidade servindo
            self.quantidade_servindo = np.sum(self.estado_servidor)
            if (self.quantidade_servindo == 0):
                self.estado_do_sistema = 0 # ocioso

        else: # Fila nao vazia
            # Acumula informcoes da tarefa que saiu da fila
            # e foi para o servidor
            # Serão usadas para calcular o tempo médio na fila
            # Tempo de espera na fila da tarefa que vai ser atendida
            #print('tempo')
            #print(self.tempo)
            #print('tempo_de_chegada_na_fila')
            #print(self.tempo_de_chegada_na_fila)
            espera = self.tempo - self.tempo_de_chegada_na_fila[0]
            # Acumula tempo de espera na fila
            self.tempo_total_de_espera = self.tempo_total_de_espera + espera
            #print('espera')
            #print(espera)

            # Retira a primeira tarefa da fila
            self.tempo_de_chegada_na_fila = \
                np.delete(self.tempo_de_chegada_na_fila,[0])
            #print('tempo_de_chegada_na_fila')
            #print(self.tempo_de_chegada_na_fila)
            # Decrementa quantidade de tarefas na fila
            self.tamanho_da_fila = self.tamanho_da_fila - 1
            #print('tamanho_da_fila')
            #print(self.tamanho_da_fila)

            # Programa o proximo evento de fim de servico
            tempo_de_servico = st.expon.rvs(0, self.tempo_de_servico_medio,size=1)
            self.Agenda[0,self.servidor] = self.tempo + tempo_de_servico
            self.total_de_tempo_de_servico =\
                self.total_de_tempo_de_servico + tempo_de_servico

        #print(self.Agenda)
        #print('&&&&&&&&&&&&&')


    def estatisticas(self, nsim):
        print('--------------------------------------------------------------')
        print('Numero de eventos                               : '
              '{:.0f}'.format(self.numero_de_eventos))
        print('Lambda                                          : '
              '{:.4f}'.format(self.lb))
        print('Mu                                              : '
              '{:.4f}'.format(self.mu))
        print('Numero de servidores                            : '
              '{:.4f}'.format(self.m))
        print('Ro                                              : '
              '{:.4f}'.format(self.ro))
        print('Epsilon                                         : '
              '{:.4f}'.format(self.epsilon))
        print('P0                                              : '
              '{:.4f}'.format(self.p0))
        print('Taxa de perda                                   : '
              '{:.4f}'.format(self.perda / self.numero_de_eventos))
        print('--------------------------------------------------------------\n')\

        # Cálculo das estatisticas da simulação
        tempo_medio_na_fila_simulado = self.tempo_total_de_espera / self.numero_de_eventos
        tamanho_medio_da_fila_simulado = self.tamanho_fila_x_tempo / self.tempo
        tempo_medio_de_servico_simulado = \
            self.total_de_tempo_de_servico[0] / self.numero_de_eventos
        tempo_medio_de_resposta_simulado = \
            tempo_medio_na_fila_simulado + tempo_medio_de_servico_simulado
        taxa_de_utilizacao_sistema = self.estado_sistema_x_tempo / self.tempo

        # Reporta as estatisticas da simulacao
        print('Tempo medio na fila (simulado)                  : '
              '{:.4f}'.format(tempo_medio_na_fila_simulado))
        print('Numero medio de elementos na fila (simulado)    : '
              '{:.4f}'.format(tamanho_medio_da_fila_simulado))
        print('Tempo medio de servico (simulado)               : '
              '{:.4f}'.format(tempo_medio_de_servico_simulado))
        print('Numero medio de elementos servidos (simulado)   : '
                '{:.4f}'.format(self.lb *tempo_medio_de_servico_simulado))
        print('Tempo medio de resposta (simulado)              : '
              '{:.4f}'.format(tempo_medio_de_resposta_simulado))
        print('Numero medio de elemento no sistema (simulado)  : '
              '{:.4f}'.format(self.lb*tempo_medio_de_resposta_simulado))
        print('Taxa de utilizacao do sistema (simulado)        : '
              '{:.4f}'.format(taxa_de_utilizacao_sistema))
        print('--------------------------------------------------------------\n')

        #Calcula os parametros pelas formulas analiticas
        # Tempo medio na fila
        tempo_medio_na_fila_analitico = self.epsilon / (self.m * self.mu * (1 - self.ro))
        # Tamanho medio da fila
        tamanho_medio_da_fila_analitico = (self.ro * self.epsilon) / (1 - self.ro)
        # Tempo médio de resposta
        tempo_medio_de_resposta_analitico = (1 / self.mu) + tempo_medio_na_fila_analitico

        # Reporta os valores analíticos
        print('Tempo medio na fila (analítico)                 : '
              '{:.4f}'.format(tempo_medio_na_fila_analitico))
        print('Numero medio de elementos na fila (analitico)   : '
              '{:.4f}'.format(tamanho_medio_da_fila_analitico))
        print('Tempo medio de servico (analítico)              : '
              '{:.4f}'.format(self.tempo_de_servico_medio))
        print('Numero medio de elementos servidos (analitico)  : '
              '{:.4f}'.format(self.lb*self.tempo_de_servico_medio))
        print('Tempo medio de resposta (analítico)             : '
              '{:.4f}'.format(tempo_medio_de_resposta_analitico))
        print('Numero medio de elemento no sistema (analitico) : '
              '{:.4f}'.format(self.lb*tempo_medio_de_resposta_analitico))
        print('Taxa de utilização do sistema (analítico)       : '
              '{:.4f}'.format(1 - self.p0))
        print('--------------------------------------------------------------\n')
