"""Modelo comum de evento.

Todo scraper traduz os dados da sua fonte para um objeto Evento. Assim, o
resto do sistema (deduplicação, banco, API, site) só precisa conhecer um
formato, não importa de onde o evento veio.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone

# Valores aceitos nos campos com opções fixas.
TIPOS = ("hackathon", "meetup", "conferencia", "workshop", "outro")
MODALIDADES = ("presencial", "online", "hibrido")
STATUS = ("pendente", "aprovado")

# O Ceará não tem horário de verão, então um deslocamento fixo de -3h basta.
# (ZoneInfo("America/Fortaleza") exigiria instalar o pacote tzdata no Windows.)
FUSO_CEARA = timezone(timedelta(hours=-3))


def agora() -> datetime:
    """Data e hora atuais no fuso do Ceará."""
    return datetime.now(FUSO_CEARA)


@dataclass
class Evento:
    # Obrigatórios: sem eles a ficha não tem o que mostrar (titulo),
    # não dá para deduplicar (url) nem saber de onde veio (fonte).
    # Na dataclass, campos sem valor padrão precisam vir primeiro.
    titulo: str
    url: str
    fonte: str

    # Opcionais: ficam None quando a fonte não informa.
    tipo: str = "outro"
    descricao: str | None = None
    organizador: str | None = None
    modalidade: str | None = None
    cidade: str | None = None
    local: str | None = None
    inicio: datetime | None = None
    fim: datetime | None = None
    prazo_inscricao: datetime | None = None
    url_inscricao: str | None = None
    imagem: str | None = None  # URL da imagem de capa
    status: str = "pendente"
    # default_factory chama agora() a cada novo evento. Com "= agora()",
    # o horário seria calculado uma única vez e repetido em todos.
    coletado_em: datetime = field(default_factory=agora)

    def __post_init__(self) -> None:
        """Valida a ficha logo ao ser criada, para o erro apontar o scraper culpado."""
        self.titulo = self.titulo.strip()
        self.url = self.url.strip()
        if not self.titulo:
            raise ValueError("evento sem título")
        if not self.url:
            raise ValueError(f"evento sem url: {self.titulo!r}")
        if self.tipo not in TIPOS:
            raise ValueError(f"tipo inválido {self.tipo!r}; use um de {TIPOS}")
        if self.modalidade is not None and self.modalidade not in MODALIDADES:
            raise ValueError(f"modalidade inválida {self.modalidade!r}; use um de {MODALIDADES}")
        if self.status not in STATUS:
            raise ValueError(f"status inválido {self.status!r}; use um de {STATUS}")

    def para_dict(self) -> dict:
        """Converte para dicionário pronto para JSON (datas viram texto ISO 8601)."""
        dados = asdict(self)
        for chave, valor in dados.items():
            if isinstance(valor, datetime):
                dados[chave] = valor.isoformat()
        return dados
