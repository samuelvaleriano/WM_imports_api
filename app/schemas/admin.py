from pydantic import BaseModel, Field, HttpUrl


class CampanhaBanner(BaseModel):
    id: int | None = None
    imagem_url: HttpUrl
    frase_promocional: str = Field(min_length=1, max_length=200)
    badge: str | None = Field(default=None, max_length=100)
    titulo: str | None = Field(default=None, max_length=200)
    subtitulo: str | None = Field(default=None, max_length=500)
    link: str | None = Field(default=None, max_length=500)
    texto_botao: str | None = Field(default=None, max_length=100)


class AtualizarBanners(BaseModel):
    campanhas: list[CampanhaBanner]


class HeroBannerResponse(BaseModel):
    campanhas: list[CampanhaBanner]
