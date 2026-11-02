"""Orquestrador: coleta → consolidação → exportação."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from afiliados.config import (
    NOME_CSV,
    NOME_MARKDOWN,
    NOME_PAINEL,
    NOME_XLSX,
    CredenciaisShopee,
)
from afiliados.consolidador import consolidar
from afiliados.exportadores import salvar_csv, salvar_markdown, salvar_painel, salvar_xlsx
from afiliados.shopee import ColetorShopee


@dataclass(frozen=True)
class ArquivosGerados:
    csv: Path
    xlsx: Path
    markdown: Path
    painel: Path


class RoboShopee:
    """Coordena as etapas; as regras de cada etapa ficam em seus próprios módulos."""

    def __init__(self, coletor: ColetorShopee) -> None:
        self.coletor = coletor
        self.log = logging.getLogger("RoboShopee")

    @classmethod
    def a_partir_das_credenciais(cls, credenciais: CredenciaisShopee) -> RoboShopee:
        return cls(ColetorShopee(credenciais))

    def executar(self, pasta_saida: Path, paginas: int) -> tuple[pd.DataFrame, ArquivosGerados]:
        produtos = self.coletor.coletar(paginas)
        ranking = consolidar(produtos)
        arquivos = self._exportar(ranking, pasta_saida)
        self.log.info("Concluído: %d produtos. Abra %s para ver o painel.", len(ranking), arquivos.painel)
        return ranking, arquivos

    @staticmethod
    def _exportar(ranking: pd.DataFrame, pasta_saida: Path) -> ArquivosGerados:
        pasta_saida.mkdir(parents=True, exist_ok=True)
        return ArquivosGerados(
            csv=salvar_csv(ranking, pasta_saida / NOME_CSV),
            xlsx=salvar_xlsx(ranking, pasta_saida / NOME_XLSX),
            markdown=salvar_markdown(ranking, pasta_saida / NOME_MARKDOWN),
            painel=salvar_painel(ranking, pasta_saida / NOME_PAINEL),
        )
