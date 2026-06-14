"""
carreira.py — LOOP DO MANAGER (núcleo)
======================================
Estado de uma carreira (um humano comanda UM clube) e a progressão rodada a
rodada. Reaproveita partida/liga/evolucao; não imprime nada nem lê teclado —
isso é responsabilidade de jogar.py (a interação) e apresentacao.py (o texto).

Decisões do manager por rodada:
- ATITUDE do time (retranca / equilibrado / ataque total)
- ESCALAÇÃO (melhor XI p/ vencer  x  XI jovem p/ desenvolver  x  manual)
A escalação importa duplamente: muda o resultado E quem joga evolui.
"""

import random
from dataclasses import dataclass, field

from . import config as cfg
from .nomes import CIDADES
from .modelos import gera_time
from .partida import simula_partida
from .liga import gera_calendario, aplica_resultado
from .evolucao import aplica_evolucao
from . import regen


@dataclass
class Carreira:
    times: list
    calendario: list            # lista de rodadas; cada rodada = [(TimeCasa, TimeFora)]
    clube_humano: int           # índice do clube do jogador em `times`
    rng: random.Random
    temporada: int = 1
    rodada_idx: int = 0
    artilharia: dict = field(default_factory=dict)
    disciplina: dict = field(default_factory=lambda: {"AMARELO": 0, "VERMELHO": 0})

    # ----- acessos de conveniência -----
    @property
    def clube(self):
        return self.times[self.clube_humano]

    @property
    def n_rodadas(self):
        return len(self.calendario)

    def temporada_acabou(self):
        return self.rodada_idx >= len(self.calendario)

    def confronto_do_humano(self):
        """Devolve (adversario, em_casa) da rodada atual, ou None se já acabou."""
        if self.temporada_acabou():
            return None
        eu = self.clube
        for casa, fora in self.calendario[self.rodada_idx]:
            if casa is eu:
                return (fora, True)
            if fora is eu:
                return (casa, False)
        return None


# ---------------------------------------------------------------------
# Criação e progressão
# ---------------------------------------------------------------------
def nova_carreira(clube_humano: int, seed: int = None) -> Carreira:
    rng = random.Random(seed) if seed is not None else random.Random()
    times = [gera_time(rng, nome) for nome in CIDADES]
    # atitude inicial: clubes da CPU variam; o humano começa equilibrado
    for i, t in enumerate(times):
        if i != clube_humano:
            t.atitude = rng.choice(["RETRANCA", "EQUILIBRADO", "EQUILIBRADO", "ATAQUE_TOTAL"])
    calendario = gera_calendario(times)
    return Carreira(times=times, calendario=calendario,
                    clube_humano=clube_humano, rng=rng)


def _acumula(c: Carreira, res: dict):
    """Soma artilharia, disciplina e pontos de evolução de uma partida."""
    for nome, g in res["artilheiros"].items():
        c.artilharia[nome] = c.artilharia.get(nome, 0) + g
    for _, tipo in res["cartoes"]:
        chave = "VERMELHO" if "VERMELHO" in tipo else "AMARELO"
        c.disciplina[chave] += 1
    for jog, nota, _ in res["notas"]:
        jog.pontos_evolucao += (nota - cfg.NOTA_NEUTRA_EVOLUCAO)
        jog.jogos_disputados += 1


def jogar_rodada(c: Carreira, xi_humano=None):
    """
    Simula a rodada atual. O jogo do humano é narrado (com xi_humano, se dado);
    os demais rodam no automático. Devolve o resultado do jogo do humano (ou None).
    Avança a rodada.
    """
    if c.temporada_acabou():
        return None
    eu = c.clube
    eu.escalacao_manual = xi_humano   # None => a 'IA' escala os melhores

    res_humano = None
    for casa, fora in c.calendario[c.rodada_idx]:
        humano_joga = (casa is eu or fora is eu)
        res = simula_partida(casa, fora, c.rng, narrar=humano_joga)
        aplica_resultado(casa, fora, res)
        _acumula(c, res)
        if humano_joga:
            res_humano = res

    eu.escalacao_manual = None        # limpa: o humano re-escala a cada rodada
    c.rodada_idx += 1
    return res_humano


def virar_temporada(c: Carreira):
    """Aplica evolução, envelhece o elenco, processa aposentadoria + base,
    zera a tabela e remonta o calendário. Devolve {'evolucao':..., 'regen':...}."""
    resumo = aplica_evolucao(c.times)        # evolui e envelhece +1 ano
    regen_info = regen.processa_liga(c.times, c.rng)  # aposenta e repõe da base
    c.temporada += 1
    c.rodada_idx = 0
    c.artilharia = {}
    c.disciplina = {"AMARELO": 0, "VERMELHO": 0}
    for t in c.times:
        t.pontos = t.vit = t.emp = t.der = t.gp = t.gc = 0
    c.calendario = gera_calendario(c.times)
    return {"evolucao": resumo, "regen": regen_info}


# ---------------------------------------------------------------------
# Classificação
# ---------------------------------------------------------------------
def classificacao(c: Carreira):
    return sorted(c.times, key=lambda t: (t.pontos, t.saldo, t.gp), reverse=True)


def posicao_do_humano(c: Carreira):
    return classificacao(c).index(c.clube) + 1
