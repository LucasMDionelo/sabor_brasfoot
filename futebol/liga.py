"""
liga.py — COMPETIÇÃO (núcleo)
=============================
Monta o calendário (turno e returno), aplica resultados na tabela e simula a
temporada inteira. Continua sendo puro núcleo — não imprime nada.

Dependências: `partida` (para simular cada jogo).
"""

from . import config as cfg
from .partida import simula_partida


def gera_calendario(times):
    """Round-robin simples (ida e volta) pelo método do círculo."""
    lst = list(times)
    if len(lst) % 2:
        lst.append(None)  # bye para número ímpar de times
    m = len(lst)
    rodadas_ida = []
    for r in range(m - 1):
        jogos = []
        for i in range(m // 2):
            a, b = lst[i], lst[m - 1 - i]
            if a and b:
                jogos.append((a, b) if r % 2 == 0 else (b, a))
        rodadas_ida.append(jogos)
        lst.insert(1, lst.pop())  # rotaciona, fixando o primeiro
    rodadas_volta = [[(b, a) for (a, b) in rodada] for rodada in rodadas_ida]
    return rodadas_ida + rodadas_volta


def aplica_resultado(casa, fora, res):
    """Atualiza pontos, vitórias/empates/derrotas e gols dos dois times."""
    gc, gf = res["gols_casa"], res["gols_fora"]
    casa.gp += gc; casa.gc += gf
    fora.gp += gf; fora.gc += gc
    if gc > gf:
        casa.pontos += 3; casa.vit += 1; fora.der += 1
    elif gf > gc:
        fora.pontos += 3; fora.vit += 1; casa.der += 1
    else:
        casa.pontos += 1; fora.pontos += 1
        casa.emp += 1; fora.emp += 1


def simula_liga(times, rng):
    """Simula a temporada inteira. Devolve artilharia, disciplina e nº de rodadas."""
    calendario = gera_calendario(times)
    artilharia = {}
    disciplina = {"AMARELO": 0, "VERMELHO": 0}
    for rodada in calendario:
        for casa, fora in rodada:
            res = simula_partida(casa, fora, rng, narrar=False)
            aplica_resultado(casa, fora, res)
            for nome, g in res["artilheiros"].items():
                artilharia[nome] = artilharia.get(nome, 0) + g
            for _, tipo in res["cartoes"]:
                chave = "VERMELHO" if "VERMELHO" in tipo else "AMARELO"
                disciplina[chave] += 1
            # pontos de evolução = desempenho (nota) acima/abaixo da neutra
            for jog, nota, _ in res["notas"]:
                jog.pontos_evolucao += (nota - cfg.NOTA_NEUTRA_EVOLUCAO)
                jog.jogos_disputados += 1
    return artilharia, disciplina, len(calendario)
