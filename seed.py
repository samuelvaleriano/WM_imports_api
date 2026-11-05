import os

from app.db.database import SessionLocal
from app.db.models import (
    Categoria,
    Produto,
    Subcategoria,
    Time,
    Usuario,
    VariacaoProduto,
    TamanhoEnum,
)
from app.core.security import hash_password


CATALOGO_PADRAO = {
    "Brasileiros": {
        "Rio de Janeiro": ["Flamengo", "Fluminense", "Botafogo", "Vasco"],
        "Minas Gerais": ["Atlético MG", "Cruzeiro"],
        "Nordeste": ["Bahia", "Fortaleza"],
        "São Paulo": ["Corinthians", "Palmeiras", "São Paulo", "Santos"],
        "Rio Grande do Sul": ["Internacional", "Grêmio"],
    },
    "Internacionais": {
        "Bundesliga": [
            "Bayer Leverkusen",
            "Bayern de Munique",
            "Borussia Dortmund",
            "RB Leipzig",
        ],
        "La Liga": [
            "Real Madrid",
            "Barcelona",
            "Atlético de Madrid",
            "Real Sociedad",
            "Athletic Bilbao",
            "Sevilla",
            "Valencia",
            "Villarreal",
        ],
        "Ligue 1": ["Lyon", "Mônaco", "PSG", "Marseille"],
        "Premier League": [
            "Arsenal",
            "Chelsea",
            "Everton",
            "Liverpool",
            "Manchester City",
            "Manchester United",
            "Newcastle United",
            "Tottenham",
            "West Ham",
            "Wolverhampton",
            "Aston Villa",
        ],
        "Serie A": ["Inter de Milão", "AC Milan", "Juventus", "Roma", "Napoli"],
        "Libertadores": [],
        "UEFA Champions League": [],
        "Resto do Mundo": [],
    },
    "Seleções": {
        "África": [],
        "América Sul/Norte": [],
        "Ásia": [],
        "Europa": [],
    },
    "Retrô": {},
    "Femininas": {},
}


def _slugify(value):
    import re
    import unicodedata

    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]+", "-", without_accents.lower()).strip("-")


def _time_slug(nome):
    if nome == "São Paulo":
        return "sao-paulo-fc"
    return _slugify(nome)


def sincronizar_catalogo():
    db = SessionLocal()
    try:
        times_existentes = {
            time.nome: time for time in db.query(Time).all()
        }

        for categoria_nome, subcategorias in CATALOGO_PADRAO.items():
            categoria = (
                db.query(Categoria)
                .filter(Categoria.slug == _slugify(categoria_nome))
                .first()
            )
            if categoria is None:
                categoria = Categoria(
                    nome=categoria_nome,
                    slug=_slugify(categoria_nome),
                )
                db.add(categoria)
                db.flush()
            elif categoria.nome != categoria_nome:
                categoria.nome = categoria_nome

            for subcategoria_nome, nomes_times in subcategorias.items():
                subcategoria = (
                    db.query(Subcategoria)
                    .filter(Subcategoria.slug == _slugify(subcategoria_nome))
                    .first()
                )
                if subcategoria is None:
                    subcategoria = Subcategoria(
                        categoria_id=categoria.id,
                        nome=subcategoria_nome,
                        slug=_slugify(subcategoria_nome),
                    )
                    db.add(subcategoria)
                    db.flush()
                else:
                    subcategoria.nome = subcategoria_nome
                    subcategoria.categoria_id = categoria.id

                for time_nome in nomes_times:
                    time = times_existentes.get(time_nome)
                    if time is None:
                        time = Time(
                            subcategoria_id=subcategoria.id,
                            nome=time_nome,
                            slug=_time_slug(time_nome),
                        )
                        db.add(time)
                        db.flush()
                        times_existentes[time_nome] = time
                    else:
                        time.subcategoria_id = subcategoria.id
                        time.slug = _time_slug(time_nome)

        for subcategoria in (
            db.query(Subcategoria)
            .filter(Subcategoria.slug == "clubes-nacionais")
            .all()
        ):
            if not db.query(Time).filter(Time.subcategoria_id == subcategoria.id).first():
                db.delete(subcategoria)

        for categoria in db.query(Categoria).filter(Categoria.slug == "futebol").all():
            if not db.query(Subcategoria).filter(
                Subcategoria.categoria_id == categoria.id
            ).first():
                db.delete(categoria)

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def criar_admin_padrao():
    email = os.getenv("ADMIN_EMAIL", "admin@wmimports.com")
    senha = os.getenv("ADMIN_PASSWORD", "Admin@123456")
    nome = os.getenv("ADMIN_NAME", "Administrador")

    db = SessionLocal()
    try:
        admin = db.query(Usuario).filter(Usuario.email == email).first()
        if admin is None:
            db.add(
                Usuario(
                    nome=nome,
                    email=email,
                    hashed_password=hash_password(senha),
                    role="admin",
                )
            )
            db.commit()
        elif admin.role != "admin":
            admin.role = "admin"
            db.commit()
    finally:
        db.close()

def popular_banco():
    db = SessionLocal()
    try:
        cat_futebol = Categoria(nome="Futebol", slug="futebol")
        db.add(cat_futebol)
        db.commit()

        sub_nacionais = Subcategoria(categoria_id=cat_futebol.id, nome="Clubes Nacionais", slug="clubes-nacionais")
        db.add(sub_nacionais)
        db.commit()

        flamengo = Time(subcategoria_id=sub_nacionais.id, nome="Flamengo", slug="flamengo", escudo_url="https://via.placeholder.com/150")
        db.add(flamengo)
        db.commit()

        camisa = Produto(
            time_id=flamengo.id,
            nome="Camisa Flamengo I 24/25 - Torcedor",
            descricao="Camisa oficial do Mengão",
            preco=349.90,
            imagem_capa="https://via.placeholder.com/300",
            ativo=True
        )
        db.add(camisa)
        db.commit()

        var_g = VariacaoProduto(produto_id=camisa.id, tamanho=TamanhoEnum.G, estoque=10)
        var_gg = VariacaoProduto(produto_id=camisa.id, tamanho=TamanhoEnum.GG, estoque=5)
        db.add_all([var_g, var_gg])
        db.commit()

        print("Dados de teste inseridos com sucesso!")
    except Exception as e:
        print(f"Erro ao popular banco: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    popular_banco()