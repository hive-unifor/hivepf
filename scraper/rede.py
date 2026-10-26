"""Requisições HTTP com as regras de coleta do projeto.

Toda fonte deve baixar páginas e feeds por aqui (inclusive RSS: baixe com
baixar() e passe o conteúdo para o feedparser). Assim as regras valem para
todas as fontes sem precisar repeti-las:
- User-Agent identificando o projeto;
- pausa mínima entre requisições ao mesmo site;
- tempo limite, para um site travado não segurar a coleta inteira.
"""
import time
from urllib.parse import urlparse

import requests

USER_AGENT = "HIVE-TCC/0.1 (projeto academico)"
PAUSA_MINIMA = 1.0  # segundos entre requisições ao mesmo site
TIMEOUT = 20  # segundos esperando o site responder

# Sites que pedem uma pausa maior no robots.txt (Crawl-delay).
PAUSA_POR_SITE = {
    "gdg.community.dev": 2.0,
}

# A sessão guarda o cabeçalho e reaproveita a conexão com cada site.
_sessao = requests.Session()
_sessao.headers["User-Agent"] = USER_AGENT

# Momento da última requisição a cada site, por exemplo {"www.sympla.com.br": 1234.5}.
_ultima_requisicao: dict[str, float] = {}


def baixar(url: str, **kwargs) -> requests.Response:
    """Faz um GET respeitando a pausa por site.

    Os kwargs vão direto para requests (ex.: params={"q": "hackathon"}).
    Lança exceção se o site não responder ou devolver erro (404, 500...).
    """
    site = urlparse(url).netloc

    # monotonic() é um relógio que só anda para frente: ajustes no relógio
    # do Windows durante a coleta não bagunçam a conta da pausa.
    ultima = _ultima_requisicao.get(site)
    if ultima is not None:
        pausa = PAUSA_POR_SITE.get(site, PAUSA_MINIMA)
        espera = pausa - (time.monotonic() - ultima)
        if espera > 0:
            time.sleep(espera)

    try:
        resposta = _sessao.get(url, timeout=TIMEOUT, **kwargs)
    finally:
        # Registra mesmo se der erro: uma falha também conta como requisição ao site.
        _ultima_requisicao[site] = time.monotonic()

    resposta.raise_for_status()
    return resposta
