#!/usr/bin/env python3
"""Ponto de entrada: `python main.py [--paginas N] [--saida PASTA] [--abrir]`."""

from __future__ import annotations

import argparse
import webbrowser
from pathlib import Path

from afiliados.config import PAGINAS_PADRAO, PASTA_SAIDA_PADRAO, carregar_credenciais
from afiliados.robo import RoboShopee
from afiliados.utilitarios import configurar_logs


def ler_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Robô Rastreador de Afiliados — Shopee.")
    parser.add_argument(
        "--paginas", type=int, default=PAGINAS_PADRAO,
        help=f"páginas de produtos a buscar, 20 por página (padrão: {PAGINAS_PADRAO})",
    )
    parser.add_argument(
        "--saida", type=Path, default=PASTA_SAIDA_PADRAO,
        help=f"pasta de saída dos arquivos (padrão: {PASTA_SAIDA_PADRAO})",
    )
    parser.add_argument("--abrir", action="store_true", help="abre o painel no navegador ao terminar")
    argumentos = parser.parse_args()
    if argumentos.paginas < 1:
        parser.error("--paginas deve ser pelo menos 1")
    return argumentos


def main() -> None:
    argumentos = ler_argumentos()
    configurar_logs()

    robo = RoboShopee.a_partir_das_credenciais(carregar_credenciais())
    _, arquivos = robo.executar(argumentos.saida, argumentos.paginas)

    if argumentos.abrir:
        webbrowser.open(arquivos.painel.resolve().as_uri())


if __name__ == "__main__":
    main()
