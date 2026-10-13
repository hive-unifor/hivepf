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
web/                front-end (a definir)
data/               resultado da coleta enquanto não há banco de dados
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

## Status

Em desenvolvimento: estrutura inicial do projeto.
