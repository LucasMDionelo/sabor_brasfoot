"""
apresentacao.py — CAMADA DE APRESENTAÇÃO (texto)
================================================
Transforma os dados do núcleo (eventos, tabela) em texto legível no terminal.

ESTA é a camada que, no jogo de verdade, o Godot substitui: ela só LÊ o que o
núcleo produziu e mostra. Não decide nada do jogo. Trocar este arquivo por uma
tela gráfica não mexe em uma única linha de regra.
"""

# marcador visual + se o evento deve aparecer no feed (liga/desliga aqui)
MARCAS = {
    "GOL":                ("⚽ GOL!",                  True),
    "GOLACO":             ("⚽ GOLAÇO de fora!",        True),
    "GOL_PENALTI":        ("⚽ GOL de pênalti!",        True),
    "PENALTI":            ("◎ PÊNALTI marcado!",       True),
    "PENALTI_PERDIDO":    ("✗ perdeu o pênalti!",      True),
    "PENALTI_DEFENDIDO":  ("🧤 PÊNALTI defendido!",     True),
    "CHUTE_LONGE":        ("» arrisca de longe",       True),
    "ATAQUE_PERIGOSO":    ("⚡ ataque perigoso",        True),
    "DEFESA_GOL":         ("🧤 defesa do goleiro",      True),
    "CHANCE_PERDIDA":     ("↗ finalizou pra fora",     True),
    "VERMELHO":           ("🟥 VERMELHO",              True),
    "2ºAMARELO→VERMELHO": ("🟨🟥 2º amarelo → expulso",  True),
    "AMARELO":            ("🟨 amarelo",               True),
    "FALTA":              ("• falta",                  False),
    "DESARME":            ("✓ desarme",                False),
    "IMPEDIMENTO":        ("🚩 impedimento",            True),
    "LESÃO":              ("✚ LESÃO",                  True),
    "SUBSTITUICAO":       ("⇄ substituição",           True),
}


def narra_partida(res):
    print(f"\n{'=' * 58}")
    print(f"  {res['casa']}  {res['gols_casa']} x {res['gols_fora']}  {res['fora']}")
    print(f"{'=' * 58}")
    for minuto, tipo, time, jogador in res["eventos"]:
        marca, mostra = MARCAS.get(tipo, (tipo, True))
        if mostra:
            print(f"  {minuto:>2}'  {marca:<22} {jogador} ({time})")
    print(f"  + {res['acrescimos']} min de acréscimos")


def tabela(times):
    print(f"\n{'=' * 70}")
    print("  CLASSIFICAÇÃO FINAL")
    print(f"{'=' * 70}")
    print(f"  {'#':>2} {'TIME':<18}{'P':>4}{'J':>4}{'V':>4}{'E':>4}{'D':>4}"
          f"{'GP':>4}{'GC':>4}{'SG':>5}")
    ordenados = sorted(times, key=lambda t: (t.pontos, t.saldo, t.gp), reverse=True)
    for i, t in enumerate(ordenados, 1):
        zona = "🏆" if i == 1 else ("⬇ " if i > len(times) - 2 else "  ")
        print(f"{zona}{i:>2} {t.nome:<18}{t.pontos:>4}{t.jogos:>4}"
              f"{t.vit:>4}{t.emp:>4}{t.der:>4}{t.gp:>4}{t.gc:>4}{t.saldo:>+5}")


def artilharia(art, n=8):
    print(f"\n{'=' * 40}\n  ARTILHARIA\n{'=' * 40}")
    for nome, g in sorted(art.items(), key=lambda x: -x[1])[:n]:
        print(f"  {g:>2} gols  —  {nome}")


def sanidade(times, disciplina):
    total_gols = sum(t.gp for t in times)
    n_jogos = sum(t.jogos for t in times) // 2
    print(f"\n{'=' * 40}\n  SANIDADE DA CALIBRAGEM\n{'=' * 40}")
    print(f"  Jogos:            {n_jogos}")
    print(f"  Gols totais:      {total_gols}")
    print(f"  Média gols/jogo:  {total_gols / n_jogos:.2f}   (alvo realista: 2.4–3.0)")
    print(f"  Amarelos:         {disciplina['AMARELO']}")
    print(f"  Vermelhos:        {disciplina['VERMELHO']}")
    print("\n  >> Gire os botões em futebol/config.py e rode de novo")
    print("     para ajustar o 'sabor' do jogo.\n")


def notas_partida(res):
    """Mostra as notas de desempenho dos dois times na partida."""
    print(f"\n  NOTAS DE DESEMPENHO")
    print(f"  {'-' * 40}")
    for time_nome in (res["casa"], res["fora"]):
        jogadores = sorted(
            [(j, n) for j, n, t in res["notas"] if t == time_nome],
            key=lambda x: -x[1],
        )
        print(f"  {time_nome}:")
        for jog, nota in jogadores:
            destaque = " ★" if nota >= 8.0 else ("  ✗" if nota <= 5.0 else "")
            print(f"    {nota:>4.1f}  {jog.pos:<3} {jog.nome}{destaque}")


def evolucao_resumo(resumo, n=6):
    """Mostra as maiores subidas e quedas de atributo da temporada."""
    jogou = [r for r in resumo if r["jogos"] > 0]
    subidas = sorted(jogou, key=lambda r: -r["delta"])[:n]
    quedas = sorted(jogou, key=lambda r: r["delta"])[:n]

    print(f"\n{'=' * 56}\n  EVOLUÇÃO DA TEMPORADA (idade + desempenho)\n{'=' * 56}")
    print("  MAIORES SUBIDAS (jovens em alta):")
    for r in subidas:
        print(f"    {r['overall_antes']:>2}→{r['overall_depois']:<2} "
              f"({r['delta']:+d})  {r['nome']} ({r['pos']}, {r['idade']}a, "
              f"{r['faixa']}, nota méd. {_media(r)})")
    print("  MAIORES QUEDAS (veteranos em baixa):")
    for r in quedas:
        print(f"    {r['overall_antes']:>2}→{r['overall_depois']:<2} "
              f"({r['delta']:+d})  {r['nome']} ({r['pos']}, {r['idade']}a, "
              f"{r['faixa']}, nota méd. {_media(r)})")


def _media(r):
    if r["jogos"] == 0:
        return "—"
    # pontos = soma de (nota - neutra); nota média ≈ neutra + pontos/jogos
    from . import config as cfg
    return f"{cfg.NOTA_NEUTRA_EVOLUCAO + r['pontos'] / r['jogos']:.1f}"
