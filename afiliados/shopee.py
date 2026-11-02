"""
Coletor da Shopee — Affiliate Open API (GraphQL).

Consulta `productOfferV2` ordenada por itens vendidos. A autenticação é uma
assinatura SHA256 de: AppID + timestamp + corpo da requisição + Secret.

A consulta "completa" pede campos extras (loja, avaliação, desconto). Se a API
recusar algum deles, o coletor recua automaticamente para a consulta "básica",
que contém apenas os campos essenciais.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time

import requests

from afiliados.config import (
    PAUSA_ENTRE_REQUISICOES,
    PRODUTOS_POR_PAGINA,
    TIMEOUT_SEGUNDOS,
    CredenciaisShopee,
)
from afiliados.modelos import Produto
from afiliados.utilitarios import criar_sessao_http, para_float, para_int

ENDPOINT = "https://open-api.affiliate.shopee.com.br/graphql"

_CAMPOS_BASICOS = "productName commissionRate priceMin priceMax sales imageUrl productLink offerLink"
_CAMPOS_EXTRAS = "shopName ratingStar priceDiscountRate"

_MODELO_CONSULTA = """
query ($page: Int!, $limit: Int!) {{
  productOfferV2(listType: 0, sortType: 2, page: $page, limit: $limit) {{
    nodes {{ {campos} }}
  }}
}}
"""
CONSULTA_COMPLETA = _MODELO_CONSULTA.format(campos=f"{_CAMPOS_BASICOS} {_CAMPOS_EXTRAS}")
CONSULTA_BASICA = _MODELO_CONSULTA.format(campos=_CAMPOS_BASICOS)


class ColetorShopee:
    """Busca os produtos mais vendidos da Shopee e os converte em `Produto`."""

    def __init__(self, credenciais: CredenciaisShopee, sessao: requests.Session | None = None) -> None:
        self.credenciais = credenciais
        self.sessao = sessao or criar_sessao_http()
        self.log = logging.getLogger("Shopee")
        self._consulta = CONSULTA_COMPLETA

    # -- API pública --------------------------------------------------------- #

    def coletar(self, paginas: int) -> list[Produto]:
        """Coleta até `paginas` páginas. Nunca lança exceção: falhas viram log."""
        if not self.credenciais.completas:
            self.log.error(
                "Credenciais ausentes. Preencha SHOPEE_AFFILIATE_APP_ID e "
                "SHOPEE_AFFILIATE_SECRET no arquivo .env."
            )
            return []

        produtos: list[Produto] = []
        for pagina in range(1, paginas + 1):
            self.log.info("Buscando página %d de %d...", pagina, paginas)
            itens = self._buscar_pagina(pagina)
            if not itens:
                break  # fim dos resultados (ou falha já registrada)
            produtos += [self._converter(item) for item in itens]
            time.sleep(PAUSA_ENTRE_REQUISICOES)

        self.log.info("%d produtos coletados.", len(produtos))
        return produtos

    # -- requisição ---------------------------------------------------------- #

    def _buscar_pagina(self, pagina: int) -> list[dict]:
        resposta = self._executar_consulta(pagina)

        # Campos extras recusados? Recua uma única vez para a consulta básica.
        if self._consulta is CONSULTA_COMPLETA and self._tem_erros_graphql(resposta):
            self.log.warning("A API recusou os campos extras; usando a consulta básica.")
            self._consulta = CONSULTA_BASICA
            resposta = self._executar_consulta(pagina)

        if not isinstance(resposta, dict):
            return []
        if resposta.get("errors"):
            self.log.error("A API retornou erros: %s", resposta["errors"])
            return []
        return ((resposta.get("data") or {}).get("productOfferV2") or {}).get("nodes") or []

    def _executar_consulta(self, pagina: int) -> dict | None:
        corpo = json.dumps(
            {"query": self._consulta, "variables": {"page": pagina, "limit": PRODUTOS_POR_PAGINA}},
            separators=(",", ":"),
        )
        try:
            resposta = self.sessao.post(
                ENDPOINT, data=corpo, headers=self._cabecalhos_assinados(corpo), timeout=TIMEOUT_SEGUNDOS
            )
            resposta.raise_for_status()
            return resposta.json()
        except (requests.RequestException, ValueError) as erro:
            self.log.error("Falha na página %d: %s", pagina, erro)
            return None

    def _cabecalhos_assinados(self, corpo: str) -> dict[str, str]:
        timestamp = str(int(time.time()))
        base = f"{self.credenciais.app_id}{timestamp}{corpo}{self.credenciais.secret}"
        assinatura = hashlib.sha256(base.encode()).hexdigest()
        return {
            "Authorization": (
                f"SHA256 Credential={self.credenciais.app_id}, "
                f"Timestamp={timestamp}, Signature={assinatura}"
            ),
            "Content-Type": "application/json",
        }

    @staticmethod
    def _tem_erros_graphql(resposta: dict | None) -> bool:
        return isinstance(resposta, dict) and bool(resposta.get("errors"))

    # -- conversão ----------------------------------------------------------- #

    @staticmethod
    def _converter(item: dict) -> Produto:
        taxa = para_float(item.get("commissionRate"))
        comissao_pct = taxa * 100 if taxa <= 1 else taxa  # a API costuma enviar fração (0.08)

        preco_min = para_float(item.get("priceMin"))
        preco_max = para_float(item.get("priceMax"))
        preco_medio = (preco_min + preco_max) / 2 if preco_max else preco_min

        desconto = para_float(item.get("priceDiscountRate"))
        desconto_pct = desconto * 100 if 0 < desconto <= 1 else desconto

        return Produto(
            titulo=str(item.get("productName") or "Sem título").strip(),
            loja=str(item.get("shopName") or "").strip(),
            preco=round(preco_medio, 2),
            comissao_pct=round(comissao_pct, 2),
            vendas=para_int(item.get("sales")),
            avaliacao=round(para_float(item.get("ratingStar")), 2),
            desconto_pct=round(desconto_pct, 1),
            url=item.get("offerLink") or item.get("productLink") or "",
            imagem_url=item.get("imageUrl") or "",
        )
