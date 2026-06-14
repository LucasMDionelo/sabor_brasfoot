# Manager de Futebol — Status do Projeto

Documento enxuto do que foi decidido e construído até aqui.

## Visão

Jogo de gerenciamento de futebol (estilo Brasfoot). O jogador é o **manager**: escala, define tática e assiste às partidas. Foco em mecânicas que tragam o jogador de volta todo dia.

**Plano de lançamento:** offline single-player primeiro (Steam + mobile), com a estrutura já pronta para virar online (PvP) depois.

## Decisões de design

| Tema | Decisão |
|------|---------|
| Como a partida é decidida | **Resultado primeiro**: os duelos são decididos por *atributos + sorte calibrada*, não por física. O núcleo decreta o lance; a tela só encena. Mantém o controle total da calibragem. |
| Reprodutibilidade | **Determinismo**: mesma seed + mesmas escalações = exatamente o mesmo jogo. Sustenta replay e o futuro servidor online. |
| Separação | **Núcleo de regras** totalmente isolado da **apresentação**. Trocar a tela não toca em uma linha de regra. |
| Engine / linguagem | **Godot 2D** (gratuito, leve, forte em 2D). Núcleo prototipado em **Python** (Teste 0). |
| Mobile vs Steam | Um projeto, um núcleo, uma engine — só a "casca" (UI/toque vs mouse, integrações de loja) é adaptada por plataforma. |
| Online (futuro) | Servidor é a autoridade: roda o núcleo e manda o **roteiro de eventos** para o cliente apenas animar. Modelo **assíncrono** primeiro. |
| ML | Não usar. IA clássica (atributos + regras) dá controle e é barata. |

## O "roteiro de eventos"

A ponte entre núcleo e tela. O núcleo simula a partida e devolve uma **lista de eventos** (minuto, tipo, time, jogador). A apresentação lê essa lista e encena. É essa mesma lista que o servidor mandaria no online.

## Arquitetura atual (Teste 0)

```
run.py                 # demo automática — simula uma temporada inteira
jogar.py               # JOGÁVEL — você comanda um clube (loop de manager)  [interação]
futebol/
├── config.py          # CALIBRAGEM — todos os botões num lugar só
├── nomes.py           # dados fictícios (jogadores e clubes)
├── modelos.py         # entidades Jogador e Time + geradores + escalações
├── partida.py         # MOTOR de partida (eventos + notas de desempenho)  [núcleo]
├── liga.py            # calendário e simulação de temporada               [núcleo]
├── evolucao.py        # evolução de jogadores entre temporadas            [núcleo]
├── regen.py           # aposentadoria + regeneração de base               [núcleo]
├── carreira.py        # loop do manager: estado e progressão da carreira  [núcleo]
├── persistencia.py    # salvar/carregar em JSON (vira banco no online)    [núcleo]
└── apresentacao.py    # renderização em texto (o Godot substitui isto)
```

O núcleo é o que um dia roda no servidor. A apresentação e a interação (`jogar.py`) são descartáveis.

Rodar a demo automática: `python3 run.py`
Jogar como manager: `python3 jogar.py`

## O que o Teste 0 já faz

Simula uma **partida lance a lance** (com narração) e uma **liga inteira** (turno e returno) com tabela, artilharia e disciplina.

**Atributos dos jogadores**
- Físico fixo: altura (não evolui).
- Habilidades de linha: finalização, drible, passe, velocidade, cabeceio, desarme, chute de longe.
- Goleiro: defesa, reflexo, defesa de pênalti.
- Estado/temperamento: idade, moral, resistência, agressividade.

**Mecânicas de partida**
- Atitude do time: retranca / equilibrado / ataque total.
- Geração de chances por força dos setores + vantagem de casa + sorte.
- Finalização normal, chute de longe (golaço), ataque perigoso travado.
- Pênalti: convertido, defendido ou perdido.
- Falta → cartão (amarelo/vermelho) decidido pela agressividade.
- Cartão vermelho derruba a força do time (jogar com 10).
- Impedimento, cansaço drenando ao longo do jogo, lesões, acréscimos.
- Substituições automáticas (por lesão e por cansaço), mostrando quem sai/entra.
- "IA" básica dos clubes escalando os melhores por posição.

**Nota de desempenho (por partida)**
- Cada jogador recebe uma nota a partir de NOTA_BASE (6.0), ajustada pelos seus acertos/erros: gols, defesas, desarmes, pênalti defendido (+); cartões, pênalti perdido, gol sofrido pelo goleiro (−); mais um bônus/ônus pelo resultado do time.
- A nota é só *leitura dos eventos* — não realimenta a simulação, então não altera o resultado nem a calibragem.

**Evolução entre temporadas (idade + desempenho)**
- A nota vira "pontos de evolução" (nota acima/abaixo da neutra, NÃO aleatório).
- No fim da temporada: `delta = drift(idade) + média_pontos × sensibilidade(idade)`.
- Jovem (≤23) evolui rápido, auge (24–29) devagar, veterano (≥30) retrocede. Desempenho amplia/atenua a magnitude.
- Equilíbrio: variação do overall médio da liga ~−0.3/temporada (leve, vinda do envelhecimento do elenco fechado — não do sistema em si).

## Calibragem

Tudo em `futebol/config.py`. Botões principais:
- `FATOR_SORTE` — o mais importante: o quão imprevisível é o jogo.
- `BASE_CHANCE_POR_MIN`, `CONVERSAO_BASE` — volume de gols.
- Limiares de cartão, pênalti, chute de longe, substituições.
- Pesos das notas (`NOTA_*`) e da evolução (`EVO_DRIFT`, `EVO_SENS`, faixas de idade).

**Sanidade atual:** ~2.5 gols/jogo (faixa realista 2.4–3.0), cartões em patamar crível, tabela coerente com zebras pontuais, notas plausíveis (8–9 destaques, ~6 medianos), evolução equilibrada.

**Loop do manager (jogável, texto) — FEITO**
- Você comanda um clube; a cada rodada define atitude e escalação (melhor XI p/ vencer × XI jovem p/ desenvolver × manual), assiste ao jogo narrado com notas, e vê a tabela mexer.
- Save/load em JSON, com o estado do RNG — continuar um jogo salvo é determinístico.
- A escalação tem peso duplo: muda o resultado E quem joga evolui (a tensão "vencer agora × desenvolver").
- **Formações + fora de posição:** 5 formações (4-3-3, 4-4-2, 4-2-3-1, 3-5-2, 5-3-2). Ao montar o XI, cada vaga mostra o jogador e sinaliza quem está fora de posição (gravidade leve/média/grave + % de perda). Jogar fora de posição reduz o rendimento do setor na simulação; dá pra trocar por alguém da posição certa no editor manual.

**Aposentadoria + regeneração de base — FEITO**
- A cada virada de temporada, cada jogador pode se aposentar: chance 0 antes dos 32, ~5% aos 32, subindo linearmente até 100% aos 51.
- Para CADA aposentado entra UM garoto novo (17–19 anos) na MESMA posição → o tamanho do elenco fica constante.
- A qualidade da base é ancorada no nível histórico do clube (`nivel_base`), evitando espiral de queda.
- Desenvolvimento de treino: quem não joga ainda evolui um pouco (atenuado), então a base não estagna no banco.
- Equilíbrio verificado: ao longo de 20 temporadas o overall médio da liga assenta numa faixa estável (~58–63) em todas as seeds testadas, sem colapsar nem inflar.

## Próximos passos

**Evoluir o núcleo** (cada item entra como um módulo novo ou um `_resolve_*`, sem reescrita):
- Mercado de transferências + economia básica (mais decisões diárias; já há base de jovens para negociar).
- Cobrança de falta direta; escanteio (cabeceio + altura vs defesa); copas/mata-mata.

**Teste 1 — primeira fatia jogável (mobile, Godot):**
- Reaproveitar `partida.py` (eventos) e o loop de `carreira.py` (já testado em texto).
- Escalar time → apertar "jogar" → ver os pontos encenando os eventos na tela.
- Incluir substituição e controle de tempo (pausar/acelerar).
- Critério de sucesso: dar vontade de jogar "só mais uma".

**Online (fase posterior):** mover o núcleo para um servidor autoritativo, contas + banco de dados (substituindo `persistencia.py`), partidas assíncronas.
