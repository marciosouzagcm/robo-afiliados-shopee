"""Gera o arquivo `DOCUMENTACAO_AFILIADOS.md` com o ranking e as imagens."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from afiliados import VERSAO
from afiliados.config import LIMITE_NO_MARKDOWN

_CABECALHO_TABELA = (
    "| Nº | Imagem | Produto | Loja | Preço (R$) | Comissão (%) | Comissão Est. (R$) | Vendas |\n"
    "|--:|:------:|---------|------|-----------:|-------------:|-------------------:|-------:|"
)

_RODAPE = """## 🛠️ Como atualizar

```bash
python main.py
```

Consulte o `README.md` para o passo a passo completo. Para uma visualização
interativa, abra o arquivo `painel.html` no navegador.

> **Aviso:** a comissão estimada é uma projeção (preço médio × percentual da
> oferta). O ganho real depende das regras do programa de afiliados da Shopee.
"""


def _sanitizar(texto: str) -> str:
    """Impede que títulos quebrem a tabela Markdown ou injetem HTML."""
    texto = re.sub(r"\s+", " ", str(texto)).strip()
    return texto.replace("|", "/").replace("<", "&lt;").replace(">", "&gt;")


def _linha_da_tabela(produto: pd.Series) -> str:
    titulo = _sanitizar(produto["titulo"])[:90]
    return (
        f"| {produto['posicao']} "
        f'| <img src="{produto["imagem_url"]}" width="60" /> '
        f"| [{titulo}]({produto['url']}) "
        f"| {_sanitizar(produto['loja']) or '—'} "
        f"| {produto['preco']:.2f} | {produto['comissao_pct']:.2f}% "
        f"| **{produto['comissao_estimada']:.2f}** | {int(produto['vendas'])} |"
    )


def montar_markdown(ranking: pd.DataFrame, agora: datetime | None = None) -> str:
    """Devolve o conteúdo completo do documento."""
    agora = agora or datetime.now()
    linhas = [
        "# 📊 Robô Rastreador de Afiliados — Shopee",
        "",
        f"**Última atualização:** {agora:%d/%m/%Y às %H:%M:%S}  ",
        f"**Versão da aplicação:** {VERSAO}  ",
        f"**Total de produtos consolidados:** {len(ranking)}  ",
        "**Ordenação:** maior comissão estimada (R$) e, no empate, maior volume de vendas",
        "",
        "## 🏆 Ranking",
        "",
    ]

    if ranking.empty:
        linhas.append("_Nenhum produto coletado. Verifique o `.env` e os logs de execução._")
    else:
        linhas.append(_CABECALHO_TABELA)
        linhas += [_linha_da_tabela(p) for _, p in ranking.head(LIMITE_NO_MARKDOWN).iterrows()]

    linhas += ["", "---", "", _RODAPE]
    return "\n".join(linhas)


def salvar_markdown(ranking: pd.DataFrame, caminho: Path) -> Path:
    caminho.write_text(montar_markdown(ranking), encoding="utf-8")
    return caminho
