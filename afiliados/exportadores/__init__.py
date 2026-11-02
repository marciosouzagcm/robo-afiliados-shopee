"""Exportadores: transformam o ranking em CSV, Excel, Markdown e painel web."""

from afiliados.exportadores.markdown import salvar_markdown
from afiliados.exportadores.painel import salvar_painel
from afiliados.exportadores.planilhas import salvar_csv, salvar_xlsx

__all__ = ["salvar_csv", "salvar_xlsx", "salvar_markdown", "salvar_painel"]
