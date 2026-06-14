"""
jogar.py — INTERAÇÃO (texto)
============================
O loop jogável: você comanda UM clube, define tática e escalação a cada rodada,
assiste ao jogo e vê seu elenco evoluir entre temporadas. Pode salvar e continuar.

Esta é a camada de INTERAÇÃO temporária — é ela (e a apresentação) que o Godot
vai substituir. Toda a regra vive no pacote `futebol/`. Aqui só há menus.

Uso:
    python3 jogar.py
"""

import os

from futebol.nomes import CIDADES
from futebol.modelos import FORMACOES, penalidade_posicao, gravidade
from futebol import carreira as C
from futebol import persistencia as P
from futebol import apresentacao as ui

SAVE = "save.json"
ATITUDES = {"1": "RETRANCA", "2": "EQUILIBRADO", "3": "ATAQUE_TOTAL"}


def ler(prompt=""):
    try:
        return input(prompt).strip()
    except EOFError:
        print("\n[entrada encerrada — até a próxima]")
        raise SystemExit


# ---------------------------------------------------------------------
# Menu inicial
# ---------------------------------------------------------------------
def main():
    print("\n" + "█" * 50)
    print("  MANAGER DE FUTEBOL — carreira (texto)")
    print("█" * 50)
    while True:
        print("\n  [1] Nova carreira")
        print("  [2] Carregar carreira" + ("" if os.path.exists(SAVE) else "  (nenhum save)"))
        print("  [3] Sair")
        op = ler("  > ")
        if op == "1":
            jogar_carreira(criar_nova())
        elif op == "2":
            if os.path.exists(SAVE):
                print("  Carregando...")
                jogar_carreira(P.carregar(SAVE))
            else:
                print("  Nenhum save encontrado.")
        elif op == "3":
            print("  Até mais!")
            return


def criar_nova():
    print("\n  Escolha seu clube:")
    for i, nome in enumerate(CIDADES):
        print(f"   [{i+1:>2}] {nome}")
    while True:
        op = ler("  Clube nº > ")
        if op.isdigit() and 1 <= int(op) <= len(CIDADES):
            idx = int(op) - 1
            break
        print("  Número inválido.")
    c = C.nova_carreira(clube_humano=idx)
    print(f"\n  Você assumiu o {c.clube.nome}! Boa sorte, treinador.")
    return c


# ---------------------------------------------------------------------
# Loop da carreira
# ---------------------------------------------------------------------
def jogar_carreira(c):
    while True:
        if c.temporada_acabou():
            fim_de_temporada(c)
            continue

        eu = c.clube
        adv, em_casa = c.confronto_do_humano()
        print("\n" + "─" * 50)
        print(f"  Temporada {c.temporada} · Rodada {c.rodada_idx + 1}/{c.n_rodadas}"
              f"  ·  {c.clube.nome} ({C.posicao_do_humano(c)}º, {eu.pontos} pts)")
        local = "EM CASA vs" if em_casa else "FORA contra"
        print(f"  Próximo jogo: {local} {adv.nome}  (força ~{_forca(adv)})")
        print("\n  [1] Escalar e jogar   [2] Tabela   [3] Elenco   [4] Salvar   [5] Salvar e sair")
        op = ler("  > ")
        if op == "1":
            escalar_e_jogar(c)
        elif op == "2":
            ui.tabela(c.times)
        elif op == "3":
            mostra_elenco(eu)
        elif op == "4":
            P.salvar(c, SAVE); print(f"  Salvo em {SAVE}.")
        elif op == "5":
            P.salvar(c, SAVE); print(f"  Salvo em {SAVE}. Voltando ao menu.")
            return


def escolhe_formacao(eu):
    nomes = list(FORMACOES)
    print("\n  Formação:")
    for i, n in enumerate(nomes, 1):
        atual = "  (atual)" if n == eu.formacao else ""
        print(f"   [{i}] {n}{atual}")
    op = ler("  > ")
    if op.isdigit() and 1 <= int(op) <= len(nomes):
        eu.formacao = nomes[int(op) - 1]
    return eu.formacao


def mostra_escalacao(eu, xi):
    """Lista as vagas da formação e marca quem está fora de posição."""
    slots = FORMACOES[eu.formacao]
    print(f"\n  {eu.formacao} — vaga → jogador:")
    foras = 0
    for i, (slot, j) in enumerate(zip(slots, xi), 1):
        if slot == j.pos:
            flag = ""
        else:
            foras += 1
            f = penalidade_posicao(slot, j.pos)
            flag = f"   ⚠ {j.pos} fora de posição [{gravidade(f)}, -{round((1-f)*100)}%]"
        print(f"   [{i:>2}] {slot:<3} {j.nome:<20} ov {j.overall:<3} {j.idade}a{flag}")
    if foras:
        print(f"  ⚠ {foras} fora de posição — rendem menos. Troque por alguém da posição.")
    else:
        print("  ✓ todos na posição certa.")
    return foras


def editar_manual(eu, xi):
    """Troca jogadores entre as vagas (1–11) e o banco, vendo o fora de posição."""
    slots = FORMACOES[eu.formacao]
    while True:
        mostra_escalacao(eu, xi)
        banco = [j for j in eu.elenco if j not in xi and not j.lesionado and not j.expulso]
        print("  RESERVAS:")
        for i, j in enumerate(banco, 12):
            print(f"   [{i:>2}] {j.pos:<3} {j.nome:<20} ov {j.overall:<3} {j.idade}a")
        cmd = ler("  Trocar 'vaga reserva' (ex: 2 14), 'vaga vaga' p/ inverter, ou ENTER > ")
        if cmd == "":
            return xi
        p = cmd.split()
        if len(p) == 2 and all(x.isdigit() for x in p):
            a, b = int(p[0]), int(p[1])
            if 1 <= a <= 11 and 12 <= b < 12 + len(banco):       # vaga ↔ reserva
                entra = banco[b - 12]; sai = xi[a - 1]; xi[a - 1] = entra
                print(f"  vaga {a} ({slots[a-1]}): ↓ {sai.nome}  ↑ {entra.nome}")
                continue
            if 1 <= a <= 11 and 1 <= b <= 11:                    # inverte duas vagas
                xi[a - 1], xi[b - 1] = xi[b - 1], xi[a - 1]
                print(f"  inverteu as vagas {a} e {b}")
                continue
        print("  Comando inválido.")


def escalar_e_jogar(c):
    eu = c.clube
    # 1) atitude
    print("\n  Atitude do time:  [1] Retranca   [2] Equilibrado   [3] Ataque total")
    eu.atitude = ATITUDES.get(ler("  > "), "EQUILIBRADO")

    # 2) formação
    escolhe_formacao(eu)

    # 3) montagem do XI (já alinhado às vagas da formação)
    print("\n  Montar XI:")
    print("   [1] Melhor XI (vencer agora)")
    print("   [2] XI jovem (desenvolver o elenco)")
    print("   [3] Editar manualmente")
    op = ler("  > ")
    xi = eu.escalacao_jovens() if op == "2" else eu.escalacao_por_overall()
    if op == "3":
        xi = editar_manual(eu, xi)
    else:
        mostra_escalacao(eu, xi)

    ov = sum(j.overall for j in xi) / len(xi)
    idade = sum(j.idade for j in xi) / len(xi)
    print(f"\n  XI escalado ({eu.formacao}): overall médio {ov:.0f}, idade média {idade:.1f}")

    # 4) joga a rodada
    res = C.jogar_rodada(c, xi_humano=xi)
    if res:
        ui.narra_partida(res)
        ui.notas_partida(res)
    # 5) mini-tabela
    print("\n  CLASSIFICAÇÃO (topo):")
    tab = C.classificacao(c)
    for i, t in enumerate(tab[:5], 1):
        marca = " ←você" if t is eu else ""
        print(f"   {i:>2}. {t.nome:<16} {t.pontos:>3} pts  (SG {t.saldo:+d}){marca}")
    if eu not in tab[:5]:
        p = C.posicao_do_humano(c)
        print(f"   ...\n   {p:>2}. {eu.nome:<16} {eu.pontos:>3} pts  ←você")


# ---------------------------------------------------------------------
# Fim de temporada
# ---------------------------------------------------------------------
def fim_de_temporada(c):
    eu = c.clube
    pos = C.posicao_do_humano(c)
    print("\n" + "═" * 50)
    print(f"  FIM DA TEMPORADA {c.temporada}")
    print("═" * 50)
    ui.tabela(c.times)
    ui.artilharia(c.artilharia)
    troféu = "🏆 CAMPEÃO!" if pos == 1 else f"{pos}º lugar"
    print(f"\n  >> {eu.nome}: {troféu} ({eu.pontos} pts)")

    info = C.virar_temporada(c)
    resumo = info["evolucao"]
    regen = info["regen"]
    meu = [r for r in resumo if r["time"] == eu.nome and r["jogos"] > 0]
    sobe = sorted(meu, key=lambda r: -r["delta"])[:4]
    cai = sorted(meu, key=lambda r: r["delta"])[:4]
    print(f"\n  EVOLUÇÃO DO SEU ELENCO (entrando na temporada {c.temporada}):")
    for r in sobe + cai:
        if r["delta"] != 0:
            print(f"   {r['overall_antes']:>2}→{r['overall_depois']:<2} ({r['delta']:+d})  "
                  f"{r['nome']} ({r['pos']}, {r['idade']}a, {r['faixa']})")

    meu_regen = regen.get(eu.nome, {"aposentados": [], "novatos": []})
    if meu_regen["aposentados"]:
        print("\n  SE APOSENTARAM:")
        for j in meu_regen["aposentados"]:
            print(f"   {j.pos:<3} {j.nome} ({j.idade}a, ov {j.overall})")
    if meu_regen["novatos"]:
        print("\n  SUBIRAM DA BASE:")
        for j in meu_regen["novatos"]:
            print(f"   {j.pos:<3} {j.nome} ({j.idade}a, ov {j.overall})  ✦ promessa")
    ler("\n  ENTER para começar a próxima temporada...")


def mostra_elenco(t):
    print(f"\n  ELENCO — {t.nome}")
    for j in sorted(t.elenco, key=lambda x: (-x.overall)):
        print(f"   {j.pos:<3} {j.nome:<22} ov {j.overall:<3} {j.idade}a "
              f"mor {j.moral} res {j.resistencia}")


def _forca(t):
    xi = t.escalacao_por_overall()
    return round(sum(j.overall for j in xi) / len(xi))


if __name__ == "__main__":
    main()
