from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.db.database import engine, Base
import app.db.models as models

from app.api.v1.auth import router as auth_router
from app.api.v1.admin import router as admin_router
from app.api.v1.cep import router as cep_router
from app.api.v1.produtos import router as produtos_router
from seed import criar_admin_padrao, sincronizar_catalogo

Base.metadata.create_all(bind=engine)
if "usuarios" in inspect(engine).get_table_names():
    colunas_usuario = {coluna["name"] for coluna in inspect(engine).get_columns("usuarios")}
    if "role" not in colunas_usuario:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'cliente'")
            )
if "produtos" in inspect(engine).get_table_names():
    colunas_produto = {coluna["name"] for coluna in inspect(engine).get_columns("produtos")}
    if "imagem_url" not in colunas_produto:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE produtos ADD COLUMN IF NOT EXISTS imagem_url VARCHAR(500)")
            )
    if "desconto_percentual" not in colunas_produto:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE produtos ADD COLUMN IF NOT EXISTS "
                    "desconto_percentual DOUBLE PRECISION NOT NULL DEFAULT 0"
                )
            )
if "hero_banners" in inspect(engine).get_table_names():
    colunas_banner = {
        coluna["name"] for coluna in inspect(engine).get_columns("hero_banners")
    }
    novas_colunas_banner = {
        "badge": "VARCHAR(100)",
        "titulo": "VARCHAR(200)",
        "subtitulo": "VARCHAR(500)",
        "link": "VARCHAR(500)",
        "texto_botao": "VARCHAR(100)",
    }
    for nome_coluna, tipo_coluna in novas_colunas_banner.items():
        if nome_coluna not in colunas_banner:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        f"ALTER TABLE hero_banners ADD COLUMN IF NOT EXISTS "
                        f"{nome_coluna} {tipo_coluna}"
                    )
                )
criar_admin_padrao()
sincronizar_catalogo()

app = FastAPI(title="WM_Imports API")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api")
app.include_router(cep_router, prefix="/api/v1")
app.include_router(produtos_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"status": "API WM_Imports rodando com sucesso!"}