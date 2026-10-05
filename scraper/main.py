"""Roda todas as fontes, deduplica os eventos por URL e salva o resultado.

Uso (na raiz do projeto):
    python -m scraper.main

Saídas:
- data/eventos.json    eventos da execução atual (sobrescrito a cada vez)
- data/metricas.jsonl  uma linha por execução, para a seção de resultados do relatório
- logs/coleta.log      andamento e erros (fora do Git)
"""
import json
import logging
import time
from pathlib import Path
from types import ModuleType

from scraper.modelo import Evento, agora

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_EVENTOS = RAIZ / "data" / "eventos.json"
ARQUIVO_METRICAS = RAIZ / "data" / "metricas.jsonl"
ARQUIVO_LOG = RAIZ / "logs" / "coleta.log"

# Fontes que rodam na coleta. Para desligar uma, basta comentar a linha.
# Cada módulo precisa ter uma função coletar() que devolve list[Evento].
FONTES: list[ModuleType] = []

log = logging.getLogger("hive")


def configurar_log() -> None:
    """Manda o log para o terminal e para logs/coleta.log ao mesmo tempo."""
    ARQUIVO_LOG.parent.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(ARQUIVO_LOG, encoding="utf-8"),
        ],
    )


def nome_da_fonte(fonte: ModuleType) -> str:
    # "scraper.fontes.sympla" -> "sympla"
    return fonte.__name__.rsplit(".", 1)[-1]


def executar(fontes: list[ModuleType]) -> dict:
    """Coleta de todas as fontes e devolve as métricas da execução."""
    # Sem fontes não há o que medir: para aqui para não gravar métricas vazias.
    if not fontes:
        log.warning("nenhuma fonte configurada em FONTES; nada foi coletado")
        return {}

    inicio = agora()
    cronometro = time.monotonic()
    por_fonte: dict[str, int] = {}
    falhas: list[dict] = []
    # Dicionário com a URL como chave: uma URL repetida não entra de novo.
    eventos: dict[str, Evento] = {}
    duplicatas = 0

    for fonte in fontes:
        nome = nome_da_fonte(fonte)
        # O try fica em volta de cada fonte, não da coleta inteira:
        # uma fonte com erro não pode derrubar as outras.
        try:
            coletados = fonte.coletar()
        except Exception as erro:
            # log.exception grava também o traceback, útil para depurar depois.
            log.exception("%s: falhou", nome)
            falhas.append({"fonte": nome, "erro": f"{type(erro).__name__}: {erro}"})
            continue

        por_fonte[nome] = len(coletados)
        log.info("%s: %d eventos", nome, len(coletados))
        for evento in coletados:
            if evento.url in eventos:
                duplicatas += 1
            else:
                eventos[evento.url] = evento

    total_coletado = sum(por_fonte.values())
    log.info(
        "total: %d coletados, %d duplicatas, %d únicos, %d fontes com falha",
        total_coletado, duplicatas, len(eventos), len(falhas),
    )

    # Se todas as fontes falharam (ex.: sem internet), mantém o arquivo
    # anterior em vez de trocá-lo por uma lista vazia.
    salvou = len(falhas) < len(fontes)
    if salvou:
        salvar_eventos(list(eventos.values()))
    else:
        log.warning("nenhuma fonte funcionou; %s não foi alterado", ARQUIVO_EVENTOS.name)

    metricas = {
        "inicio": inicio.isoformat(timespec="seconds"),
        "duracao_s": round(time.monotonic() - cronometro, 1),
        "por_fonte": por_fonte,
        "falhas": falhas,
        "total_coletado": total_coletado,
        "duplicatas": duplicatas,
        "total_unico": len(eventos),
        "salvou": salvou,
    }
    registrar_metricas(metricas)
    return metricas


def salvar_eventos(eventos: list[Evento]) -> None:
    ARQUIVO_EVENTOS.parent.mkdir(exist_ok=True)
    dados = [evento.para_dict() for evento in eventos]
    # ensure_ascii=False mantém os acentos legíveis; encoding utf-8 é
    # necessário no Windows, que por padrão usa outra codificação.
    ARQUIVO_EVENTOS.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info("%d eventos salvos em %s", len(dados), ARQUIVO_EVENTOS)


def registrar_metricas(metricas: dict) -> None:
    # Modo "a" (append) acrescenta uma linha no fim, preservando o histórico.
    with ARQUIVO_METRICAS.open("a", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(metricas, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    configurar_log()
    executar(FONTES)
