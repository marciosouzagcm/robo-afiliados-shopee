"""
Configuração da aplicação.

  * Lê as credenciais da Shopee no arquivo `.env` (ou nas variáveis de ambiente).
  * Reúne os parâmetros fixos de execução.

Nenhuma credencial é gravada no código-fonte.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# --------------------------------------------------------------------------- #
# Parâmetros fixos
# --------------------------------------------------------------------------- #

TIMEOUT_SEGUNDOS = 20
PAUSA_ENTRE_REQUISICOES = 0.5   # segundos; respeita o limite de taxa da API
PRODUTOS_POR_PAGINA = 20
PAGINAS_PADRAO = 5              # 5 páginas × 20 = até 100 produtos
LIMITE_NO_MARKDOWN = 100

PASTA_SAIDA_PADRAO = Path("saida")
NOME_CSV = "afiliados_shopee.csv"
NOME_XLSX = "afiliados_shopee.xlsx"
NOME_PAINEL = "painel.html"
NOME_MARKDOWN = "DOCUMENTACAO_AFILIADOS.md"


# --------------------------------------------------------------------------- #
# Credenciais
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CredenciaisShopee:
    """AppID e Secret da Shopee Affiliate Open API."""

    app_id: str
    secret: str

    @property
    def completas(self) -> bool:
        return bool(self.app_id and self.secret)


def carregar_credenciais(caminho_env: Path | None = None) -> CredenciaisShopee:
    """
    Lê o `.env` e devolve as credenciais.

    Procura o arquivo na pasta atual e, depois, na raiz do projeto. Variáveis
    já definidas no sistema operacional têm prioridade sobre o arquivo.
    """
    raiz_projeto = Path(__file__).resolve().parent.parent
    candidatos = [caminho_env] if caminho_env else [Path.cwd() / ".env", raiz_projeto / ".env"]
    for arquivo in candidatos:
        if arquivo and arquivo.is_file():
            load_dotenv(arquivo, override=False)
            break

    return CredenciaisShopee(
        app_id=os.getenv("SHOPEE_AFFILIATE_APP_ID", "").strip(),
        secret=os.getenv("SHOPEE_AFFILIATE_SECRET", "").strip(),
    )
