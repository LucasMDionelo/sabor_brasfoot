"""
regen.py — APOSENTADORIA + REGENERAÇÃO DE BASE (núcleo)
======================================================
Fecha o ciclo de vida do jogador, garantindo que o elenco seja uma população
que se renova (e não um grupo fechado que só envelhece):

- APOSENTADORIA: a cada virada de temporada, cada jogador pode se aposentar.
  A chance é 0 antes de IDADE_APOSENTA_MIN (32), ~baixa nesse mínimo, e sobe
  linearmente até 100% em IDADE_APOSENTA_MAX (51).

- REGENERAÇÃO: para CADA aposentado entra UM garoto novo da base, NA MESMA
  POSIÇÃO. Assim o tamanho do elenco e o equilíbrio posicional ficam estáveis.
  O prospecto entra jovem (17-19) e fraco (abaixo da média do clube), com muito
  espaço para crescer pelo sistema de evolução — se ganhar minutos em campo.

Roda dentro de carreira.virar_temporada(), depois da evolução (que já envelhece
os jogadores em +1 ano).
"""

from . import config as cfg
from .modelos import gera_jogador


def prob_aposentadoria(idade: int) -> float:
    """0 antes do mínimo; sobe linearmente até 1.0 no máximo."""
    if idade < cfg.IDADE_APOSENTA_MIN:
        return 0.0
    span = cfg.IDADE_APOSENTA_MAX - (cfg.IDADE_APOSENTA_MIN - 1)
    return min(1.0, (idade - (cfg.IDADE_APOSENTA_MIN - 1)) / span)


def _nivel_clube(time) -> float:
    """Reputação da base: nível histórico do clube (âncora estável, não decai)."""
    return getattr(time, "nivel_base", None) or (
        sum(j.overall for j in time.elenco) / len(time.elenco)
        if time.elenco else cfg.YOUTH_OVERALL_MIN
    )


def aposenta_e_repoe(time, rng):
    """Aposenta quem 'sorteou' e repõe com garotos na mesma posição.
    Devolve (aposentados, novatos). O tamanho do elenco não muda."""
    aposentados = [j for j in time.elenco
                   if rng.random() < prob_aposentadoria(j.idade)]
    if not aposentados:
        return [], []

    nivel = _nivel_clube(time)            # nível ANTES de mexer no elenco
    base_jovem = max(cfg.YOUTH_OVERALL_MIN, round(nivel) - cfg.YOUTH_OVERALL_OFFSET)

    novatos = [
        gera_jogador(rng, velho.pos, base_jovem,
                     cfg.YOUTH_IDADE_MIN, cfg.YOUTH_IDADE_MAX)
        for velho in aposentados
    ]

    for velho in aposentados:
        time.elenco.remove(velho)
    time.elenco.extend(novatos)
    time.escalacao_manual = None          # segurança: não referenciar quem saiu
    return aposentados, novatos


def processa_liga(times, rng):
    """Aplica aposentadoria + regeneração em todos os clubes.
    Devolve {nome_do_time: {'aposentados': [...], 'novatos': [...]}}."""
    info = {}
    for t in times:
        ap, nov = aposenta_e_repoe(t, rng)
        info[t.nome] = {"aposentados": ap, "novatos": nov}
    return info
