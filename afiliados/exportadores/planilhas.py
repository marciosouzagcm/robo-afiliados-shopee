"""
Exportação em planilha.

  * CSV  — pensado para abrir direto no Excel brasileiro: separador `;`,
           vírgula decimal, UTF-8 com BOM e cabeçalhos legíveis.
  * XLSX — planilha formatada: cabeçalho colorido, filtros, painel congelado,
           moeda em R$, links clicáveis e barras de dados na comissão.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.formatting.rule import DataBarRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# coluna interna -> cabeçalho exibido ao usuário (a ordem é a das colunas)
CABECALHOS = {
    "posicao": "Nº",
    "titulo": "Produto",
    "loja": "Loja",
    "preco": "Preço (R$)",
    "comissao_pct": "Comissão (%)",
    "comissao_estimada": "Comissão estimada (R$)",
    "vendas": "Vendas",
    "avaliacao": "Avaliação",
    "desconto_pct": "Desconto (%)",
    "url": "Link de afiliado",
    "imagem_url": "Link da imagem",
}

_COR_CABECALHO = "EE4D2D"
_COR_LINHA_ALTERNADA = "FFF4F1"
_COR_DESTAQUE = "FFE3DC"


# --------------------------------------------------------------------------- #
# CSV
# --------------------------------------------------------------------------- #


def salvar_csv(ranking: pd.DataFrame, caminho: Path) -> Path:
    """Grava o CSV no padrão brasileiro (`;` e vírgula decimal)."""
    legivel = ranking[list(CABECALHOS)].rename(columns=CABECALHOS)
    legivel.to_csv(caminho, index=False, sep=";", decimal=",", encoding="utf-8-sig", float_format="%.2f")
    return caminho


# --------------------------------------------------------------------------- #
# XLSX
# --------------------------------------------------------------------------- #

# cabeçalho -> (largura da coluna, formato numérico, alinhamento horizontal)
_FORMATO_COLUNAS = {
    "posicao": (6, "0", "center"),
    "titulo": (58, None, "left"),
    "loja": (24, None, "left"),
    "preco": (14, '"R$" #,##0.00', "right"),
    "comissao_pct": (14, '0.00"%"', "right"),
    "comissao_estimada": (22, '"R$" #,##0.00', "right"),
    "vendas": (12, "#,##0", "right"),
    "avaliacao": (11, "0.0", "center"),
    "desconto_pct": (12, '0.0"%"', "right"),
    "url": (18, None, "center"),
    "imagem_url": (16, None, "center"),
}
_COLUNAS_COM_LINK = {"url": "Abrir produto", "imagem_url": "Ver imagem"}


def salvar_xlsx(ranking: pd.DataFrame, caminho: Path) -> Path:
    """Grava uma planilha Excel formatada com o ranking."""
    planilha = Workbook()
    aba = planilha.active
    aba.title = "Ranking Shopee"

    colunas = list(CABECALHOS)
    _escrever_cabecalho(aba, colunas)
    for numero_linha, (_, produto) in enumerate(ranking.iterrows(), start=2):
        _escrever_linha(aba, numero_linha, colunas, produto)

    _aplicar_ajustes_gerais(aba, colunas, total_linhas=len(ranking))
    planilha.save(caminho)
    return caminho


def _escrever_cabecalho(aba, colunas: list[str]) -> None:
    borda = Side(style="thin", color="D9D9D9")
    for indice, coluna in enumerate(colunas, start=1):
        celula = aba.cell(row=1, column=indice, value=CABECALHOS[coluna])
        celula.font = Font(bold=True, color="FFFFFF", size=11)
        celula.fill = PatternFill("solid", fgColor=_COR_CABECALHO)
        celula.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        celula.border = Border(bottom=borda)
    aba.row_dimensions[1].height = 32


def _escrever_linha(aba, numero_linha: int, colunas: list[str], produto: pd.Series) -> None:
    for indice, coluna in enumerate(colunas, start=1):
        _, formato, alinhamento = _FORMATO_COLUNAS[coluna]
        valor = produto[coluna]
        celula = aba.cell(row=numero_linha, column=indice)

        if coluna in _COLUNAS_COM_LINK:
            celula.value = _COLUNAS_COM_LINK[coluna]
            celula.hyperlink = str(valor)[:2000]  # limite do Excel para links
            celula.font = Font(color="0563C1", underline="single")
        else:
            celula.value = valor.item() if hasattr(valor, "item") else valor
        if formato:
            celula.number_format = formato

        celula.alignment = Alignment(
            horizontal=alinhamento, vertical="center", wrap_text=(coluna == "titulo")
        )
        if numero_linha % 2 == 1:
            celula.fill = PatternFill("solid", fgColor=_COR_LINHA_ALTERNADA)

        if coluna == "comissao_estimada":
            celula.font = Font(bold=True, color="B42318")

    aba.row_dimensions[numero_linha].height = 34


def _aplicar_ajustes_gerais(aba, colunas: list[str], total_linhas: int) -> None:
    for indice, coluna in enumerate(colunas, start=1):
        aba.column_dimensions[get_column_letter(indice)].width = _FORMATO_COLUNAS[coluna][0]

    aba.freeze_panes = "C2"  # mantém Nº e Produto visíveis ao rolar
    ultima_coluna = get_column_letter(len(colunas))
    aba.auto_filter.ref = f"A1:{ultima_coluna}{max(total_linhas + 1, 2)}"

    if total_linhas:
        letra = get_column_letter(colunas.index("comissao_estimada") + 1)
        aba.conditional_formatting.add(
            f"{letra}2:{letra}{total_linhas + 1}",
            DataBarRule(start_type="min", end_type="max", color=_COR_DESTAQUE),
        )
