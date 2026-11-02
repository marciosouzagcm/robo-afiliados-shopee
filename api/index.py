"""API HTTP do rastreador de afiliados, compatível com Vercel Functions."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from afiliados.config import PAGINAS_PADRAO, CredenciaisShopee, carregar_credenciais
from afiliados.consolidador import consolidar
from afiliados.exportadores.painel import montar_painel
from afiliados.shopee import ColetorShopee

log = logging.getLogger(__name__)
app = FastAPI(
    title="Robô Rastreador de Afiliados — Shopee",
    description="Painel visual e API JSON para ofertas da Shopee Affiliate Open API.",
    version="1.0.0",
)


def _obter_ranking(paginas: int):
    credenciais: CredenciaisShopee = carregar_credenciais()
    if not credenciais.completas:
        raise HTTPException(
            status_code=503,
            detail=(
                "Credenciais ausentes. Configure SHOPEE_AFFILIATE_APP_ID e "
                "SHOPEE_AFFILIATE_SECRET nas variáveis de ambiente da Vercel."
            ),
        )

    try:
        produtos = ColetorShopee(credenciais).coletar(paginas)
        return consolidar(produtos)
    except Exception as erro:
        log.exception("Falha ao rastrear ofertas da Shopee")
        raise HTTPException(
            status_code=502,
            detail="Não foi possível consultar e consolidar as ofertas da Shopee.",
        ) from erro


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def inicio(paginas: int = Query(default=PAGINAS_PADRAO, ge=1, le=5)) -> HTMLResponse:
    """Exibe o painel visual com busca, filtros, ordenação e cartões de produtos."""
    return HTMLResponse(content=montar_painel(_obter_ranking(paginas)))


@app.get("/api/rastrear")
@app.get("/rastrear", include_in_schema=False)
def rastrear(
    paginas: int = Query(default=PAGINAS_PADRAO, ge=1, le=5),
) -> dict:
    """Retorna em JSON o ranking consolidado; não grava arquivos em disco."""
    ranking = _obter_ranking(paginas)
    resultados = ranking.to_dict(orient="records")

    return {
        "total": len(resultados),
        "paginas_solicitadas": paginas,
        "resultados": resultados,
    }