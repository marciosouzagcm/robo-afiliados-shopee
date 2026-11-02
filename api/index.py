"""API HTTP do rastreador de afiliados, compatível com Vercel Functions."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Query

from afiliados.config import PAGINAS_PADRAO, CredenciaisShopee, carregar_credenciais
from afiliados.consolidador import consolidar
from afiliados.shopee import ColetorShopee

log = logging.getLogger(__name__)
app = FastAPI(
    title="Robô Rastreador de Afiliados — Shopee",
    description="Consulta e consolida ofertas da Shopee Affiliate Open API.",
    version="1.0.0",
)


@app.get("/api/rastrear")
def rastrear(
    paginas: int = Query(default=PAGINAS_PADRAO, ge=1, le=5),
) -> dict:
    """Retorna em JSON o ranking consolidado; não grava arquivos em disco."""
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
        ranking = consolidar(produtos)
        resultados = ranking.to_dict(orient="records")
    except Exception as erro:
        log.exception("Falha ao rastrear ofertas da Shopee")
        raise HTTPException(
            status_code=502,
            detail="Não foi possível consultar e consolidar as ofertas da Shopee.",
        ) from erro

    return {
        "total": len(resultados),
        "paginas_solicitadas": paginas,
        "resultados": resultados,
    }