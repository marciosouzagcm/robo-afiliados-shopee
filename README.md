# 📊 Robô Rastreador de Afiliados — Shopee

Robô em Python que consulta a **Shopee Affiliate Open API**, reúne os produtos mais vendidos, estima a **comissão de afiliado em R$** e entrega o resultado em quatro formatos:

| Arquivo (pasta `saida/`) | Para que serve |
|---|---|
| `painel.html` | **Painel web interativo**: cartões com foto, busca, filtros, ordenação e download do recorte filtrado |
| `afiliados_shopee.xlsx` | Planilha Excel formatada (moeda em R$, filtros, links clicáveis, barras de comissão) |
| `afiliados_shopee.csv` | CSV no padrão brasileiro (`;` e vírgula decimal), abre direto no Excel |
| `DOCUMENTACAO_AFILIADOS.md` | Ranking em Markdown com as imagens dos produtos |

O ranking é ordenado pela **maior comissão estimada (R$)** e, em caso de empate, pelo **maior volume de vendas**.

---

## Sumário

1. [Como funciona](#1-como-funciona)
2. [Estrutura do projeto](#2-estrutura-do-projeto)
3. [Requisitos](#3-requisitos)
4. [Instalação](#4-instalação)
5. [Configuração do `.env`](#5-configuração-do-env)
6. [Execução](#6-execução)
7. [Usando o painel web](#7-usando-o-painel-web)
8. [Colunas das planilhas](#8-colunas-das-planilhas)
9. [Personalização](#9-personalização)
10. [Testes](#10-testes)
11. [Solução de problemas](#11-solução-de-problemas)
12. [Segurança e boas práticas](#12-segurança-e-boas-práticas)
13. [Limitações conhecidas](#13-limitações-conhecidas)
14. [Migração da versão anterior](#14-migração-da-versão-anterior)

---

## 1. Como funciona

```
 .env ─► config ─► ColetorShopee ─► consolidador ─► exportadores ─► saida/
                   (API GraphQL)   (limpa, ordena)  ├─ planilhas  (CSV + XLSX)
                                                    ├─ markdown
                                                    └─ painel     (HTML)
```

Cálculo do ganho por venda:

```
Comissão estimada (R$) = preço médio × (comissão % ÷ 100)
```

O **preço médio** é a média entre o preço mínimo e o máximo da oferta.

Regras do consolidador:

- descarta produtos **sem preço**, **sem link** ou **sem imagem**;
- remove duplicatas (mesmo link);
- numera o ranking a partir de 1.

Se a API recusar os campos extras (loja, avaliação, desconto), o robô recua sozinho para uma consulta básica e segue funcionando — nesse caso essas colunas ficam vazias/zeradas.

## 2. Estrutura do projeto

```
robo_afiliados/
├── main.py                     # ponto de entrada
├── requirements.txt
├── .env                        # SUAS credenciais (não vai para o Git)
├── .env.example                # modelo do .env
├── README.md
├── afiliados/
│   ├── config.py               # leitura do .env e parâmetros fixos
│   ├── modelos.py              # classe Produto (+ cálculo da comissão)
│   ├── shopee.py               # coletor da Shopee (assinatura, consulta, conversão)
│   ├── consolidador.py         # limpeza, deduplicação e ordenação
│   ├── robo.py                 # orquestrador
│   ├── utilitarios.py          # conversões, sessão HTTP com retry, logs
│   ├── exportadores/
│   │   ├── planilhas.py        # CSV e XLSX
│   │   ├── markdown.py         # DOCUMENTACAO_AFILIADOS.md
│   │   └── painel.py           # gera o painel a partir do template
│   └── templates/
│       └── painel.html         # frontend (HTML + CSS + JS, sem dependências)
├── tests/
│   └── test_nucleo.py
└── saida/                      # criada na execução com os arquivos gerados
```

## 3. Requisitos

- **Python 3.10 ou superior** (`python --version`)
- Conexão com a internet
- Conta aprovada no programa de afiliados da Shopee, com **AppID** e **Secret** da Open API

## 4. Instalação

```bash
cd robo_afiliados

python -m venv .venv
source .venv/bin/activate          # Linux / macOS
.venv\Scripts\activate             # Windows

pip install -r requirements.txt
```

## 5. Configuração do `.env`

Crie o arquivo `.env` **na raiz do projeto** (ao lado do `main.py`):

```bash
cp .env.example .env               # Windows: copy .env.example .env
```

```dotenv
SHOPEE_AFFILIATE_APP_ID=seu_app_id
SHOPEE_AFFILIATE_SECRET=seu_secret
```

- Uma variável por linha, sem espaços ao redor do `=`.
- Variáveis já definidas no sistema operacional têm prioridade sobre o arquivo.
- No Windows, confirme que o arquivo se chama exatamente `.env` (e não `.env.txt`).

## 6. Execução

```bash
python main.py
```

| Opção | Descrição | Exemplo |
|---|---|---|
| `--paginas N` | Páginas de produtos a buscar, 20 por página (padrão: 5 → até 100 produtos) | `python main.py --paginas 10` |
| `--saida PASTA` | Pasta onde salvar os arquivos (padrão: `saida`) | `python main.py --saida relatorios` |
| `--abrir` | Abre o painel no navegador ao terminar | `python main.py --abrir` |

Atalho recomendado: **`python main.py --abrir`**.

### Execução agendada (opcional)

Linux/macOS (`cron`), todo dia às 8h:

```cron
0 8 * * * cd /caminho/robo_afiliados && .venv/bin/python main.py >> robo.log 2>&1
```

No Windows, use o **Agendador de Tarefas** com o programa `.venv\Scripts\python.exe`, argumento `main.py` e "Iniciar em" na pasta do projeto.

## 7. Usando o painel web

Abra `saida/painel.html` com duplo clique (ou use `--abrir`). Não precisa de servidor.

- **Indicadores no topo:** quantidade de produtos, maior comissão por venda, comissão média e preço médio — sempre calculados sobre o que está filtrado.
- **Filtros:** busca por produto/loja, loja, faixa de preço, comissão mínima (%) e vendas mínimas.
- **Ordenação:** por comissão (R$ ou %), vendas, avaliação ou preço. Na visão em tabela, clique no cabeçalho da coluna.
- **Dois modos de visualização:** cartões (com foto e botão "Abrir na Shopee") ou tabela compacta. A escolha fica lembrada.
- **Baixar CSV filtrado:** exporta apenas os produtos que estão na tela.
- **Tema claro/escuro:** botão no canto superior (acompanha o tema do sistema por padrão).
- Funciona no celular.

> O painel é um retrato do momento da coleta. Para atualizar, rode `python main.py` de novo e recarregue a página.
> As fotos são carregadas dos servidores da Shopee, então é preciso estar online para vê-las.

## 8. Colunas das planilhas

| Coluna | Significado |
|---|---|
| Nº | Posição no ranking |
| Produto | Título do produto (no XLSX, é um link para o produto) |
| Loja | Nome da loja (vazio se a API não informar) |
| Preço (R$) | Preço médio da oferta |
| Comissão (%) | Percentual de comissão da oferta |
| Comissão estimada (R$) | Preço × comissão % |
| Vendas | Unidades vendidas informadas pela API |
| Avaliação | Nota média (0 se não informada) |
| Desconto (%) | Desconto atual (0 se não informado) |
| Link de afiliado | Link para divulgar e receber a comissão |
| Link da imagem | URL direta da foto do produto |

**Abrindo o CSV no Excel:** dê duplo clique no arquivo — o formato (`;`, vírgula decimal, UTF-8 com BOM) é o esperado pelo Excel em português. Se preferir mais conforto visual, use o `.xlsx`.

## 9. Personalização

| O que mudar | Onde |
|---|---|
| Itens por página, páginas padrão, timeout, pausa entre requisições, nomes dos arquivos | constantes no topo de `afiliados/config.py` |
| Campos pedidos à API | `_CAMPOS_BASICOS` / `_CAMPOS_EXTRAS` em `afiliados/shopee.py` |
| Critério de ordenação do ranking | `afiliados/consolidador.py` |
| Colunas, cores e formatos do Excel | `afiliados/exportadores/planilhas.py` |
| Aparência e comportamento do painel | `afiliados/templates/painel.html` (variáveis de cor no início do `<style>`) |

## 10. Testes

```bash
pytest -q
```

Não usam a internet. Cobrem: cálculo de comissão, consolidação, coletor (inclusive o recuo para a consulta básica e falhas de rede), CSV, XLSX, Markdown e a proteção do painel contra injeção de script.

## 11. Solução de problemas

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `Credenciais ausentes` | Variáveis ausentes, com nome diferente ou `.env` fora da raiz | Confira os nomes na seção 5 e o local do arquivo |
| `A API retornou erros` | AppID/Secret incorretos, ou app sem aprovação | Verifique as credenciais no portal de afiliados |
| `Falha na página N` | Problema de rede ou limite de requisições | Tente novamente; aumente `PAUSA_ENTRE_REQUISICOES` em `config.py` |
| `A API recusou os campos extras` | A API não aceita loja/avaliação/desconto | Aviso informativo: o robô seguiu com a consulta básica |
| Painel sem produtos | Nenhum produto coletado | Veja os avisos no terminal e rode de novo |
| Fotos não aparecem no painel | Sem internet, ou bloqueio do servidor de imagens | Confira a conexão; as demais informações continuam visíveis |
| `ModuleNotFoundError` | Dependências não instaladas / `.venv` inativo | Ative o `.venv` e rode `pip install -r requirements.txt` |
| `PermissionError` ao salvar | O Excel está com o `.xlsx`/`.csv` aberto | Feche o arquivo e rode novamente |

## 12. Segurança e boas práticas

- **Nunca** envie o `.env` ao Git (já está no `.gitignore`).
- Se uma credencial vazar (chat, print, repositório), **revogue e gere outra**.
- As credenciais não aparecem em logs nem nos arquivos gerados.
- O painel monta a página com `textContent` e embute os dados de forma escapada, então títulos de produtos não conseguem executar código. Links que não sejam `http`/`https` são bloqueados.
- Respeite os Termos de Uso e os limites de requisição da Shopee.

## 13. Limitações conhecidas

- A comissão exibida é uma **estimativa** (preço médio × percentual da oferta). O ganho real depende das regras do programa de afiliados.
- A coleta traz os **mais vendidos em geral**, sem filtro por categoria.
- Os campos de loja, avaliação e desconto dependem de a API aceitá-los para a sua conta.
- O formato da API segue a documentação conhecida no desenvolvimento; se a Shopee alterar o formato, o log indicará onde ajustar.

## 14. Migração da versão anterior

A versão 3 é **somente Shopee**. Foram removidos: Mercado Livre, AliExpress, `afiliados/categorias.py`, as variáveis dessas plataformas no `.env` e o arquivo `.ml_tokens.json` (pode apagá-los). Os arquivos agora são gravados em `saida/`, com os nomes `afiliados_shopee.csv` e `afiliados_shopee.xlsx`.
