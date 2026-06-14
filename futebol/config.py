"""
config.py — CALIBRAGEM
======================
Todos os "botões" do jogo num lugar só. TODA a mágica de balanceamento mora aqui.
Mudar um número e rodar de novo já muda o "sabor" do jogo, sem tocar no motor.

Mantido separado de propósito: no futuro, dá pra carregar estes valores de um
arquivo externo (JSON/banco) e ajustar o balanceamento sem recompilar nada.
"""

SEED = 42                    # troque para gerar outra temporada (determinismo)
MINUTOS = 90                 # duração base da partida

# Quão "imprevisível" é o jogo. 0 = só o mais forte ganha (chato).
# Valores altos = muita zebra (frustrante). Este é O botão mais importante.
FATOR_SORTE = 0.45

VANTAGEM_CASA = 0.08         # empurrãozinho de jogar em casa (na geração de chances)
BASE_CHANCE_POR_MIN = 0.132  # prob. base de um lance perigoso por time, por minuto
CONVERSAO_BASE = 0.40        # fração das chances claras que viram finalização real
PROB_FALTA_NO_DESARME = 0.46 # ao tentar desarme malsucedido, chance de virar falta
PESO_AGRESSIVIDADE_CARTAO = 0.55  # quanto a agressividade puxa a falta pra cartão
LIMIAR_AMARELO = 0.58        # acima disso, falta vira amarelo
LIMIAR_VERMELHO = 0.94       # acima disso, falta vira vermelho direto
PROB_IMPEDIMENTO = 0.11      # fração de ataques anulados por impedimento
PROB_LESAO_POR_JOGO = 0.06   # chance de uma lesão por time por partida
DRENO_RESISTENCIA = 0.18     # quanto o cansaço derruba o desempenho até os 90'
ACRESCIMO_MAX = 5            # acréscimos sorteados de 0..ACRESCIMO_MAX

PROB_ATAQUE_TRAVADO = 0.22   # chance de um ataque perigoso ser bloqueado antes do chute
PROB_CHUTE_LONGE = 0.20      # fração das finalizações que são tentadas de longe
CONVERSAO_LONGE = 0.55       # chute de longe converte menos que finalização de dentro
PROB_FALTA_NA_AREA = 0.13    # fração das faltas que acontecem dentro da área (= pênalti)
CONVERSAO_PENALTI = 0.76     # prob. base de converter o pênalti (antes do goleiro)
MAX_SUBSTITUICOES = 3        # substituições por time
MIN_SUB_TATICA = 58          # a partir de que minuto começam as trocas por cansaço
PROB_SUB_TATICA = 0.020      # prob. por minuto de uma troca tática (após MIN_SUB_TATICA)

# Modificadores por atitude do time (recuado / equilibrado / ataque total)
ATITUDES = {
    "RETRANCA":     {"ataque": 0.78, "defesa": 1.18, "agressividade": 1.15},
    "EQUILIBRADO":  {"ataque": 1.00, "defesa": 1.00, "agressividade": 1.00},
    "ATAQUE_TOTAL": {"ataque": 1.25, "defesa": 0.80, "agressividade": 0.95},
}


# =====================================================================
# NOTAS DE DESEMPENHO (por partida) — pesos de cada acerto/erro.
# A nota parte de NOTA_BASE e sobe/desce conforme os eventos do jogador.
# Mantida em [NOTA_MIN, NOTA_MAX]. NÃO realimenta a simulação (não muda
# o resultado): é só leitura dos eventos -> equilíbrio preservado.
# =====================================================================
NOTA_BASE = 6.0              # ponto de partida de todo jogador que entra
NOTA_MIN = 3.0
NOTA_MAX = 10.0
NOTA_RESULTADO = 0.30        # bônus/ônus aplicado a quem jogou (vitória/derrota)

NOTA_GOL = 1.00              # gol normal
NOTA_GOLACO = 1.20           # gol de fora da área
NOTA_GOL_PENALTI = 0.80      # gol de pênalti (vale um pouco menos)
NOTA_DEFESA = 0.22           # cada defesa do goleiro
NOTA_PENALTI_DEFENDIDO = 1.00
NOTA_PENALTI_PERDIDO = -1.00 # cobrador que perde o pênalti
NOTA_AMARELO = -0.40
NOTA_VERMELHO = -1.30
NOTA_DESARME = 0.10          # cada desarme bem-sucedido
NOTA_GOL_SOFRIDO_GK = -0.30  # goleiro a cada gol sofrido

# =====================================================================
# EVOLUÇÃO ENTRE TEMPORADAS — idade define a tendência, desempenho a magnitude.
# pontos_evolucao do jogador = soma, por partida, de (nota - NOTA_NEUTRA).
# No fim da temporada: delta = drift(idade) + media_pontos * sensibilidade(idade).
# =====================================================================
NOTA_NEUTRA_EVOLUCAO = 6.5   # nota "mediana"; acima disso acumula evolução positiva
IDADE_JOVEM = 23             # <= : evolui rápido
IDADE_VETERANO = 30          # >= : retrocede

# drift = tendência natural por faixa etária (com desempenho mediano)
EVO_DRIFT = {"jovem": 1.6, "auge": 0.2, "veterano": -1.4}
# sensibilidade = quanto o desempenho amplia/atenua a evolução
EVO_SENS = {"jovem": 1.4, "auge": 0.8, "veterano": 0.5}
EVO_DELTA_MAX = 4            # teto de variação de atributo por temporada (+/-)


# =====================================================================
# APOSENTADORIA + REGENERAÇÃO DE BASE
# A cada virada de temporada: jogadores podem se aposentar (probabilístico,
# de IDADE_APOSENTA_MIN a IDADE_APOSENTA_MAX) e, para CADA aposentado, entra
# um garoto novo NA MESMA POSIÇÃO — o tamanho do elenco fica constante.
# A chance é ~baixa no mínimo e sobe linearmente até 100% no máximo.
# =====================================================================
IDADE_APOSENTA_MIN = 32      # antes disso, ninguém se aposenta
IDADE_APOSENTA_MAX = 51      # nesta idade (ou mais), aposenta com 100% de chance

YOUTH_IDADE_MIN = 17         # faixa etária dos garotos que sobem da base
YOUTH_IDADE_MAX = 19
YOUTH_OVERALL_OFFSET = 9     # prospecto entra ~este tanto abaixo do nivel_base do clube
YOUTH_OVERALL_MIN = 35       # piso de qualidade do prospecto

TREINO_SEM_JOGAR = 0.45      # quanto do drift por idade vale para quem não joga (treino)
