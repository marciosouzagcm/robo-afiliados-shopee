"""Testes das regras principais (sem acesso à internet)."""

from datetime import datetime
from unittest.mock import MagicMock

import pandas as pd
from openpyxl import load_workbook

from afiliados.config import CredenciaisShopee
from afiliados.consolidador import consolidar
from afiliados.exportadores import salvar_csv, salvar_markdown, salvar_painel, salvar_xlsx
from afiliados.exportadores.markdown import montar_markdown
from afiliados.exportadores.painel import montar_painel
from afiliados.modelos import Produto
from afiliados.shopee import CONSULTA_BASICA, CONSULTA_COMPLETA, ColetorShopee
from afiliados.utilitarios import para_float


def criar_produto(**alteracoes) -> Produto:
    dados = dict(
        titulo="Produto", loja="Loja X", preco=100.0, comissao_pct=10.0, vendas=5,
        avaliacao=4.8, desconto_pct=0.0, url="https://s/1", imagem_url="https://s/1.jpg",
    )
    return Produto(**{**dados, **alteracoes})


# ---------- domínio ---------- #

def test_comissao_estimada_em_reais():
    assert criar_produto(preco=250.0, comissao_pct=8.0).comissao_estimada == 20.0


def test_para_float_formato_brasileiro():
    assert para_float("R$ 1.234,56") == 1234.56
    assert para_float("7,5%") == 7.5
    assert para_float("lixo", padrao=-1) == -1


# ---------- consolidação ---------- #

def test_consolidar_ordena_remove_duplicatas_e_exige_imagem():
    ranking = consolidar([
        criar_produto(url="a", preco=10),               # comissão 1,00
        criar_produto(url="b", preco=500),              # comissão 50,00
        criar_produto(url="b", preco=500),              # duplicata
        criar_produto(url="c", imagem_url=""),          # sem imagem
        criar_produto(url="d", preco=0),                # sem preço
    ])
    assert list(ranking["url"]) == ["b", "a"]
    assert list(ranking["posicao"]) == [1, 2]


def test_consolidar_desempata_por_vendas():
    ranking = consolidar([criar_produto(url="a", vendas=1), criar_produto(url="b", vendas=9)])
    assert list(ranking["url"]) == ["b", "a"]


def test_consolidar_lista_vazia_mantem_colunas():
    assert consolidar([]).empty


# ---------- coletor ---------- #

def test_coletor_sem_credenciais_nao_faz_requisicao():
    sessao = MagicMock()
    assert ColetorShopee(CredenciaisShopee("", ""), sessao=sessao).coletar(2) == []
    sessao.post.assert_not_called()


def test_conversao_fracao_de_comissao_preco_medio_e_extras():
    produto = ColetorShopee._converter({
        "productName": " X ", "commissionRate": "0.08", "priceMin": "10", "priceMax": "30",
        "sales": 7, "offerLink": "https://s/1", "imageUrl": "https://s/1.jpg",
        "shopName": "Loja", "ratingStar": "4.9", "priceDiscountRate": 0.25,
    })
    assert (produto.titulo, produto.comissao_pct, produto.preco, produto.vendas) == ("X", 8.0, 20.0, 7)
    assert (produto.loja, produto.avaliacao, produto.desconto_pct) == ("Loja", 4.9, 25.0)


def _resposta(corpo: dict) -> MagicMock:
    resposta = MagicMock()
    resposta.json.return_value = corpo
    return resposta


def test_recua_para_consulta_basica_quando_campos_extras_sao_recusados():
    sessao = MagicMock()
    item = {"productName": "P", "commissionRate": 0.1, "priceMin": 10, "priceMax": 10,
            "sales": 1, "offerLink": "https://s/1", "imageUrl": "https://s/1.jpg"}
    sessao.post.side_effect = [
        _resposta({"errors": [{"message": "Cannot query field ratingStar"}]}),
        _resposta({"data": {"productOfferV2": {"nodes": [item]}}}),
        _resposta({"data": {"productOfferV2": {"nodes": []}}}),   # página 2 vazia → encerra
    ]
    coletor = ColetorShopee(CredenciaisShopee("id", "segredo"), sessao=sessao)
    produtos = coletor.coletar(paginas=3)

    assert len(produtos) == 1
    assert coletor._consulta is CONSULTA_BASICA
    assert CONSULTA_COMPLETA != CONSULTA_BASICA


def test_falha_de_rede_devolve_lista_vazia():
    import requests
    sessao = MagicMock()
    sessao.post.side_effect = requests.ConnectionError("sem rede")
    assert ColetorShopee(CredenciaisShopee("id", "s"), sessao=sessao).coletar(2) == []


# ---------- exportação ---------- #

def _ranking_exemplo() -> pd.DataFrame:
    return consolidar([
        criar_produto(url="https://s/1", titulo="Fone <b>Bluetooth</b> | Pro", preco=200, comissao_pct=12),
        criar_produto(url="https://s/2", titulo="Garrafa térmica", preco=50, comissao_pct=5, vendas=900),
    ])


def test_csv_no_padrao_brasileiro(tmp_path):
    caminho = salvar_csv(_ranking_exemplo(), tmp_path / "x.csv")
    texto = caminho.read_text(encoding="utf-8-sig")
    assert texto.splitlines()[0].startswith("Nº;Produto;Loja;Preço (R$)")
    assert "24,00" in texto  # 200 × 12% com vírgula decimal


def test_xlsx_formatado(tmp_path):
    caminho = salvar_xlsx(_ranking_exemplo(), tmp_path / "x.xlsx")
    aba = load_workbook(caminho).active
    assert aba["B1"].value == "Produto"
    assert aba["F2"].value == 24.0 and aba["F2"].number_format == '"R$" #,##0.00'
    assert aba["J2"].hyperlink.target == "https://s/1"
    assert aba.freeze_panes == "C2" and aba.auto_filter.ref


def test_markdown_tem_imagem_metadados_e_nao_quebra_tabela():
    texto = montar_markdown(_ranking_exemplo(), agora=datetime(2026, 1, 2, 3, 4, 5))
    assert '<img src="https://s/1.jpg" width="60" />' in texto
    assert "02/01/2026 às 03:04:05" in texto
    assert "<b>" not in texto and "Fone &lt;b&gt;Bluetooth&lt;/b&gt; / Pro" in texto


def test_painel_embute_dados_e_bloqueia_injecao_de_script():
    ranking = consolidar([criar_produto(titulo="</script><script>alert(1)</script>")])
    html = montar_painel(ranking)
    assert "__DADOS_JSON__" not in html and "__ATUALIZADO_EM__" not in html
    assert "</script><script>alert(1)" not in html


def test_salvar_todos_os_formatos(tmp_path):
    ranking = _ranking_exemplo()
    for funcao, nome in [(salvar_csv, "a.csv"), (salvar_xlsx, "a.xlsx"),
                         (salvar_markdown, "a.md"), (salvar_painel, "a.html")]:
        assert funcao(ranking, tmp_path / nome).stat().st_size > 0
