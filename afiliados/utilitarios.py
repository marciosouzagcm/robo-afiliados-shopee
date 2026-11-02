"""Funções auxiliares sem dependência do domínio: conversões, HTTP e logs."""

from __future__ import annotations

import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from afiliados import VERSAO


def para_float(valor, padrao: float = 0.0) -> float:
    """
    Converte para float sem lançar exceção.

    Aceita números, 'R$ 1.234,56', '7,5%' e '12.5'. Retorna `padrao` se inválido.
    """
    if valor is None:
        return padrao
    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).replace("R$", "").replace("%", "").strip()
    if "," in texto and "." in texto:  # formato brasileiro: 1.234,56
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return padrao


def para_int(valor, padrao: int = 0) -> int:
    """Versão inteira de `para_float`."""
    return int(para_float(valor, padrao))


def criar_sessao_http() -> requests.Session:
    """Sessão HTTP com novas tentativas automáticas para falhas transitórias."""
    politica = Retry(
        total=3,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
    )
    sessao = requests.Session()
    sessao.mount("https://", HTTPAdapter(max_retries=politica))
    sessao.headers["User-Agent"] = f"RoboAfiliados/{VERSAO}"
    return sessao


def configurar_logs(nivel: int = logging.INFO) -> None:
    """Formato único de log para toda a aplicação."""
    logging.basicConfig(
        level=nivel,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
