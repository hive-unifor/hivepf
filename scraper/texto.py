"""Funções de texto usadas por várias fontes: filtro de tecnologia e tipo do evento."""
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


def tipo_pelo_titulo(titulo: str, padrao: str = "outro") -> str:
    do_titulo = palavras(titulo)
    for tipo, chaves in TIPOS.items():
        if do_titulo & chaves:
            return tipo
    return padrao
