"""Modelo de domínio: um produto da Shopee já normalizado (valores em R$)."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Produto:
    titulo: str
    loja: str
    preco: float            # preço médio entre o mínimo e o máximo da oferta
    comissao_pct: float     # comissão do afiliado, em %
    vendas: int
    avaliacao: float        # nota média (0 quando não informada)
    desconto_pct: float     # desconto atual, em % (0 quando não informado)
    url: str                # link de afiliado (ou link do produto)
    imagem_url: str

    @property
    def comissao_estimada(self) -> float:
        """Ganho estimado por venda: preço × (comissão % ÷ 100)."""
        return round(self.preco * self.comissao_pct / 100.0, 2)

    def para_dicionario(self) -> dict:
        """Dados do produto + comissão estimada, prontos para virar linha de tabela."""
        return {**asdict(self), "comissao_estimada": self.comissao_estimada}
