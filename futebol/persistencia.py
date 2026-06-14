"""
persistencia.py — SAVE / LOAD
=============================
Serializa o estado do jogo para JSON e lê de volta. Cada Jogador/Time vira um
dicionário simples — exatamente como uma "linha de banco de dados". Essa é a
mesma camada que, no online, será substituída por um banco de verdade no
servidor; por isso o estado é modelado de forma plana e portável.

Salvamos também o estado do gerador aleatório, para que continuar um jogo
salvo seja determinístico (a temporada segue idêntica de onde parou).
"""

import json
import random
from dataclasses import asdict, fields

from .modelos import Jogador, Time


def _jogador_para_dict(j: Jogador) -> dict:
    d = asdict(j)
    for transitorio in ("cansaco", "amarelos_jogo", "expulso", "lesionado",
                        "pos_campo", "fator_posicao"):
        d.pop(transitorio, None)
    return d


def _jogador_de_dict(d: dict) -> Jogador:
    campos = {f.name for f in fields(Jogador)}
    return Jogador(**{k: v for k, v in d.items() if k in campos})


def _time_para_dict(t: Time) -> dict:
    return {
        "nome": t.nome, "atitude": t.atitude, "nivel_base": t.nivel_base,
        "formacao": t.formacao,
        "pontos": t.pontos, "vit": t.vit, "emp": t.emp, "der": t.der,
        "gp": t.gp, "gc": t.gc,
        "elenco": [_jogador_para_dict(j) for j in t.elenco],
    }


def _time_de_dict(d: dict) -> Time:
    t = Time(nome=d["nome"], atitude=d.get("atitude", "EQUILIBRADO"),
             nivel_base=d.get("nivel_base", 60), formacao=d.get("formacao", "4-3-3"))
    t.pontos = d.get("pontos", 0); t.vit = d.get("vit", 0)
    t.emp = d.get("emp", 0); t.der = d.get("der", 0)
    t.gp = d.get("gp", 0); t.gc = d.get("gc", 0)
    t.elenco = [_jogador_de_dict(jd) for jd in d["elenco"]]
    return t


def salvar(carreira, caminho: str):
    """Grava a carreira inteira em um arquivo JSON."""
    estado_rng = carreira.rng.getstate()  # (versão, tupla de ints, gauss)
    dados = {
        "temporada": carreira.temporada,
        "rodada_idx": carreira.rodada_idx,
        "clube_humano": carreira.clube_humano,
        "artilharia": carreira.artilharia,
        "disciplina": carreira.disciplina,
        "times": [_time_para_dict(t) for t in carreira.times],
        # calendário guardado por NOMES (referências são religadas ao carregar)
        "calendario": [[[a.nome, b.nome] for (a, b) in rodada]
                       for rodada in carreira.calendario],
        "rng": [estado_rng[0], list(estado_rng[1]), estado_rng[2]],
    }
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False)


def carregar(caminho: str):
    """Lê um arquivo JSON e reconstrói a carreira (importação tardia evita ciclo)."""
    from .carreira import Carreira

    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)

    times = [_time_de_dict(td) for td in dados["times"]]
    por_nome = {t.nome: t for t in times}
    calendario = [[(por_nome[a], por_nome[b]) for (a, b) in rodada]
                  for rodada in dados["calendario"]]

    rng = random.Random()
    v, estado, gauss = dados["rng"]
    rng.setstate((v, tuple(estado), gauss))

    return Carreira(
        times=times, calendario=calendario,
        clube_humano=dados["clube_humano"], rng=rng,
        temporada=dados["temporada"], rodada_idx=dados["rodada_idx"],
        artilharia=dados.get("artilharia", {}),
        disciplina=dados.get("disciplina", {"AMARELO": 0, "VERMELHO": 0}),
    )
