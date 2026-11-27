"""Fonte Unifor: eventos de tecnologia da agenda unifor.br/eventos.

A agenda mistura todos os cursos, então só ficam os eventos com palavra de
tecnologia no título. Cada cartão traz data ("26 novembro 2026" ou
"De 12 a 13 novembro 2026"), título, local e horário ("8h às 18h").
A primeira página já tem os 20 eventos mais à frente no calendário.

O robots.txt da Unifor libera tudo.

Teste isolado: python -m scraper.fontes.unifor
"""
import re
from datetime import datetime

from bs4 import BeautifulSoup

from scraper.modelo import FUSO_CEARA, Evento, agora
from scraper.rede import baixar
from scraper.texto import eh_tecnologia, tipo_pelo_titulo

AGENDA = "https://unifor.br/eventos"

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


def ler_datas(data: str, horario: str) -> tuple[datetime, datetime | None]:
    """('De 3 a 5 novembro 2026', '8h às 17h') -> (03/11 08:00, 05/11 17:00)"""
    dias = re.findall(r"\d+", data)
    nome_do_mes = re.search(r"([a-zç]+) \d{4}", data.lower()).group(1)
    mes = MESES.index(nome_do_mes) + 1
    ano = int(dias[-1])
    dia_inicio, dia_fim = int(dias[0]), int(dias[-2])

    # "13h30 às 15h10" -> [(13, 30), (15, 10)]; sem horário, começa 00:00.
    horas = [(int(h), int(m or 0)) for h, m in re.findall(r"(\d{1,2})h(\d{2})?", horario)]
    hora_inicio = horas[0] if horas else (0, 0)

    inicio = datetime(ano, mes, dia_inicio, *hora_inicio, tzinfo=FUSO_CEARA)
    fim = None
    if len(horas) > 1 or dia_fim != dia_inicio:
        hora_fim = horas[-1] if len(horas) > 1 else (0, 0)
        fim = datetime(ano, mes, dia_fim, *hora_fim, tzinfo=FUSO_CEARA)
    return inicio, fim


def descricao(url: str) -> str | None:
    """O texto da notícia do evento, parágrafo por parágrafo (os <p> de .asset-content)."""
    sopa = BeautifulSoup(baixar(url).text, "html.parser")
    corpo = sopa.select_one(".asset-content")
    if not corpo:
        return None
    paragrafos = [" ".join(p.get_text(" ").split()) for p in corpo.find_all("p")]
    return "\n".join(p for p in paragrafos if p) or None


def coletar() -> list[Evento]:
    sopa = BeautifulSoup(baixar(AGENDA).text, "html.parser")
    eventos = []
    for cartao in sopa.select("a.card-thumb"):
        titulo = cartao.select_one(".card-thumb__title").get_text(" ", strip=True)
        if not eh_tecnologia(titulo):
            continue

        data = cartao.select_one(".card-thumb__time").get_text(" ", strip=True)
        # O bloco de local tem o lugar e o horário separados por <br>.
        linhas = list(cartao.select_one(".card-thumb__localtime").stripped_strings)
        horario = linhas[-1] if linhas and re.search(r"\d+h", linhas[-1]) else ""
        lugar = linhas[0] if linhas and linhas[0] != horario else None

        inicio, fim = ler_datas(data, horario)
        # Compara só o dia: sem horário, o fim fica 00:00 e o evento
        # sumiria logo no começo do último dia.
        if (fim or inicio).date() < agora().date():
            continue

        imagem = cartao.select_one("img")
        try:
            texto = descricao(cartao["href"])
        except Exception:
            texto = None  # sem a descrição o evento ainda serve
        eventos.append(Evento(
            titulo=titulo,
            url=cartao["href"],
            fonte="unifor",
            tipo=tipo_pelo_titulo(titulo),
            descricao=texto,
            organizador="Unifor",
            modalidade="presencial",
            cidade="Fortaleza",
            local=f"{lugar} - Unifor" if lugar else "Unifor",
            inicio=inicio,
            fim=fim,
            url_inscricao=cartao["href"],
            imagem=imagem["src"] if imagem else None,
        ))
    return eventos


if __name__ == "__main__":
    for evento in coletar():
        print(f"{evento.inicio:%d/%m %H:%M}  {evento.tipo:<11}  {evento.titulo}")
