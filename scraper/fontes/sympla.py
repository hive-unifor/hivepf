"""Fonte Sympla: eventos de tecnologia em Fortaleza.

A Sympla é feita em Next.js e já manda os eventos dentro do HTML, em blocos
<script>self.__next_f.push([1, "..."])</script>. Juntamos esses blocos, lemos
o JSON e ficamos com os objetos que têm nome, url e data de início.

O robots.txt da Sympla libera tudo (Allow: /).

Teste isolado: python -m scraper.fontes.sympla
"""
import json
import re
from datetime import datetime

from scraper.modelo import FUSO_CEARA, Evento, agora
from scraper.rede import baixar
from scraper.texto import eh_tecnologia, html_para_texto, tipo_pelo_titulo

BASE = "https://www.sympla.com.br/eventos/fortaleza-ce"

# Categoria tecnologia: todos os eventos servem. A página principal tem
# seções (destaques, próximos...) e a listagem "todos-eventos" é paginada.
PAGINA_TECNOLOGIA = f"{BASE}/tecnologia"
LISTAGEM_TECNOLOGIA = f"{BASE}/tecnologia/todos-eventos"

# Categorias gerais: só entram eventos com palavra de tecnologia no título.
PAGINAS_GERAIS = [f"{BASE}/congresso-palestra/todos-eventos", f"{BASE}/curso-workshop/todos-eventos"]


def eventos_da_pagina(url: str) -> list[dict]:
    html = baixar(url).text
    pedacos = re.findall(r"self\.__next_f\.push\((\[1,.*?\])\)</script>", html, re.S)
    texto = "".join(json.loads(p)[1] for p in pedacos)

    # O texto junto tem uma linha por bloco, no formato "id:conteudo".
    # Nem toda linha é JSON, então as que derem erro são puladas.
    achados = []
    for linha in texto.split("\n"):
        conteudo = linha.partition(":")[2]
        try:
            procurar_eventos(json.loads(conteudo), achados)
        except ValueError:
            pass
    return achados


def procurar_eventos(obj, achados: list[dict]) -> None:
    """Percorre o JSON inteiro guardando os dicionários com cara de evento.

    Assim não dependemos do nome de cada seção da página.
    """
    if isinstance(obj, dict):
        if "name" in obj and "start_date" in obj and "/evento/" in str(obj.get("url")):
            achados.append(obj)
        filhos = obj.values()
    elif isinstance(obj, list):
        filhos = obj
    else:
        return
    for filho in filhos:
        procurar_eventos(filho, achados)


def eventos_paginados(url: str) -> list[dict]:
    eventos = []
    for pagina in range(1, 6):  # no máximo 5 páginas de 16 eventos
        achados = eventos_da_pagina(f"{url}?page={pagina}")
        if not achados:
            break
        eventos += achados
    return eventos


def converter(bruto: dict) -> Evento:
    local = bruto.get("location") or {}
    endereco = " ".join(filter(None, [local.get("address"), local.get("address_num")]))
    imagens = bruto.get("images") or {}
    return Evento(
        titulo=" ".join(bruto["name"].split()),
        url=bruto["url"],
        fonte="sympla",
        tipo=tipo_pelo_titulo(bruto["name"]),
        organizador=(bruto.get("organizer") or {}).get("name"),
        # Evento online vem sem cidade.
        modalidade="presencial" if local.get("city") else "online",
        cidade=local.get("city") or None,
        local=", ".join(filter(None, [local.get("name"), endereco, local.get("neighborhood")])) or None,
        inicio=datetime.fromisoformat(bruto["start_date"]).astimezone(FUSO_CEARA),
        fim=datetime.fromisoformat(bruto["end_date"]).astimezone(FUSO_CEARA) if bruto.get("end_date") else None,
        url_inscricao=bruto["url"],
        imagem=imagens.get("lg") or imagens.get("original"),
    )


def descricao(url: str) -> str | None:
    """A listagem não traz a descrição; ela fica na página do evento,
    no campo "detail" do bloco __NEXT_DATA__ (em HTML)."""
    pagina = baixar(url).text
    bloco = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', pagina, re.S)
    if not bloco:
        return None
    dados = json.loads(bloco.group(1))
    evento = dados["props"]["pageProps"].get("hydrationData", {}).get("eventHydration", {}).get("event", {})
    return html_para_texto(evento.get("detail"))


def coletar() -> list[Evento]:
    brutos = eventos_da_pagina(PAGINA_TECNOLOGIA) + eventos_paginados(LISTAGEM_TECNOLOGIA)
    for url in PAGINAS_GERAIS:
        brutos += [e for e in eventos_paginados(url) if eh_tecnologia(e["name"])]

    # O mesmo evento aparece em mais de uma página; a URL resolve.
    unicos = {bruto["url"]: bruto for bruto in brutos}

    eventos = []
    for bruto in unicos.values():
        if (bruto.get("location") or {}).get("state") not in (None, "", "CE"):
            continue
        evento = converter(bruto)
        if (evento.fim or evento.inicio) < agora():
            continue  # já terminou
        # Sem a descrição o evento ainda serve; uma página com erro não derruba a fonte.
        try:
            evento.descricao = descricao(evento.url)
        except Exception:
            pass
        eventos.append(evento)

    eventos.sort(key=lambda e: e.inicio)
    return eventos


if __name__ == "__main__":
    for evento in coletar():
        print(f"{evento.inicio:%d/%m %H:%M}  {evento.tipo:<11}  {evento.titulo}")
