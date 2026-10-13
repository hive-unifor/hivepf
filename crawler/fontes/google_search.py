"""Aranha: descobre URLs de eventos pesquisando no Google pela API do Serper.

A Aranha não extrai dados das páginas: só lista as URLs dos resultados
orgânicos, para o scraper visitar depois. As requisições passam por
scraper.rede, para seguir as mesmas regras de coleta do projeto.

Uso (na raiz do projeto, com o .venv ativado e SERPER_API_KEY no .env):
    python -m crawler.fontes.google_search

Saída:
- data/urls_descobertas.json  lista de URLs únicas (sobrescrito a cada vez)

Cada palavra-chave gasta um crédito da conta do Serper.
"""
import json
import logging
import os
from pathlib import Path
from urllib.parse import urldefrag, urlparse

from dotenv import load_dotenv

from scraper.rede import baixar

RAIZ = Path(__file__).resolve().parents[2]
ARQUIVO_ENV = RAIZ / ".env"
ARQUIVO_URLS = RAIZ / "data" / "urls_descobertas.json"

ENDPOINT = "https://google.serper.dev/search"
# Google Brasil, resultados em português.
PARAMETROS_FIXOS = {"gl": "br", "hl": "pt-br"}

# Buscas feitas quando o módulo roda sozinho.
PALAVRAS_CHAVE = [
    "hackathon ceará",
    "hackathon fortaleza",
    "evento de tecnologia fortaleza",
    "meetup tecnologia fortaleza",
    "workshop programação fortaleza",
]

# Páginas de redes sociais exigem login e não têm o evento estruturado.
# Subdomínios (ex.: m.facebook.com, br.linkedin.com) também são ignorados.
DOMINIOS_IGNORADOS = ("instagram.com", "facebook.com", "linkedin.com")

log = logging.getLogger("hive")


def obter_chave() -> str:
    """Lê a chave do Serper do .env (ou do ambiente, como no GitHub Actions)."""
    # load_dotenv não sobrescreve variáveis que já existem: no GitHub Actions
    # a chave vem dos secrets e o .env, que nem existe lá, é ignorado.
    load_dotenv(ARQUIVO_ENV)
    chave = os.getenv("SERPER_API_KEY")
    if not chave:
        raise RuntimeError(
            "SERPER_API_KEY não definida: copie .env.example para .env e preencha a chave"
        )
    return chave


def pesquisar(termo: str, chave: str) -> list[str]:
    """Faz uma busca e devolve os links dos resultados orgânicos, na ordem do Google."""
    # A chave vai no cabeçalho, não na URL (?apiKey=...): se o Serper devolver
    # erro, a mensagem da exceção traz a URL completa e vai para o log,
    # e a chave vazaria junto.
    resposta = baixar(
        ENDPOINT,
        params={"q": termo, **PARAMETROS_FIXOS},
        headers={"X-API-KEY": chave},
    )
    # "organic" são os resultados comuns; anúncios, "as pessoas também
    # perguntam" e afins vêm em outras chaves e ficam de fora.
    resultados = resposta.json().get("organic", [])
    return [resultado["link"] for resultado in resultados if resultado.get("link")]


def normalizar(url: str) -> str:
    # Tira o "#trecho", que só aponta para uma parte da mesma página.
    return urldefrag(url.strip()).url


def eh_rede_social(url: str) -> bool:
    dominio = (urlparse(url).hostname or "").lower()
    return any(
        dominio == ignorado or dominio.endswith("." + ignorado)
        for ignorado in DOMINIOS_IGNORADOS
    )


def buscar_urls(palavras_chave: list[str]) -> list[str]:
    """Pesquisa cada palavra-chave e devolve as URLs únicas, sem redes sociais.

    Lança exceção se todas as buscas falharem, para quem chamou não
    sobrescrever um resultado bom com uma lista vazia.
    """
    if not palavras_chave:
        raise ValueError("nenhuma palavra-chave informada")
    chave = obter_chave()

    # Dicionário com a URL como chave: deduplica e mantém a ordem de chegada.
    urls: dict[str, None] = {}
    falhas = 0
    ignoradas = 0

    for termo in palavras_chave:
        # O try fica em volta de cada busca: uma falha não derruba as outras.
        try:
            links = pesquisar(termo, chave)
        except Exception:
            log.exception("google_search: busca %r falhou", termo)
            falhas += 1
            continue

        novas = 0
        for link in links:
            url = normalizar(link)
            if eh_rede_social(url):
                ignoradas += 1
            elif url not in urls:
                urls[url] = None
                novas += 1
        log.info("google_search: %r: %d resultados, %d URLs novas", termo, len(links), novas)

    if falhas == len(palavras_chave):
        raise RuntimeError("nenhuma busca funcionou; veja os erros acima")

    log.info(
        "google_search: %d URLs únicas, %d de redes sociais ignoradas, %d buscas com falha",
        len(urls), ignoradas, falhas,
    )
    return list(urls)


def salvar_urls(urls: list[str]) -> None:
    ARQUIVO_URLS.parent.mkdir(exist_ok=True)
    ARQUIVO_URLS.write_text(
        json.dumps(urls, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info("%d URLs salvas em %s", len(urls), ARQUIVO_URLS)


if __name__ == "__main__":
    from scraper.main import configurar_log

    configurar_log()
    salvar_urls(buscar_urls(PALAVRAS_CHAVE))
