# Contexto do Projeto — Diretrizes de Trabalho + Status

Documento único para **não perder o contexto** entre sessões. Tem duas partes:

1. **Como trabalhar** — diretrizes de conduta para o desenvolvimento (inspiradas em Andrej Karpathy).
2. **Onde estamos** — o status do projeto (decisões, arquitetura, o que está feito, próximos passos).

> **Como usar:** cole este documento no início de uma nova conversa. A Parte 1 alinha *como* conduzir o trabalho; a Parte 2 recupera *o que* já foi construído. Anexe também os arquivos do pacote `futebol/` quando for mexer no código.

---

# PARTE 1 — Diretrizes de Trabalho

> Derivadas das observações de [Andrej Karpathy](https://x.com/karpathy/status/2015883857489522876) sobre armadilhas de LLMs ao programar. Fonte: repositório `multica-ai/andrej-karpathy-skills` (licença MIT). Tradução/adaptação para o português.

**Compromisso:** estas diretrizes priorizam cautela sobre velocidade. Para tarefas triviais, use o bom senso.

## 1. Pensar antes de codar
**Não suponha. Não esconda a confusão. Exponha os tradeoffs.**

Antes de implementar:
- Declare as suposições explicitamente. Se houver incerteza, pergunte.
- Se existem várias interpretações, apresente-as — não escolha em silêncio.
- Se existe um caminho mais simples, diga. Discorde quando fizer sentido.
- Se algo está obscuro, pare. Nomeie o que está confuso. Pergunte.

## 2. Simplicidade primeiro
**O mínimo de código que resolve o problema. Nada especulativo.**

- Nenhuma funcionalidade além do que foi pedido.
- Nenhuma abstração para código de uso único.
- Nenhuma "flexibilidade" ou "configurabilidade" que não foi solicitada.
- Nenhum tratamento de erro para cenários impossíveis.
- Se você escreveu 200 linhas e dava pra fazer em 50, reescreva.

Pergunte-se: "um engenheiro sênior diria que isso está complicado demais?" Se sim, simplifique.

## 3. Mudanças cirúrgicas
**Toque só no que precisa. Limpe só a sua própria bagunça.**

Ao editar código existente:
- Não "melhore" código, comentários ou formatação adjacentes.
- Não refatore o que não está quebrado.
- Siga o estilo existente, mesmo que você fizesse diferente.
- Se notar código morto não relacionado, mencione — não apague.

Quando suas mudanças criam órfãos:
- Remova imports/variáveis/funções que as SUAS mudanças deixaram sem uso.
- Não remova código morto pré-existente sem ser pedido.

O teste: toda linha alterada deve rastrear diretamente ao pedido do usuário.

## 4. Execução orientada a metas
**Defina o critério de sucesso. Itere até verificar.**

Transforme tarefas em metas verificáveis:
- "Adicionar validação" → "Escrever testes para entradas inválidas e fazê-los passar"
- "Corrigir o bug" → "Escrever um teste que o reproduz e fazê-lo passar"
- "Refatorar X" → "Garantir que os testes passam antes e depois"

Para tarefas com vários passos, declare um plano breve:
```
1. [Passo] → verificar: [checagem]
2. [Passo] → verificar: [checagem]
3. [Passo] → verificar: [checagem]
```

Critérios fortes permitem iterar sozinho. Critérios fracos ("faça funcionar") exigem esclarecimento constante.

**Estas diretrizes estão funcionando se:** menos mudanças desnecessárias nos diffs, menos reescritas por excesso de complexidade, e as perguntas de esclarecimento vêm antes da implementação — não depois do erro.

---

# PARTE 2 — Status do Projeto

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
├── modelos.py         # entidades Jogador e Time + geradores + escalações/formações
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
- Desenvolvimento de treino: quem não joga ainda evolui um pouco (atenuado).

**Formações + fora de posição**
- 5 formações (4-3-3, 4-4-2, 4-2-3-1, 3-5-2, 5-3-2).
- Ao montar o XI, cada vaga mostra o jogador e sinaliza quem está fora de posição (gravidade leve/média/grave + % de perda).
- Jogar fora de posição reduz o rendimento do setor na simulação; o agrupamento de setores usa o **papel** (vaga ocupada), não a posição natural. Dá pra trocar por alguém da posição certa no editor manual.
- A escalação automática (clubes da CPU) nunca gera fora de posição — só o humano cria, de propósito.

**Aposentadoria + regeneração de base**
- A cada virada de temporada, cada jogador pode se aposentar: chance 0 antes dos 32, ~5% aos 32, subindo linearmente até 100% aos 51.
- Para CADA aposentado entra UM garoto novo (17–19 anos) na MESMA posição → o tamanho do elenco fica constante.
- A qualidade da base é ancorada no nível histórico do clube (`nivel_base`), evitando espiral de queda.
- Equilíbrio verificado: ao longo de 20 temporadas o overall médio da liga assenta numa faixa estável (~58–63) em todas as seeds testadas.

**Loop do manager (jogável, texto)**
- Você comanda um clube; a cada rodada define atitude, formação e escalação (melhor XI p/ vencer × XI jovem p/ desenvolver × manual), assiste ao jogo narrado com notas, e vê a tabela mexer.
- Save/load em JSON, com o estado do RNG — continuar um jogo salvo é determinístico.
- A escalação tem peso duplo: muda o resultado E quem joga evolui (a tensão "vencer agora × desenvolver").

## Calibragem

Tudo em `futebol/config.py`. Botões principais:
- `FATOR_SORTE` — o mais importante: o quão imprevisível é o jogo.
- `BASE_CHANCE_POR_MIN`, `CONVERSAO_BASE` — volume de gols.
- Limiares de cartão, pênalti, chute de longe, substituições.
- Pesos das notas (`NOTA_*`) e da evolução (`EVO_DRIFT`, `EVO_SENS`, faixas de idade).
- Aposentadoria/base (`IDADE_APOSENTA_MIN/MAX`, `YOUTH_*`).

**Sanidade atual:** ~2.5–2.7 gols/jogo (faixa realista 2.4–3.0), cartões em patamar crível, tabela coerente com zebras pontuais, evolução e pool de jogadores equilibrados.

## Protótipo visual (à parte, não é o núcleo)

`visualizador_partida.html` — um campo 2D em HTML/Canvas que anima o roteiro de eventos de uma partida real do núcleo (posse de bola, passes, gols, pausas com banner, som). É só prova de conceito da ponte núcleo→tela; o trabalho atual está focado no núcleo.

## Próximos passos

**Evoluir o núcleo** (cada item entra como um módulo novo ou um `_resolve_*`, sem reescrita):
- Mercado de transferências + economia básica (mais decisões diárias; já há base de jovens para negociar).
- Cobrança de falta direta; escanteio (cabeceio + altura vs defesa); copas/mata-mata.
- Compatibilidades de posição mais finas (ex.: VOL que joga bem de MEI).

**Teste 1 — primeira fatia jogável (mobile, Godot):**
- Reaproveitar `partida.py` (eventos) e o loop de `carreira.py` (já testado em texto).
- Escalar time → apertar "jogar" → ver os pontos encenando os eventos na tela.
- Incluir substituição e controle de tempo (pausar/acelerar).
- Critério de sucesso: dar vontade de jogar "só mais uma".

**Online (fase posterior):** mover o núcleo para um servidor autoritativo, contas + banco de dados (substituindo `persistencia.py`), partidas assíncronas.
