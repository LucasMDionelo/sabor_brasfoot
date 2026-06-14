"""
modelos.py — ENTIDADES DE DADOS
===============================
Jogador e Time, modelados "como se fossem linhas de banco de dados" (pensando
no futuro online). Aqui não há nenhuma regra de partida nem nada de tela:
só a estrutura dos dados e como gerar elencos.

Dependências: apenas `nomes` (listas fictícias).
"""

import random
from dataclasses import dataclass, field

from .nomes import PRIMEIROS, SOBRENOMES

# Formação base (compatível com a 4-3-3 padrão). Mantida para retrocompatibilidade.
POSICOES = ["GOL", "ZAG", "ZAG", "LAT", "LAT", "VOL", "MEI", "MEI", "ATA", "ATA", "ATA"]

# Formações disponíveis — cada uma é o molde de 11 vagas (slots) por posição.
# A "4-3-3" é idêntica à POSICOES (escala automática não muda de comportamento).
FORMACOES = {
    "4-3-3":   ["GOL", "ZAG", "ZAG", "LAT", "LAT", "VOL", "MEI", "MEI", "ATA", "ATA", "ATA"],
    "4-4-2":   ["GOL", "ZAG", "ZAG", "LAT", "LAT", "VOL", "VOL", "MEI", "MEI", "ATA", "ATA"],
    "4-2-3-1": ["GOL", "ZAG", "ZAG", "LAT", "LAT", "VOL", "VOL", "MEI", "MEI", "MEI", "ATA"],
    "3-5-2":   ["GOL", "ZAG", "ZAG", "ZAG", "VOL", "VOL", "MEI", "MEI", "MEI", "ATA", "ATA"],
    "5-3-2":   ["GOL", "ZAG", "ZAG", "ZAG", "LAT", "LAT", "VOL", "MEI", "MEI", "ATA", "ATA"],
}

# Eixo defesa→ataque das posições, para medir o quão "fora" um jogador está.
_ORDEM = {"GOL": 0, "ZAG": 2, "LAT": 2, "VOL": 4, "MEI": 6, "ATA": 8}


def penalidade_posicao(slot: str, pos: str) -> float:
    """Multiplicador de rendimento (<=1.0) por escalar um jogador 'pos' numa
    vaga 'slot'. 1.0 = na posição certa; menor = mais fora de posição."""
    if slot == pos:
        return 1.0
    if slot == "GOL" or pos == "GOL":   # jogador de linha no gol, ou goleiro na linha
        return 0.45
    d = abs(_ORDEM[slot] - _ORDEM[pos])
    return max(0.60, 0.97 - 0.05 * d)


def fora_de_posicao(slot: str, pos: str) -> bool:
    return slot != pos


def gravidade(fator: float) -> str:
    """Rótulo do quão grave é o fora de posição, a partir do fator."""
    if fator >= 0.999:
        return "ok"
    if fator >= 0.93:
        return "leve"
    if fator >= 0.80:
        return "média"
    return "grave"


def escalar_formacao(time, formacao_nome, chave=None):
    """Monta um XI ordenado conforme o molde da formação. Para cada vaga, pega o
    melhor candidato APTO da mesma posição (por `chave`); se faltar, completa com
    o melhor restante (que ficará fora de posição). Devolve a lista de 11 alinhada
    aos slots de FORMACOES[formacao_nome]."""
    slots = FORMACOES.get(formacao_nome, POSICOES)
    if chave is None:
        chave = lambda j: j.overall
    aptos = [j for j in time.elenco if not j.lesionado and not j.expulso]
    usados, xi = set(), []
    # 1ª passada: preenche cada vaga com jogador da posição exata
    for slot in slots:
        cands = [j for j in aptos if j.pos == slot and id(j) not in usados]
        if cands:
            esc = max(cands, key=chave)
            usados.add(id(esc)); xi.append(esc)
        else:
            xi.append(None)  # vaga a completar na 2ª passada
    # 2ª passada: completa vagas vazias com o melhor restante (fora de posição)
    for i, slot in enumerate(slots):
        if xi[i] is None:
            resto = [j for j in aptos if id(j) not in usados]
            if resto:
                esc = max(resto, key=lambda j: j.overall)
                usados.add(id(esc)); xi[i] = esc
    return [j for j in xi if j is not None]


def aplica_posicoes(lineup, formacao_nome):
    """Marca, para cada jogador do XI, em que vaga ele está jogando (pos_campo)
    e o fator de rendimento (1.0 se na posição certa, menor se fora)."""
    slots = FORMACOES.get(formacao_nome, POSICOES)
    for i, j in enumerate(lineup):
        slot = slots[i] if i < len(slots) else j.pos
        j.pos_campo = slot
        j.fator_posicao = penalidade_posicao(slot, j.pos)


@dataclass
class Jogador:
    nome: str
    pos: str
    idade: int
    # físico fixo (NÃO evolui como skill)
    altura: int
    # habilidades 1..100 (evoluem/regridem)
    finalizacao: int = 50
    drible: int = 50
    passe: int = 50
    velocidade: int = 50
    cabeceio: int = 50
    desarme: int = 50
    chute_longo: int = 50
    # goleiro
    gk_defesa: int = 50
    gk_reflexo: int = 50
    gk_penalti: int = 50
    # temperamento e estado de carreira
    agressividade: int = 50   # alto = mais cartões
    moral: int = 70
    resistencia: int = 75
    # estado de jogo (resetado a cada partida)
    cansaco: float = 0.0
    amarelos_jogo: int = 0
    expulso: bool = False
    lesionado: bool = False
    # posição em que está jogando NESTA partida (pode diferir de `pos`) + fator
    pos_campo: str = None
    fator_posicao: float = 1.0
    # acúmulo de temporada (resetado ao aplicar a evolução)
    pontos_evolucao: float = 0.0
    jogos_disputados: int = 0

    @property
    def papel(self) -> str:
        """Posição em que atua na partida (a vaga ocupada, ou a própria posição)."""
        return self.pos_campo or self.pos

    @property
    def overall(self) -> int:
        if self.pos == "GOL":
            return round((self.gk_defesa + self.gk_reflexo + self.gk_penalti) / 3)
        return round((self.finalizacao + self.drible + self.passe +
                      self.velocidade + self.desarme + self.cabeceio) / 6)

    def skills_evoluiveis(self):
        """Nomes dos atributos que crescem/declinam (altura e estado ficam de fora)."""
        if self.pos == "GOL":
            return ["gk_defesa", "gk_reflexo", "gk_penalti"]
        return ["finalizacao", "drible", "passe", "velocidade",
                "cabeceio", "desarme", "chute_longo"]


@dataclass
class Time:
    nome: str
    elenco: list = field(default_factory=list)
    atitude: str = "EQUILIBRADO"
    # nível histórico/reputação do clube — âncora estável para a base (não decai)
    nivel_base: int = 60
    # formação tática atual (molde de 11 vagas)
    formacao: str = "4-3-3"
    # escalação escolhida pelo humano (None = a 'IA' escala os melhores)
    escalacao_manual: list = None
    # estatísticas de campeonato
    pontos: int = 0
    vit: int = 0
    emp: int = 0
    der: int = 0
    gp: int = 0
    gc: int = 0

    @property
    def saldo(self):
        return self.gp - self.gc

    @property
    def jogos(self):
        return self.vit + self.emp + self.der

    def titulares(self):
        """Escala o time. Honra a escalação manual do humano se ela estiver
        completa e apta; caso contrário, escala os melhores pela formação atual."""
        if self.escalacao_manual:
            aptos = [j for j in self.escalacao_manual
                     if not j.lesionado and not j.expulso]
            if len(aptos) == 11:
                return list(aptos)
        return escalar_formacao(self, self.formacao)

    def escalacao_por_overall(self):
        """XI focado em VENCER: melhores por posição, na formação atual."""
        return escalar_formacao(self, self.formacao, chave=lambda j: j.overall)

    def escalacao_jovens(self):
        """XI focado em DESENVOLVER: o mais jovem apto de cada posição."""
        return escalar_formacao(self, self.formacao, chave=lambda j: -j.idade)

    def reset_jogo(self):
        for j in self.elenco:
            j.cansaco = 0.0
            j.amarelos_jogo = 0
            j.expulso = False
            j.lesionado = False   # lesão multi-jogo fica para fase 2
            j.pos_campo = None    # posição-em-campo é recalculada a cada partida
            j.fator_posicao = 1.0


def gera_jogador(rng: random.Random, pos: str, base: int,
                 idade_min: int = 18, idade_max: int = 35) -> Jogador:
    """Cria um jogador com atributos em torno de 'base' (força do clube).
    A faixa etária pode ser restrita (ex.: garotos da base com 17-19)."""
    def attr(centro=base, espalhamento=10):
        return max(1, min(99, round(rng.gauss(centro, espalhamento))))

    j = Jogador(
        nome=f"{rng.choice(PRIMEIROS)} {rng.choice(SOBRENOMES)}",
        pos=pos,
        idade=rng.randint(idade_min, idade_max),
        altura=rng.randint(168, 196),
        agressividade=attr(50, 18),
        moral=attr(70, 8),
        resistencia=attr(75, 8),
    )
    if pos == "GOL":
        j.gk_defesa = attr(); j.gk_reflexo = attr(); j.gk_penalti = attr()
        j.altura = rng.randint(183, 198)
    else:
        # enfatiza atributos conforme a posição (decisão do manager tem peso)
        j.finalizacao = attr(base + (12 if pos == "ATA" else -8))
        j.drible = attr(base + (8 if pos in ("ATA", "MEI") else -4))
        j.passe = attr(base + (8 if pos in ("MEI", "VOL") else 0))
        j.velocidade = attr(base + (6 if pos in ("LAT", "ATA") else 0))
        j.desarme = attr(base + (12 if pos in ("ZAG", "VOL") else -6))
        j.cabeceio = attr(base + (8 if pos in ("ZAG", "ATA") else 0))
        j.chute_longo = attr()
    return j


def gera_time(rng: random.Random, nome: str) -> Time:
    base = rng.randint(48, 78)  # força média do clube
    elenco = [
        gera_jogador(rng, "GOL", base),
        gera_jogador(rng, "GOL", base - 6),
    ]
    for pos in ["ZAG", "ZAG", "ZAG", "LAT", "LAT", "LAT", "VOL", "VOL",
                "MEI", "MEI", "MEI", "ATA", "ATA", "ATA", "ATA"]:
        elenco.append(gera_jogador(rng, pos, base + rng.randint(-6, 6)))
    return Time(nome=nome, elenco=elenco, nivel_base=base)
