"""
evolucao.py — EVOLUÇÃO ENTRE TEMPORADAS (núcleo)
================================================
Converte o desempenho da temporada (pontos_evolucao, acumulados a partir das
notas) em ganho ou perda de atributos, modulado pela IDADE:

    jovem (<= IDADE_JOVEM)      -> evolui rápido
    auge  (meio)               -> evolui devagar
    veterano (>= IDADE_VETERANO) -> retrocede

A magnitude depende do desempenho (NÃO é aleatória): jogar bem acelera a
evolução do jovem e segura a queda do veterano; jogar mal faz o oposto.

Fórmula por jogador:
    media  = pontos_evolucao / jogos_disputados      (centrado perto de 0)
    delta  = drift(idade) + media * sensibilidade(idade)
    delta  = limitado a +/- EVO_DELTA_MAX
e o delta é aplicado a cada atributo de habilidade do jogador.
"""

from . import config as cfg


def _faixa(idade):
    if idade <= cfg.IDADE_JOVEM:
        return "jovem"
    if idade >= cfg.IDADE_VETERANO:
        return "veterano"
    return "auge"


def calcula_delta(jogador):
    """Quanto o jogador deve variar nos atributos nesta virada de temporada."""
    faixa = _faixa(jogador.idade)
    if jogador.jogos_disputados == 0:
        # sem minutos: desenvolve (ou decai) só pelo TREINO — a tendência da
        # idade, atenuada. Jovem ainda cresce no treino; jogar cresce mais.
        delta = cfg.EVO_DRIFT[faixa] * cfg.TREINO_SEM_JOGAR
    else:
        media = jogador.pontos_evolucao / jogador.jogos_disputados
        delta = cfg.EVO_DRIFT[faixa] + media * cfg.EVO_SENS[faixa]
    return max(-cfg.EVO_DELTA_MAX, min(cfg.EVO_DELTA_MAX, delta))


def aplica_evolucao(times):
    """
    Aplica a evolução a todos os jogadores, envelhece +1 ano e zera os
    acumuladores da temporada. Devolve um resumo (lista de dicts) para exibição.
    """
    resumo = []
    for t in times:
        for j in t.elenco:
            delta = calcula_delta(j)
            d_int = round(delta)
            antes = j.overall
            if d_int != 0:
                for attr in j.skills_evoluiveis():
                    novo = getattr(j, attr) + d_int
                    setattr(j, attr, max(1, min(99, novo)))
            resumo.append({
                "time": t.nome, "nome": j.nome, "pos": j.pos,
                "idade": j.idade, "faixa": _faixa(j.idade),
                "jogos": j.jogos_disputados,
                "pontos": round(j.pontos_evolucao, 1),
                "delta": d_int, "overall_antes": antes,
                "overall_depois": j.overall,
            })
            # vira a temporada: envelhece e zera os acumuladores
            j.idade += 1
            j.pontos_evolucao = 0.0
            j.jogos_disputados = 0
    return resumo
