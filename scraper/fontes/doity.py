"""Fonte Doity: eventos de tecnologia no Ceará.

A listagem (doity.com.br/eventos?estado_id=6) traz só título, área, cidade e
data sem horário. Por isso a coleta é em duas etapas:
1. lê a listagem e separa os eventos de tecnologia pelo título e pela área;
2. abre a página de cada um desses e lê o JSON-LD, que tem os dados completos.
Assim só baixamos a página dos eventos que interessam.

O robots.txt do Doity libera tudo (Allow: /).

Teste isolado: python -m scraper.fontes.doity
"""
from bs4 import BeautifulSoup

from scraper import jsonld
from scraper.modelo import Evento, agora
from scraper.rede import baixar
from scraper.texto import eh_tecnologia

LISTAGEM = "https://doity.com.br/eventos?estado_id=6"  # 6 = Ceará no filtro do site
MAX_PAGINAS = 10


def links_de_tecnologia() -> list[str]:
    links = []
    for pagina in range(1, MAX_PAGINAS + 1):
        sopa = BeautifulSoup(baixar(f"{LISTAGEM}&page={pagina}").text, "html.parser")
        cartoes = [li for li in sopa.find_all("li") if li.find("h2") and li.find("a", href=True)]
        if not cartoes:
            break
        for cartao in cartoes:
            # O primeiro <p> do cartão é a área (ex.: "Tecnologia", "Saúde").
            area = cartao.find("p").get_text(strip=True) if cartao.find("p") else ""
            titulo = cartao.find("h2").get_text(strip=True)
            if eh_tecnologia(f"{titulo} {area}"):
                links.append(cartao.find("a")["href"])
    return links


def coletar() -> list[Evento]:
    eventos = []
    for link in links_de_tecnologia():
        for dados in jsonld.eventos_no_html(baixar(link).text):
            evento = jsonld.converter(dados, "doity")
            termino = evento.fim or evento.inicio
            if termino and termino >= agora():
                eventos.append(evento)
    return eventos


if __name__ == "__main__":
    for evento in coletar():
        print(f"{evento.inicio:%d/%m %H:%M}  {evento.tipo:<11}  {evento.cidade}  {evento.titulo}")
