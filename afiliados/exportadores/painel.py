"""
Gera o painel web (`painel.html`): um único arquivo HTML autossuficiente.

Os dados do ranking são embutidos no próprio arquivo, então o painel abre com
duplo clique no navegador — sem servidor, sem internet para o código (só para
carregar as imagens dos produtos).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from afiliados import VERSAO

_TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "painel.html"


def _para_json_seguro(ranking: pd.DataFrame) -> str:
    """
    Serializa o ranking para embutir em <script>.

    `ensure_ascii` + troca de `<` evitam que um título malicioso feche a tag
    <script> (XSS). O painel ainda monta o DOM com `textContent`.
    """
    registros = [
        {
            "pos": int(linha.posicao),
            "titulo": linha.titulo,
            "loja": linha.loja,
            "preco": float(linha.preco),
            "pct": float(linha.comissao_pct),
            "comissao": float(linha.comissao_estimada),
            "vendas": int(linha.vendas),
            "nota": float(linha.avaliacao),
            "desconto": float(linha.desconto_pct),
            "url": linha.url,
            "imagem": linha.imagem_url,
        }
        for linha in ranking.itertuples(index=False)
    ]
    return json.dumps(registros, ensure_ascii=True).replace("<", "\\u003c")


def montar_painel(ranking: pd.DataFrame, agora: datetime | None = None) -> str:
    agora = agora or datetime.now()
    html = _TEMPLATE.read_text(encoding="utf-8")
    substituicoes = {
        "__DADOS_JSON__": _para_json_seguro(ranking),
        "__ATUALIZADO_EM__": f"{agora:%d/%m/%Y às %H:%M}",
        "__VERSAO__": VERSAO,
    }
    for marcador, valor in substituicoes.items():
        html = html.replace(marcador, valor)
    return html


def salvar_painel(ranking: pd.DataFrame, caminho: Path) -> Path:
    caminho.write_text(montar_painel(ranking), encoding="utf-8")
    return caminho
