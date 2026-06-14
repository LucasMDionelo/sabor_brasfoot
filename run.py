"""
run.py — PONTO DE ENTRADA
=========================
Só orquestra as camadas: gera os times, mostra uma partida narrada e simula a
liga. Toda a lógica vive no pacote `futebol/`. Este arquivo é fino de propósito.

Uso:
    python3 run.py
"""

import random

from futebol import config
from futebol.nomes import CIDADES
from futebol.modelos import gera_time
from futebol.partida import simula_partida
from futebol.liga import simula_liga
from futebol.evolucao import aplica_evolucao
from futebol import apresentacao as ui


def main():
    # Fontes de aleatoriedade SEPARADAS e determinísticas:
    # geração dos times, partida-demo e liga não interferem entre si.
    rng_times = random.Random(config.SEED)
    rng_demo = random.Random(config.SEED + 1)
    rng_liga = random.Random(config.SEED + 2)

    times = [gera_time(rng_times, nome) for nome in CIDADES]
    for t in times:  # variedade de atitudes (decisão tática que afeta o jogo)
        t.atitude = rng_times.choice(["RETRANCA", "EQUILIBRADO", "EQUILIBRADO", "ATAQUE_TOTAL"])

    print("\n" + "█" * 58)
    print("  TESTE 0 — NÚCLEO DE FUTEBOL (modular, sem tela)")
    print(f"  Seed: {config.SEED} | Fator-sorte: {config.FATOR_SORTE} | Times: {len(times)}")
    print("█" * 58)

    # 1) Uma partida narrada lance a lance — procura um confronto com gols
    #    (continua determinístico: mesma seed -> mesma busca -> mesmo jogo)
    print("\n>> AMOSTRA: UMA PARTIDA LANCE A LANCE")
    tentativa = None
    for _ in range(20):
        a, b = rng_demo.sample(times, 2)
        tentativa = simula_partida(a, b, rng_demo, narrar=True)
        if tentativa["gols_casa"] + tentativa["gols_fora"] >= 2:
            break
    ui.narra_partida(tentativa)
    ui.notas_partida(tentativa)

    # As partidas-demo não devem contar para a evolução da temporada:
    # zera os acumuladores antes de simular a liga "pra valer".
    for t in times:
        for j in t.elenco:
            j.pontos_evolucao = 0.0
            j.jogos_disputados = 0

    # 2) Liga inteira
    print("\n\n>> SIMULANDO A LIGA COMPLETA (turno e returno)...")
    art, disciplina, n_rodadas = simula_liga(times, rng_liga)
    print(f"   {n_rodadas} rodadas simuladas.")
    ui.tabela(times)
    ui.artilharia(art)
    ui.sanidade(times, disciplina)

    # 3) Evolução entre temporadas (idade + desempenho)
    resumo = aplica_evolucao(times)
    ui.evolucao_resumo(resumo)


if __name__ == "__main__":
    main()
