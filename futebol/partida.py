"""
partida.py — MOTOR DE PARTIDA (núcleo)
======================================
Simula uma partida lance a lance e devolve um "roteiro de eventos" (lista de
tuplas: minuto, tipo, time, jogador) e as NOTAS DE DESEMPENHO de cada jogador.

Filosofia: RESULTADO PRIMEIRO. Os duelos são decididos por ATRIBUTOS + SORTE
calibrada — o placar é decretado aqui, não emerge de física. Mesma seed +
mesmas escalações = exatamente o mesmo jogo (determinismo).

As NOTAS são lidas dos eventos do jogo (gols, defesas, cartões, etc.) e NÃO
realimentam a simulação: por isso não alteram o resultado nem a calibragem.

Nenhuma linha deste arquivo sabe desenhar nada. É puro núcleo.
"""

import random
from collections import defaultdict

from .modelos import Time, aplica_posicoes, penalidade_posicao
from . import config as cfg


# ---------------------------------------------------------------------
# Estado da partida: carrega tudo que os resolvedores precisam compartilhar.
# Concentra eventos, placar, artilheiros, cartões e os ajustes de nota.
# ---------------------------------------------------------------------
class _Estado:
    def __init__(self, time_casa, time_fora, narrar):
        self.casa_nome = time_casa.nome
        self.fora_nome = time_fora.nome
        self.narrar = narrar
        self.eventos = []
        self.placar = {time_casa.nome: 0, time_fora.nome: 0}
        self.artilheiros = {}          # nome -> gols
        self.cartoes = []              # (nome, tipo)
        self.aj = defaultdict(float)   # id(jogador) -> ajuste de nota
        self.ref = {}                  # id(jogador) -> jogador
        self.time_de = {}              # id(jogador) -> nome do time

    def registra(self, jogador, time_nome):
        """Marca que o jogador atuou (para ganhar nota no fim)."""
        self.ref[id(jogador)] = jogador
        self.time_de[id(jogador)] = time_nome

    def nota(self, jogador, valor):
        """Soma um ajuste de nota ao jogador (acerto positivo, erro negativo)."""
        self.aj[id(jogador)] += valor
        self.ref[id(jogador)] = jogador

    def emite(self, minuto, tipo, time_nome, quem):
        if self.narrar:
            self.eventos.append((minuto, tipo, time_nome, quem))


def forca_setor(jogadores, attrs, atitude_mod):
    """Média ponderada de um setor, descontando cansaço, fora-de-posição e atitude."""
    if not jogadores:
        return 30.0
    total = 0.0
    for j in jogadores:
        val = sum(getattr(j, a) for a in attrs) / len(attrs)
        val *= (1 - j.cansaco * cfg.DRENO_RESISTENCIA)   # cansaço derruba o jogo
        val *= (0.9 + 0.2 * (j.moral / 100))             # moral pesa um pouco
        val *= j.fator_posicao                            # fora de posição rende menos
        total += val
    return (total / len(jogadores)) * atitude_mod


def simula_partida(time_casa: Time, time_fora: Time, rng: random.Random, narrar=False):
    time_casa.reset_jogo()
    time_fora.reset_jogo()
    casa = time_casa.titulares()
    fora = time_fora.titulares()
    aplica_posicoes(casa, time_casa.formacao)   # marca pos_campo + fator por vaga
    aplica_posicoes(fora, time_fora.formacao)

    est = _Estado(time_casa, time_fora, narrar)
    for j in casa:
        est.registra(j, time_casa.nome)
    for j in fora:
        est.registra(j, time_fora.nome)

    # bancos de reservas (quem não é titular e está apto)
    bancos = {
        id(casa): [j for j in time_casa.elenco
                   if j not in casa and not j.lesionado and not j.expulso],
        id(fora): [j for j in time_fora.elenco
                   if j not in fora and not j.lesionado and not j.expulso],
    }
    subs_feitas = {time_casa.nome: 0, time_fora.nome: 0}

    def substituir(lineup, time_obj, quem_sai, minuto):
        """Troca um jogador por um reserva apto. Emite evento de substituição."""
        if subs_feitas[time_obj.nome] >= cfg.MAX_SUBSTITUICOES:
            return False
        banco = bancos[id(lineup)]
        candidatos = ([r for r in banco if r.pos == quem_sai.pos]
                      or [r for r in banco if r.pos != "GOL"])
        if not candidatos:
            return False
        entra = max(candidatos, key=lambda x: x.overall)
        entra.cansaco = 0.0
        entra.pos_campo = quem_sai.papel                       # herda a vaga
        entra.fator_posicao = penalidade_posicao(entra.papel, entra.pos)
        lineup[lineup.index(quem_sai)] = entra
        banco.remove(entra)
        subs_feitas[time_obj.nome] += 1
        est.registra(entra, time_obj.nome)   # reserva que entrou também recebe nota
        est.emite(minuto, "SUBSTITUICAO", time_obj.nome,
                  f"↓ {quem_sai.nome}  ↑ {entra.nome}")
        return True

    acrescimos = rng.randint(0, cfg.ACRESCIMO_MAX)
    total_min = cfg.MINUTOS + acrescimos

    for minuto in range(1, total_min + 1):
        # cansaço acumula ao longo do jogo (mais em quem tem pouca resistência)
        for lado in (casa, fora):
            for j in lado:
                j.cansaco = min(1.0, j.cansaco + (1 - j.resistencia / 100) * 0.012 + 0.004)

        for atacante, defensor, em_casa in ((casa, fora, True), (fora, casa, False)):
            atk_time = time_casa if em_casa else time_fora
            def_time = time_fora if em_casa else time_casa
            mod_atk = cfg.ATITUDES[atk_time.atitude]
            mod_def = cfg.ATITUDES[def_time.atitude]

            atacantes = [j for j in atacante if j.papel in ("ATA", "MEI")]
            defensores = [j for j in defensor if j.papel in ("ZAG", "LAT", "VOL")]
            goleiro = next((j for j in defensor if j.papel == "GOL"), None)

            f_atk = forca_setor(atacantes, ["finalizacao", "drible", "passe"], mod_atk["ataque"])
            f_def = forca_setor(defensores, ["desarme", "cabeceio"], mod_def["defesa"])

            n_def = len([j for j in defensor if not j.expulso])
            if n_def < 11:
                f_def *= (n_def / 11)

            vantagem = (f_atk - f_def) / 100
            prob = cfg.BASE_CHANCE_POR_MIN * (1 + vantagem)
            prob *= (1 + (cfg.VANTAGEM_CASA if em_casa else -cfg.VANTAGEM_CASA))
            prob += rng.uniform(-cfg.FATOR_SORTE, cfg.FATOR_SORTE) * cfg.BASE_CHANCE_POR_MIN
            if rng.random() > max(0.005, prob):
                continue

            # --- IMPEDIMENTO ---
            if rng.random() < cfg.PROB_IMPEDIMENTO:
                est.emite(minuto, "IMPEDIMENTO", atk_time.nome, "—")
                continue

            # --- DESARME / FALTA / CARTÃO / PÊNALTI ---
            if defensores and rng.random() < 0.5:
                marcador = max(defensores, key=lambda x: x.desarme)
                if rng.random() < (marcador.desarme / 140):
                    est.nota(marcador, cfg.NOTA_DESARME)
                    est.emite(minuto, "DESARME", def_time.nome, marcador.nome)
                    continue
                if rng.random() < cfg.PROB_FALTA_NO_DESARME:
                    _resolve_falta(est, minuto, marcador, def_time, rng)
                    if atacantes and rng.random() < cfg.PROB_FALTA_NA_AREA:
                        _resolve_penalti(est, minuto, atacantes, goleiro,
                                         atk_time, def_time, rng)
                    continue

            # --- FINALIZAÇÃO ---
            if not atacantes:
                continue

            if rng.random() < cfg.PROB_ATAQUE_TRAVADO:
                est.emite(minuto, "ATAQUE_PERIGOSO", atk_time.nome, "—")
                continue

            gk_val = (goleiro.gk_reflexo + goleiro.gk_defesa) / 2 if goleiro else 30

            if rng.random() < cfg.PROB_CHUTE_LONGE:
                _resolve_chute_longe(est, minuto, atacantes, goleiro, gk_val,
                                     atk_time, def_time, rng)
                continue

            _resolve_finalizacao(est, minuto, atacantes, goleiro, gk_val,
                                 atk_time, def_time, rng)

        # --- LESÃO (força substituição) ---
        if rng.random() < (cfg.PROB_LESAO_POR_JOGO / total_min):
            lado = casa if rng.random() < 0.5 else fora
            time_obj = time_casa if lado is casa else time_fora
            vivos = [j for j in lado if not j.expulso and not j.lesionado]
            if vivos:
                vit = rng.choice(vivos)
                vit.lesionado = True
                est.emite(minuto, "LESÃO", time_obj.nome, vit.nome)
                substituir(lado, time_obj, vit, minuto)

        # --- SUBSTITUIÇÃO TÁTICA (tira o mais cansado de linha) ---
        if minuto >= cfg.MIN_SUB_TATICA:
            for lado, time_obj in ((casa, time_casa), (fora, time_fora)):
                if rng.random() < cfg.PROB_SUB_TATICA:
                    de_linha = [j for j in lado if j.pos != "GOL" and not j.expulso]
                    if de_linha:
                        cansado = max(de_linha, key=lambda x: x.cansaco)
                        if cansado.cansaco > 0.4:
                            substituir(lado, time_obj, cansado, minuto)

    gols_casa = est.placar[time_casa.nome]
    gols_fora = est.placar[time_fora.nome]
    notas = _calcula_notas(est, gols_casa, gols_fora)

    return {
        "casa": time_casa.nome, "fora": time_fora.nome,
        "gols_casa": gols_casa, "gols_fora": gols_fora,
        "eventos": est.eventos, "artilheiros": est.artilheiros,
        "cartoes": est.cartoes, "acrescimos": acrescimos,
        "notas": notas,   # lista de (jogador, nota, time_nome)
    }


def _calcula_notas(est, gols_casa, gols_fora):
    """Fecha a nota de cada jogador que atuou: base + ajustes + resultado."""
    if gols_casa > gols_fora:
        mod = {est.casa_nome: +cfg.NOTA_RESULTADO, est.fora_nome: -cfg.NOTA_RESULTADO}
    elif gols_fora > gols_casa:
        mod = {est.casa_nome: -cfg.NOTA_RESULTADO, est.fora_nome: +cfg.NOTA_RESULTADO}
    else:
        mod = {est.casa_nome: 0.0, est.fora_nome: 0.0}

    notas = []
    for id_, jog in est.ref.items():
        time_nome = est.time_de.get(id_, est.casa_nome)
        bruta = cfg.NOTA_BASE + est.aj.get(id_, 0.0) + mod[time_nome]
        nota = round(min(cfg.NOTA_MAX, max(cfg.NOTA_MIN, bruta)), 1)
        notas.append((jog, nota, time_nome))
    return notas


# ---------------------------------------------------------------------
# Resolvedores de lance — cada um trata um tipo de evento e credita as notas.
# ---------------------------------------------------------------------
def _resolve_falta(est, minuto, marcador, def_time, rng):
    sev = ((marcador.agressividade / 100) * cfg.PESO_AGRESSIVIDADE_CARTAO
           + rng.uniform(0, 1 - cfg.PESO_AGRESSIVIDADE_CARTAO))
    if sev > cfg.LIMIAR_VERMELHO:
        marcador.expulso = True
        est.cartoes.append((marcador.nome, "VERMELHO"))
        est.nota(marcador, cfg.NOTA_VERMELHO)
        est.emite(minuto, "VERMELHO", def_time.nome, marcador.nome)
    elif sev > cfg.LIMIAR_AMARELO:
        marcador.amarelos_jogo += 1
        tipo = "AMARELO"
        est.nota(marcador, cfg.NOTA_AMARELO)
        if marcador.amarelos_jogo >= 2:
            marcador.expulso = True
            tipo = "2ºAMARELO→VERMELHO"
            est.nota(marcador, cfg.NOTA_VERMELHO - cfg.NOTA_AMARELO)  # ajusta p/ expulsão
        est.cartoes.append((marcador.nome, tipo))
        est.emite(minuto, tipo, def_time.nome, marcador.nome)
    else:
        est.emite(minuto, "FALTA", def_time.nome, marcador.nome)


def _resolve_penalti(est, minuto, atacantes, goleiro, atk_time, def_time, rng):
    cobrador = max(atacantes, key=lambda x: x.finalizacao)
    est.emite(minuto, "PENALTI", atk_time.nome, cobrador.nome)
    gk_pen = goleiro.gk_penalti if goleiro else 30
    chance_pen = (cfg.CONVERSAO_PENALTI - (gk_pen - 50) / 220
                  + (cobrador.finalizacao - 50) / 300
                  + rng.uniform(-cfg.FATOR_SORTE, cfg.FATOR_SORTE) * 0.25)
    roll = rng.random()
    if roll < chance_pen:
        est.placar[atk_time.nome] += 1
        est.artilheiros[cobrador.nome] = est.artilheiros.get(cobrador.nome, 0) + 1
        cobrador.moral = min(100, cobrador.moral + 4)
        est.nota(cobrador, cfg.NOTA_GOL_PENALTI)
        if goleiro:
            est.nota(goleiro, cfg.NOTA_GOL_SOFRIDO_GK)
        est.emite(minuto, "GOL_PENALTI", atk_time.nome, cobrador.nome)
    elif roll < chance_pen + 0.45 * (1 - chance_pen):
        if goleiro:
            est.nota(goleiro, cfg.NOTA_PENALTI_DEFENDIDO)
        est.emite(minuto, "PENALTI_DEFENDIDO", def_time.nome,
                  goleiro.nome if goleiro else "—")
    else:
        cobrador.moral = max(20, cobrador.moral - 4)
        est.nota(cobrador, cfg.NOTA_PENALTI_PERDIDO)
        est.emite(minuto, "PENALTI_PERDIDO", atk_time.nome, cobrador.nome)


def _resolve_chute_longe(est, minuto, atacantes, goleiro, gk_val, atk_time, def_time, rng):
    chutador = max(atacantes, key=lambda x: x.chute_longo + rng.uniform(0, 25))
    est.emite(minuto, "CHUTE_LONGE", atk_time.nome, chutador.nome)
    atk_val = chutador.chute_longo * (1 - chutador.cansaco * cfg.DRENO_RESISTENCIA) * chutador.fator_posicao
    chance_gol = (atk_val / (atk_val + gk_val)) * cfg.CONVERSAO_LONGE
    chance_gol += rng.uniform(-cfg.FATOR_SORTE, cfg.FATOR_SORTE) * 0.4
    if rng.random() < chance_gol:
        est.placar[atk_time.nome] += 1
        est.artilheiros[chutador.nome] = est.artilheiros.get(chutador.nome, 0) + 1
        chutador.moral = min(100, chutador.moral + 3)
        est.nota(chutador, cfg.NOTA_GOLACO)
        if goleiro:
            est.nota(goleiro, cfg.NOTA_GOL_SOFRIDO_GK)
        est.emite(minuto, "GOLACO", atk_time.nome, chutador.nome)
    else:
        if goleiro:
            est.nota(goleiro, cfg.NOTA_DEFESA)
        est.emite(minuto, "DEFESA_GOL", def_time.nome, goleiro.nome if goleiro else "—")


def _resolve_finalizacao(est, minuto, atacantes, goleiro, gk_val, atk_time, def_time, rng):
    finalizador = max(atacantes, key=lambda x: x.finalizacao + rng.uniform(0, 30))
    if rng.random() > cfg.CONVERSAO_BASE:
        est.emite(minuto, "CHANCE_PERDIDA", atk_time.nome, finalizador.nome)
        return
    atk_val = finalizador.finalizacao * (1 - finalizador.cansaco * cfg.DRENO_RESISTENCIA) * finalizador.fator_posicao
    chance_gol = atk_val / (atk_val + gk_val)
    chance_gol += rng.uniform(-cfg.FATOR_SORTE, cfg.FATOR_SORTE) * 0.5
    if rng.random() < chance_gol:
        est.placar[atk_time.nome] += 1
        est.artilheiros[finalizador.nome] = est.artilheiros.get(finalizador.nome, 0) + 1
        finalizador.moral = min(100, finalizador.moral + 3)
        est.nota(finalizador, cfg.NOTA_GOL)
        if goleiro:
            est.nota(goleiro, cfg.NOTA_GOL_SOFRIDO_GK)
        est.emite(minuto, "GOL", atk_time.nome, finalizador.nome)
    else:
        if goleiro:
            est.nota(goleiro, cfg.NOTA_DEFESA)
        est.emite(minuto, "DEFESA_GOL", def_time.nome, goleiro.nome if goleiro else "—")
