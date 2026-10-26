"""Fonte GDG: eventos dos Google Developer Groups do Ceará.

A página do grupo (gdg.community.dev/<grupo>/) é feita em Next.js e traz os
próximos eventos no bloco __NEXT_DATA__. A página de cada evento tem JSON-LD
com horário e endereço, mas sem url e sem imagem, que pegamos da listagem.

robots.txt: proíbe /api/ (não usamos) e pede 2s entre requisições
(Crawl-delay), configurado em scraper/rede.py.

Teste isolado: python -m scraper.fontes.gdg
"""
import json
import re

from scraper import jsonld
from scraper.modelo import Evento, agora
from scraper.rede import baixar

# Endereço do grupo na plataforma -> nome mostrado no site.
# Em 25/10/2026, Fortaleza era o único GDG do Ceará na plataforma.
GRUPOS = {"gdg-fortaleza": "GDG Fortaleza"}


def proximos_eventos(grupo: str) -> list[dict]:
    pagina = baixar(f"https://gdg.community.dev/{grupo}/").text
    dados = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', pagina, re.S).group(1)
    return json.loads(dados)["props"]["pageProps"]["prerenderData"]["upcomingEvents"]["results"]


def coletar() -> list[Evento]:
    eventos = []
    for grupo, nome in GRUPOS.items():
        for item in proximos_eventos(grupo):
            for dados in jsonld.eventos_no_html(baixar(item["url"]).text):
                dados["url"] = dados.get("url") or item["url"]
                dados["image"] = dados.get("image") or item.get("cropped_banner_url")
                evento = jsonld.converter(dados, "gdg")
                evento.organizador = nome
                if evento.tipo == "outro":
                    evento.tipo = "meetup"  # evento de comunidade sem tipo no título
                termino = evento.fim or evento.inicio
                if termino and termino >= agora():
                    eventos.append(evento)
    return eventos


if __name__ == "__main__":
    for evento in coletar():
        print(f"{evento.inicio:%d/%m %H:%M}  {evento.tipo:<11}  {evento.local}  {evento.titulo}")
