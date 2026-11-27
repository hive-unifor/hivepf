"""Funções de texto usadas por várias fontes: filtro de tecnologia, tipo do
evento e limpeza das descrições."""
import html
import re
import unicodedata

# Palavras sem acento e em minúsculas, comparadas palavra por palavra.
# Ficaram de fora de propósito: "digital" (marketing digital), "data" (datas)
# e "programacao" (em título de evento quase sempre é a programação do evento).
PALAVRAS_TECH = {
    "tecnologia", "tech", "hackathon", "programar", "codigo", "coding", "devops",
    "frontend", "backend", "fullstack", "dev", "devs", "devfest", "gdg",
    "software", "dados", "ia", "ai", "python", "java", "javascript", "react", "cloud",
    "nuvem", "aws", "azure", "stack", "sql", "startup", "startups", "inovacao",
    "ciberseguranca", "blockchain", "robotica", "robo", "computacao", "ux", "web",
    "internet",
}

TIPOS = {
    "hackathon": {"hackathon", "hackaton"},
    "meetup": {"meetup", "encontro", "gdg", "comunidade"},
    "workshop": {"workshop", "oficina", "curso", "imersao", "bootcamp", "treinamento", "aula", "minicurso"},
    "conferencia": {"conferencia", "congresso", "summit", "devfest", "week", "semana", "forum",
                    "roadshow", "festival", "palestra", "talk", "seminario", "simposio", "jornada"},
}


def palavras(texto: str) -> set[str]:
    """'Computação em Nuvem' -> {'computacao', 'em', 'nuvem'}"""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return set(re.findall(r"\w+", sem_acento.lower()))


def eh_tecnologia(texto: str) -> bool:
    return bool(palavras(texto) & PALAVRAS_TECH)


def html_para_texto(conteudo: str | None) -> str | None:
    """Tira as tags HTML mas mantém os parágrafos, um por linha.

    '<p>Oficina</p><p><b>Dia 17</b>: robôs</p>' -> 'Oficina\\nDia 17: robôs'
    """
    if not conteudo:
        return None
    # Fim de parágrafo, quebra de linha e item de lista viram "\n".
    conteudo = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h\d>", "\n", conteudo, flags=re.I)
    conteudo = re.sub(r"<li[^>]*>", "\n• ", conteudo, flags=re.I)
    conteudo = html.unescape(re.sub(r"<[^>]+>", "", conteudo))
    linhas = (" ".join(linha.split()) for linha in conteudo.splitlines())
    texto = "\n".join(linha for linha in linhas if linha)
    return texto or None


def tipo_pelo_titulo(titulo: str, padrao: str = "outro") -> str:
    do_titulo = palavras(titulo)
    for tipo, chaves in TIPOS.items():
        if do_titulo & chaves:
            return tipo
    return padrao
