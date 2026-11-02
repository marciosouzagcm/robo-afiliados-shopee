"""Limpa, remove duplicatas e ordena o ranking de produtos."""

from __future__ import annotations

import pandas as pd

from afiliados.modelos import Produto

COLUNAS = [
    "posicao", "titulo", "loja", "preco", "comissao_pct", "comissao_estimada",
    "vendas", "avaliacao", "desconto_pct", "url", "imagem_url",
]


def consolidar(produtos: list[Produto]) -> pd.DataFrame:
    """
    Regras aplicadas:
      * descarta itens sem preço, sem link ou sem imagem (a imagem é obrigatória);
      * remove duplicatas (mesmo link);
      * ordena por comissão estimada (R$) e, no empate, por vendas — ambos decrescentes;
      * numera o ranking a partir de 1 na coluna `posicao`.
    """
    if not produtos:
        return pd.DataFrame(columns=COLUNAS)

    tabela = pd.DataFrame([p.para_dicionario() for p in produtos])
    valido = (
        (tabela["preco"] > 0)
        & (tabela["url"].str.strip() != "")
        & (tabela["imagem_url"].str.strip() != "")
    )
    tabela = (
        tabela[valido]
        .drop_duplicates(subset=["url"])
        .sort_values(["comissao_estimada", "vendas"], ascending=False)
        .reset_index(drop=True)
    )
    tabela.insert(0, "posicao", tabela.index + 1)
    return tabela[COLUNAS]
