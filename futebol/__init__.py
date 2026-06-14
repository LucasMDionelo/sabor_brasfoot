"""
futebol — núcleo de simulação de futebol (Teste 0)
==================================================
Pacote modular. Camadas:

    config        -> os "botões" de calibragem (a mágica do balanceamento)
    nomes         -> dados fictícios (jogadores e clubes)
    modelos       -> entidades Jogador e Time + geradores
    partida       -> motor de partida (gera o roteiro de eventos)   [NÚCLEO]
    liga          -> calendário e simulação de temporada            [NÚCLEO]
    apresentacao  -> renderização em texto (o Godot substitui isto)

O "núcleo" (modelos + partida + liga + config) é o que um dia roda no servidor.
A apresentação é descartável/substituível sem tocar nas regras.
"""

from . import config
from .modelos import Jogador, Time, gera_jogador, gera_time, POSICOES
from .partida import simula_partida
from .liga import gera_calendario, aplica_resultado, simula_liga
from .evolucao import aplica_evolucao, calcula_delta
from .carreira import (
    Carreira, nova_carreira, jogar_rodada, virar_temporada,
    classificacao, posicao_do_humano,
)
from . import persistencia

__all__ = [
    "config", "Jogador", "Time", "gera_jogador", "gera_time", "POSICOES",
    "simula_partida", "gera_calendario", "aplica_resultado", "simula_liga",
    "aplica_evolucao", "calcula_delta",
    "Carreira", "nova_carreira", "jogar_rodada", "virar_temporada",
    "classificacao", "posicao_do_humano", "persistencia",
]
