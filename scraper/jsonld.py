"""Lê eventos em JSON-LD (padrão schema.org) e converte para Evento.

Muitos sites colocam os dados do evento num bloco
<script type="application/ld+json"> para o Google entender a página.
Como o formato é padronizado, a mesma função serve para várias fontes.
"""
import html
import json
import re
from datetime import datetime

from scraper.modelo import FUSO_CEARA, Evento
from scraper.texto import html_para_texto, tipo_pelo_titulo

MODALIDADES = {
    "OfflineEventAttendanceMode": "presencial",
    "OnlineEventAttendanceMode": "online",
    "MixedEventAttendanceMode": "hibrido",
}


def eventos_no_html(pagina: str) -> list[dict]:
    """Devolve os objetos do tipo Event (ou EducationEvent, BusinessEvent...) da página."""
    eventos = []
    blocos = re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', pagina, re.S)
    for bloco in blocos:
        try:
            dados = json.loads(bloco)
        except ValueError:
            continue
        # Um bloco pode ter um objeto, uma lista ou um "@graph" com vários.
        if isinstance(dados, dict):
            dados = dados.get("@graph", [dados])
        for item in dados:
            if isinstance(item, dict) and str(item.get("@type", "")).endswith("Event"):
                eventos.append(item)
    return eventos


def ler_data(texto: str | None) -> datetime | None:
    if not texto:
        return None
    # O Doity manda "2026-11-27-0307:30" (data, fuso -03, hora); aqui vira ISO.
    doity = re.fullmatch(r"(\d{4}-\d{2}-\d{2})-(\d{2})(\d{2}:\d{2})", texto)
    if doity:
        data, fuso, hora = doity.groups()
        texto = f"{data}T{hora}:00-{fuso}:00"
    data = datetime.fromisoformat(texto)
    if data.tzinfo is None:
        data = data.replace(tzinfo=FUSO_CEARA)
    return data.astimezone(FUSO_CEARA)


def converter(dados: dict, fonte: str) -> Evento:
    local = dados.get("location") or {}
    if isinstance(local, list):
        local = local[0] if local else {}
    endereco = local.get("address") or {}
    if isinstance(endereco, str):
        endereco = {"streetAddress": endereco}

    imagem = dados.get("image")
    if isinstance(imagem, list):
        imagem = imagem[0] if imagem else None
    if isinstance(imagem, dict):
        imagem = imagem.get("url")

    organizador = dados.get("organizer") or {}
    if isinstance(organizador, list):
        organizador = organizador[0] if organizador else {}

    nome_local = local.get("name")
    rua = endereco.get("streetAddress")
    # Alguns sites repetem o endereço no nome do local; aí fica só um.
    if nome_local and rua and nome_local.strip(" ,") in rua:
        nome_local = None

    modo = str(dados.get("eventAttendanceMode", "")).rsplit("/", 1)[-1]

    return Evento(
        titulo=" ".join(dados["name"].split()),
        url=dados["url"],
        fonte=fonte,
        tipo=tipo_pelo_titulo(dados["name"]),
        # O Doity às vezes manda o HTML já escapado (&lt;p&gt;), por isso o unescape antes.
        descricao=html_para_texto(html.unescape(dados.get("description") or "")),
        organizador=organizador.get("name") if isinstance(organizador, dict) else None,
        modalidade=MODALIDADES.get(modo),
        cidade=endereco.get("addressLocality"),
        local=", ".join(filter(None, [nome_local, rua])) or None,
        inicio=ler_data(dados.get("startDate")),
        fim=ler_data(dados.get("endDate")),
        url_inscricao=dados["url"],
        imagem=imagem,
    )
