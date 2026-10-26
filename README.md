# HIVE

Plataforma web que reúne, em um só lugar, os hackathons e eventos de tecnologia
realizados no Ceará.

Projeto Integrador (TCC) do curso de Ciência da Computação da Unifor,
desenvolvido por Leticia, Lucas e João.

## Problema

Os eventos de tecnologia do Ceará são divulgados em lugares diferentes:
plataformas de ingresso, sites de instituições, notícias e redes sociais.
O HIVE junta essas fontes combinando coleta automática com cadastro
colaborativo moderado.

## Escopo

- **Incluído:** hackathons e eventos de tecnologia (meetups, conferências,
  workshops) que acontecem no Ceará.
- **Fora do escopo:** bolsas, editais e eventos de outros estados.

## Como os eventos chegam ao HIVE

1. Coleta em páginas públicas de plataformas de eventos.
2. Feeds RSS e iCal de sites e calendários institucionais.
3. Radar de notícias, que gera candidatos para revisão manual.
4. Formulário para organizadores cadastrarem eventos, com aprovação manual.

## Estrutura do repositório

```
crawler/            Aranha: descobre URLs de eventos (Python)
  fontes/           um módulo por fonte de busca
scraper/            coleta de eventos (Python)
  fontes/           um módulo por fonte
api/                back-end (a definir)
web/                página que lista os eventos
data/               resultado da coleta enquanto não há banco de dados
tests/              demonstração da base da coleta
.github/workflows/  automações (coleta diária)
```

## Preparando o ambiente

Requisitos: Python 3.14 e Git. Os comandos abaixo são para o PowerShell (Windows).

```powershell
# Criar o ambiente virtual
py -3.14 -m venv .venv

# Ativar o ambiente virtual
.venv\Scripts\Activate.ps1

# Instalar as dependências
pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação, libere scripts locais para o seu usuário:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

A busca no Google (`crawler/fontes/google_search.py`) usa a API do
[Serper](https://serper.dev). Crie o arquivo `.env` a partir do modelo e
preencha `SERPER_API_KEY`:

```powershell
Copy-Item .env.example .env
```

## Rodando a demo

Com o ambiente virtual ativado, na raiz do projeto:

```powershell
# 1. Coletar os eventos (salva em data/eventos.json)
python -m scraper.main

# 2. Servir a página
python -m http.server 8000
```

Depois abra http://localhost:8000/web/ no navegador.

A página lê o `data/eventos.json`, então ela precisa ser aberta pelo servidor:
abrindo o `index.html` direto do disco o navegador bloqueia a leitura do arquivo.

Os comandos usam `python -m` e devem rodar a partir da raiz, porque o código
importa os módulos como `scraper.modelo`, `scraper.rede` etc. Rodar
`python scraper/main.py` dá `ModuleNotFoundError`.

Outros comandos úteis:

```powershell
# Ver os eventos de uma fonte só, sem salvar nada (sympla, gdg, doity, unifor)
python -m scraper.fontes.sympla

# Demonstração da base da coleta (não altera a pasta data/)
python -m tests.demonstracao
```

## Status

Em desenvolvimento. Já funciona:

- coleta de eventos de tecnologia no Ceará em quatro fontes: Sympla, GDG
  Fortaleza, Doity e agenda da Unifor (`scraper/fontes/`);
- deduplicação por URL e por título parecido no mesmo dia (o mesmo evento
  divulgado em dois sites);
- página web listando os eventos, com busca e filtro por tipo.
