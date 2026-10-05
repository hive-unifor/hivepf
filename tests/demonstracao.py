"""Demonstração da base da coleta, passo a passo, com explicações na tela.

Uso (na raiz do projeto, com o .venv ativado):
    python -m tests.demonstracao

Usa fontes de mentira e grava os arquivos numa pasta temporária,
então a pasta data/ do projeto não é alterada.
"""
import json
import tempfile
from pathlib import Path
from types import ModuleType

import scraper.main as main
from scraper.modelo import Evento
from scraper.rede import baixar


def titulo(texto: str) -> None:
    print("\n" + "=" * 60)
    print(texto)
    print("=" * 60)


# ---------------------------------------------------------------------------
titulo("PARTE 1 - O formulário padrão (modelo.py)")

print("Criando uma ficha de evento correta...")
ficha = Evento(
    titulo="Hackathon de Exemplo",
    url="https://exemplo.com/hackathon",
    fonte="demonstracao",
    tipo="hackathon",
    cidade="Fortaleza",
)
print("Ficha criada. Veja como ela fica (repare em status e coletado_em,")
print("que foram preenchidos sozinhos, e nos campos vazios = None):")
print(json.dumps(ficha.para_dict(), ensure_ascii=False, indent=2))

print("\nAgora tentando criar uma ficha com tipo errado ('Hackathon' com H maiúsculo)...")
try:
    Evento(titulo="Ficha errada", url="https://exemplo.com/x", fonte="demonstracao", tipo="Hackathon")
except ValueError as erro:
    print("O formulário recusou, como esperado. Motivo:", erro)

# ---------------------------------------------------------------------------
titulo("PARTE 2 - As regras de educação (rede.py)")

print("Baixando uma página de teste (httpbin.org) que responde com o")
print("nome que o nosso programa usou para se apresentar...")
try:
    resposta = baixar("https://httpbin.org/user-agent")
    print("O site recebeu:", resposta.json()["user-agent"])
except Exception as erro:
    print("Não deu para acessar a internet agora:", erro)

# ---------------------------------------------------------------------------
titulo("PARTE 3 - O recepcionista em ação (main.py)")

# Três "mensageiros" de mentira. Um deles traz um evento repetido
# e outro sempre dá erro, para vermos como o main.py reage.
def coletar_mensageiro_1():
    return [
        Evento(titulo="Hackathon do Porto", url="https://exemplo.com/1", fonte="mensageiro_1", tipo="hackathon"),
        Evento(titulo="Meetup de Python", url="https://exemplo.com/2", fonte="mensageiro_1", tipo="meetup"),
    ]

def coletar_mensageiro_2():
    return [
        Evento(titulo="Hackathon do Porto (repetido)", url="https://exemplo.com/1", fonte="mensageiro_2"),
        Evento(titulo="Workshop de Git", url="https://exemplo.com/3", fonte="mensageiro_2", tipo="workshop"),
    ]

def coletar_mensageiro_perdido():
    raise ConnectionError("o site está fora do ar")

def criar_fonte(nome, funcao):
    fonte = ModuleType(f"scraper.fontes.{nome}")
    fonte.coletar = funcao
    return fonte

fontes = [
    criar_fonte("mensageiro_1", coletar_mensageiro_1),
    criar_fonte("mensageiro_perdido", coletar_mensageiro_perdido),
    criar_fonte("mensageiro_2", coletar_mensageiro_2),
]

# Desvia os arquivos de saída para uma pasta temporária.
pasta = Path(tempfile.mkdtemp(prefix="hive-demo-"))
main.ARQUIVO_EVENTOS = pasta / "eventos.json"
main.ARQUIVO_METRICAS = pasta / "metricas.jsonl"
main.ARQUIVO_LOG = pasta / "coleta.log"
main.configurar_log()

print("O que esperar:")
print("- mensageiro_1 traz 2 eventos;")
print("- mensageiro_perdido dá erro, mas NÃO pode parar a coleta;")
print("- mensageiro_2 traz 2 eventos, sendo 1 repetido do mensageiro_1;")
print("- resultado final: 3 eventos únicos.\n")
print("Log do recepcionista (o texto grande de erro é proposital):\n")

metricas = main.executar(fontes)

eventos = json.loads(main.ARQUIVO_EVENTOS.read_text(encoding="utf-8"))
print("\nEventos guardados no arquivo final:")
for evento in eventos:
    print(f"  - {evento['titulo']} ({evento['tipo']}) vindo de {evento['fonte']}")

print("\nAnotações do caderno (métricas desta execução):")
print(json.dumps(metricas, ensure_ascii=False, indent=2))

# ---------------------------------------------------------------------------
titulo("CONFERINDO O RESULTADO")
ok = len(eventos) == 3 and metricas["duplicatas"] == 1 and len(metricas["falhas"]) == 1
print("Tudo como esperado!" if ok else "ALGO DEU DIFERENTE do esperado, veja acima.")
print("Arquivos gerados (pode abrir para olhar):", pasta)
